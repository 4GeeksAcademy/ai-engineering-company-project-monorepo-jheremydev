from threading import Lock
from time import monotonic
from typing import Callable, Generic, Optional, TypeVar

from fastapi import APIRouter, HTTPException, Query

from models.inventory import (
	Articulo,
	ArticuloCreate,
	Local,
	LocalCreate,
	Movimiento,
	MovimientoCreate,
	StockResponse,
)
from storage import inventory as storage
from storage import telemetry


router = APIRouter(prefix="/inventory", tags=["inventory"])

ARTICLES_CACHE_TTL_SECONDS = 300
LOCALS_CACHE_TTL_SECONDS = 900

T = TypeVar("T")


class _TTLCache(Generic[T]):
	def __init__(self, ttl_seconds: int) -> None:
		self._ttl_seconds = ttl_seconds
		self._entry: Optional[tuple[float, T]] = None
		self._generation = 0
		self._lock = Lock()

	def get_or_load(self, loader: Callable[[], T]) -> T:
		with self._lock:
			now = monotonic()
			if self._entry is not None and self._entry[0] > now:
				return self._entry[1]
			generation = self._generation

		value = loader()

		with self._lock:
			if generation == self._generation:
				self._entry = (monotonic() + self._ttl_seconds, value)
		return value

	def invalidate(self) -> None:
		with self._lock:
			self._generation += 1
			self._entry = None


_articles_cache: _TTLCache[list[Articulo]] = _TTLCache(ARTICLES_CACHE_TTL_SECONDS)
_locals_cache: _TTLCache[list[Local]] = _TTLCache(LOCALS_CACHE_TTL_SECONDS)


@router.post("/locals", response_model=Local, status_code=201)
def create_local(payload: LocalCreate) -> Local:
	local = storage.create_local(payload)
	_locals_cache.invalidate()
	telemetry.emit(
		"inventory.local_created",
		{"localId": local.id, **telemetry.form_attempt_property()},
	)
	return local


@router.get("/locals", response_model=list[Local])
def list_locals() -> list[Local]:
	return _locals_cache.get_or_load(storage.list_locals)


@router.post("/articles", response_model=Articulo, status_code=201)
def create_article(payload: ArticuloCreate) -> Articulo:
	article = storage.create_article(payload)
	_articles_cache.invalidate()
	reorder_point = telemetry.decimal_string(article.punto_reorden)
	if reorder_point is not None:
		telemetry.emit(
			"inventory.article_created",
			{
				"articleId": article.id,
				"category": article.categoria.value,
				"unit": article.unidad_medida.value,
				"reorderPoint": reorder_point,
				**telemetry.form_attempt_property(),
			},
		)
	return article


@router.get("/articles", response_model=list[Articulo])
def list_articles() -> list[Articulo]:
	return _articles_cache.get_or_load(storage.list_articles)


def _find_article(article_id: str) -> Articulo:
	article = storage.find_article(article_id)
	if article is None:
		raise HTTPException(status_code=404, detail="Artículo no encontrado")
	return article


@router.get("/articles/{article_id}", response_model=Articulo)
def get_article(article_id: str) -> Articulo:
	return _find_article(article_id)


@router.post("/movements", response_model=Movimiento, status_code=201)
def create_movement(payload: MovimientoCreate) -> Movimiento:
	movement_type = payload.tipo.value
	form_attempt = telemetry.form_attempt_property()
	try:
		movement = storage.register_movement(payload)
	except (storage.ArticleNotFoundError, storage.LocalNotFoundError) as error:
		telemetry.emit(
			"inventory.movement_reference_rejected",
			{
				"httpStatus": 404,
				"missingEntity": "article" if isinstance(error, storage.ArticleNotFoundError) else "local",
				"movementType": movement_type,
				**form_attempt,
			},
		)
		raise HTTPException(status_code=404, detail=str(error)) from error
	except storage.NegativeStockError as error:
		_emit_negative_stock_rejected(payload, form_attempt)
		raise HTTPException(status_code=409, detail=str(error)) from error

	article = storage.find_article(movement.articulo_id)
	quantity = telemetry.decimal_string(movement.cantidad)
	stock_after = telemetry.decimal_string(storage.calculate_stock(movement.articulo_id, movement.local))
	if article is not None and quantity is not None and stock_after is not None:
		telemetry.emit(
			"inventory.movement_created",
			{
				"httpStatus": 201,
				"movementId": movement.id,
				"articleId": movement.articulo_id,
				"localId": movement.local,
				"movementType": movement_type,
				"quantity": quantity,
				"stockAfter": stock_after,
				"unit": article.unidad_medida.value,
				**form_attempt,
			},
		)
	return movement


def _emit_negative_stock_rejected(payload: MovimientoCreate, form_attempt: dict[str, str]) -> None:
	article = storage.find_article(payload.articulo_id)
	quantity = telemetry.decimal_string(payload.cantidad)
	stock_before = telemetry.decimal_string(storage.calculate_stock(payload.articulo_id, payload.local))
	if article is None or quantity is None or stock_before is None:
		return
	telemetry.emit(
		"inventory.movement_negative_stock_rejected",
		{
			"httpStatus": 409,
			"articleId": payload.articulo_id,
			"localId": payload.local,
			"movementType": payload.tipo.value,
			"quantity": quantity,
			"stockBefore": stock_before,
			"unit": article.unidad_medida.value,
			**form_attempt,
		},
	)


@router.get("/movements", response_model=list[Movimiento])
def list_movements(
	articulo_id: Optional[str] = None,
	local: Optional[str] = None,
) -> list[Movimiento]:
	if articulo_id is not None and storage.find_article(articulo_id) is None:
		raise HTTPException(status_code=404, detail="Artículo no encontrado")
	if local is not None and storage.find_local(local) is None:
		raise HTTPException(status_code=404, detail="Local no encontrado")
	return storage.list_movements(articulo_id=articulo_id, local=local)


@router.get("/movements/{movement_id}", response_model=Movimiento)
def get_movement(movement_id: str) -> Movimiento:
	movement = storage.find_movement(movement_id)
	if movement is None:
		raise HTTPException(status_code=404, detail="Movimiento no encontrado")
	return movement


@router.get("/stock", response_model=StockResponse)
def get_stock(
	articulo_id: str = Query(min_length=1),
	local: str = Query(min_length=1),
) -> StockResponse:
	article = _find_article(articulo_id)
	if storage.find_local(local) is None:
		raise HTTPException(status_code=404, detail="Local no encontrado")
	stock = storage.calculate_stock(article.id, local)
	below_reorder_point = stock < article.punto_reorden
	if below_reorder_point:
		stock_text = telemetry.decimal_string(stock)
		reorder_point = telemetry.decimal_string(article.punto_reorden)
		if stock_text is not None and reorder_point is not None:
			telemetry.emit(
				"inventory.reorder_signal_active",
				{
					"articleId": article.id,
					"localId": local,
					"stock": stock_text,
					"reorderPoint": reorder_point,
					"unit": article.unidad_medida.value,
					"belowReorderPoint": True,
				},
			)
	return StockResponse(
		articulo_id=article.id,
		local=local,
		stock=stock,
		unidad_medida=article.unidad_medida.value,
		punto_reorden=article.punto_reorden,
		bajo_punto_reorden=below_reorder_point,
	)

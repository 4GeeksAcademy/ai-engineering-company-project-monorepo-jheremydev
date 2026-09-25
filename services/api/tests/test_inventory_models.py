import unittest
from datetime import datetime
from decimal import Decimal

from pydantic import ValidationError

from models.inventory import (
    Articulo,
    ArticuloCreate,
    CategoriaArticulo,
    Movimiento,
    MovimientoCreate,
    TipoMovimiento,
)


class InventoryModelTests(unittest.TestCase):
    def test_article_accepts_all_categories_and_simple_units(self) -> None:
        for category in CategoriaArticulo:
            with self.subTest(category=category):
                article = ArticuloCreate(
                    nombre="Tomate",
                    categoria=category,
                    unidad_medida="kg",
                )
                self.assertEqual(article.categoria, category)

    def test_persisted_article_requires_id(self) -> None:
        with self.assertRaises(ValidationError):
            Articulo(
                nombre="Tomate",
                categoria=CategoriaArticulo.VERDURAS,
                unidad_medida="kg",
            )

    def test_article_rejects_invalid_category_and_empty_required_fields(self) -> None:
        with self.assertRaises(ValidationError):
            ArticuloCreate(
                nombre="Tomate",
                categoria="frutas",
                unidad_medida="kg",
            )

        valid_payload = {
            "nombre": "Tomate",
            "categoria": CategoriaArticulo.VERDURAS,
            "unidad_medida": "kg",
        }
        for field in ("nombre", "categoria", "unidad_medida"):
            with self.subTest(field=field):
                payload = valid_payload.copy()
                del payload[field]
                with self.assertRaises(ValidationError):
                    ArticuloCreate(**payload)

        with self.assertRaises(ValidationError):
            ArticuloCreate(
                nombre="   ",
                categoria=CategoriaArticulo.VERDURAS,
                unidad_medida="kg",
            )

    def test_movement_accepts_types_decimal_quantities_and_optional_reason(self) -> None:
        for movement_type, quantity in (
            (TipoMovimiento.ENTRADA, Decimal("2.75")),
            (TipoMovimiento.SALIDA, Decimal("1.25")),
            (TipoMovimiento.AJUSTE, Decimal("3.50")),
            (TipoMovimiento.AJUSTE, Decimal("-0.50")),
        ):
            with self.subTest(movement_type=movement_type, quantity=quantity):
                movement = MovimientoCreate(
                    articulo_id="article-1",
                    local="Brasaland Norte",
                    tipo=movement_type,
                    cantidad=quantity,
                    autor="operador",
                    fecha=datetime(2026, 9, 25, 12, 0),
                )
                self.assertEqual(movement.cantidad, quantity)
                self.assertIsNone(movement.motivo)

        with_reason = self.valid_movement_payload(motivo="Inventario inicial")
        self.assertEqual(MovimientoCreate(**with_reason).motivo, "Inventario inicial")

    def test_persisted_movement_requires_id(self) -> None:
        with self.assertRaises(ValidationError):
            Movimiento(**self.valid_movement_payload())

    def test_movement_rejects_invalid_type_and_invalid_quantity_sign(self) -> None:
        with self.assertRaises(ValidationError):
            MovimientoCreate(**self.valid_movement_payload(tipo="transferencia"))

        for movement_type, quantity in (
            (TipoMovimiento.ENTRADA, Decimal("-1")),
            (TipoMovimiento.SALIDA, Decimal("0")),
            (TipoMovimiento.AJUSTE, Decimal("0")),
            (TipoMovimiento.ENTRADA, Decimal("NaN")),
            (TipoMovimiento.ENTRADA, Decimal("Infinity")),
        ):
            with self.subTest(movement_type=movement_type, quantity=quantity):
                with self.assertRaises(ValidationError):
                    MovimientoCreate(
                        **self.valid_movement_payload(
                            tipo=movement_type,
                            cantidad=quantity,
                        )
                    )

    def test_movement_requires_identifiers_type_quantity_author_and_date(self) -> None:
        valid_payload = self.valid_movement_payload()
        for field in ("articulo_id", "local", "tipo", "cantidad", "autor", "fecha"):
            with self.subTest(field=field):
                payload = valid_payload.copy()
                del payload[field]
                with self.assertRaises(ValidationError):
                    MovimientoCreate(**payload)

        for field in ("local", "autor"):
            with self.subTest(empty_field=field):
                payload = valid_payload.copy()
                payload[field] = "   "
                with self.assertRaises(ValidationError):
                    MovimientoCreate(**payload)

    @staticmethod
    def valid_movement_payload(**overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "articulo_id": "article-1",
            "local": "Brasaland Norte",
            "tipo": TipoMovimiento.ENTRADA,
            "cantidad": Decimal("2.5"),
            "autor": "operador",
            "fecha": datetime(2026, 9, 25, 12, 0),
        }
        payload.update(overrides)
        return payload


if __name__ == "__main__":
    unittest.main()

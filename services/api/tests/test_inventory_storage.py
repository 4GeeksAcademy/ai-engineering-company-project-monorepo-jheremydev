import unittest
from datetime import datetime
from decimal import Decimal

from models.inventory import (
    ArticuloCreate,
    LocalCreate,
    MovimientoCreate,
    TipoMovimiento,
)
from storage import inventory


class InventoryStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        inventory.articulos.clear()
        inventory.locales.clear()
        inventory.movimientos.clear()

    def create_article(self, name: str = "Tomate") -> str:
        article = inventory.create_article(
            ArticuloCreate(
                nombre=name,
                categoria="verduras",
                unidad_medida="kg",
            )
        )
        return article.id

    def create_local(self, name: str = "Local de prueba") -> str:
        local = inventory.create_local(LocalCreate(nombre=name))
        return local.id

    def register_movement(
        self,
        article_id: str,
        local_id: str,
        movement_type: TipoMovimiento,
        quantity: Decimal,
    ):
        return inventory.register_movement(
            MovimientoCreate(
                articulo_id=article_id,
                local=local_id,
                tipo=movement_type,
                cantidad=quantity,
                autor="operador",
                fecha=datetime(2026, 9, 25, 12, 0),
            )
        )

    def test_stock_is_zero_without_movements(self) -> None:
        article_id = self.create_article()
        local_id = self.create_local()

        self.assertEqual(
            inventory.calculate_stock(article_id, local_id),
            Decimal("0"),
        )

    def test_article_operations_create_find_and_list(self) -> None:
        first_id = self.create_article("Tomate")
        second_id = self.create_article("Lechuga")

        self.assertNotEqual(first_id, second_id)
        self.assertEqual(len(inventory.list_articles()), 2)
        self.assertEqual(inventory.find_article(first_id).nombre, "Tomate")
        self.assertIsNone(inventory.find_article("missing-article"))

    def test_local_operations_create_find_and_list(self) -> None:
        first_id = self.create_local("Local Norte")
        second_id = self.create_local("Local Sur")

        self.assertNotEqual(first_id, second_id)
        self.assertEqual(len(inventory.list_locals()), 2)
        self.assertEqual(inventory.find_local(first_id).nombre, "Local Norte")
        self.assertIsNone(inventory.find_local("missing-local"))

    def test_stock_is_isolated_by_article_and_local(self) -> None:
        first_id = self.create_article("Tomate")
        second_id = self.create_article("Lechuga")
        local_1_id = self.create_local("Local Norte")
        local_2_id = self.create_local("Local Sur")
        self.register_movement(
            first_id, local_1_id, TipoMovimiento.ENTRADA, Decimal("10")
        )
        self.register_movement(
            second_id, local_1_id, TipoMovimiento.ENTRADA, Decimal("40")
        )
        self.register_movement(
            first_id, local_2_id, TipoMovimiento.ENTRADA, Decimal("25")
        )

        self.assertEqual(
            inventory.calculate_stock(first_id, local_1_id), Decimal("10")
        )
        self.assertEqual(
            inventory.calculate_stock(second_id, local_1_id), Decimal("40")
        )
        self.assertEqual(
            inventory.calculate_stock(first_id, local_2_id), Decimal("25")
        )

    def test_entries_add_and_exits_subtract_decimal_quantities(self) -> None:
        article_id = self.create_article()
        local_id = self.create_local()
        entry = self.register_movement(
            article_id,
            local_id,
            TipoMovimiento.ENTRADA,
            Decimal("10.75"),
        )
        exit_movement = self.register_movement(
            article_id,
            local_id,
            TipoMovimiento.SALIDA,
            Decimal("2.25"),
        )

        self.assertEqual(entry.cantidad, Decimal("10.75"))
        self.assertEqual(exit_movement.cantidad, Decimal("2.25"))
        self.assertEqual(
            inventory.calculate_stock(article_id, local_id),
            Decimal("8.50"),
        )

    def test_adjustments_apply_their_positive_or_negative_sign(self) -> None:
        article_id = self.create_article()
        local_id = self.create_local()
        self.register_movement(
            article_id,
            local_id,
            TipoMovimiento.AJUSTE,
            Decimal("5.5"),
        )
        self.register_movement(
            article_id,
            local_id,
            TipoMovimiento.AJUSTE,
            Decimal("-1.25"),
        )

        self.assertEqual(
            inventory.calculate_stock(article_id, local_id),
            Decimal("4.25"),
        )

    def test_movements_can_be_listed_and_found(self) -> None:
        article_id = self.create_article()
        local_1_id = self.create_local("Local Norte")
        local_2_id = self.create_local("Local Sur")
        first_movement = self.register_movement(
            article_id,
            local_1_id,
            TipoMovimiento.ENTRADA,
            Decimal("3"),
        )
        self.register_movement(
            article_id,
            local_2_id,
            TipoMovimiento.ENTRADA,
            Decimal("7"),
        )

        self.assertEqual(len(inventory.list_movements()), 2)
        self.assertEqual(
            inventory.list_movements(articulo_id=article_id, local=local_1_id),
            [first_movement],
        )
        self.assertEqual(
            inventory.find_movement(first_movement.id), first_movement
        )
        self.assertIsNone(inventory.find_movement("missing-movement"))

    def test_register_rejects_unknown_article_without_changing_history(self) -> None:
        local_id = self.create_local()
        movement_payload = MovimientoCreate(
            articulo_id="missing-article",
            local=local_id,
            tipo=TipoMovimiento.ENTRADA,
            cantidad=Decimal("1"),
            autor="operador",
            fecha=datetime(2026, 9, 25, 12, 0),
        )

        with self.assertRaises(inventory.ArticleNotFoundError):
            inventory.register_movement(movement_payload)

        self.assertEqual(inventory.movimientos, [])

    def test_register_rejects_unknown_local_without_changing_history(self) -> None:
        article_id = self.create_article()
        movement_payload = MovimientoCreate(
            articulo_id=article_id,
            local="missing-local",
            tipo=TipoMovimiento.ENTRADA,
            cantidad=Decimal("1"),
            autor="operador",
            fecha=datetime(2026, 9, 25, 12, 0),
        )

        with self.assertRaises(inventory.LocalNotFoundError):
            inventory.register_movement(movement_payload)

        self.assertEqual(inventory.movimientos, [])

    def test_negative_exit_or_adjustment_preserves_stock_and_history(self) -> None:
        article_id = self.create_article()
        local_id = self.create_local()
        self.register_movement(
            article_id,
            local_id,
            TipoMovimiento.ENTRADA,
            Decimal("5.5"),
        )
        previous_history = inventory.list_movements()

        for movement_type, quantity in (
            (TipoMovimiento.SALIDA, Decimal("5.51")),
            (TipoMovimiento.AJUSTE, Decimal("-5.51")),
        ):
            with self.subTest(movement_type=movement_type):
                with self.assertRaises(inventory.NegativeStockError):
                    self.register_movement(
                        article_id,
                        local_id,
                        movement_type,
                        quantity,
                    )
                self.assertEqual(inventory.list_movements(), previous_history)
                self.assertEqual(
                    inventory.calculate_stock(article_id, local_id),
                    Decimal("5.5"),
                )


if __name__ == "__main__":
    unittest.main()
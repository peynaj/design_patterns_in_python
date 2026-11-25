"""
Composite
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional
import pytest


# === Exceptions ===

class NegativePrice(Exception):
    ...


class ParentExists(Exception):
    ...


class ForbiddenChild(Exception):
    ...


class DuplicateProduct(Exception):
    ...


class ChildNotFound(Exception):
    ...


# === Composite Structure===

class ProductComponent(ABC):
    _parent: Optional["ProductComponent"]

    @abstractmethod
    def calculate_price(self) -> Decimal:
        ...

    @abstractmethod
    def get_products(self) -> list["ProductComponent"]:
        ...

    @property
    def parent(self) -> Optional["ProductComponent"]:
        return getattr(self, "_parent", None)

    def _set_parent(self, _parent: Optional["ProductComponent"]):
        if _parent is not None and getattr(self, "_parent", None) is not None:
            raise ParentExists
        setattr(self, "_parent", _parent)


class SimpleProduct(ProductComponent):
    id: int
    name: str
    _price: Decimal

    def __init__(self, id: int, name: str, price: Decimal):
        self._validate_price(price)

        self.id = id
        self.name = name
        self._price = price

    @staticmethod
    def _validate_price(price: Decimal):
        if not isinstance(price, Decimal):
            raise TypeError("price must be Decimal")
        if price < 0:
            raise NegativePrice
        if not price.is_finite():
            raise ValueError("price must be finite")

    @property
    def price(self) -> Decimal:
        return self._price

    @price.setter
    def price(self, price: Decimal):
        self._validate_price(price)
        self._price = price

    def calculate_price(self) -> Decimal:
        return self.price

    def get_products(self) -> list["ProductComponent"]:
        return [self]


class ProductBundle(ProductComponent):
    id: int
    name: str
    children: set[ProductComponent]

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.children = set()

    def contains(self, target: ProductComponent) -> bool:
        if self is target:
            return True

        return any(
            isinstance(child, ProductBundle)
            and child.contains(target)
            for child in self.children
        )

    def add(self, product: ProductComponent):
        self._validate_new_child(product)
        self.children.add(product)
        product._set_parent(self)

    def _validate_new_child(self, product: ProductComponent):
        if isinstance(product, ProductBundle) and product.contains(self):
            raise ForbiddenChild

        if product in self.children:
            raise DuplicateProduct

        if product.parent is not None:
            raise ParentExists

    def remove(self, product: ProductComponent):
        if product not in self.children:
            raise ChildNotFound

        self.children.remove(product)
        product._set_parent(None)

    def calculate_price(self) -> Decimal:
        return sum((child.calculate_price() for child in self.children), Decimal("0"))

    def get_products(self) -> list[ProductComponent]:
        return [
            product
            for child in self.children
            for product in child.get_products()
        ]


# === Tests ===

class TestProductComposite:

    def test_empty_bundle(self):
        b = ProductBundle(1, "bundle 1")
        assert b.calculate_price() == Decimal("0")

    def test_simple_product(self):
        price = Decimal("5")
        p = SimpleProduct(1, "product 1", price)
        assert p.calculate_price() == price

    def test_bundle_with_two_product(self):
        b = ProductBundle(1, "bundle 1")
        price_1 = Decimal("1.5")
        price_2 = Decimal("5.75")
        b.add(SimpleProduct(2, "product 2", price_1))
        b.add(SimpleProduct(3, "product 3", price_2))
        assert b.calculate_price() == sum([price_1, price_2])

    def test_nested_bundle_with(self):
        b1 = ProductBundle(1, "bundle 1")
        price_1 = Decimal("1.5")
        price_2 = Decimal("5.75")
        price_3 = Decimal("1.35")
        b1.add(SimpleProduct(2, "product 2", price_1))
        b1.add(SimpleProduct(3, "product 3", price_2))

        b2 = ProductBundle(2, "bundle 2")
        b2.add(SimpleProduct(3, "p3", price_3))

        b = ProductBundle(3, "b3")
        b.add(b1)
        b.add(b2)

        assert b.calculate_price() == sum([price_1, price_2, price_3])

    def test_get_products(self):
        b1 = ProductBundle(1, "bundle 1")
        price_1 = Decimal("1.5")
        p1 = SimpleProduct(2, "product 2", price_1)
        b1.add(p1)
        price_2 = Decimal("5.75")
        p2 = SimpleProduct(3, "product 3", price_2)
        b1.add(p2)

        b2 = ProductBundle(2, "bundle 2")
        price_3 = Decimal("1.35")
        p3 = SimpleProduct(3, "p3", price_3)
        b2.add(p3)

        b = ProductBundle(3, "b3")
        b.add(b1)
        b.add(b2)

        products = b.get_products()
        assert len(products) == 3
        assert p1 in products
        assert p2 in products
        assert p3 in products

    def test_negative_price(self):
        with pytest.raises(NegativePrice):
            SimpleProduct(1, "p1", Decimal("-9.95"))

    def test_adding_self(self):
        b1 = ProductBundle(1, "bundle 1")
        with pytest.raises(ForbiddenChild):
            b1.add(b1)

    def test_cycle(self):
        a = ProductBundle(1, "A")
        b = ProductBundle(2, "B")
        c = ProductBundle(3, "C")

        a.add(b)
        b.add(c)

        with pytest.raises(ForbiddenChild):
            c.add(a)

    def test_duplicate_child(self):
        b = ProductBundle(1, "bundle 1")
        price_1 = Decimal("1.5")
        p = SimpleProduct(1, "product 1", price_1)
        b.add(p)

        with pytest.raises(DuplicateProduct):
            b.add(p)

    def test_price_after_remove_child(self):
        b = ProductBundle(1, "bundle 1")
        price_1 = Decimal("1.5")
        price_2 = Decimal("5.75")
        p1 = SimpleProduct(2, "product 2", price_1)
        b.add(p1)
        b.add(SimpleProduct(3, "product 3", price_2))
        assert b.calculate_price() == sum([price_1, price_2])
        b.remove(p1)
        assert b.calculate_price() == price_2

    def test_remove_non_exsited_product(self):
        b = ProductBundle(1, "bundle 1")
        price_1 = Decimal("1.5")
        p1 = SimpleProduct(2, "product 2", price_1)
        with pytest.raises(ChildNotFound):
            b.remove(p1)

    def test_multiple_parent(self):
        p = SimpleProduct(1, "P", Decimal("123"))
        b1 = ProductBundle(1, "A")
        b2 = ProductBundle(1, "B")
        b1.add(p)
        with pytest.raises(ParentExists):
            b2.add(p)

    def test_parent_after_remove(self):
        b = ProductBundle(1, "B")
        p = SimpleProduct(1, "P", Decimal("10"))

        b.add(p)
        b.remove(p)

        assert p.parent is None

    def test_move_child_between_bundles(self):
        b1 = ProductBundle(1, "A")
        b2 = ProductBundle(2, "B")
        p = SimpleProduct(1, "P", Decimal("10"))

        b1.add(p)
        b1.remove(p)
        b2.add(p)

        assert p.parent is b2

    def test_invalid_price_type(self):
        with pytest.raises(TypeError):
            SimpleProduct(1, "P", 10.5)

    def test_price_after_product_price_change(self):
        b = ProductBundle(1, "B")
        p = SimpleProduct(1, "P", Decimal("10"))

        b.add(p)
        p.price = Decimal("20")

        assert b.calculate_price() == Decimal("20")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))

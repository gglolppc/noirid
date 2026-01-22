from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.order import Order, OrderItem
from app.db.models.product import Product, Variant


class CartRepo:
    @staticmethod
    async def get_order(session: AsyncSession, order_id: str) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id, Order.status == "draft")
            .options(selectinload(Order.items))
        )
        res = await session.execute(stmt)
        return res.scalars().unique().first()

    @staticmethod
    async def create_order(session: AsyncSession, currency: str = "USD") -> Order:
        # Явно задаем items=[], чтобы коллекция не была в состоянии "не загружена"
        order = Order(currency=currency, status="draft", items=[])
        session.add(order)
        await session.flush()
        return order

    @staticmethod
    async def add_item(
        session: AsyncSession,
        order: Order,
        product: Product,
        variant: Variant | None,
        qty: int,
        personalization: dict[str, Any],
        unit_price: Decimal,
    ) -> None:
        # если item с таким product+variant+personalization уже есть — увеличим qty
        for it in order.items:
            if it.product_id == product.id and it.variant_id == (variant.id if variant else None) and (
                    it.personalization_json or {}) == (personalization or {}):
                it.qty += qty
                it.unit_price = unit_price
                it.title_snapshot = product.title
                return

        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            variant_id=(variant.id if variant else None),
            title_snapshot=product.title,
            unit_price=unit_price,
            qty=qty,
            personalization_json=personalization or {},
        )
        order.items.append(item)
        # session.add(item)

    @staticmethod
    async def update_qty(session: AsyncSession, order: Order, item_id: int, qty: int) -> None:
        # тупо в памяти (order.items уже загружены)
        item = next((x for x in order.items if x.id == item_id), None)
        if not item:
            raise KeyError("Item not found")
        item.qty = qty

    @staticmethod
    async def remove_item(session: AsyncSession, order: Order, item_id: int) -> None:
        # Ищем объект в уже загруженных items
        item = next((x for x in order.items if x.id == item_id), None)
        if item:
            order.items.remove(item)
            await session.delete(item)
        # Никакой refresh не нужен, в памяти всё актуально

    @staticmethod
    async def load_product(session: AsyncSession, product_id: int) -> Product | None:
        res = await session.execute(select(Product).where(Product.id == product_id, Product.is_active.is_(True)))
        return res.scalars().first()

    @staticmethod
    async def load_variant(session: AsyncSession, variant_id: int) -> Variant | None:
        res = await session.execute(select(Variant).where(Variant.id == variant_id, Variant.is_active.is_(True)))
        return res.scalars().first()

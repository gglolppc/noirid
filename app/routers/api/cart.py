from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.repos.cart import CartRepo
from app.schemas.cart import CartAddIn, CartOut, CartRemoveIn, CartUpdateQtyIn
from app.services.cart import CartService
from app.services.pricing import PricingService

router = APIRouter(prefix="/api/cart", tags=["cart"])

SESSION_ORDER_KEY = "order_id"


def _cart_to_out(order) -> CartOut:
    items_out = []
    for it in order.items:
        unit = it.unit_price or Decimal("0.00")
        line = (unit * int(it.qty or 0)).quantize(Decimal("0.01"))
        items_out.append(
            {
                "id": it.id,
                "title": it.title_snapshot,
                "qty": it.qty,
                "unit_price": unit,
                "line_total": line,
                "variant_id": it.variant_id,
                "personalization": it.personalization_json or {},
            }
        )
    return CartOut(
        order_id=order.id,
        currency=order.currency,
        subtotal=order.subtotal,
        total=order.total,
        items=items_out,
    )


@router.get("", response_model=CartOut)
async def get_cart(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order_id = request.session.get(SESSION_ORDER_KEY)
    if not order_id:
        raise HTTPException(status_code=404, detail="Cart is empty")

    order = await CartRepo.get_order(session, order_id)
    if not order:
        request.session.pop(SESSION_ORDER_KEY, None)
        raise HTTPException(status_code=404, detail="Cart is empty")

    # на всякий пересчёт (если кто-то руками менял qty)
    CartService.recalc(order)
    await session.commit()

    return _cart_to_out(order)


@router.post("/add", response_model=CartOut)
async def add_to_cart(
    payload: CartAddIn,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order_id = request.session.get(SESSION_ORDER_KEY)
    order = await CartRepo.get_order(session, order_id) if order_id else None

    if order and order.status != "draft":
        raise HTTPException(400, "Order is locked for payment")

    if not order:
        order = await CartRepo.create_order(session, currency="USD")
        request.session[SESSION_ORDER_KEY] = order.id

    product = await CartRepo.load_product(session, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    variant = None
    if payload.variant_id is not None:
        variant = await CartRepo.load_variant(session, payload.variant_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")

    unit_price = PricingService.calc_unit_price(product, variant)

    await CartRepo.add_item(
        session=session,
        order=order,
        product=product,
        variant=variant,
        qty=payload.qty,
        personalization=payload.personalization,
        unit_price=unit_price,
    )

    # await session.refresh(order)  # чтобы items подхватились
    CartService.recalc(order)
    await session.commit()

    return _cart_to_out(order)


@router.post("/update-qty", response_model=CartOut)
async def update_qty(
    payload: CartUpdateQtyIn,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order_id = request.session.get(SESSION_ORDER_KEY)
    if not order_id:
        raise HTTPException(status_code=404, detail="Cart is empty")

    order = await CartRepo.get_order(session, order_id)

    if order and order.status != "draft":
        raise HTTPException(400, "Order is locked for payment")

    if not order:
        request.session.pop(SESSION_ORDER_KEY, None)
        raise HTTPException(status_code=404, detail="Cart is empty")

    try:
        await CartRepo.update_qty(session, order, payload.item_id, payload.qty)
    except KeyError:
        raise HTTPException(status_code=404, detail="Item not found")

    CartService.recalc(order)
    await session.commit()

    return _cart_to_out(order)


@router.post("/remove", response_model=CartOut)
async def remove_item(
    payload: CartRemoveIn,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order_id = request.session.get(SESSION_ORDER_KEY)
    if not order_id:
        raise HTTPException(status_code=404, detail="Cart is empty")

    order = await CartRepo.get_order(session, order_id)

    if order and order.status != "draft":
        raise HTTPException(400, "Order is locked for payment")

    if not order:
        request.session.pop(SESSION_ORDER_KEY, None)
        raise HTTPException(status_code=404, detail="Cart is empty")

    await CartRepo.remove_item(session, order, payload.item_id)

    # перезагрузим актуальный order (items могли поменяться)
    order = await CartRepo.get_order(session, order_id)
    if not order or not order.items:
        # корзина пустая — можно снести из session
        request.session.pop(SESSION_ORDER_KEY, None)
        raise HTTPException(status_code=404, detail="Cart is empty")

    CartService.recalc(order)
    await session.commit()

    return _cart_to_out(order)

@router.post("/clear")
async def clear_cart(request: Request):
    request.session.pop(SESSION_ORDER_KEY, None)
    return {"ok": True}


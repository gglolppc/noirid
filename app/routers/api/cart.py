from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.repos.cart import CartRepo
from app.repos.checkout import CheckoutRepo
from app.schemas.cart import CartAddIn, CartOut, CartRemoveIn, CartUpdateQtyIn
from app.services.cart import CartService
from app.services.pricing import PricingService

router = APIRouter(prefix="/api/cart", tags=["cart"])

SESSION_ORDER_KEY = "order_id"


async def _load_order_any(request: Request, session: AsyncSession):
    order_id = request.session.get(SESSION_ORDER_KEY)
    if not order_id:
        return None
    order = await CheckoutRepo.get_order_any(session, order_id)
    if not order:
        request.session.pop(SESSION_ORDER_KEY, None)
        return None
    return order


async def _ensure_draft_order(
    request: Request,
    session: AsyncSession,
    *,
    create_if_missing: bool = False,
):
    order = await _load_order_any(request, session)
    if not order:
        if create_if_missing:
            order = await CartRepo.create_order(session, currency="EUR")
            request.session[SESSION_ORDER_KEY] = order.id
        return order

    if order.payment_status == "paid":
        request.session.pop(SESSION_ORDER_KEY, None)
        if create_if_missing:
            order = await CartRepo.create_order(session, currency=order.currency or "EUR")
            request.session[SESSION_ORDER_KEY] = order.id
            return order
        return None

    if order.status != "draft":
        draft = await CartRepo.create_order(session, currency=order.currency or "EUR")
        await CartRepo.clone_items(session, order, draft)
        request.session[SESSION_ORDER_KEY] = draft.id
        return draft

    return order


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
                "preview_url": it.preview_url,
            }
        )
    return CartOut(
        order_id=order.id,
        currency=order.currency,
        subtotal=order.subtotal,
        discount_amount=getattr(order, "discount_amount", Decimal("0.00")),
        discount_reason=getattr(order, "discount_reason", None),
        total=order.total,
        items=items_out,
    )


@router.get("", response_model=CartOut)
async def get_cart(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order = await _ensure_draft_order(request, session)

    # Если заказа нет или в нем нет айтемов — отдаем "заглушку" пустой корзины
    if not order or not order.items:
        return CartOut(
            order_id='id-1', # id заказа или 0, если заказа нет
            currency="EUR",                  # Валюта по умолчанию
            subtotal=Decimal("0.00"),
            total=Decimal("0.00"),
            items=[]                         # Пустой список для фронта
        )

    # Если заказ есть и не пустой — считаем и отдаем как обычно
    CartService.recalc(order)
    await session.commit()

    return _cart_to_out(order)

@router.post("/add", response_model=CartOut)
async def add_to_cart(
    payload: CartAddIn,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order = await _ensure_draft_order(request, session, create_if_missing=True)
    if not order:
        raise HTTPException(status_code=400, detail="Cart is empty")

    product = await CartRepo.load_product(session, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.variant_id is None:
        raise HTTPException(status_code=400, detail="Variant is required")

    variant = await CartRepo.load_variant(session, payload.variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    preview_url = (payload.preview_url or "").strip() or None
    if preview_url and not preview_url.startswith("/static/out/mockups/"):
        raise HTTPException(status_code=400, detail="Invalid preview_url")

    personalization_payload = payload.personalization or {}
    schema = product.personalization_schema or {}
    personalization: dict[str, str] = {}
    if schema:
        for key, limit in schema.items():
            value = str(personalization_payload.get(key, "")).strip()
            if not value:
                raise HTTPException(status_code=400, detail=f"Personalization '{key}' is required")
            if isinstance(limit, dict):
                limit = limit.get("max_len", 0)
            try:
                limit_value = int(limit)
            except (TypeError, ValueError):
                limit_value = 0
            if limit_value > 0 and len(value) > limit_value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Personalization '{key}' must be {limit_value} characters or less",
                )
            personalization[key] = value
    else:
        personalization = {
            str(key): str(value).strip()
            for key, value in personalization_payload.items()
            if str(value).strip()
        }

    unit_price = PricingService.calc_unit_price(product, variant)

    await CartRepo.add_item(
        session=session,
        order=order,
        product=product,
        variant=variant,
        qty=payload.qty,
        personalization=personalization,
        unit_price=unit_price,
        preview_url=preview_url
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
    order = await _load_order_any(request, session)
    if not order:
        raise HTTPException(status_code=404, detail="Cart is empty")

    if order.payment_status == "paid":
        request.session.pop(SESSION_ORDER_KEY, None)
        raise HTTPException(status_code=404, detail="Cart is empty")

    if order.status != "draft":
        source_order = order
        source_item = next((x for x in source_order.items if x.id == payload.item_id), None)
        order = await CartRepo.create_order(session, currency=source_order.currency or "EUR")
        await CartRepo.clone_items(session, source_order, order)
        request.session[SESSION_ORDER_KEY] = order.id

        if not source_item:
            raise HTTPException(status_code=404, detail="Item not found")

        target = next(
            (
                x
                for x in order.items
                if x.product_id == source_item.product_id
                and x.variant_id == source_item.variant_id
                and (x.personalization_json or {}) == (source_item.personalization_json or {})
            ),
            None,
        )
        if not target:
            raise HTTPException(status_code=404, detail="Item not found")
        await CartRepo.update_qty(session, order, target.id, payload.qty)
    else:
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
    order = await _load_order_any(request, session)
    if not order:
        raise HTTPException(status_code=404, detail="Cart is empty")

    if order.payment_status == "paid":
        request.session.pop(SESSION_ORDER_KEY, None)
        raise HTTPException(status_code=404, detail="Cart is empty")

    if order.status != "draft":
        source_order = order
        source_item = next((x for x in source_order.items if x.id == payload.item_id), None)
        order = await CartRepo.create_order(session, currency=source_order.currency or "EUR")
        await CartRepo.clone_items(session, source_order, order)
        request.session[SESSION_ORDER_KEY] = order.id

        if not source_item:
            raise HTTPException(status_code=404, detail="Item not found")

        target = next(
            (
                x
                for x in order.items
                if x.product_id == source_item.product_id
                and x.variant_id == source_item.variant_id
                and (x.personalization_json or {}) == (source_item.personalization_json or {})
            ),
            None,
        )
        if not target:
            raise HTTPException(status_code=404, detail="Item not found")
        await CartRepo.remove_item(session, order, target.id)
    else:
        await CartRepo.remove_item(session, order, payload.item_id)

    if not order.items:
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


@router.get("/summary")
async def cart_summary(cart = Depends(get_cart)):
    return {
        "items_count": sum(item.qty for item in cart.items),
        "total": f"{cart.total:.0f}",
        "currency": cart.currency
    }

"""Pricing calculation. Support has reported incorrect customer totals."""
from decimal import Decimal, ROUND_HALF_UP
from .validation import validate_order


def quote(lines, discount=Decimal("0")):
    validate_order(lines, discount)
    subtotal = Decimal("0")
    for line in lines:
        line_total = (line["unit_price"] * line["quantity"]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal += line_total
    discount_amount = (subtotal * discount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    discounted_goods = subtotal - discount_amount
    shipping = Decimal("0") if discounted_goods >= Decimal("100") else Decimal("5")
    total = discounted_goods + shipping
    return {"subtotal": subtotal, "shipping": shipping, "total": total}

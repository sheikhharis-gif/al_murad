from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def acct(value):
    """Accounting-style number: comma thousands, 2dp, negatives in
    parentheses, zero shown as a dash - matches CLIENT RATE FILE.xlsx."""
    if value in (None, ""):
        return ""
    try:
        d = Decimal(value)
    except (InvalidOperation, TypeError):
        return value
    if d == 0:
        return "-"
    formatted = "{:,.2f}".format(abs(d))
    return "({})".format(formatted) if d < 0 else formatted


@register.filter
def pct(value):
    """Comma thousands, 2dp, trailing % sign, keeps a leading minus for
    negatives - matches CLIENT RATE FILE.xlsx's Fuel Price Change % column."""
    if value in (None, ""):
        return ""
    try:
        d = Decimal(value)
    except (InvalidOperation, TypeError):
        return value
    return "{:,.2f}%".format(d)


@register.filter
def pct_trim(value):
    """Comma thousands, trims trailing .00 - matches CLIENT RATE FILE.xlsx's
    Effective % column (e.g. 50.00 -> 50%, 37.50 -> 37.5%)."""
    if value in (None, ""):
        return ""
    try:
        d = Decimal(value)
    except (InvalidOperation, TypeError):
        return value
    formatted = "{:,.2f}".format(d).rstrip("0").rstrip(".")
    return "{}%".format(formatted)

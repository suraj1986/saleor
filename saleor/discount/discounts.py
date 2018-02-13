from decimal import Decimal

from prices.discount import (
    fixed_discount, percentage_discount as prices_percentage_discount)


class FixedDiscount:
    """Reduces price by a fixed amount."""

    def __init__(self, amount, name=None):
        self.amount = amount
        self.name = name

    def __repr__(self):
        return 'Discount(%r, name=%r)' % (self.amount, self.name)

    def apply(self, base):
        return fixed_discount(base, self.amount)


def percentage_discount(base, percentage, name=None):
    fixed_discount_amount = prices_percentage_discount(base, percentage)
    taxed_discount_amount = base - fixed_discount_amount
    return FixedDiscount(amount=taxed_discount_amount, name=name)

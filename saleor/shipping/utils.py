from prices import Price, PriceRange

from .models import ShippingMethodCountry


def get_shipment_options(country_code):
    shipping_methods_qs = ShippingMethodCountry.objects.select_related(
        'shipping_method')
    shipping_methods = shipping_methods_qs.filter(country_code=country_code)
    if not shipping_methods.exists():
        shipping_methods = shipping_methods_qs.filter(country_code='')
    if shipping_methods:
        shipping_methods = shipping_methods.values_list('price', flat=True)
        min_amount = min(shipping_methods)
        max_amount = max(shipping_methods)
        return PriceRange(
            min_price=Price(net=min_amount, gross=min_amount),
            max_price=Price(net=max_amount, gross=max_amount))

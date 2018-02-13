import graphene
from django_prices.templatetags import prices_i18n


class TaxedMoneyType(graphene.ObjectType):
    currency = graphene.String()
    gross = graphene.Float()
    gross_localized = graphene.String()
    net = graphene.Float()
    net_localized = graphene.String()

    def resolve_gross(self, info):
        return self.gross.amount

    def resolve_gross_localized(self, info):
        return prices_i18n.amount(self.gross)

    def resolve_net(self, info):
        return self.net.amount

    def resolve_net_localized(self, info):
        return prices_i18n.amount(self.net)


class TaxedMoneyRangeType(graphene.ObjectType):
    start = graphene.Field(lambda: TaxedMoneyType)
    stop = graphene.Field(lambda: TaxedMoneyType)

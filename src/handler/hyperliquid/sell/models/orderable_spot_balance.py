from handler.models.spot_balance import SpotBalance


class OrderableSpotbalance(SpotBalance):
    is_sell: bool = False

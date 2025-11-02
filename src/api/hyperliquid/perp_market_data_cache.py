from hypurrquant.models.perp_market_data import (
    MarketData as PerpMarketData,
)
from hypurrquant.utils.singleton import singleton
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from ..utils import send_request, BASE_URL
from hypurrquant.utils.graceful_shutdown import GracefulShutdownMixin

from typing import Dict


_logger = configure_logging(__name__)


@singleton
class PerpMarketDataCache(GracefulShutdownMixin):
    def __init__(self):
        super().__init__()
        self.market_datas: Dict["str", PerpMarketData] = {}

    @force_coroutine_logging
    async def _fetch_market_data(self):
        response = await send_request(
            "GET",
            f"{BASE_URL}/data/perp-market-data",
        )

        market_data = {}
        for key, value in response.data.items():
            market_data[key] = PerpMarketData(**value)

        return market_data

    async def _build_data(self):
        self.market_datas = await self._fetch_market_data()

    async def run_once(self):
        _logger.debug("PerpMarketDataCache run_once called")
        await perp_market_data_cache._build_data()


perp_market_data_cache = PerpMarketDataCache()

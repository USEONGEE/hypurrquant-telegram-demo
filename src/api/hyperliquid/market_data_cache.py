from hypurrquant.models.market_data import MarketData
from hypurrquant.logging_config import configure_logging
from ..utils import send_request, BASE_URL

from typing import List, Dict
import asyncio

# ================================
# 설정 정보
# ================================
_logger = configure_logging(__name__)


# ================================
# 싱글톤 메타클래스
# ================================
class Singleton(type):
    """
    메타클래스 Singleton은 클래스의 인스턴스가 단 하나만 생성되도록 보장합니다.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # 인스턴스가 존재하지 않으면 생성
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# ================================
# api 모듈
# ================================
class MarketDataCache(metaclass=Singleton):
    def __init__(self):
        self._market_datas: List[MarketData] = []
        self._coin_by_Tname: Dict[str, MarketData] = None
        self._Tname_by_coin: Dict[str, MarketData] = None
        self._coin_list: List[str] = None

    @property
    def coin_list(self):
        if not self._coin_list:
            _logger.error("Coin list is empty")
        return self._coin_list

    @property
    def coin_by_Tname(self):
        if not self._coin_by_Tname:
            _logger.error("Coin by Tname is empty")
        return self._coin_by_Tname

    @property
    def Tname_by_coin(self):
        if not self._Tname_by_coin:
            _logger.error("Tname by coin is empty")
        return self._Tname_by_coin

    @property
    def market_datas(self):
        if not self._market_datas:
            _logger.error("Market data is empty")
            raise Exception("Market data is empty")
        return self._market_datas

    async def _build_data(self):
        market_data = await send_request(
            "GET",
            f"{BASE_URL}/data/market-data",
        )
        self._market_datas = [MarketData(**data) for data in market_data.data]
        self._coin_by_Tname = {data.Tname: data for data in self.market_datas}
        self._Tname_by_coin = {data.coin: data for data in self.market_datas}
        self._coin_list = [spot_meta.coin for spot_meta in self.market_datas]

    def filter_by_Tname(self, ticker: str):
        Tname = self.coin_by_Tname[ticker]
        if not Tname:
            _logger.error(f"{ticker} is not found in coin_by_Tname")
        return Tname

    def filter_by_coin(self, coin: str):
        coin = self.Tname_by_coin[coin]
        if not coin:
            _logger.error(f"{coin} is not found in Tname_by_coin")
        return coin


async def periodic_task(singleton_instance: MarketDataCache, interval):
    while True:
        try:
            await singleton_instance._build_data()
        except Exception as e:
            _logger.exception("마켓 데이터를 가져오던 중 예외가 발생했습니다.")
        await asyncio.sleep(interval)

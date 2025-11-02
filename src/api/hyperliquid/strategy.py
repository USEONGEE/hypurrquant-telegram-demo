from hypurrquant.logging_config import configure_logging
from hypurrquant.utils.singleton import Singleton
from hypurrquant.models.market_data import MarketData
from ..utils import BASE_URL, send_request
from ..models import BaseResponse
from ..exception import NoDataWihtFilter
from .models import StrategyMeta
from typing import Dict, List, Optional

# ================================
# 설정 정보
# ================================
_logger = configure_logging(__name__)


class StrategyService(metaclass=Singleton):
    async def execute_strategy(self, strategy_meta: StrategyMeta) -> List[MarketData]:
        """
        StrategyMeta 객체를 사용해 API를 호출
        """
        if not isinstance(strategy_meta, StrategyMeta):
            raise TypeError("strategy_meta는 StrategyMeta 객체여야 합니다.")

        # default_params -> { "momentum_pct": ParamConfig(...), ... }
        # 실제 요청 시에는 { "momentum_pct": 0.2, ... } 로 변환
        request_params = {
            param_name: param_config.default
            for param_name, param_config in strategy_meta.default_params.items()
        }

        # API 요청
        response: BaseResponse = await send_request(
            method="GET",
            url=f"{BASE_URL}/strategy{strategy_meta.endpoint}",
            params=request_params,
        )

        # 응답 데이터를 pydantic 모델(MarketData)로 변환
        data = [MarketData(**item) for item in response.data]

        if not data:
            _logger.info("사용자의 필터에 해당하는 데이터가 없습니다.")
            raise NoDataWihtFilter()

        return data

    async def get_strategies(
        self, strategy_type: Optional[str] = None
    ) -> Dict[str, StrategyMeta]:
        """
        서버에서 특정 장(시장상태)에 대한 전략 목록을 가져온다.
        예: https://.../strategy/general/strategies?state=UPTREND
        """
        response: BaseResponse = await send_request(
            method="GET",
            url=f"{BASE_URL}/strategy/general/strategies",
            params={"state": strategy_type} if strategy_type else None,
        )

        # response.data -> { "price_momentum": {...}, "smallcap_opportunity": {...}, ... }
        # 각 value는 {"name": "", "endpoint": "", "default_params": {...}} 구조를 가정
        data = {}
        for key, value in response.data.items():
            # StrategyMeta(**value)를 통해 Pydantic 검증
            # default_params가 올바른 형태(ParamConfig)인지 검사
            data[key] = StrategyMeta(**value)

        _logger.debug(f"전략 목록: {data}")

        return data

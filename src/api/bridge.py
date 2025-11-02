# solana_bridge.py

from hypurrquant.logging_config import configure_logging
from hypurrquant.utils.singleton import singleton
from hypurrquant.api.async_http import send_request_for_external
from hypurrquant.db.redis import get_redis_async
from hypurrquant.constant.redis import TelegramRedisKey

from .hyperliquid import MarketDataCache
import asyncio
import json
from enum import Enum


# ------------------------------------------------------------------
# 기본 상수
# ------------------------------------------------------------------
# UNIT_API = "https://unitproxy.hypurrquant.com"  # NOTE: 미국 리전 전용으로 사용하는 프록시 api
UNIT_API = "https://api.hyperunit.xyz"  # Hyper-Unit API URL
LAMPORTS_PER_SOL = 1_000_000_000  # 1 SOL = 10^9 lamports

_logger = configure_logging(__name__)
market_data = MarketDataCache()


class Chain(Enum):
    SOLANA = "solana"
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"


@singleton
class BridgeService:

    def __init__(self):
        self.redis_client = get_redis_async()

    async def get_bridge_address(self, dst_evm_addr: str, chain: Chain) -> str:
        """
        HyperUnit API 를 이용해 **Solana → Hyperliquid(Arbitrum)** 입금 주소를 생성한다.

        Parameters
        ----------
        dst_evm_addr : str
            Hyperliquid(또는 EVM) 지갑 주소 (0x… 형태)

        Returns
        -------
        dict
        {'solana_address': '5DPouTqvvS2oxZdpnWpMQZPzF93e1y7fnndfM1TxwLNb',
        'signatures': {'field-node': 'x9PKwmLvN0NPM85MuHh709F687kWhi78keh7Pd8lkYF8NwbtsE6c3/IOQkN9sT5DrTVsLMpQDC1LBBI6Av/9IQ==',
        'hl-node': 'xlDG++pyTj1gkaQiqDyOAvU3XMc076+ibCUpCxJ9KAEIf/ivy/HidknnV6c2x7x2p1rK44aJqmbGwfxOUp5/MQ==',
        'unit-node': 'e4IkH1LQAmjqOEq9eMP8njIjE+b7WexlbSOT4eXBjiDX1CwJz9lD5EJYijvKO2VfTiMaP3G1p9x7Yk2iyfHUug=='}}
        """

        async def has_cache_then_return():
            """
            캐시된 Solana 주소가 있는지 확인. 한 번 캐시되면 1시간 동안 재사용.
            """
            cache_key = TelegramRedisKey.BRIDGE_ADDRESS.value.format(
                chain=chain.value, address=dst_evm_addr
            )
            if await self.redis_client.exists(cache_key):
                cached_data = await self.redis_client.get(cache_key)
                _logger.debug(f"캐시된 Solana 주소를 사용합니다: {cached_data}")
                return cached_data

        if chain == Chain.SOLANA:
            endpoint = "/gen/solana/hyperliquid/sol"
        elif chain == Chain.BITCOIN:
            endpoint = "/gen/bitcoin/hyperliquid/btc"
        elif chain == Chain.ETHEREUM:
            endpoint = "/gen/ethereum/hyperliquid/eth"
        else:
            raise ValueError(f"Unsupported chain: {chain}")

        error_msg = "Fail to fetch Solana address."
        try:
            cached = await has_cache_then_return()
            if cached:
                return cached
            j = await send_request_for_external(
                "GET", f"{UNIT_API}{endpoint}/{dst_evm_addr}"
            )

            if j.get("status") != "OK":
                _logger.error(f"Failed to generate Solana address for {dst_evm_addr}")
                return error_msg

            asyncio.create_task(
                self.redis_client.setex(
                    TelegramRedisKey.BRIDGE_ADDRESS.value.format(
                        chain=chain.value,  # chain은 Chain Enum의 value 사용
                        address=dst_evm_addr,
                    ),
                    3600 * 24 * 31,  # 31 days cache
                    j["address"],
                )
            )
            return j["address"]
        except Exception:
            _logger.exception(f"솔라나 지갑 주소 fetch 중 에러 발생")
            return error_msg

    async def estimate_solana_fees(
        self,
        convert_to_usd: bool = True,
    ) -> dict:
        """
        Hyper-Unit v2 estimate-fees API 에서 Solana 수수료 정보를 조회 후
        lamport·SOL·(선택)USD 단위로 반환한다.

        Parameters
        ----------
        convert_to_usd : bool, default=True
            True → 실시간 SOL 가격을 조회해 USD 환산 필드도 포함.

        Returns
        -------
        float
            Solana 입금 수수료 (lamport 단위, 1 SOL = 10^9 lamports)
            convert_to_usd=True 이면 USD 환산 값도 함께 반환.
        """

        async def has_cache_then_return():
            """
            캐시된 Solana 주소가 있는지 확인. 한 번 캐시되면 10분동안 재사용
            """
            cache_key = TelegramRedisKey.BRIDGE_FEE.value
            if await self.redis_client.exists(cache_key):
                cached_data = await self.redis_client.get(cache_key)

                _logger.debug(f"캐시된 Solana 수수료를 사용합니다: {cached_data}")
                return json.loads(cached_data)

        global market_data
        try:
            cached = await has_cache_then_return()
            if cached:
                return cached
            r = await send_request_for_external("GET", f"{UNIT_API}/v2/estimate-fees")
            fees = r["solana"]
            deposit_fees = float(fees["depositFee"]) / LAMPORTS_PER_SOL

            if convert_to_usd:
                sol_data = market_data.filter_by_Tname("USOL")
                sol_price = sol_data.markPx
                deposit_fees = deposit_fees * sol_price

            r["fee"] = deposit_fees
            # r을 직렬화해서 저장
            asyncio.create_task(
                self.redis_client.setex(
                    TelegramRedisKey.BRIDGE_FEE.value,
                    60,
                    json.dumps(r, ensure_ascii=False),
                )
            )

            return r
        except Exception as e:
            print(f"Error estimating Solana fees: {e}")
            return {}

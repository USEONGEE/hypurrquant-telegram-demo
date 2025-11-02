from hypurrquant.api.async_http import send_request_for_external
from hypurrquant.utils.singleton import Singleton
from hypurrquant.logging_config import configure_logging
from .utils import send_request, BASE_URL
from .models import (
    LpVaultWithConfigDict,
    DexInforesponse,
    BaseResponse,
    CoreToken,
    AccountDto,
    LpvaultSettingsDict,
)
import asyncio
from dotenv import load_dotenv
from typing import List
import aiocache

# ================================
# 설정 정보
# ================================
_logger = configure_logging(__name__)
load_dotenv()


# ================================
# 계좌 정보 서비스
# ================================
class LpVaultService(metaclass=Singleton):

    async def register_defi_lp_vault_account(
        self, telegram_id: str, nickname: str
    ) -> AccountDto:
        """
        Register a DeFi LP Vault account.

        Args:
            telegram_id (str): Telegram ID of the user.
            nickname (str): Nickname for the account.

        Returns:
            AccountDto: DTO containing account details.
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/lp-vault/register",
            json={"telegram_id": str(telegram_id), "nickname": nickname},
        )
        return response.data

    async def unregister_defi_lp_vault_account(self, public_key: str) -> bool:
        """
        Unregister a DeFi LP Vault account.

        Args:
            public_key (str): Public key of the account to unregister.

        Returns:
            bool: True if unregistration was successful, False otherwise.
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/lp-vault/unregister",
            json={"public_key": public_key},
        )
        return response.data

    # ================================
    # Lpvault CURD
    # ================================
    async def dex_list(self, chain: str) -> List[DexInforesponse]:
        """
        사용 가능한 DEX 목록을 조회합니다.

        Returns:
            List[str]: DEX 목록
        """
        response: BaseResponse = await send_request(
            "GET", f"{BASE_URL}/dex/lp-vault/dex_list?chain={chain}"
        )
        return response.data

    async def pool_list(self, chain: str, dex_type: str) -> dict:
        """
        사용 가능한 DEX의 풀 목록을 조회합니다.

        Args:
            dex_type (str): DEX 종류 (HYBRA, HYPERSWAP, PRJX)

        Returns:
            List[dict]: 풀 목록
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/dex/lp-vault/pool_list?dex_type={dex_type}&chain={chain}",
        )
        return response.data

    async def aggregator_list(self, chain: str) -> List[str]:
        """
        사용 가능한 DEX의 Aggregator 목록을 조회합니다.

        Returns:
            List[str]: Aggregator 목록
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/dex/lp-vault/aggregator_list?chain={chain}",
        )
        return response.data

    async def lp_list(self, public_key: str) -> List[LpVaultWithConfigDict]:
        """
        사용자의 Uniswap V3 유사형 NFT LP 포지션 정보를 조회합니다.

        Args:
            public_key (str): 사용자 지갑 주소

        Returns:
            List[LpVaultPositionResponse]: LP 포지션 정보 리스트
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/dex/lp-vault/list?public_key={public_key}",
        )
        return response.data

    @aiocache.cached()
    async def get_address_by_ticker(self, chain: str, ticker: str) -> str:
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/dex/ticker-to-address?chain={chain}&ticker={ticker}",
        )
        return response.data

    @aiocache.cached()
    async def get_core_tokens(self, chain: str) -> CoreToken:
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/dex/core-tokens?chain={chain}",
        )
        return response.data

    async def get_positions(self, public_key: str, chain: str, dex_type: str) -> list:
        """
        현재 민팅된 포지션을 조회합니다.

        Returns:
            List[LpVaultPositionResponse]: 민팅된 포지션 리스트
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/dex/lp-vault/positions?public_key={public_key}&dex_type={dex_type}&chain={chain}",
        )
        return response.data

    async def get_profits(self, public_key: str, chain: str, positions: list) -> list:
        """
        현재 민팅된 포지션의 수익을 조회합니다.

        Args:
            public_key (str): 사용자 지갑 주소
            positions (list): 민팅된 포지션 리스트

        Returns:
            List[LpVaultPositionResponse]: 민팅된 포지션의 수익 리스트
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/dex/lp-vault/profit",
            json={"positions": positions, "public_key": public_key, "chain": chain},
        )
        return response.data

    async def manual_mint(
        self,
        public_key: str,
        chain,
        dex_type: str,
        token0: str,
        token1: str,
        fee: int | None,
        lower_range_pct: float,
        upper_range_pct: float,
        aggregator: str,
    ):
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/dex/lp-vault/mint",
            json={
                "public_key": public_key,
                "chain": chain,
                "dex_type": dex_type,
                "token0": token0,
                "token1": token1,
                "fee": fee,
                "lower_range_pct": lower_range_pct,
                "upper_range_pct": upper_range_pct,
                "aggregator": aggregator,
            },
            timeout=60,  # TODO 이거 좀 길 수도 있음.
        )
        return response.data

    async def register(
        self,
        public_key,
        chain,
        aggregator,
        aggregator_mode,
        dex_type,
        token0,
        token1,
        fee,
        upper_range_pct,
        lower_range_pct,
        auto_claim,
        swap_target_token_address,
    ):
        """
        계좌 정보를 가져오는 메서드

        Args:
            public_key (str): Public Key

        Returns:
            AccountDto: 계좌 정보 DTO
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/dex/lp-vault",
            json={
                "public_key": public_key,
                "chain": chain,
                "aggregator": aggregator,
                "aggregator_mode": aggregator_mode,
                "dex_type": dex_type,
                "token0": token0,
                "token1": token1,
                "fee": fee,
                "upper_range_pct": upper_range_pct,
                "lower_range_pct": lower_range_pct,
                "auto_claim": auto_claim,
                "swap_target_token_address": swap_target_token_address,
            },
        )
        return response.data

    async def unregister(self, lp_vault_id, *, remove_nft_positions=False):
        """
        계좌 정보를 삭제하는 메서드

        Args:
            public_key (str): Public Key
            lp_vault_id (str): LP Vault ID
        """
        response: BaseResponse = await send_request(
            "DELETE",
            f"{BASE_URL}/dex/lp-vault/{lp_vault_id}?remove_nft_positions={remove_nft_positions}",
        )
        return response.data

    # ================================
    # Points
    # ================================
    async def get_points(self, public_key: str, chain: str):
        if chain == "HYPERLIQUID":
            # a, b, c, d = await asyncio.gather(
            #     self._get_hybra_points(public_key),
            #     self._get_prjx_points(public_key),
            #     self._get_gliquid_points(public_key),
            #     self._get_hyperbloom_points(public_key),
            # )
            # return {
            #     "Hybra": a,
            #     "Prjx": b,
            #     "GLiquid": c,
            #     "Hyperbloom": d,
            # }

            a, b, d = await asyncio.gather(
                self._get_hybra_points(public_key),
                self._get_prjx_points(public_key),
                self._get_hyperbloom_points(public_key),
            )
            return {
                "Hybra": a,
                "Prjx": b,
                "Hyperbloom": d,
            }

        _logger.info(f"Unsupported chain for points: {chain}")

    @aiocache.cached(ttl=300, cache=aiocache.SimpleMemoryCache)
    async def _get_hybra_points(self, public_key: str) -> float:
        """
        Get Hybra points for a specific account.

        Args:
            public_key (str): Public key of the account.

        Returns:
            float: Hybra points value.
        """
        response = await send_request_for_external(
            "GET",
            f"https://server.hybra.finance/api/points/user/{public_key}",
            retry=False,
            timeout=20,
        )
        _logger.debug(f"Hybra points response: {response}")
        if not response or not isinstance(response, dict):
            return 0
        return float((response.get("data") or {}).get("totalPoints") or 0.0)

    @aiocache.cached(ttl=300, cache=aiocache.SimpleMemoryCache)
    async def _get_prjx_points(self, public_key: str) -> float:
        """
        Get PRJX points for a specific account.

        Args:
            public_key (str): Public key of the account.

        Returns:
            float: PRJX points value.
        """
        try:
            response = await send_request_for_external(
                "GET",
                f"https://api.prjx.com/scorecard/impersonate/{public_key}?format=json",
                retry=False,
                timeout=20,
            )
            if not response or not isinstance(response, dict):
                return 0
            return float((response.get("stats") or {}).get("totalPoints") or 0.0)
        except Exception as e:
            _logger.info(f"Error fetching PRJX points for {public_key}: {e}")
            return 0.0

    @aiocache.cached(ttl=300, cache=aiocache.SimpleMemoryCache)
    async def _get_hyperbloom_points(self, public_key: str) -> float:
        """
        Get Hyperbloom points for a specific account.

        Args:
            public_key (str): Public key of the account.

        Returns:
            float: Hyperbloom points value.
        """
        try:
            response = await send_request_for_external(
                "GET",
                f"https://api.hyperbloom.xyz/points?address={public_key}",
                retry=False,
                timeout=20,
            )
            _logger.debug(f"Hyperbloom points response: {response}")
            if not response or not isinstance(response, dict):
                return 0
            return float(response.get("points", 0.0))
        except Exception as e:
            _logger.info(f"Error fetching Hyperbloom points for {public_key}: {e}")
            return 0.0

    async def _get_gliquid_points(self, public_key: str) -> float:
        """
        Get GLiquid points for a specific account.

        Args:
            public_key (str): Public key of the account.

        Returns:
            float: GLiquid points value.
        """
        try:
            parsed = await self._get_gliquid_all_points()
            user_data = parsed.get(public_key.lower(), {})
            points = user_data.get("points", 0)
            return float(points)
        except Exception as e:
            _logger.info(f"Error fetching GLiquid points for {public_key}: {e}")
            return 0.0

    @aiocache.cached(ttl=300, cache=aiocache.SimpleMemoryCache)
    async def _get_gliquid_all_points(self) -> dict:
        """
        Get all GLiquid points for all accounts.

        Returns:
            dict: Dictionary of public keys and their GLiquid points.
        """
        try:
            response = await send_request_for_external(
                "GET",
                "https://api.gliquid.xyz/api/referrals/getAllReferralUsersFast",
                retry=False,
                timeout=20,
            )
            return {data["address"].lower(): data for data in response["users"]}
        except Exception as e:
            _logger.exception(f"Error fetching GLiquid points: {e}")
            return {}

    # ================================
    # Swap
    # ================================
    async def get_tokens_for_swap(self, public_key: str, chain: str):
        """
        Get tokens available for swap for a specific account.

        Args:
            public_key (str): Public key of the account.

        Returns:
            {
                "USDT0": {
                    "address": "0xB8CE59FC3717ada4C02eaDF9682A9e934F625ebb",
                    "amount": 5.758302
                },
                ...
            }

        """
        return (
            await send_request(
                "GET",
                f"{BASE_URL}/dex/swap/tokens?public_key={public_key}&chain={chain}",
            )
        ).data

    async def create_routes(self, public_key, chain, token_in, token_out, amount):
        return (
            await send_request(
                "POST",
                f"{BASE_URL}/dex/swap/routes",
                json={
                    "public_key": public_key,
                    "chain": chain,
                    "token_in": token_in,
                    "token_out": token_out,
                    "amount": amount,
                },
            )
        ).data

    async def execute_swap(self, ctx_id, aggregator):
        """
        Execute a swap operation.

        Args:
            ctx_id (str): Context ID for the swap.
            aggregator (str, optional): Aggregator to use for the swap. Defaults to None.

        Returns:
            dict: Result of the swap execution.
        """
        return (
            await send_request(
                "POST",
                f"{BASE_URL}/dex/swap/routes/execute/{ctx_id}?aggregator={aggregator}",
                timeout=60 * 10,
            )
        ).data


class LpVaultSettingsService(metaclass=Singleton):

    async def get_settings(self, public_key: str, chain: str) -> LpvaultSettingsDict:
        return (
            await send_request(
                "GET",
                f"{BASE_URL}/dex/lp-vault/settings",
                params={"public_key": public_key, "chain": chain},
            )
        ).data

    async def update_auto_toggle(
        self, public_key: str, chain: str, value: dict
    ) -> LpvaultSettingsDict:
        endpoint = ""
        val = None

        for k, v in value.items():
            if k not in ["auto_claim"]:
                raise ValueError("Invalid key in value dictionary")
            endpoint = k
            val = v
        endpoint = endpoint.replace("_", "-")

        return (
            await send_request(
                "POST",
                f"{BASE_URL}/dex/lp-vault/settings/{endpoint}",
                json={"public_key": public_key, "chain": chain, "value": val},
            )
        ).data

    async def change_aggregator(
        self, public_key: str, chain: str, aggregator: str
    ) -> LpvaultSettingsDict:

        return (
            await send_request(
                "POST",
                f"{BASE_URL}/dex/lp-vault/settings/aggregator",
                json={
                    "public_key": public_key,
                    "chain": chain,
                    "aggregator": aggregator,
                },
            )
        ).data

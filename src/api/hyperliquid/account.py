from hypurrquant.utils.singleton import singleton
from ..utils import send_request, BASE_URL
from .models import (
    SpotBalanceMappingDTO,
    PerpBalanceMappingDTO,
    USDCBalanceItem,
)
from ..models import BaseResponse, AccountDto
from hypurrquant.logging_config import configure_logging

from typing import List

# ================================
# 설정 정보
# ================================
_logger = configure_logging(__name__)


# ================================
# 계좌 정보 서비스
# ================================
@singleton
class HLAccountService:
    async def get_spot_balance(
        self, telegram_id: str, nickname: str
    ) -> SpotBalanceMappingDTO:
        """
        return: {balance, margin_summary}
            Name  Balance  hold  entryNtl  EntryPrice    Price     Value      PNL       PNL%
            0  BTC     0.5   0.0    20000    40000.0   45000.0  22500.0   2500.0   12.500000
            1  ETH     2.0   0.0     3000     1500.0    1800.0   3600.0    600.0   20.000000

            summary -> float
        """

        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/balance/spot?telegram_id={telegram_id}&nickname={nickname}",
        )
        return SpotBalanceMappingDTO(**(response.data))

    async def get_spot_balance_by_public_key(
        self, public_key: str
    ) -> SpotBalanceMappingDTO:
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/balance/spot/by_public_key?public_key={public_key}",
        )
        return SpotBalanceMappingDTO(**(response.data))

    async def get_perp_balance(
        self, telegram_id: str, nickname: str
    ) -> PerpBalanceMappingDTO:
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/balance/perp?telegram_id={telegram_id}&nickname={nickname}",
        )
        return PerpBalanceMappingDTO(**(response.data))

    async def spot_to_perp(self, telegram_id, value: float):
        """
        transfer USDC in between spot and perp wallet

        Args:
            secret_key (_type_): Secret Key
            value (float) : USDC
            is_spot (bool): True is Spot to perp,
                            False is perp to spot
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/spot_to_perp",
            json={"telegram_id": str(telegram_id), "value": float(value)},
        )
        return True

    async def perp_to_spot(self, telegram_id, value: float):
        """
        transfer USDC in between spot and perp wallet

        Args:
            secret_key (_type_): Secret Key
            value (float) : USDC
            is_spot (bool): True is Spot to perp,
                            False is perp to spot
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/perp_to_spot",
            json={"telegram_id": str(telegram_id), "value": float(value)},
        )
        return True

    async def send_usdc(self, telegram_id, destination, value):
        """
        transfer USDC in between spot and perp wallet

        Args:
            secret_key (_type_): Secret Key
            value (float) : USDC
            is_spot (bool): True is Spot to perp,
                            False is perp to spot
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/send_usdc",
            json={
                "telegram_id": str(telegram_id),
                "recipient_address": destination,
                "value": float(value),
            },
        )
        return True

    async def get_rebalance_account(self, telegram_id) -> AccountDto:
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/rebalance?telegram_id={telegram_id}",
        )
        # if response.data is None:
        #     return None

        return AccountDto(
            nickname=response.data["nickname"],
            public_key=response.data["public_key"],
            is_active=response.data["is_active"],
            is_approved_builder_fee=response.data["is_approved_builder_fee"],
        )

    async def get_copytrading_account(self, telegram_id: str) -> AccountDto:
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/copytrading?telegram_id={telegram_id}",
        )
        _logger.debug(response)
        return AccountDto(
            nickname=response.data["nickname"],
            public_key=response.data["public_key"],
            is_active=response.data["is_active"],
            is_approved_builder_fee=response.data["is_approved_builder_fee"],
        )

    async def approve_builder_fee(self, telegram_id: str, nickname: str):
        """
        approve builder fee

        Args:
            telegram_id (str): Telegram ID
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/approve_builder_fee",
            json={"telegram_id": str(telegram_id), "nickname": nickname},
        )
        return response.data

    async def get_usdc_balances_all(self, telegram_id: str) -> List[USDCBalanceItem]:
        """
        Get USDC balances for multiple addresses.

        Args:
            addresses (List[str]): List of account addresses to check balances for.

        Returns:
            List[SpotBalanceMappingDTO]: List of SpotBalanceMappingDTO containing balances.
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/balance/usdc/all?telegram_id={telegram_id}",
        )
        return response.data

    async def get_usdc_balance_by_nickname(
        self, telegram_id: str, nickname: str
    ) -> USDCBalanceItem:
        """
        Get USDC balance for a specific account.

        Args:
            telegram_id (str): Telegram ID of the user.
            nickname (str): Nickname of the account.

        Returns:
            USDCBalanceItem: USDC balance item containing public key, nickname, spot USDC, and withdrawable amount.
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/balance/usdc?telegram_id={telegram_id}&nickname={nickname}",
        )
        return USDCBalanceItem(**response.data)

    async def get_withdrawable(self, public_key: str) -> float:
        """
        Get withdrawable amount for the user's account.

        Args:
            public_key (str): address.

        Returns:
            float: Withdrawable amount in USDC.
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/balance/withdrawable/precompile?public_key={public_key}",
        )
        return response.data

    async def get_spot_balance_precompile(
        self, public_key: str, tickers: List[str]
    ) -> dict:
        """
        Get spot balances for a specific account.

        Args:
            public_key (str): address.
            nickname (str): Nickname of the account.

        Returns:
            SpotBalanceMappingDTO: Spot balance mapping DTO containing balances and margin summary.
        """
        if not tickers:
            raise ValueError("Ticker list cannot be empty")
        query_param = "&".join([f"tickers={ticker}" for ticker in tickers])

        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/balance/spot/precompile?public_key={public_key}&{query_param}",
        )
        return response.data

    async def grid_status(
        self,
        public_key: str,
    ) -> None:
        """
        Send grid status notification.

        Args:
            public_key (str): Public key of the account.
            chat_id (str): Telegram chat ID to send the notification.
            interval (str): Time interval for the grid status (default is "1h").
            num_candles (int): Number of candles to include in the status (default is 30).
            boll_window (int): Bollinger band window size (default is 20).
        """

        response = await send_request(
            "GET",
            f"{BASE_URL}/account/grid/status/unit?public_key={public_key}",
        )
        return response.data

    async def spot_to_evm(
        self, telegram_id: str, nickname: str, ticker: str, amount: float
    ) -> bool:
        """
        Transfer USDC from spot to EVM wallet.

        Args:
            telegram_id (str): Telegram ID of the user.
            value (float): Amount of USDC to transfer.

        Returns:
            bool: True if the transfer was successful.
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/evm/spot_to_evm",
            json={
                "telegram_id": str(telegram_id),
                "nickname": nickname,
                "ticker": ticker,
                "amount": float(amount),
            },
        )
        return response.data

    async def evm_to_spot(
        self, telegram_id: str, nickname: str, ticker: str, amount: float
    ) -> bool:
        """
        Transfer USDC from EVM wallet to spot.

        Args:
            telegram_id (str): Telegram ID of the user.
            value (float): Amount of USDC to transfer.

        Returns:
            bool: True if the transfer was successful.
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/evm/evm_to_spot",
            json={
                "telegram_id": str(telegram_id),
                "nickname": nickname,
                "ticker": ticker,
                "amount": float(amount),
            },
        )
        return response.data

    async def wrap(self, telegram_id: str, nickname: str, amount: float) -> str:
        """
        Wrap HYPE to WHYPE.

        Args:
            telegram_id (str): Telegram ID of the user.
            nickname (str): Nickname of the account.
            amount (float): Amount of WHYPE to wrap.

        Returns:
            str: Transaction hash of the wrapping operation.
        """
        amount = amount - 0.1
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/evm/wrap",
            json={
                "telegram_id": str(telegram_id),
                "nickname": nickname,
                "amount": float(amount),
            },
        )
        return response.data

    async def unwrap(self, telegram_id: str, nickname: str, amount: float) -> str:
        """
        Unwrap WHYPE to HYPE.

        Args:
            telegram_id (str): Telegram ID of the user.
            nickname (str): Nickname of the account.
            amount (float): Amount of WHYPE to unwrap.

        Returns:
            str: Transaction hash of the unwrapping operation.
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/evm/unwrap",
            json={
                "telegram_id": str(telegram_id),
                "nickname": nickname,
                "amount": float(amount),
            },
        )
        return response.data

from hypurrquant.utils.singleton import Singleton
from hypurrquant.evm import Chain
from .utils import send_request, BASE_URL
from .models import BaseResponse, ReferralSummaryDict, AccountDto, EvmBalanceDto
from hypurrquant.logging_config import configure_logging

from typing import List

# ================================
# 설정 정보
# ================================
_logger = configure_logging(__name__)


# ================================
# 계좌 정보 서비스
# ================================
class AccountService(metaclass=Singleton):

    async def get_account_detail(self, public_key):
        """
        계좌 정보를 가져오는 메서드

        Args:
            public_key (str): Public Key

        Returns:
            AccountDto: 계좌 정보 DTO
        """
        response: BaseResponse = await send_request(
            "GET", f"{BASE_URL}/account/detail?public_key={public_key}"
        )
        return response.data

    async def get_account_by_account_type(
        self, telegram_id: str, account_type: str
    ) -> AccountDto:
        """
        Get account by account type.
        Args:
            telegram_id (str): Telegram ID of the user.
            account_type (str): Type of the account (e.g., "rebalance", "copytrading").
        Returns:
            AccountDto: Account DTO containing nickname, public key, active status, and builder fee approval.
        """
        _logger.debug(
            "Fetching account by type: %s for user: %s", account_type, telegram_id
        )
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/by_account_type?telegram_id={telegram_id}&account_type={account_type}",
        )
        return AccountDto(
            nickname=response.data["nickname"],
            public_key=response.data["public_key"],
            is_active=response.data["is_active"],
            is_approved_builder_fee=response.data["is_approved_builder_fee"],
        )

    async def create_account(
        self, telegram_id: str, nickname: str = "default"
    ) -> AccountDto:
        """
        EVM 계정 생성하는 메서드

        Returns:
            tuple: (address, secret_key)
        """

        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/create_account",
            json={"telegram_id": str(telegram_id), "nickname": nickname},
        )
        return AccountDto(
            nickname=response.data["nickname"],
            public_key=response.data["public_key"],
            is_active=response.data["is_active"],
            is_approved_builder_fee=response.data["is_approved_builder_fee"],
        )

    async def get_all_accounts(self, telegram_id: str) -> List[AccountDto]:
        """
        모든 계정 정보를 가져오는 메서드

        Returns:
            _type_: _description_
        """
        response: BaseResponse = await send_request(
            "GET", f"{BASE_URL}/account/all?telegram_id={telegram_id}"
        )
        print(response)
        accounts = response.data
        return [
            AccountDto(
                nickname=account["nickname"],
                public_key=account["public_key"],
                is_active=account["is_active"],
                is_approved_builder_fee=account["is_approved_builder_fee"],
            )
            for account in accounts
        ]

    async def active_account(self, telegram_id: str, nickname: str) -> AccountDto:
        """
        계정 활성화 메서드

        Args:
            telegram_id (str): Telegram ID
            nickname (str): 계정 별칭
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/activate",
            json={"telegram_id": str(telegram_id), "nickname": nickname},
        )
        return AccountDto(
            nickname=response.data["nickname"],
            public_key=response.data["public_key"],
            is_active=response.data["is_active"],
            is_approved_builder_fee=response.data["is_approved_builder_fee"],
        )

    async def import_account(self, telegram_id, private_key, nickname):
        """
        import account

        Args:
            telegram_id (str): Telegram ID
            private_key (str): Private Key
            nickname (str): Nickname
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/import_account",
            json={
                "telegram_id": str(telegram_id),
                "private_key": private_key,
                "nickname": nickname,
            },
        )
        return AccountDto(
            nickname=response.data["nickname"],
            public_key=response.data["public_key"],
            is_active=response.data["is_active"],
            is_approved_builder_fee=response.data["is_approved_builder_fee"],
        )

    async def delete_account(self, telegram_id, nickname):
        """
        import account

        Args:
            telegram_id (str): Telegram ID
            nickname (str): Nickname
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/delete_account",
            json={
                "telegram_id": str(telegram_id),
                "nickname": nickname,
            },
        )

    async def export_account(self, telegram_id) -> str:
        """
        import account

        Args:
            telegram_id (str): Telegram ID
            private_key (str): Private Key
            nickname (str): Nickname
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/export_account?telegram_id={telegram_id}",
        )
        return response.data["private_key"]

    async def send_chat_id(self, telegram_id, chat_id):
        """
        transfer USDC in between spot and perp wallet

        Args:
            secret_key (_type_): Secret Key
            value (float) : USDC
            is_spot (bool): True is Spot to perp,
                            False is perp to spot
        """
        _logger.debug(f"chat_id: {chat_id}")
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/chat_id",
            json={
                "telegram_id": str(telegram_id),
                "chat_id": str(chat_id),
            },
        )
        return True

    async def get_referral_code(self, telegram_id: str) -> str:
        """
        get referral code

        Args:
            telegram_id (str): Telegram ID
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/referral/code?telegram_id={str(telegram_id)}",
        )
        return response.data

    async def add_referral(self, referral_code, telegram_id: str) -> str:
        """
        add referral code

        Args:
            telegram_id (str): Telegram ID
        """
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/referral/add",
            json={
                "referral_code": referral_code,
                "referee_telegram_id": str(telegram_id),
            },
        )
        return response.data

    async def get_referral_summary(self, telegram_id: str) -> ReferralSummaryDict:
        """
        get referral summary

        Args:
            telegram_id (str): Telegram ID
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/referral/summary?telegram_id={telegram_id}",
        )
        return response.data

    async def get_evm_balances(self, public_key: str, addresses: List[str]) -> dict:
        """
        Get EVM balances for a specific account.

        Args:
            public_key (str): Public key of the account.
            tickers (List[str]): List of tickers to query balances for.

        Returns:
            dict: Dictionary containing EVM balances.
        """
        if not addresses:
            raise ValueError("Address list cannot be empty")
        query_param = "&".join([f"addresses={address}" for address in addresses])

        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/evm/balance?public_key={public_key}&{query_param}",
        )
        return response.data

    async def get_evm_native(
        self, public_key: str, chain: Chain = Chain.HYPERLIQUID
    ) -> float:
        """
        Get the EVM native balance for a specific account.

        Args:
            public_key (str): Public key of the account.

        Returns:
            float: EVM hype value.
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/evm/balance/native",
            params={"public_key": public_key, "chain": chain},
        )
        return response.data

    async def get_native_wrapped(
        self, public_key: str, chain: Chain = Chain.HYPERLIQUID
    ):
        """
        Get WHYPE balance for the user's account.

        Returns:
            float: WHYPE balance.
        """
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/evm/balance/wrapped",
            params={"public_key": public_key, "chain": chain},
        )
        return response.data

    async def get_evm_balance_for_ui(
        self, public_key: str, addresses: List[str], chain: Chain = Chain.HYPERLIQUID
    ) -> EvmBalanceDto:
        """
        Get EVM balances for UI display.

        Args:
            public_key (str): Public key of the account.

        Returns:
            dict: Dictionary containing EVM balances formatted for UI.
        """
        if not addresses:
            raise ValueError("Address list cannot be empty")
        query_param = "&".join([f"addresses={address}" for address in addresses])
        response: BaseResponse = await send_request(
            "GET",
            f"{BASE_URL}/account/evm/balance/ui?chain={chain}&public_key={public_key}&{query_param}",
        )
        return response.data

    async def get_evm_managed_token(self, chain: Chain) -> List[str]:
        response: BaseResponse = await send_request(
            "GET", f"{BASE_URL}/dex/managed-tokens", params={"chain": chain}
        )
        return response.data

    async def send_erc20(
        self,
        telegram_id: str,
        nickname: str,
        to_address: str,
        token_address: str,
        raw_amount: int,
        chain: Chain,
    ) -> bool:
        """
        Send ERC20 tokens.

        Args:
            telegram_id (str): Telegram ID of the user.
            nickname (str): Nickname of the user.
            to_address (str): Recipient address.
            amount (float): Amount to send.
            token_address (str): Token address.

        Returns:
            str: Transaction hash.
        """
        _logger.debug(
            f"Sending ERC20 tokens: {telegram_id}, {nickname}, {to_address}, {raw_amount}, {token_address}, {chain}"
        )
        response: BaseResponse = await send_request(
            "POST",
            f"{BASE_URL}/account/evm/send",
            json={
                "telegram_id": str(telegram_id),
                "nickname": nickname,
                "to_address": to_address,
                "token_address": token_address,
                "raw_amount": raw_amount,
            },
            params={"chain": chain},
        )
        _logger.debug(f"ERC20 send response: {response}")
        return response.data

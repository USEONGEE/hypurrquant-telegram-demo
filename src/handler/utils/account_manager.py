from api import (
    AccountDto,
    AccountService,
)
from api.hyperliquid import (
    PerpBalanceMappingDTO,
    SpotBalanceMappingDTO,
    RebalanceService,
    HLAccountService,
    CopytradingService,
)
from hypurrquant.models.account import Account
from handler.models.spot_balance import SpotBalanceMapping
from handler.models.perp_balance import PerpBalanceMapping
from hypurrquant.logging_config import configure_logging

from pydantic import BaseModel, Field, PrivateAttr
import time
from typing import List, Optional
from asyncio import Lock
import asyncio

accountService = AccountService()
rebalanceService = RebalanceService()
hlAccountService = HLAccountService()
copytradingService = CopytradingService()


logger = configure_logging(__name__)


# ================================
# Account를 보관하는 Utility Manager
# ================================
class AccountManager(BaseModel):
    telegram_id: str
    active_account: Optional[Account] = None
    spot_balance_mapping: Optional[SpotBalanceMapping] = None
    perp_balance_mapping: Optional[PerpBalanceMapping] = None
    spot_last_refresh_time: float = Field(default=0.0)
    perp_last_refresh_time: float = Field(default=0.0)
    refresh_all_last_refresh_time: float = Field(default=0.0)

    # Private fields for locks
    _account_lock: Lock = PrivateAttr(default_factory=Lock)
    _spot_refresh_lock: Lock = PrivateAttr(default_factory=Lock)
    _perp_refresh_lock: Lock = PrivateAttr(default_factory=Lock)
    _refresh_all_lock: Lock = PrivateAttr(default_factory=Lock)

    # ================================
    # getter 메소드
    # ================================
    async def get_spot_balance_mapping(
        self, account: Account = None
    ) -> SpotBalanceMapping:
        if not account:
            account: Account = await self.get_active_account()
        await self.refresh_spot_balance(account)

        if not self.spot_balance_mapping:
            raise ValueError("No spot balance mapping")
        return self.spot_balance_mapping

    async def get_perp_balance_mapping(
        self, account: Account = None
    ) -> PerpBalanceMapping:
        if not account:
            account: Account = await self.get_active_account()
        await self.refresh_perp_balance(account)

        if not self.perp_balance_mapping:
            raise ValueError("No perp balance mapping")
        return self.perp_balance_mapping

    async def get_active_account(self, force=False) -> Account:
        if force:
            account_list: List[Account] = await self.get_all_accounts()
            for account in account_list:
                if account.is_active:
                    self.active_account = account

        if not self.active_account or not self.active_account.is_active:
            account_list: List[Account] = await self.get_all_accounts()
            for account in account_list:
                if account.is_active:
                    self.active_account = account

        if not self.active_account:  # 서버 에러임
            logger.error(f"telegram_id: {self.telegram_id} No active account")
            raise ValueError("No active account")

        return self.active_account

    async def get_all_accounts(self) -> List[Account]:
        accounts: List[AccountDto] = await accountService.get_all_accounts(
            self.telegram_id
        )
        return [
            Account(
                nickname=ac.nickname,
                public_key=ac.public_key,
                is_active=ac.is_active,
                is_approved_builder_fee=ac.is_approved_builder_fee,
            )
            for ac in accounts
        ]

    async def get_rebalance_account(self) -> Optional[Account]:
        account_dto: AccountDto = await hlAccountService.get_rebalance_account(
            self.telegram_id
        )
        if not account_dto:
            return None

        account = Account(
            nickname=account_dto.nickname,
            public_key=account_dto.public_key,
            is_active=account_dto.is_active,
            is_approved_builder_fee=account_dto.is_approved_builder_fee,
        )
        return account

    async def get_copytrading_account(self) -> Optional[Account]:
        account_dto: AccountDto = await hlAccountService.get_copytrading_account(
            self.telegram_id
        )
        if not account_dto:
            return None

        account = Account(
            nickname=account_dto.nickname,
            public_key=account_dto.public_key,
            is_active=account_dto.is_active,
            is_approved_builder_fee=account_dto.is_approved_builder_fee,
        )
        return account

    # ================================
    # refresh 메소드
    # ================================
    async def _refresh_perp_balance(self, account: Account):
        dto_resposne: PerpBalanceMappingDTO = await hlAccountService.get_perp_balance(
            self.telegram_id, account.nickname
        )
        perp_balance_mapping = PerpBalanceMapping.model_validate(
            dto_resposne.model_dump()
        )
        self.perp_balance_mapping = perp_balance_mapping

    async def refresh_perp_balance(
        self,
        account: Optional[Account] = None,
        force: bool = False,
        max_age: float = 10.0,
    ) -> Optional[PerpBalanceMapping]:
        """
        - force: 무조건 갱신할지 여부
        - max_age: 캐싱된 데이터의 최대 유효 시간 (초 단위)
        """
        async with self._perp_refresh_lock:
            if not account:
                account = await self.get_active_account()

            current_time = time.time()

            # 강제 갱신이 필요한 경우
            if force:
                await self._refresh_perp_balance(account)
                return self.perp_balance_mapping

            # 캐싱된 데이터가 유효한지 확인
            if (
                current_time - self.perp_last_refresh_time
            ) < max_age and self.perp_balance_mapping:
                return self.perp_balance_mapping

            # 캐시가 만료되었거나 데이터가 없는 경우 갱신
            await self._refresh_perp_balance(account)
            self.perp_last_refresh_time = current_time
            return self.perp_balance_mapping

    async def _refresh_spot_balance(self, account: Account):

        dto_resposne: SpotBalanceMappingDTO = await hlAccountService.get_spot_balance(
            self.telegram_id, account.nickname
        )
        spot_balance_mapping = SpotBalanceMapping.model_validate(
            dto_resposne.model_dump()
        )
        self.spot_balance_mapping = spot_balance_mapping

    async def refresh_spot_balance(
        self,
        account: Optional[Account] = None,
        force: bool = False,
        max_age: float = 10.0,
    ) -> SpotBalanceMapping:
        """
        SpotBalanceMapping을 갱신한다.
        - force: 무조건 갱신할지 여부
        - max_age: 캐싱된 데이터의 최대 유효 시간 (초 단위)
        """
        async with self._spot_refresh_lock:
            if not account:
                account = await self.get_active_account()

            current_time = time.time()

            # 강제 갱신이 필요한 경우
            if force:
                await self._refresh_spot_balance(account)
                return self.spot_balance_mapping

            # 캐싱된 데이터가 유효한지 확인
            if (
                current_time - self.spot_last_refresh_time
            ) < max_age and self.spot_balance_mapping:
                return self.spot_balance_mapping

            # 캐시가 만료되었거나 데이터가 없는 경우 갱신
            await self._refresh_spot_balance(account)
            self.spot_last_refresh_time = current_time
            return self.spot_balance_mapping

    async def refresh_all(
        self,
        account: Account = None,
        force=False,
        max_age: float = 10.0,
    ):
        async with self._refresh_all_lock:
            if not account:
                account = await self.get_active_account()
                # 여기는 동기적으로 처리해도 되지만, 원한다면 여기에도 gather를 쓸 수 있습니다
                await asyncio.gather(
                    self._refresh_spot_balance(account),
                    self._refresh_perp_balance(account),
                )
                return self.spot_balance_mapping, self.perp_balance_mapping

            current_time = time.time()
            should_refresh = not (
                (current_time - self.refresh_all_last_refresh_time) < max_age
                and self.spot_balance_mapping
                and self.perp_balance_mapping
            )

            if force or should_refresh:
                # spot, perp를 병렬로 한 번에 요청
                await asyncio.gather(
                    self._refresh_spot_balance(account),
                    self._refresh_perp_balance(account),
                )
                self.refresh_all_last_refresh_time = current_time
                return self.spot_balance_mapping, self.perp_balance_mapping

            # 갱신 안 해도 될 때
            return self.spot_balance_mapping, self.perp_balance_mapping

    # ================================
    # wallet-setting에서 사용
    # ================================
    async def create_wallet(self, nickname: str = "default") -> Account:
        accounts: List[Account] = await self.get_all_accounts()
        for account in accounts:
            if account.nickname == nickname:
                raise ValueError("Nickname already exists")

        async with self._account_lock:
            account_dto: AccountDto = await accountService.create_account(
                self.telegram_id, nickname
            )
            account = Account(
                nickname=account_dto.nickname,
                public_key=account_dto.public_key,
                is_active=account_dto.is_active,
                is_approved_builder_fee=account_dto.is_approved_builder_fee,
            )
            return account

    async def import_wallet(self, private_key: str, nickname: str) -> Account:
        async with self._account_lock:
            account_dto: AccountDto = await accountService.import_account(
                self.telegram_id, private_key, nickname
            )

            if account_dto is None:
                raise ValueError("Failed to import account")

            account = Account(
                nickname=account_dto.nickname,
                public_key=account_dto.public_key,
                is_active=account_dto.is_active,
                is_approved_builder_fee=account_dto.is_approved_builder_fee,
            )
            return account

    async def change_wallet(self, nickname: str) -> Account:
        async with self._account_lock:
            response: AccountDto = await accountService.active_account(
                self.telegram_id, nickname
            )

            account: Account = Account(
                nickname=response.nickname,
                public_key=response.public_key,
                is_active=response.is_active,
                is_approved_builder_fee=response.is_approved_builder_fee,
            )

            logger.info(f"prev active wallet: {self.active_account.nickname}")
            self.active_account = account
            logger.info(f"new active wallet: {self.active_account.nickname}")
            await self.refresh_all(account, force=True)

            return self.active_account

    async def delete_wallet(self, nickname: str):
        async with self._account_lock:
            await accountService.delete_account(self.telegram_id, nickname)

            account: Account = await self.get_active_account(force=True)
            self.active_account = account
            await self.refresh_all(account, force=True)

            return self.active_account

    async def change_rebalance_account(self, nickname: str):
        async with self._account_lock:
            await rebalanceService.register_rebalance_account(
                self.telegram_id, nickname
            )

    async def change_copytrading_account(self, nickname: str):
        async with self._account_lock:
            await copytradingService.register_copytrading_account(
                self.telegram_id, nickname
            )

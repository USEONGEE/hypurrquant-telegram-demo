from telegram.ext import (
    ContextTypes,
)

from api import AccountService, AccountDto
from hypurrquant.models.account import Account
from handler.utils.account_manager import AccountManager
from handler.models.spot_balance import SpotBalance
from hypurrquant.logging_config import configure_logging

from typing import List, Dict

logger = configure_logging(__name__)

# ================================
# 외부 API
# ================================
accountService = AccountService()

ACCOUNT_MANAGER_KEY = "account_manager"


# ================================
# AccountManager 가져오기
# ================================
async def fetch_account_manager(context: ContextTypes.DEFAULT_TYPE) -> AccountManager:
    if context.user_data.get(ACCOUNT_MANAGER_KEY):
        return context.user_data[ACCOUNT_MANAGER_KEY]

    account_manager = AccountManager(telegram_id=str(context._user_id))
    await account_manager.refresh_all(force=True)
    context.user_data[ACCOUNT_MANAGER_KEY] = account_manager

    return account_manager


async def fetch_active_account(
    context: ContextTypes.DEFAULT_TYPE, force: bool = False
) -> Account:
    """
    현재 활성화된 계정을 가져옵니다.
    만약 활성화된 계정이 없다면, AccountManager를 통해 새로 가져옵니다.
    """
    account_manager: AccountManager = await fetch_account_manager(context)
    active_account: Account = await account_manager.get_active_account(force=force)

    if not active_account:
        raise ValueError(
            "Something went wrong. No active account found. Please contact support."
        )

    return active_account


# ================================
# SPOT USDC 편의 메소드
# ================================
async def fetch_active_wallet_usdc_balance(context: ContextTypes.DEFAULT_TYPE) -> float:
    account_manager: AccountManager = await fetch_account_manager(context)
    spot_balance_mapping = await account_manager.get_spot_balance_mapping()
    return spot_balance_mapping.usdc_balance


# ================================
# 현재 잔고와 보유 종목, 수익률 정보 가져오기
# ================================
async def fetch_balance_and_portfolio(
    context: ContextTypes.DEFAULT_TYPE,
) -> Dict[str, List[SpotBalance]]:
    account_manager: AccountManager = await fetch_account_manager(context)
    spot_balance_mapping = await account_manager.get_spot_balance_mapping()
    spot_balance: List[SpotBalance] = list(spot_balance_mapping.balances.values())

    return {"spot": spot_balance}

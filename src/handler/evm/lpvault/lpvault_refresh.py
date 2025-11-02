from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.account import AccountService
from api.lpvault import LpVaultService
from handler.utils.utils import answer
from .lpvault_start import lpvault_command

logger = configure_logging(__name__)

account_service = AccountService()
lp_vault_service = LpVaultService()


@force_coroutine_logging
async def lpvault_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    return await lpvault_command(update, context)

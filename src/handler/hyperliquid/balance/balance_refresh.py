from telegram import Update, Update
from telegram.ext import (
    ContextTypes,
)

from .balance_start import balance_start
from .states import BalanceStates
from .settings import RefreshSetting
from handler.utils.utils import answer, send_or_edit
from handler.utils.cancel import main_menu, initialize_handler
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)

logger = configure_logging(__name__)


@force_coroutine_logging
@initialize_handler(setting_cls=RefreshSetting)
async def balance_refresh_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    setting: RefreshSetting = RefreshSetting.get_setting(context)
    await answer(update)

    account_holder: AccountManager = await fetch_account_manager(context)
    await account_holder.refresh_all()

    await send_or_edit(update, context, "Success")
    await balance_start(update, context)
    return await main_menu(update, context, setting.return_to)

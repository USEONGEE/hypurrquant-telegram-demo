from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api.exception import RebalanceAccountNotRegisteredException
from api import AccountService
from api.hyperliquid import RebalanceService
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from handler.utils.cancel import create_cancel_inline_button
from handler.command import Command
from .states import *
from .utils import generate_info_text
from .settings import RebalanceSetting
from handler.utils.utils import answer, send_or_edit

logger = configure_logging(__name__)

account_service = AccountService()
rebalance_service = RebalanceService()


@force_coroutine_logging
async def rebalance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    account_hodler: AccountManager = await fetch_account_manager(context)
    try:
        response = await account_hodler.get_rebalance_account()
        RebalanceSetting.get_setting(context).account = response
        logger.info(response)
        logger.info("리밸런싱 계좌 정보 가져오기 성공")
    except (
        RebalanceAccountNotRegisteredException
    ) as e:  # 리밸런싱 계좌가 등록되어 있지 않은 경우
        keyboard = [
            [
                InlineKeyboardButton(
                    "Register Account", callback_data=SelectStates.START.value
                )
            ]
        ]

        # TODO send_or_edit 함수로 변경
        await send_or_edit(
            update,
            context,
            "The alarm account is not registered. Please register an account.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return RebalanceStates.SELECT_ACTION
    except Exception as e:
        logger.error(e)
        await send_or_edit(
            update,
            context,
            "There was a problem retrieving the alarm account information. Please try again.",
        )
        return ConversationHandler.END

    # 리밸런싱 계좌가 등록된 경우
    message = await generate_info_text(context=context)
    keyboard = [
        [
            InlineKeyboardButton(
                "Select Account", callback_data=SelectStates.START.value
            ),
        ],
        [
            InlineKeyboardButton(
                "Set PNL(%) Alert Target", callback_data=PnlStates.START.value
            ),
        ],
        [
            InlineKeyboardButton(
                "Enable/Disable PNL(%) Alert",
                callback_data=RebalanceStates.TOGGLE_ALARM.value,
            ),
        ],
        [
            InlineKeyboardButton(
                "Unregister", callback_data=UnregisterStates.START.value
            ),
        ],
        [
            InlineKeyboardButton("refresh", callback_data=RefreshStates.START.value),
        ],
        [create_cancel_inline_button(Command.HYPERLIQUID_CORE_START)],
        # [
        #     InlineKeyboardButton(
        #         "자동 매매 On/Off",
        #         callback_data=RebalanceStates.TOGGLE_AUTO_TRADING.value,
        #     ),
        # ],
    ]

    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
    return RebalanceStates.SELECT_ACTION


@force_coroutine_logging
async def rebalance_alarm_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await update.callback_query.answer()
    await rebalance_service.update_pnl_alarm_toggle_rebalancing(context._user_id)

    await update.callback_query.edit_message_text(
        "PNL target alert preference has been changed.", parse_mode="Markdown"
    )
    await rebalance_start(update, context)
    return RebalanceStates.SELECT_ACTION


@force_coroutine_logging
async def rebalance_auto_trading_toggle(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await update.callback_query.answer()
    await rebalance_service.update_auto_trading_toggle_rebalancing(context._user_id)

    await update.callback_query.edit_message_text(
        "Auto trading settings have been changed.", parse_mode="Markdown"
    )
    await rebalance_start(update, context)
    return RebalanceStates.SELECT_ACTION

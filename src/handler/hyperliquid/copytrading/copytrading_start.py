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
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from handler.utils.cancel import create_cancel_inline_button
from handler.command import Command
from .states import *
from .utils import generate_info_text
from .settings import CopytradingSetting
from handler.utils.utils import answer, send_or_edit

logger = configure_logging(__name__)

account_service = AccountService()


@force_coroutine_logging
async def copytrading_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    account_hodler: AccountManager = await fetch_account_manager(context)
    try:
        logger.info("copytrading 계좌 정보 가져오기")
        response = await account_hodler.get_copytrading_account()
        copytrading_setting = CopytradingSetting.get_setting(context)
        copytrading_setting.account = response
        logger.info(response)
        logger.info("copytrading 계좌 정보 가져오기 성공")
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

        await update.effective_message.reply_text(
            "The copy trading account is not registered. Please register an account.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return CopytradingStates.SELECT_ACTION
    except Exception as e:
        logger.exception("Error fetching copy trading account information")
        await update.effective_message.reply_text(
            "There was a problem retrieving the copy traidng account information. Please try again."
        )
        return ConversationHandler.END

    # 리밸런싱 계좌가 등록된 경우
    message = await generate_info_text(context=context)
    keyboard = [
        [
            InlineKeyboardButton(
                "Subscribe", callback_data=SubscribeStates.START.value
            ),
            InlineKeyboardButton(
                "UnSubscribe", callback_data=UnsubscribeStates.START.value
            ),
        ],
        [
            InlineKeyboardButton(
                "Follow the others", callback_data=FollowStates.START.value
            ),
        ],
        [
            InlineKeyboardButton(
                "Set PNL(%) Target", callback_data=PnlStates.START.value
            ),
            InlineKeyboardButton(
                "Set Leverage ", callback_data=LeverageStates.START.value
            ),
        ],
        [
            InlineKeyboardButton(
                "Set Order Size ", callback_data=OrderValueStates.START.value
            ),
            InlineKeyboardButton(
                "Copy Trading Type ", callback_data=SellTypeStates.START.value
            ),
        ],
        [
            InlineKeyboardButton(
                "Unregister", callback_data=UnregisterStates.START.value
            ),
        ],
        [
            InlineKeyboardButton("Set Account", callback_data=SelectStates.START.value),
            InlineKeyboardButton("refresh", callback_data=RefreshStates.START.value),
        ],
        [create_cancel_inline_button(Command.HYPERLIQUID_CORE_START)],
    ]
    await send_or_edit(
        update,
        context,
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2",
    )
    return CopytradingStates.SELECT_ACTION

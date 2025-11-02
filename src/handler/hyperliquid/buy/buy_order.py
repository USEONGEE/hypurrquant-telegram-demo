from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from api.hyperliquid import BuyOrderService

from handler.command import Command
from .settings import (
    BuySetting,
    OrderSetting,
)
from .pagenations import ConfirmPagination
from .states import OrderStates
from .utils import (
    get_needed_balance,
    MINIMUM_PER_ORDER,
    is_sufficient_balance,
)


from handler.utils.account_helpers import (
    fetch_active_wallet_usdc_balance,
    fetch_account_manager,
)
from hypurrquant.models.account import Account
from handler.utils.account_manager import AccountManager
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)

from typing import List


logger = configure_logging(__name__)

# =============== #

buyOrderService = BuyOrderService()

CALLBACK_PREFIX = "BUY_ORDER"


# =============== #
# 1) 엔트리 함수  #
# =============== #
@force_coroutine_logging
async def start_stock_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    logger.debug("start_stock_selection")
    query = update.callback_query
    await query.answer()

    buy_setting: BuySetting = BuySetting.get_setting(context)
    order_setting: OrderSetting = OrderSetting.get_setting(context)
    order_setting.pagination = ConfirmPagination(
        market_data=buy_setting.orderable_market_data, page_size=15
    )

    buy_setting = BuySetting.get_setting(context)
    buy_setting.orderable_market_data = order_setting.pagination.data

    needed_balance = get_needed_balance(buy_setting.orderable_market_data)
    balance = await fetch_active_wallet_usdc_balance(context)

    message = f"How much would you like to purchase?\n\n"
    message += f"💰 Max USDC: {balance}\n"
    message += f"💰 Min USDC: {needed_balance}\n\n"
    message += f"Please choose carefully, as your input cannot be canceled."

    await update.callback_query.edit_message_text(
        message,
        parse_mode="Markdown",
    )
    logger.debug("PURCHASE_AMOUNT_SELECTION로 넘어가야 한다.")
    return OrderStates.PURCHASE_AMOUNT_SELECTION


# =============== #
# 2) 주문   #
# =============== #
@force_coroutine_logging
async def purchase_amount_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    구매량 선택
    """
    logger.debug("purchase_amount_selection")
    message = update.message

    # validaiton: 숫자만 허용
    try:
        value = float(message.text)
    except ValueError:
        await message.reply_text(f"Please enter a number. Try again. /{Command.BUY}")
        return ConversationHandler.END

    # validation: 주문 내역 검증
    request_body = await create_order_body(update, context, value)
    if not request_body:
        return ConversationHandler.END
    logger.debug(f"request_body: {request_body}")
    response = await buyOrderService.buy_order_market_usdc(
        context._user_id, request_body
    )

    if response:
        account_hodler: AccountManager = await fetch_account_manager(context)
        await account_hodler.refresh_spot_balance(force=True)
        await message.reply_text(
            f"Success! You can check your order history using /{Command.BALANCE}"
        )
        return ConversationHandler.END
    else:
        await message.reply_text("Failed to place the order. Please try again later.")
        return ConversationHandler.END


async def create_order_body(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    value: float,
) -> List[dict]:

    logger.debug(f"order_value = {value}")

    # 잔액 재조회
    account_hodler: AccountManager = await fetch_account_manager(context)
    await account_hodler.refresh_spot_balance(force=True)
    balance: float = await fetch_active_wallet_usdc_balance(context)

    order_setting: OrderSetting = OrderSetting.get_setting(context)
    orderable_data = order_setting.pagination.data
    # 구매할 종목만 필터링
    selected_stocks = [data for data in orderable_data if data.is_buy]

    # validaiton: 선택된 종목이 없을 경우
    if not selected_stocks:
        await update.effective_message.reply_text(
            "No stocks selected. Please select at least one stock to proceed."
        )
        return None

    per_stock_value = value / len(selected_stocks)

    # validaiton: 최소 주문 금액
    if per_stock_value < MINIMUM_PER_ORDER:
        await update.effective_message.reply_text(
            f"You have insufficient balance to place the order. Try again. /{Command.BUY}"
        )
        return None

    # validaiton: 최소 주문 금액
    if not is_sufficient_balance(selected_stocks, balance):
        await update.effective_message.reply_text(
            f"You have insufficient balance to place the order. Try again. /{Command.BUY}"
        )
        return None

    # 주문 바디 생성
    body = [
        {"name": stock.Tname, "value": round(per_stock_value, 2)}
        for stock in selected_stocks
    ]

    return body


order_states = {
    OrderStates.START: [
        CallbackQueryHandler(start_stock_selection, pattern="^GO_ORDER")
    ],
    OrderStates.PURCHASE_AMOUNT_SELECTION: [
        MessageHandler(filters.TEXT, purchase_amount_selection)
    ],
}

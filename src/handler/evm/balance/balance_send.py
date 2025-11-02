from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from hypurrquant.evm import Chain
from api import AccountService, EvmBalanceItemDto
from .states import SendState
from .settings import SendUsdcSetting, EvmBalanceSetting
from .pagination import EvmSendPagination
from handler.utils.cancel import (
    main_menu,
    initialize_handler,
    create_cancel_inline_button,
)
from handler.utils.account_helpers import fetch_account_manager
from handler.utils.account_manager import AccountManager
from handler.utils.utils import send_or_edit, answer

import asyncio
from decimal import Decimal, getcontext, ROUND_DOWN

getcontext().prec = 50
getcontext().rounding = ROUND_DOWN

logger = configure_logging(__name__)
account_service = AccountService()
CALLBACK_PREFIX = "EVMBALANCE_SEND"

CHAIN = Chain.HYPERLIQUID


# ================================
# 1) 시작
# ================================
@force_coroutine_logging
@initialize_handler(setting_cls=SendUsdcSetting)
async def send_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    setting = SendUsdcSetting.get_setting(context)
    evm_setting = EvmBalanceSetting.get_setting(context)
    # 1. 계좌 조회
    account_manager: AccountManager = await fetch_account_manager(context)
    account_list, active_account = await asyncio.gather(
        account_manager.get_all_accounts(), account_manager.get_active_account()
    )
    # 2. Pagination setting
    if evm_setting.pagination:
        evm_balance_dto = evm_setting.pagination.raw_data
    else:
        addresses = await account_service.get_evm_managed_token(CHAIN)
        evm_balance_dto = await account_service.get_evm_balance_for_ui(
            active_account.public_key, addresses
        )
    setting.pagination = EvmSendPagination(evm_balance_dto, CHAIN)

    if len(setting.pagination.data) < 1:
        await send_or_edit(
            update,
            context,
            "You have no tokens to send.",
            parse_mode="Markdown",
        )
        await asyncio.sleep(1)
        return await main_menu(update, context, setting.return_to)

    # 3. 계좌 선택
    message = "Which account would you like to send to?\n\n"
    kb = []

    for account in account_list:
        if account.nickname == active_account.nickname:
            continue
        kb.append(
            [
                InlineKeyboardButton(
                    text=f"{account.nickname}({account.public_key[:4]}...{account.public_key[-4:]})",
                    callback_data=f"evm_ac_se|{account.public_key}",
                )
            ]
        )

    kb.append([create_cancel_inline_button(setting.return_to)])
    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

    return SendState.SELECT_ACCOUNT


# ================================
# 2) 도착 계좌 선택
# ================================
@force_coroutine_logging
async def select_dest_acct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    setting = SendUsdcSetting.get_setting(context)

    # 1. 도착지 계좌 데이터 추출하기
    if update.message:
        dest_addr = str(update.message.text)
    elif update.callback_query:
        query = update.callback_query
        await answer(update)
        dest_addr = str(query.data.split("|")[1])
    else:
        await update.effective_message.reply_text(
            "Please enter a valid account public key."
        )
        return ConversationHandler.END
    logger.debug(f"destination_account: {dest_addr}")
    setting.destination_address = dest_addr

    # 2. 메세지, 키보드 생성(취소 버튼 포함)
    message = "Which token would you like to send?\n\n"
    message += setting.pagination.generate_info_text()
    kb: list[list] = setting.pagination.generate_buttons(CALLBACK_PREFIX)
    kb[-1].append(create_cancel_inline_button(setting.return_to))

    await send_or_edit(
        update,
        context,
        message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb),
    )

    return SendState.SELECT_TOKEN


# ================================
# 3) 토큰 선택
# ================================
@force_coroutine_logging
async def select_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    # 1. 사용자가 선택한 토큰 정보 가져오기
    data = update.callback_query.data
    token_address = data.split("|")[1]
    setting = SendUsdcSetting.get_setting(context)

    # 2. 사용자가 선택한 토큰 metadata 저장
    setting.selected_item = (
        setting.pagination.raw_data["erc20"].get(token_address)
        or setting.pagination.raw_data["wrapped"]
    )
    logger.debug(f"select_token {setting.selected_item=}")

    # 3. 메시지 생성
    message = f"You have selected *{setting.selected_item['ticker']}*.\n"
    message += f"Your balance is *{setting.selected_item['decimal_amount']:.4f} {setting.selected_item['ticker']}*.\n"
    message += (
        "How much would you like to send?\n If you want to send all, please type `all`."
    )

    kb = [[create_cancel_inline_button(setting.return_to)]]

    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return SendState.SELECT_AMOUNT


# ================================
# 4) 토큰 금액 선택
# ================================
@force_coroutine_logging
async def select_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    setting = SendUsdcSetting.get_setting(context)

    # 1. 사용자가 입력한 금액 가져오기
    if update.message:
        amount_str = str(update.message.text).strip().lower()
    else:
        await update.effective_message.reply_text(
            "Please enter a valid amount to send."
        )
        return ConversationHandler.END
    logger.debug(f"amount_str: {amount_str}")
    # 2. 금액 유효성 검사
    selected_token: EvmBalanceItemDto = setting.selected_item
    if amount_str == "all":
        setting.amount = selected_token["raw_amount"]
    else:
        try:
            if not (
                0
                < Decimal(amount_str)
                <= Decimal(selected_token["raw_amount"])
                / Decimal(10) ** selected_token["decimal"]
            ):
                await update.effective_message.reply_text(
                    "Insufficient balance. Please enter a lower amount."
                )
                return ConversationHandler.END
            setting.amount = int(
                Decimal(amount_str) * Decimal(10) ** selected_token["decimal"]
            )
        except Exception:
            await update.effective_message.reply_text(
                "Please enter a valid amount to send."
            )
            return ConversationHandler.END
    show_amount = setting.amount / (10 ** selected_token["decimal"])
    # 3. 확인 메세지 보내기
    message = f"You are about to send *{show_amount:.4f} {selected_token['ticker']}* to address *{setting.destination_address}*.\n"
    kb = [
        [
            InlineKeyboardButton(
                text="Confirm",
                callback_data=f"{SendState.CONFIRM}|ok",
            ),
            create_cancel_inline_button(setting.return_to),
        ]
    ]
    await send_or_edit(
        update,
        context,
        message,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

    return SendState.CONFIRM


# ================================
# 5) 전송 확인
# ================================
@force_coroutine_logging
async def confirm_send(update: Update, context: ContextTypes.DEFAULT_TYPE):

    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    setting = SendUsdcSetting.get_setting(context)
    account_manager = await fetch_account_manager(context)
    active_account = await account_manager.get_active_account()

    # 1. 전송 트랜잭션 생성 및 서명
    is_success = await account_service.send_erc20(
        telegram_id=context._user_id,
        nickname=active_account.nickname,
        to_address=setting.destination_address,
        raw_amount=setting.amount,
        token_address=setting.selected_item["address"],
        chain=CHAIN,
    )

    message = (
        "success."
        if is_success
        else "Something went wrong during the transaction. Please try again later."
    )

    await send_or_edit(
        update,
        context,
        message,
        parse_mode="Markdown",
    )
    return await main_menu(update, context, setting.return_to)


send_state = {
    SendState.SELECT_ACCOUNT: [
        MessageHandler(filters.TEXT & ~filters.COMMAND, select_dest_acct),
        CallbackQueryHandler(
            callback=select_dest_acct,
            pattern=f"^evm_ac_se",
        ),
    ],
    SendState.SELECT_TOKEN: [
        CallbackQueryHandler(callback=select_token, pattern=f"^{CALLBACK_PREFIX}")
    ],
    SendState.SELECT_AMOUNT: [MessageHandler(filters.TEXT, select_amount)],
    SendState.CONFIRM: [
        CallbackQueryHandler(callback=confirm_send, pattern=f"^{SendState.CONFIRM}")
    ],
}

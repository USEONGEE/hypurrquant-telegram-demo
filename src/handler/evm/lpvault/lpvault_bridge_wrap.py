from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api import AccountService
from api.hyperliquid import BuyOrderService, HLAccountService
from handler.utils.utils import answer, send_or_edit
from .cancel import cancel_keyboard_button
from .states import LpvaultBridgeWrapState
from .settings import *
from .lpvault_start import lpvault_command
import asyncio

logger = configure_logging(__name__)

account_service = AccountService()
buy_order_service = BuyOrderService()
hl_account_service = HLAccountService()

MIN_USDC = 20.0
MIN_HYPE = 0.2


@force_coroutine_logging
async def lpvault_bridge_wrap_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    await send_or_edit(
        update,
        context,
        "Loading 🔄",
        parse_mode="Markdown",
    )
    LpvaultBridgeWrapSetting.clear_setting(context)
    setting = LpvaultBridgeWrapSetting.get_setting(context)
    account = LpvaultSetting.get_setting(context).account
    response, usdc_balance_dict, evm_hype = await asyncio.gather(
        hl_account_service.get_spot_balance_precompile(
            account.public_key, ["HYPE", "USDC"]
        ),
        hl_account_service.get_usdc_balance_by_nickname(
            str(context._user_id), account.nickname
        ),
        account_service.get_evm_native(account.public_key),
    )
    spot_hype = response.get("HYPE", 0.0)
    spot_usdc = response.get("USDC", 0.0)
    perp_usdc = usdc_balance_dict.get("withdrawable", 0.0)

    setting.spot_usdc = spot_usdc
    setting.spot_hype = spot_hype
    setting.evm_hype = evm_hype
    setting.perp_usdc = perp_usdc
    text = f"You can bridge your Hyperliquid Core assets to WHYPE. Choose one of your assets—USDC (minimum 20), HYPE (Core) (minimum {MIN_HYPE}), or HYPE (EVM) (minimum {MIN_HYPE}, \nThen click the button labeled with the asset you’d like to convert."
    kb = []

    if spot_usdc > MIN_USDC:
        kb.append(
            [
                InlineKeyboardButton(
                    f"USDC (Spot): {spot_usdc:.2f}",
                    callback_data=f"{LpvaultBridgeWrapState.SELECT.value}_USDCSPOT",
                )
            ]
        )

    if perp_usdc > MIN_USDC:
        kb.append(
            [
                InlineKeyboardButton(
                    f"USDC (Perp): {perp_usdc:.2f}",
                    callback_data=f"{LpvaultBridgeWrapState.SELECT.value}_USDCPERP",
                )
            ]
        )

    if spot_hype > MIN_HYPE:
        kb.append(
            [
                InlineKeyboardButton(
                    f"HYPE (Core): {spot_hype:.2f}",
                    callback_data=f"{LpvaultBridgeWrapState.SELECT.value}_HYPECORE",
                )
            ]
        )
    if evm_hype > MIN_HYPE:
        kb.append(
            [
                InlineKeyboardButton(
                    f"HYPE (EVM): {evm_hype:.2f}",
                    callback_data=f"{LpvaultBridgeWrapState.SELECT.value}_HYPEEVM",
                )
            ]
        )

    if not kb:
        text = f"You don't have enough assets(minimum {MIN_USDC} USDC or {MIN_HYPE} HYPE (Core) or {MIN_HYPE} HYPE (EVM)) to bridge. Please deposit more assets to your account."

    kb.append(cancel_keyboard_button)

    await send_or_edit(
        update,
        context,
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return LpvaultBridgeWrapState.SELECT


@force_coroutine_logging
async def lpvault_bridge_wrap_select(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info("bridge select triggered by user: %s", update.effective_user.id)
    await answer(update)

    setting = LpvaultBridgeWrapSetting.get_setting(context)
    if (
        not setting.spot_usdc
        and not setting.spot_hype
        and not setting.evm_hype
        and not setting.perp_usdc
    ):
        await send_or_edit(
            update,
            context,
            "You don't have enough assets to bridge. Please deposit more assets to your account.",
        )
        return ConversationHandler.END

    query = update.callback_query
    asset_type = query.data.split("_")[-1]

    setting.selected_ticker = asset_type

    kb = [
        [
            InlineKeyboardButton(
                "Confirm",
                callback_data=f"{LpvaultBridgeWrapState.CONFIRM.value}",
            )
        ],
        cancel_keyboard_button,
    ]

    if asset_type == "USDCSPOT":
        amount = setting.spot_usdc
    elif asset_type == "USDCPERP":
        amount = setting.perp_usdc
    elif asset_type == "HYPECORE":
        amount = setting.spot_hype
    elif asset_type == "HYPEEVM":
        amount = setting.evm_hype
    else:
        await send_or_edit(
            update,
            context,
            "Invalid asset type selected.",
        )
        return ConversationHandler.END

    await send_or_edit(
        update,
        context,
        f"You selected {asset_type} with amount {amount:.2f}. Please confirm the conversion.",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )
    return LpvaultBridgeWrapState.CONFIRM


@force_coroutine_logging
async def lpvault_bridge_wrap_confirm(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    logger.info("bridge confirm triggered by user: %s", update.effective_user.id)
    await answer(update)

    await send_or_edit(
        update,
        context,
        "Wrapping 🔄",
        parse_mode="Markdown",
    )

    setting = LpvaultBridgeWrapSetting.get_setting(context)
    account = LpvaultSetting.get_setting(context).account

    if not account:
        await send_or_edit(
            update,
            context,
            "No active account found. Please set an active account first.",
        )
        return ConversationHandler.END

    asset_type = setting.selected_ticker

    logger.debug(
        f"Bridging {asset_type} for user: {update.effective_user.id}, account: {account.public_key}"
    )
    swap_usdc = None
    spot_hype = None
    evm_hype = None
    if asset_type == "USDCPERP":
        # 1. perp -> spot usdc로 변환
        await hl_account_service.perp_to_spot(str(context._user_id), setting.perp_usdc)
        await asyncio.sleep(1)
        swap_usdc = setting.perp_usdc

    if "USDC" in asset_type:
        # 2. usdc -> hype (core) 로 변환
        if not swap_usdc:
            swap_usdc = setting.spot_usdc
        order_data = await buy_order_service.buy_order_market_usdc(
            str(context._user_id),
            [{"name": "HYPE", "value": swap_usdc}],
            charge_builder_fee=account.is_approved_builder_fee,
        )
        logger.debug(
            f"Bridged USDC for user: {update.effective_user.id}, account: {account.public_key}, order_data: {order_data}"
        )
        spot_hype = (
            order_data.filled[0].totalSz - 0.02
        )  # HL 서버에서 반올림된 값을 내려주기 때문에 에러 방지를 위해 0.02 제거
        await asyncio.sleep(1)  # wait for the transaction to be processed

    if "HYPECORE" in asset_type or "USDC" in asset_type:
        if not spot_hype:
            spot_hype = setting.spot_hype

        logger.debug(
            f"Bridging HYPE for user: {update.effective_user.id}, account: {account.public_key}, spot_hype: {spot_hype}"
        )
        await hl_account_service.spot_to_evm(
            str(context._user_id), account.nickname, "HYPE", spot_hype
        )
        await asyncio.sleep(3)  # wait for the transaction to be processed
        # 4. evm hype 갯수 조회
        evm_hype = spot_hype
        logger.debug(
            f"Bridged HYPE for user: {update.effective_user.id}, account: {account.public_key}, evm_hype: {evm_hype}"
        )

    if not evm_hype:
        evm_hype = setting.evm_hype

    response = await hl_account_service.wrap(
        str(context._user_id), account.nickname, evm_hype
    )
    logger.debug(f"wrap response: {response}")

    if response:
        await send_or_edit(
            update,
            context,
            f"Successfully bridged `{evm_hype:.2f}` HYPE to WHYPE.",
            parse_mode="Markdown",
        )
        await asyncio.sleep(1)
    else:
        await send_or_edit(
            update,
            context,
            "Something went wrong. Please try again later.",
        )
        await asyncio.sleep(1.5)
    return await lpvault_command(update, context)


lpvault_bridge_wrap_states = {
    LpvaultBridgeWrapState.SELECT: [
        CallbackQueryHandler(
            lpvault_bridge_wrap_select,
            pattern=f"^{LpvaultBridgeWrapState.SELECT.value}",
        ),
    ],
    LpvaultBridgeWrapState.CONFIRM: [
        CallbackQueryHandler(
            lpvault_bridge_wrap_confirm,
            pattern=f"^{LpvaultBridgeWrapState.CONFIRM.value}",
        ),
    ],
}

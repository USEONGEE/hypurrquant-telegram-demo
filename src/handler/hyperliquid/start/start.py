from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from hypurrquant.api.market_data import hyqFetch as market_data_cache

from api import AccountService, BridgeService, Chain
from api.hyperliquid import HLAccountService
from api.exception import CannotApproveBuilderFeeException

from handler.utils.cancel import cancel_handler, create_cancel_inline_button
from handler.utils.utils import send_or_edit
from handler.utils.account_helpers import fetch_active_account
from handler.start.states import StartStates
from handler.command import Command
from hypurrquant.models.account import Account
from .states import HLCoreStartState
import os
import re  # 🔹 추가
import asyncio

logger = configure_logging(__name__)

bridge_service = BridgeService()
hl_account_service = HLAccountService()
account_service = AccountService()


# 🔹 MarkdownV2 특수문자 자동 이스케이프 함수 추가
def escape_markdown_v2(text: str) -> str:
    """Telegram MarkdownV2 특수문자 자동 이스케이프"""
    return re.sub(r"([_*\[\]()~`>#\+\-=|{}.!])", r"\\\1", text)


# app.py의 디렉토리를 기준으로 이미지 경로 설정
current_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
photo_path = os.path.join(current_dir, "img/start.jpeg")


# ================================
# /start
# ================================
def HOW_TO_DEPOSIT(
    solana_address: str, eth_address, bitcoin_address, metadata: float
) -> str:
    logger.debug(f" {metadata}")
    solana_time = metadata.get(Chain.SOLANA.value, {}).get("depositEta", "unknown")
    eth_time = metadata.get(Chain.ETHEREUM.value, {}).get("depositEta", "unknown")
    bitcoin_time = metadata.get(Chain.BITCOIN.value, {}).get("depositEta", "unknown")
    fee = metadata.get("fee", 0.0)
    return (
        "**> *How to [Deposit](https://docs.hypurrquant.com/bot_commands/how-to-deposit)*\n"
        "> \n"
        "> USDC / SOL / ETH / BTC \n"
        "> \n"
        ">_*USDC\(Arbitrum\)*_\n"
        ">Please make sure to transfer USDC on the Hyperliquid L1 chain\n"
        ">If you transfer USDC to the Arbitrum chain, a deposit process on the Hyperliquid exchange will be required\n"
        "> \n"
        ">_*SOL, FARTCOIN, PUMP\(Solana\)*_\n"
        f">Please deposit at least `0.2` SOL, `20` FARTCOIN, `8000` PUMP to the following address: `{solana_address}` \(tap to copy\)\n"
        f">Est\. time: \~ {solana_time}\n"
        "> \n"
        ">_*ETH\(Mainnet\)*_\n"
        f">Please deposit at least `0.05` ETH to the following address: `{eth_address}` \(tap to copy\)\n"
        f">Est\. time: \~ {eth_time}\n"
        "> \n"
        ">_*BTC\(Mainnet\)*_\n"
        f">Please deposit at least `0.002` BTC to the following address: `{bitcoin_address}` \(tap to copy\)\n"
        f">Est\. time: \~ {bitcoin_time}\n"
        f">\n"
        f">fee\($\): `{fee:.2f}`$||\n\n"
    )


async def generate_command_message(account: Account) -> str:
    if account.is_approved_builder_fee:
        withdrawable, spot_list, sol_address, eth_address, bit_address, metadata = (
            await asyncio.gather(
                hl_account_service.get_withdrawable(account.public_key),
                hl_account_service.get_spot_balance_precompile(
                    account.public_key, ["USDC", "HYPE", "USOL", "UBTC", "UETH"]
                ),
                bridge_service.get_bridge_address(
                    chain=Chain.SOLANA,
                    dst_evm_addr=account.public_key,
                ),
                bridge_service.get_bridge_address(
                    chain=Chain.ETHEREUM,
                    dst_evm_addr=account.public_key,
                ),
                bridge_service.get_bridge_address(
                    chain=Chain.BITCOIN,
                    dst_evm_addr=account.public_key,
                ),
                bridge_service.estimate_solana_fees(convert_to_usd=True),
            )
        )
        logger.debug(f"metadata= {metadata}")
        data = {
            ticker: {
                "total": spot_list[ticker],
                "value": float(market_data_cache.filter_by_Tname(ticker).midPx)
                * spot_list[ticker],
            }
            for ticker in spot_list.keys()
        }
        how_to_deposit = HOW_TO_DEPOSIT(sol_address, eth_address, bit_address, metadata)

        return (
            "🚀 Welcome to HypurrQuant\. All\-In\-One crypto portfolio utility bot by Team [QUANT](https://t.me/hypurrquantannouncement)\n\n"
            f"{how_to_deposit}"
            f"\[Active Account\]\n👤 *{account.nickname}* \| `{account.public_key}`\(tap to copy\)\n\n"
            "**> *Balances*\n"
            "> \n"
            f">Spot USDC: `{data['USDC']['total']:.2f}`$ \| Perp USDC: `{withdrawable:.2f}`$\n"
            f">HYPE: `{data['HYPE']['total']:.8f}`\(`{data['HYPE']['value']:.2f}`$\)\n"
            f">BTC: `{data['UBTC']['total']:.8f}`\(`{data['UBTC']['value']:.2f}`$\)\n"
            f">ETH: `{data['UETH']['total']:.8f}`\(`{data['UETH']['value']:.2f}`$\)\n"
            f">SOL: `{data['USOL']['total']:.8f}`\(`{data['USOL']['value']:.2f}`$\)||\n\n"
            "ℹ️ More info: Tap Documentation below\n"
            "ℹ️ Questions? Join our [community](https://t.me/hypurrquant_official)"
        )
    else:
        sol_address, eth_address, bit_address, metadata = await asyncio.gather(
            bridge_service.get_bridge_address(
                chain=Chain.SOLANA,
                dst_evm_addr=account.public_key,
            ),
            bridge_service.get_bridge_address(
                chain=Chain.ETHEREUM,
                dst_evm_addr=account.public_key,
            ),
            bridge_service.get_bridge_address(
                chain=Chain.BITCOIN,
                dst_evm_addr=account.public_key,
            ),
            bridge_service.estimate_solana_fees(convert_to_usd=True),
        )
        how_to_deposit = HOW_TO_DEPOSIT(sol_address, eth_address, bit_address, metadata)

        msg = (
            "🚀 Welcome to HypurrQuant\. All\-In\-One crypto portfolio utility bot by Team [QUANT](https://t.me/hypurrquantannouncement)\n\n"
            f"Your account address is `{account.public_key}`\(tap to copy\)\. Please deposit at least $1 to this address, then press /start again to activate your account, or use the /wallet button to try the application with a different address\n\n"
            f"{how_to_deposit}"
            "ℹ️ More info: Tap Documentation below\n"
            "ℹ️ Questions? Join our [community](https://t.me/hypurrquant_official)"
        )
        return msg


async def add_referral_code(context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    payload = context.args[0] if context.args else None
    if payload:
        await account_service.add_referral(
            referral_code=payload,
            telegram_id=context._user_id,
        )

        logger.info(f"refferal code = {payload}")
    else:
        logger.info("No referral code provided.")


# 생성된 메시지 사용
@force_coroutine_logging
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    logger.info("hyperliquid core start")
    # 유저 정보 가져오기
    account: Account = await fetch_active_account(context)

    logger.debug(
        f"/start에서 {context._user_id} 유저의 {account.nickname} 계좌를 가져옴: {account.model_dump()}"
    )

    if (
        not account.is_approved_builder_fee
    ):  # 유저가 builder fee를 승인하지 않은 경우, approve_builder_fee 호출

        logger.debug(
            f"/start에서 {context._user_id} 유저의 {account.nickname} 계좌를 approve builder fee 하려는 시도"
        )
        try:
            await hl_account_service.approve_builder_fee(
                str(context._user_id), account.nickname
            )
            account: Account = await fetch_active_account(context, force=True)
        except CannotApproveBuilderFeeException as e:
            logger.debug(f"Cannot approve builder fee for {context._user_id}: {e}")
            pass
        except Exception as e:
            logger.exception(
                f"/start에서 {context._user_id} 유저의 {account.nickname} 계좌를 approve builder fee 하려던 도중 예외 발생"
            )

    message, _, _ = await asyncio.gather(
        generate_command_message(account),
        add_referral_code(context),
        account_service.send_chat_id(context._user_id, context._chat_id),
    )
    if account.is_approved_builder_fee:
        kb = [
            [
                InlineKeyboardButton(
                    "Spot Buy",
                    callback_data=f"{HLCoreStartState.TRIGGER.value}|{Command.BUY_ONE}",
                ),
                InlineKeyboardButton(
                    "Spot Sell",
                    callback_data=f"{HLCoreStartState.TRIGGER.value}|{Command.SELL}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "Perp Open",
                    callback_data=f"{HLCoreStartState.TRIGGER.value}|{Command.PERP_ONE}",
                ),
                InlineKeyboardButton(
                    "Perp Close",
                    callback_data=f"{HLCoreStartState.TRIGGER.value}|{Command.CLOSE}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "DCA",
                    callback_data=f"{HLCoreStartState.TRIGGER.value}|{Command.DCA}",
                ),
                InlineKeyboardButton(
                    "Copy Trading",
                    callback_data=f"{HLCoreStartState.TRIGGER.value}|{Command.COPY_TRADING}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "Grid Trading",
                    callback_data=f"{HLCoreStartState.TRIGGER.value}|{Command.GRID}",
                ),
                InlineKeyboardButton(
                    "Delta Neutral",
                    callback_data=f"{HLCoreStartState.TRIGGER.value}|{Command.DELTA}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 Balance",
                    callback_data=f"{HLCoreStartState.TRIGGER.value}|{Command.BALANCE}",
                ),
                InlineKeyboardButton(
                    "⚙️ Wallet",
                    callback_data=f"{HLCoreStartState.TRIGGER.value}|{Command.WALLET}?rt={Command.HYPERLIQUID_CORE_START}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📄 Documentation",
                    url="https://docs.hypurrquant.com/about_hypurrquant/overview",
                ),
            ],
            [create_cancel_inline_button(Command.START)],
        ]
    else:
        kb = [
            [
                InlineKeyboardButton(
                    "⚙️ Wallet",
                    callback_data=f"{HLCoreStartState.TRIGGER.value}|{Command.WALLET}?rt={Command.HYPERLIQUID_CORE_START}",
                ),
            ],
            [
                # 외부 링크 버튼 추가
                InlineKeyboardButton(
                    "📄 Documentation",
                    url="https://docs.hypurrquant.com/about_hypurrquant/overview",
                ),
            ],
            [create_cancel_inline_button(Command.START)],
        ]
    await send_or_edit(
        update,
        context,
        text=message,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(kb),
        disable_web_page_preview=True,
    )

    return HLCoreStartState.TRIGGER


hyperliquid_core_start_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.HYPERLIQUID_CORE_START, start),
        CallbackQueryHandler(
            start,
            pattern=rf"^({StartStates.TRIGGER.value}|{HLCoreStartState.TRIGGER.value})\|{Command.HYPERLIQUID_CORE_START}$",
        ),
    ],
    states={},
    fallbacks=[cancel_handler],
    name=Command.HYPERLIQUID_CORE_START,
    allow_reentry=True,
)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from api import AccountService, LpVaultService
from handler.utils.utils import answer, send_or_edit
from handler.utils.account_helpers import fetch_active_account
from handler.utils.cancel import (
    create_cancel_inline_button,
    initialize_handler,
)
from handler.wallet.states import ChangeState
from handler.evm.balance.states import EvmBalanceState
from handler.command import Command
from .settings import LpvaultSetting
from .states import *
from .utils import build_pair_table
from tabulate import tabulate
from typing import List, Dict, Any
import asyncio

logger = configure_logging(__name__)

account_service = AccountService()
lp_vault_service = LpVaultService()

CHAIN = "HYPERLIQUID"  # TODO 추후엔 LpVaultSetting으로 넘어가야함.


@force_coroutine_logging
@initialize_handler(setting_cls=LpvaultSetting)
async def lpvault_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    await answer(update)
    await send_or_edit(
        update,
        context,
        "Loading 🔄",
        parse_mode="Markdown",
    )

    # 1. 계정 정보(토큰, 포인트, LP NFT) 가져오기
    setting: LpvaultSetting = LpvaultSetting.get_setting(context)
    account = await fetch_active_account(context)
    setting.account = account
    logger.debug(f"lp_vault_account: {account}")

    (
        user_lp_list,
        whype,
        evm_hype,
        point_dict,
    ) = await asyncio.gather(
        lp_vault_service.lp_list(
            account.public_key
        ),  # 유저가 등록한 Lp Vault 리스트 조회, 현재는 체인별 1개가 최대
        account_service.get_native_wrapped(
            account.public_key
        ),  # TODO 추후에 native, erc20 tokens는 한 번에 chain 값에 따라서 가져오게 해야함.
        account_service.get_evm_native(account.public_key),
        lp_vault_service.get_points(account.public_key, CHAIN),
    )

    # 2. 유저 LP Vault 등록 정보 및 수익 조회
    logger.debug(f"user_lp_list: {user_lp_list}")
    lp_dex_set = set()
    # 2-1. 사용자가 선택한 체인의 포지션 조회
    for lp in user_lp_list:
        if lp["pool_config"]["chain"] == CHAIN:
            lp_dex_set.add(lp["pool_config"]["dex_type"])
    positions = await asyncio.gather(
        *[
            lp_vault_service.get_positions(account.public_key, CHAIN, dex)
            for dex in lp_dex_set
        ]
    )
    logger.debug(f"positions: {positions}")
    positions_dict: dict[str, list[dict]] = {}
    for dex, position in zip(lp_dex_set, positions):
        positions_dict[dex] = position

    # 3. 기본 정보 메시지 작성
    text = (
        f"*Auto LP Manager*({CHAIN})\n"
        f"👤 *{account.nickname}* | `{account.public_key}`\n\n"
    )

    # 4. Lp Vaults 메시지 작성, 사용자가 선택한 체인의 데이터만 추출
    if user_lp_list:
        text += "You register\n"
        for lp_list in user_lp_list:
            text += f"- {lp_list['pool_config']['pool_name']} ({lp_list['pool_config']['dex_type']})\n"

    # TODO 자산 추후에 체인에 따라서 다르게 가져와야 함. -> point는 잘 가져옴
    # 5. 자산 및 포인트 메시지 작성
    text += f"\nYou have\n```"
    text += tabulate(
        [["WHYPE", f"{whype:.4f}"], ["HYPE(gas)", f"{evm_hype:.4f}"]], tablefmt="grid"
    )
    text += "\nPoints\n"

    _table = []
    for key, value in point_dict.items():
        _table.append([key, f"{int(value):,}"])

    if _table:
        text += tabulate(
            _table,
            tablefmt="grid",
        )

    text += "```\n\n"

    # 6-1. NFT position 메시지 작성
    if positions_dict:
        message = await _create_position_text(account, positions_dict)

        text += f"```\n{message}\n```"

        kb = [
            [
                InlineKeyboardButton(
                    "Stop Auto LP Manager",
                    callback_data=LpvaultUnregisterState.START.value,
                )
            ],
            [
                InlineKeyboardButton(
                    "Manual Mint",
                    callback_data=LpvaultManualMintState.START.value,
                )
            ],
        ]

    # 7-2. 포지션이 없을 경우
    else:
        logger.debug(f"have not positions_dict: {positions_dict}")
        kb = [
            [
                InlineKeyboardButton(
                    "Create LP Manager",
                    callback_data=LpvaultRegisterState.START.value,
                )
            ],
            [
                InlineKeyboardButton(
                    "Manual Mint",
                    callback_data=LpvaultManualMintState.START.value,
                )
            ],
        ]

        text += "You don't have any Auto LP Manager registered yet.\n\n"

    kb += [
        [
            InlineKeyboardButton(
                "📊 Balance(evm)",
                callback_data=f"{EvmBalanceState.START.value}?rt={Command.LPVAULT_AUTO}",
            ),
            InlineKeyboardButton(
                "Swap",
                callback_data=f"{LpvaultSwapState.START.value}",
            ),
        ],
        [
            InlineKeyboardButton(
                "Wrap to WHYPE",
                callback_data=LpvaultBridgeWrapState.START.value,
            ),
            InlineKeyboardButton(
                "Unwrap to HYPE",
                callback_data=LpvaultBridgeUnwrapState.START.value,
            ),
        ],
        [
            InlineKeyboardButton(
                "Change Wallet",
                callback_data=f"{ChangeState.CHANGE.value}?rt={Command.LPVAULT_AUTO}",
            ),
            InlineKeyboardButton(
                "📄 Guide",
                url="https://docs.hypurrquant.com/bot_commands/tools/auto-lp-manager",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ Settings",
                callback_data=LpvaultSettingsState.START.value,
            )
        ],
        [
            InlineKeyboardButton(
                "Refresh",
                callback_data=LpvaultRefreshState.START.value,
            ),
            create_cancel_inline_button(setting.return_to),
        ],
    ]

    text += "💡 Tip: Register a `Create LP Manager` to auto-generate and rebalance LPs within your set pool range. If you prefer to add it later, first open a position with `Manual Mint`, then register it with `Create LP Manager`."

    # text += "🚀 Hyperbloom Boost\n"
    # text += "Earn extra Hyperbloom points when swapping via Hypurrquant."

    await send_or_edit(
        update,
        context,
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

    return LpvaultState.SELECT_ACTION


async def _create_position_text(account, positions_dict):
    logger.debug(f"have positions_dict: {positions_dict}")
    for _, position_item in positions_dict.items():
        # is_managed 필터
        filtered_positions = [pos for pos in position_item if pos.get("is_managed")]
        logger.debug(f"filtered_positions: {filtered_positions}")

        # profits 길이 안전 처리: get_profits가 포지션 순서대로 반환된다는 전제
        profits: List[Dict[str, Any]] = (
            await lp_vault_service.get_profits(
                account.public_key, CHAIN, filtered_positions
            )
            or []
        )
        if len(profits) != len(filtered_positions):
            logger.warning(
                "profits length %d != filtered_positions length %d",
                len(profits),
                len(filtered_positions),
            )

        messages_parts: List[str] = []
        for idx, filter_position in enumerate(filtered_positions):
            profit = profits[idx] if idx < len(profits) else {}
            table_str = build_pair_table(filter_position, profit)
            messages_parts.append(table_str)

        messages = "\n".join(messages_parts)
        if not messages:
            messages = "⏳ Minting Your Position…"
    return messages

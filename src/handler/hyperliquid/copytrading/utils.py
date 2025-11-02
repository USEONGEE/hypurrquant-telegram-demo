from api import AccountService
from api.hyperliquid import CopytradingService, HLAccountService
from .settings import CopytradingSetting
import asyncio

from telegram.ext import ContextTypes

account_service = AccountService()
hl_account_service = HLAccountService()
copytrading_service = CopytradingService()


async def generate_info_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    copytrading_setting: CopytradingSetting = CopytradingSetting.get_setting(context)
    account = copytrading_setting.account  # copytraindg 계좌 조회

    dto, account_detail, targets, count = await asyncio.gather(
        hl_account_service.get_perp_balance(context._user_id, account.nickname),
        account_service.get_account_detail(account.public_key),
        copytrading_service.get_targets_by_subscriber(account.public_key),
        copytrading_service.count_subscription(),
    )

    copytrading_detail = account_detail["copy_trading_details"]
    message = (
        "*Copy Trading*\n\n"
        "**>*Feature Overview*\n"
        "> \n"
        ">· Subscribe: Subscribe to the wallet from which to perform copy trading\n"
        ">· Unsubscribe: Unsubscribe from the subscribed wallet\n"
        ">· Set PNL\(%\) Target: Set the target PNL\(%\) for copy trading\n"
        ">· Set Leverage: Set the leverage for copy orders\n"
        ">· Set Order Size: Set the order size for copy orders\n"
        ">· Copy Trading Type: Set the type of copy trading\n"
        ">· Set Account:  Set the wallet for performing copy trading||\n\n"
    )
    message += "* Copy Trading Account *\n"
    message += f"👤 *{account.nickname}* \| `{account.public_key}`\n\n"
    message += "```\n"
    message += "* Subscriber *            \n"
    message += "+------------------------+\n"
    if not targets:
        message += "| No subscribers yet     |\n"
    else:
        for target in targets:
            message += f"| - {target} \n"
    message += "+------------------------+\n\n"

    message += "* Setting *\n"
    message += "+------------------------+\n"
    message += f"| Target PNL(%): {copytrading_detail['target_pnl_percent']:6.0f}% |\n"
    message += f"| close strategy:   {copytrading_detail['close_strategy'][:4]:4s} |\n"
    message += f"| order size($): {float(copytrading_detail['order_details']['order_value_usdc']):6.0f}$ |\n"
    message += f"| leverage:           X{int(copytrading_detail['order_details']['leverage'])} |\n"
    message += "+------------------------+```\n"

    message += (
        "**>*Note*\n"
        "> \n"
        f">· This feature supports only `{count['max']}` total subscriptions wallet across all users \(first\‑come, first\‑served\); "
        f"`{count['count']}` wallets have already been claimed\n"
        f">· This {count['max']} wallet limit is temporary, and capacity will be significantly expanded soon\n"
        '>· The Copy Trading Type is initially set to "Copy," which means the sales will also be executed automatically\. This can be changed in the "Copy Trading Type" section||'
    )

    return message

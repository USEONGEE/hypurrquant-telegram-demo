from api.hyperliquid import HLAccountService
from .settings import RebalanceSetting
from api.hyperliquid import RebalanceService, RebalanceDetailDto, SpotBalanceMappingDTO
from telegram.ext import ContextTypes

hl_account_service = HLAccountService()
rebalance_service = RebalanceService()


async def generate_info_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    respnose: RebalanceDetailDto = await rebalance_service.get_rebalance_detail(
        context._user_id
    )
    spot_dto: SpotBalanceMappingDTO = (
        await hl_account_service.get_spot_balance_by_public_key(respnose.public_key)
    )
    account = RebalanceSetting.get_setting(context).account

    message = (
        "*Alarm Feature*\n\n"
        "The alarm feature tracks the total PNL of the Spot assets in the selected wallet and sends an alert to the user when a specific PNL target is reached.\n\n"
        "- `Select Account`: Choose the wallet for which to set the alarm.\n"
        "- `Set PNL(%) Alert Target`: Set the target PNL percentage for the alarm.\n"
        "- `Enable/Disable PNL(%) Alert`: Turn the alarm feature on or off.\n\n"
        "*Note*: You cannot use the same wallet as for copy trading.\n\n"
    )

    message += f"📊 nickname `{account.nickname}`\n"
    message += f"📊 public key: `{account.public_key}` ```\n"
    message += "* Account Info *\n"
    message += "+------------------------+\n"
    message += f"| PNL(%):  {spot_dto.total_pnl_percent:12.2f}% |\n"
    message += f"| PNL   :  {spot_dto.total_pnl:12.2f}$ |\n"
    message += "+------------------------+\n\n"
    message += "* Setting *\n"
    message += "+------------------------+\n"
    message += f"| Target PNL(%): {respnose.target_pnl_percent:6.2f}% |\n"
    message += f"| PNL Alarm    :   {respnose.pnl_alarm:4s}  |\n"
    message += "+------------------------+\n```"
    return message

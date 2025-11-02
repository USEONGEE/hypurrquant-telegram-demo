from handler.models.perp_balance import PerpBalanceMapping
from handler.models.spot_balance import SpotBalanceMapping

CONVERSATION_HANDLER_NAME = "BALANCE"


def generate_summary(
    spot_balance_mapping=SpotBalanceMapping, perp_balance_mapping=PerpBalanceMapping
) -> str:

    # #ASCII 표 형태로 문자열 생성
    text = "📊 *Spot*\n"
    text += "```\n"
    text += "+------------+--------------+\n"
    text += "|    Item    |    Value     |\n"
    text += "+------------+--------------+\n"
    text += f"| {'Total':<10} | {spot_balance_mapping.stock_total_balance + spot_balance_mapping.usdc_balance:>11.2f}$ |\n"
    text += f"| {'USDC':<10} | {spot_balance_mapping.usdc_balance:>11.2f}$ |\n"
    text += "+------------+--------------+\n"
    text += " - Portfolio\n"
    text += "+------------+--------------+\n"
    text += (
        f"| {'Invested':<10} | {spot_balance_mapping.stock_total_balance:>11.2f}$ |\n"
    )
    text += f"| {'PNL':<10} | {spot_balance_mapping.total_pnl:>11.2f}$ |\n"
    text += f"| {'PNL(%)':<10} | {spot_balance_mapping.total_pnl_percent:>11.2f}% |\n"
    text += "+------------+--------------+\n"
    text += "```\n"

    text += "📊 *perp*\n"
    text += "```\n"
    text += "+------------+--------------+\n"
    text += "|    Item    |    Value     |\n"
    text += "+------------+--------------+\n"
    text += f"| {'Total':<10} | {perp_balance_mapping.accountValue:>11.2f}$ |\n"
    text += f"| {'Available':<10} | {perp_balance_mapping.withdrawable:>11.2f}$ |\n"
    text += "+------------+--------------+\n"
    text += " - Portfolio\n"
    text += "+------------+--------------+\n"
    text += (
        f"| {'Invested':<10} | {perp_balance_mapping.total_position_value:>11.2f}$ |\n"
    )
    text += f"| {'PNL':<10} | {perp_balance_mapping.totalUnrealizedPnl:>11.2f}$ |\n"
    text += f"| {'PNL(%)':<10} | {perp_balance_mapping.pnlPercentage:>11.2f}% |\n"
    text += "+------------+--------------+\n"
    text += "```\n"

    return text

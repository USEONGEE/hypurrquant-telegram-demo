from .settings import LpvaultRegisterSetting
from tabulate import tabulate
from typing import Dict, Any, Optional


def create_register_confirm_message(setting: LpvaultRegisterSetting):
    message = "You have registered the LP vault with the following settings\n```"
    data = [
        ["DEX", setting.dex_info["name"]],
        ["Pool", setting.all_pool_configs[setting.config_index]["pool_name"]],
        ["Range(%)", f"{setting.lower_range_pct}% ~ {setting.upper_range_pct}%"],
        [
            "Aggregator",
            "Best Route" if setting.aggregator == "__auto__" else setting.aggregator,
        ],
        ["Auto Claim", setting.auto_claim],
    ]
    if setting.swap_target_token_ticker:
        data.append(["Swap Token", setting.swap_target_token_ticker])
    message += tabulate(
        data,
        tablefmt="grid",
    )

    message += "\n```"
    return message


def fmt_usd(v: Optional[float]) -> str:
    """USD 포맷: 천단위 구분 + 소수 1자리. None은 fail to fetch."""
    if v is None:
        return "fail to fetch"
    return f"${v:,.1f}"


def build_amounts_subtable(
    token0_name: str,
    token1_name: str,
    amt0: float,
    amt1: float,
    price0: Optional[float],
    price1: Optional[float],
    total_label: str = "Total",
) -> str:
    """
    공통 서브 테이블 빌더: [Token, Amount, USD]
    - 가격이 None이면 USD 칸 'fail to fetch'
    - 두 토큰 모두 USD가 있으면 Total 표시, 아니면 'fail to fetch'
    """
    t0_usd = (
        (amt0 * price0)
        if price0 is not None and isinstance(amt0, (int, float))
        else None
    )
    t1_usd = (
        (amt1 * price1)
        if price1 is not None and isinstance(amt1, (int, float))
        else None
    )

    rows = [
        [token0_name, f"{amt0:,.6f}", fmt_usd(t0_usd)],
        [token1_name, f"{amt1:,.6f}", fmt_usd(t1_usd)],
    ]

    if (t0_usd is not None) and (t1_usd is not None):
        rows.append([total_label, "-", fmt_usd(t0_usd + t1_usd)])
    else:
        rows.append([total_label, "-", "fail to fetch"])

    return tabulate(rows, headers=["Token", "Amount", "USD"], tablefmt="grid")


def build_pos_subtable(
    filter_position: Dict[str, Any], token0_name: str, token1_name: str
) -> str:
    """Position 섹션용 서브테이블: filter_position의 token*_amount/price 사용"""
    amt0 = filter_position.get("token0_amount", 0.0) or 0.0
    amt1 = filter_position.get("token1_amount", 0.0) or 0.0
    p0 = filter_position.get("token0_price")
    p1 = filter_position.get("token1_price")
    return build_amounts_subtable(
        token0_name, token1_name, amt0, amt1, p0, p1, total_label="Total"
    )


def build_rewards_subtable(
    profit: Dict[str, Any],
) -> str:
    """
    Reward 섹션용 서브테이블:
    - Amount: profit['unclaimed_token0/1']
    - USD: position 가격(token*_price)로 환산
    """
    token0_info = profit.get("token0_info")
    token1_info = profit.get("token1_info")

    amt0 = token0_info.get("amount", 0.0) or 0.0
    amt1 = token1_info.get("amount", 0.0) or 0.0
    p0 = token0_info.get("price")
    p1 = token1_info.get("price")
    ticker0 = token0_info.get("ticker")
    ticker1 = token1_info.get("ticker")
    return build_amounts_subtable(
        ticker0, ticker1, amt0, amt1, p0, p1, total_label="Total"
    )


def build_pair_table(
    filter_position: Dict[str, Any],
    profit: Dict[str, Any],
) -> str:
    """
    개별 포지션에 대한 최종 출력 테이블 문자열을 생성
    - Pair, Range, Position(서브테이블), Rewards(서브테이블)
    """
    dex_type = filter_position["pool_config"]["dex_type"]
    pool_name = filter_position["pool_config"]["pool_name"]
    token0_name, token1_name = pool_name.split("/")

    # Range
    range_line = (
        f"{filter_position['tickLower_price']:.2f} ~ {filter_position['tickUpper_price']:.2f}\n"
        f"{filter_position['current_price']:.2f} (current)"
    )

    # Position 서브테이블
    pos_subtable = build_pos_subtable(filter_position, token0_name, token1_name)

    # Rewards 서브테이블 (금액은 profit, USD는 position의 price 사용)
    rewards_subtable = build_rewards_subtable(profit)

    # 상단( Pair / Range )
    message = tabulate(
        [
            ["Pair", f"{pool_name}({dex_type})"],
            ["Range", range_line],
        ],
        tablefmt="grid",
    )

    # Position 섹션
    message += "\nPosition\n"
    message += pos_subtable

    # Rewards 섹션
    message += "\nRewards\n"
    message += rewards_subtable

    return message

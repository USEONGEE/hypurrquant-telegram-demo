from hypurrquant.models.perp_market_data import (
    MarketData as PerpMarketData,
)

CONVERSATION_HANDLER_NAME = "BUY_ONE"


def generate_info_text(market_data: PerpMarketData) -> str:
    """
    MarketData 정보를 격자 형태의 텍스트로 생성합니다.

    섹션 구성:
      - Ticker 및 코인 정보
      - Price Comparison: markPx와 midPx 비교
      - Capital and Valuation: MarketCap와 circulatingSupply 표시
      - Profitability: 24h 변화량(금액, %) 표시
    """
    # 헤더: Ticker와 코인 이름(전체이름이 있으면 사용)
    message = f"- Ticker: {market_data.name}\n"

    # 코드 블록 시작 (예, Telegram에서 Markdown code block 사용)
    message += "```"

    message += "\n - Price & Volume\n"
    message += "+-------------+--------------+\n"
    message += "|   Price     |    Volume    |\n"
    message += "+-------------+--------------+\n"
    # markPx 값이 1 미만이면 소수점 10자리, 아니면 소수점 2자리
    mark_px_formatted = (
        f"{market_data.markPx:.5f}$"
        if market_data.markPx < 1
        else f"{market_data.markPx:.3f}"
    )
    message += f"| {mark_px_formatted:>11} | {market_data.dayBaseVlm:>11}$ |\n"
    message += "+-------------+--------------+\n"

    message += "\n - Funding & OpenInterest\n"
    message += "+-----------+----------------+\n"
    message += "|  Funding  |  OpenInterest  |\n"
    message += "+-----------+----------------+\n"
    message += f"| {market_data.funding:>8.6f}$ | {market_data.openInterest * market_data.markPx:>13,.0f}$ |\n"
    message += "+-----------+----------------+\n"

    message += "\n - Change\n"
    message += "+-------------+--------------+\n"
    message += "| 24h Change  | 24h Change(%)|\n"
    message += "+-------------+--------------+\n"
    message += f"| {market_data.midPx - market_data.prevDayPx :>10.2f}$ | {(1- market_data.prevDayPx / market_data.markPx ) * 100:>11.2f}% |\n"
    message += "+-------------+--------------+\n"

    # 코드 블록 종료
    message += "```"

    return message

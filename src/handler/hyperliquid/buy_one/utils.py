from hypurrquant.models.market_data import MarketData

CONVERSATION_HANDLER_NAME = "BUY_ONE"


def generate_info_text(market_data: MarketData) -> str:
    """
    MarketData 정보를 격자 형태의 텍스트로 생성합니다.

    섹션 구성:
      - Ticker 및 코인 정보
      - Price Comparison: markPx와 midPx 비교
      - Capital and Valuation: MarketCap와 circulatingSupply 표시
      - Profitability: 24h 변화량(금액, %) 표시
    """
    # 헤더: Ticker와 코인 이름(전체이름이 있으면 사용)
    coin_full_name = market_data.fullName if market_data.fullName else market_data.name
    message = f"- Ticker: {market_data.Tname}\n"

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
        else f"{market_data.markPx:.2f}"
    )
    message += f"| {mark_px_formatted:>10}$ | {market_data.dayNtlVlm:>11f}$ |\n"

    message += "+-------------+--------------+\n"

    message += "\n - Market Cap & Supply\n"
    message += "+-------------+--------------+\n"
    message += "|  Market Cap | Circulating  |\n"
    message += "+-------------+--------------+\n"
    message += f"| {market_data.MarketCap:>10.2f}$ | {market_data.circulatingSupply:>9.2f}$ |\n"
    message += "+-------------+--------------+\n"

    message += "\n - Change\n"
    message += "+-------------+--------------+\n"
    message += "| 24h Change  | 24h Change(%)|\n"
    message += "+-------------+--------------+\n"
    message += (
        f"| {market_data.change_24h:>10.2f}$ | {market_data.change_24h_pct:>11.2f}% |\n"
    )
    message += "+-------------+--------------+\n"

    # 코드 블록 종료
    message += "```"

    return message

from hypurrquant.logging_config import configure_logging

from telegram import Update, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from datetime import datetime
from typing import Tuple, List, Dict

logger = configure_logging(__name__)


async def answer(update: Update):
    if update is None or update.callback_query is None:
        return
    try:
        await update.callback_query.answer()
    except BadRequest as e:
        # 이미 응답했거나 쿼리가 만료된 경우
        logger.info(f"CallbackQuery.answer() skipped: {e}")


class TimeUtils:
    @staticmethod
    def remaining_time_from_iso(next_time_str: str) -> Tuple[int, int, int, int]:
        """
        주어진 ISO 형식의 시간 문자열을 현재 시간과 비교하여 남은 시간을 d, h, m, s 형태로 반환합니다.
        :param next_time_str: ISO 형식의 시간 문자열 (예: "2023-10-01T12:00:00")
        :return: 남은 시간 문자열 (예: "1d 2h 3m 4s")
        """

        next_time = datetime.fromisoformat(next_time_str)
        now = datetime.now()
        delta = next_time - now

        if delta.total_seconds() < 0:
            return 0, 0, 0, 0

        days, remainder = divmod(delta.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        return int(days), int(hours), int(minutes), int(seconds)

    @staticmethod
    def seconds_to_dhms(seconds: int) -> Tuple[int, int, int, int]:
        """
        주어진 초를 일, 시간, 분, 초로 변환합니다.
        :param seconds: 초 단위의 시간
        :return: (일, 시간, 분, 초) 형태의 튜플
        """
        if seconds < 0:
            return 0, 0, 0, 0

        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        return int(days), int(hours), int(minutes), int(seconds)


async def send_or_edit(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs
):
    """
    update.callback_query가 있으면 edit, 없으면 send.
    나머지 인자들은 **kwargs로 모두 넘겨주세요.
    """
    if update.callback_query:
        try:
            return await update.callback_query.edit_message_text(text, **kwargs)
        except BadRequest as e:
            if "Message is not modified" in str(e):
                return update.callback_query.message
            logger.exception("send_or_edit에서 문제가 발생했습니다.")
    else:
        return await update.effective_chat.send_message(text, **kwargs)


def format_buttons_grid(
    buttons: List[InlineKeyboardButton], columns: int
) -> List[List[InlineKeyboardButton]]:
    """
    InlineKeyboardButton 리스트를 열 수에 맞춰 2차원 리스트(행렬)로 포매팅.

    Args:
        buttons: InlineKeyboardButton들의 일차원 리스트
        columns: 한 행에 배치할 열 개수 (>=1)

    Returns:
        List[List[InlineKeyboardButton]]: 버튼 행렬
    """
    if columns < 1:
        raise ValueError("columns must be >= 1")

    return [buttons[i : i + columns] for i in range(0, len(buttons), columns)]


def _parse_callback_data(data: str) -> Tuple[str, Dict[str, str]]:
    """
    "BASE?k=v&a=b" -> ("BASE", {"k": "v", "a": "b"})
    값 없는 키도 허용: "BASE?flag" -> {"flag": ""}
    """
    if "?" not in data:
        return data, {}
    base, qs = data.split("?", 1)
    params: Dict[str, str] = {}
    for pair in qs.split("&"):
        if not pair:
            continue
        if "=" in pair:
            k, v = pair.split("=", 1)
            params[k] = v
        else:
            params[pair] = ""
    return base, params

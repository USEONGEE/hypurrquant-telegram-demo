from __future__ import annotations

from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram import Update, InlineKeyboardButton

from hypurrquant.logging_config import configure_logging
from handler.command import Command
from .settings import SettingMixin
from .utils import _parse_callback_data

from importlib import import_module
from functools import lru_cache
from typing import Callable, Awaitable, Dict, Optional, Tuple, Type, TypeVar

from functools import wraps
import re

logger = configure_logging(__name__)
CANCEL_RE = re.compile(r"^common_cancel\|(?P<cmd>.+)$")
COMMON_CANCEL = "common_cancel"
DEFAULT_COMMAND: str = Command.START
T = TypeVar("T", bound="SettingMixin")
Handler = Callable[..., Awaitable]


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggered by user: {context._user_id}")
    await update.callback_query.answer()

    m = CANCEL_RE.match(update.callback_query.data or "")
    if m:
        cmd = m.group("cmd")
    else:
        logger.warning(f"Invalid cancel command: {update.callback_query.data}")
        cmd = DEFAULT_COMMAND

    handler = resolve_entry(cmd)
    response = await handler(update, context)
    logger.debug(f"Cancel command '{cmd}' processed with response: {response}")
    return response


cancel_handler = CallbackQueryHandler(cancel, pattern=r"^common_cancel\|")


def create_cancel_inline_button(command: str | Command, text="Go Back"):
    """Creates a cancel button for the main menu."""
    return InlineKeyboardButton(text, callback_data=f"{COMMON_CANCEL}|{command}")


# --- 엔트리포인트 맵 ---------------------------------------------------------
# 주의: 값은 "모듈경로:함수명" 문자열로만 둡니다. (핸들러를 직접 import 하지 않음)

_prefix = "handler"
ENTRYPOINTS: Dict[str, str] = {
    Command.START: f"{_prefix}.start.start:start",
    Command.WALLET: f"{_prefix}.wallet.wallet_start:wallet_start",
    Command.LPVAULT_AUTO: f"{_prefix}.evm.lpvault.lpvault_start:lpvault_command",
    Command.EVM_BALANCE: f"{_prefix}.evm.balance.balance_start:balance_start",
    Command.REFERRAL: f"{_prefix}.referral.referral_start:referral_start",
    # hyperliquid core
    Command.HYPERLIQUID_CORE_START: f"{_prefix}.hyperliquid.start.start:start",
    Command.BALANCE: f"{_prefix}.hyperliquid.balance.balance_start:balance_start",
    Command.BUY: f"{_prefix}.hyperliquid.buy.buy_start:buy_start",
    Command.BUY_ONE: f"{_prefix}.hyperliquid.buy_one.buy_one_start:buy_one_start",
    Command.PERP_ONE: f"{_prefix}.hyperliquid.perp_one.perp_one_start:perp_one_start",
    Command.SELL: f"{_prefix}.hyperliquid.sell.sell_start:sell_start",
    Command.CLOSE: f"{_prefix}.hyperliquid.close.close_start:close_start",
    Command.COPY_TRADING: f"{_prefix}.hyperliquid.copytrading.copytrading_start:copytrading_start",
    Command.DCA: f"{_prefix}.hyperliquid.dca.dca_start:dca_start",
    Command.GRID: f"{_prefix}.hyperliquid.grid.grid_start:grid_start",
    Command.DELTA: f"{_prefix}.hyperliquid.delta.delta_start:delta_start",
    Command.REBALANCE: f"{_prefix}.hyperliquid.rebalance.rebalance_start:rebalance_start",
}


# --- 내부 유틸 ---------------------------------------------------------------
def _split_path(path: str) -> Tuple[str, str]:
    try:
        module_path, func_name = path.split(":", 1)
    except ValueError as e:
        raise ValueError(
            f"Invalid entry path (expect 'module:function'): {path}"
        ) from e
    return module_path, func_name


@lru_cache(maxsize=256)
def _load_callable(path: str) -> Handler:
    module_path, func_name = _split_path(path)
    mod = import_module(module_path)
    fn = getattr(mod, func_name, None)
    if fn is None or not callable(fn):
        raise AttributeError(f"'{module_path}:{func_name}' is not a callable handler")
    return fn  # type: ignore[return-value]


# --- 공개 API ----------------------------------------------------------------
def has_command(command: str) -> bool:
    """해당 커맨드가 라우터에 등록되어 있는지 확인."""
    return command in ENTRYPOINTS


def resolve_entry(
    command: str, *, fallback: Optional[str] = DEFAULT_COMMAND
) -> Handler:
    """커맨드 문자열을 실제 비동기 핸들러 콜러블로 해석.
    - 등록되지 않은 커맨드는 fallback으로 대체 (없으면 KeyError)
    - importlib로 지연 로딩되며 LRU 캐시에 저장
    """
    key = command
    if key not in ENTRYPOINTS:
        if fallback is None:
            raise KeyError(f"Unknown command: {command}")
        key = fallback
    return _load_callable(ENTRYPOINTS[key])


def command_key(value) -> str:
    """Enum/str 혼용 시 키를 문자열로 통일.
    - Enum이면 .value 사용, 아니면 str(value)
    """
    return getattr(value, "value", value)


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    key = command_key(command)  # Enum → str 통일
    handler = resolve_entry(key)
    return await handler(update, context)


def update_call_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    setting_cls: Type[T],
    default_return_to: str = Command.START,  # 안전망 기본값
):
    """
    모든 핸들러 시작 시 호출.
    - 기존 setting 유지값 백업
    - setting 초기화
    - callback_data 의 ?rt=... 만 파싱해서 return_to 설정
    """
    # 1) 기존값 백업
    setting = setting_cls.get_setting(context)
    prev = getattr(
        setting, "return_to"
    )  # NOTE: settingdp return_to가 없으면 예외 발생 허용 -> return_to 속성 추가 필요

    # 2) 초기화 후 다시 가져오기
    setting_cls.clear_setting(context)
    setting = setting_cls.get_setting(context)

    cq = getattr(update, "callback_query", None)
    if not cq or not cq.data:
        setting.return_to = prev
        return
    logger.debug(f"callback_data: {cq.data}")
    base, params = _parse_callback_data(cq.data)

    # 현재 핸들러가 취소 콜백으로 호출된 경우(자신의 자식 핸들러에게서 돌아온 경우)엔 이전값 유지
    if base == COMMON_CANCEL:
        setting.return_to = prev
        return

    # 오직 rt만 사용
    rt = params.get("rt")
    setting.return_to = rt or prev


def initialize_handler(setting_cls: Type[T]) -> Callable:
    """
    핸들러 시작 시 Setting을 초기화하고, callback_data로부터 CALL_COMMAND를 설정해 주는 데코레이터.

    우선순위:
    1) callback_data 쿼리스트링의 return_to (예: "...?return_to=wallet")
    2) 파이프 구분자 마지막 토큰 (예: "TRIGGER|wallet" -> wallet)
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
        ):
            update_call_command(update, context, setting_cls)
            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator

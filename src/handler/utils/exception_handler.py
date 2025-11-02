from typing import TYPE_CHECKING
from telegram.ext import ContextTypes, ConversationHandler
from hypurrquant.api.exception import BaseOrderException
from hypurrquant.logging_config import configure_logging, coroutine_id
from handler.utils.utils import send_or_edit
from api.exception import get_exception_by_code, ApiException
from pydantic import ValidationError
import traceback

logger = configure_logging(__name__)


async def exception_error_handler(
    update: object, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Log the error and send a telegram message to notify the developer."""

    # 에러 메시지 및 로그 아이디 추출
    exc_info = context.error
    cor_id = coroutine_id.get()
    short_id = cor_id[-8:]  # 마지막 8자리만 사용\
    if isinstance(exc_info, ValidationError):
        logger.debug("ValidationError")
        stack_trace = "".join(
            traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__)
        )
        await send_or_edit(
            update,
            context,
            f"Something went wrong. Please contact our support team with the following error ID: `{short_id}`",
            parse_mode="Markdown",
        )
        logger.exception(
            stack_trace,
        )
    elif isinstance(exc_info, BaseOrderException):
        logger.debug("BaseOrderException")
        mapped_exc: ApiException = get_exception_by_code(
            exc_info.code, api_response=getattr(exc_info, "api_response", None)
        )
        user_msg = mapped_exc.message or "Something went wrong. Please contact support."
        await send_or_edit(update, context, user_msg, parse_mode="Markdown")
        return ConversationHandler.END
    elif isinstance(exc_info, ApiException):
        logger.debug("ApiException")
        stack_trace = "".join(
            traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__)
        )
        await send_or_edit(update, context, exc_info.message)

    elif isinstance(exc_info, ValueError):
        logger.debug("ValueError")
        stack_trace = "".join(
            traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__)
        )
        await send_or_edit(update, context, str(exc_info))

    else:
        logger.debug("Exception")
        stack_trace = "".join(
            traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__)
        )
        await send_or_edit(
            update,
            context,
            f"Something went wrong. Please contact our support team with the following error ID: `{short_id}`",
            parse_mode="Markdown",
        )
        logger.exception(
            stack_trace,
        )

    return ConversationHandler.END

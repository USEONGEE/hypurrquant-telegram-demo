from hypurrquant.api.async_http import send_request as send_request_core
from hypurrquant.logging_config import (
    configure_logging,
)
from hypurrquant.api.exception import BaseOrderException
from .exception import get_exception_by_code
import os


# ================================
# 설정 정보
# ================================
_logger = configure_logging(__name__)
DEFAULT_SLIPPAGE = 0.01

BASE_URL = os.getenv("BASE_URL")


async def send_request(method: str, url: str, *, timeout: float = 20.0, **kwargs):
    """
    Send an HTTP request using the configured base URL.

    Args:
        method (str): HTTP method (GET, POST, etc.)
        url (str): Endpoint URL
        **kwargs: Additional parameters for the request

    Returns:
        Response: The response from the HTTP request.
    """
    try:
        return await send_request_core(method, url, timeout=timeout, **kwargs)
    except BaseOrderException as e:
        if e.code == 422:
            _logger.warning(f"Request failed with code {e.code} {e.message}")
        filtered_error = get_exception_by_code(e.code)
        raise filtered_error

    except Exception as e:
        _logger.exception("An error occurred while sending the request.")
        raise e

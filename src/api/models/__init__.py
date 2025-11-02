from pydantic import BaseModel
from typing import Any, Optional

from ._lpvault import *
from ._account import *


# ================================
# 기본 응답 DTO, 예외와 성공에 대한 응답
# ================================
class BaseResponse(BaseModel):
    code: int
    data: Any
    error_message: Optional[str] = None
    message: Optional[str] = None

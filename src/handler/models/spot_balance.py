from typing import Dict
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from hypurrquant.logging_config import configure_logging
import math

logger = configure_logging(__name__)


class SpotBalance(BaseModel):
    Name: str
    token: str
    Balance: float = Field(..., description="현재 보유 수량")
    entryNtl: float = Field(..., description="해당 토큰에 대한 원금(진입금액)")
    EntryPrice: float = Field(..., description="진입 단가 (entryNtl / Balance)")
    Price: float = Field(..., description="현재 midPx(중간가격)")
    Value: float = Field(..., description="현재 평가금액 (Balance * Price)")
    PNL: float = Field(..., description="평가손익 (Value - entryNtl)")
    PNL_percent: float = Field()

    @field_validator(
        "Balance",
        "entryNtl",
        "EntryPrice",
        "Price",
        "Value",
        "PNL",
        "PNL_percent",
        mode="before",
    )
    def validate_float_fields(cls, value, info: ValidationInfo):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            logger.info(
                f"Invalid value for {info.field_name}: {value}. Setting to 0.0."
            )
            return 0.0
        return value


class SpotBalanceMapping(BaseModel):
    balances: Dict[str, SpotBalance]
    usdc_balance: float
    stock_total_balance: float
    total_pnl: float
    total_pnl_percent: float

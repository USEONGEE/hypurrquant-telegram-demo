from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any


# --- PositionDetail 모델 ---
class PositionDetail(BaseModel):
    name: str
    szi: float
    leverage: float
    pos_type: str
    is_long: bool
    entryPx: float
    midPx: float
    positionValue: float
    marginUsed: float
    unrealizedPnl: float
    returnOnEquity: float
    liquidationPx: float


# --- MarginSummary 모델 ---
class MarginSummary(BaseModel):
    accountValue: float  # 계좌 총 가치
    totalNtlPos: float  # 전체 포지션의 명목(순) 크기
    totalRawUsd: float  # 기준(참조) Raw USD (고정)
    totalMarginUsed: float  # 포지션 유지에 사용된 증거금의 합

    @field_validator(
        "accountValue",
        "totalNtlPos",
        "totalRawUsd",
        "totalMarginUsed",
        mode="before",
    )
    def convert_to_float(cls, v):
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0


# --- Position 모델 ---
# get_perp_data에서는 assetPositions 리스트를 재구조화하여,
# 각 포지션 유형(예: "oneWay", "twoWay") 별로 코인 symbol을 key로 하는 딕셔너리 형태로 변환합니다.
class Position(BaseModel):
    oneWay: Dict[str, PositionDetail] = Field(default_factory=dict)
    twoWay: Dict[str, PositionDetail] = Field(default_factory=dict)


# --- 최종 PerpBalanceMapping DTO ---
class PerpBalanceMappingDTO(BaseModel):
    withdrawable: float  # 출금 가능한 USDC 잔액 (고정)
    accountValue: float  # 계좌 전체 가치 (현금 + 투자금액)
    invested: float  # 실제 투자 금액 (총 증거금에서 미실현 손익을 뺀 값)
    totalUnrealizedPnl: float  # 총 미실현 손익
    pnlPercentage: float  # PnL 비율 (%)
    totalMarginUsed: float  # 포지션 유지에 사용된 증거금의 총합
    crossMaintenanceMarginUsed: (
        float  # 크로스 마진 모드에서 포지션 유지에 필요한 최소 유지 증거금
    )
    time: int  # 데이터 조회 시각 (타임스탬프, 밀리초 단위)
    marginSummary: MarginSummary  # marginSummary 원본 데이터
    crossMarginSummary: MarginSummary  # crossMarginSummary 원본 데이터
    position: Position = Field(
        default_factory=Position
    )  # 포지션 정보 (이미 유형별, 코인별로 재구조화됨)

    class Config:
        extra = "ignore"  # 추가 필드는 무시

    @field_validator(
        "withdrawable",
        "accountValue",
        "invested",
        "totalUnrealizedPnl",
        "pnlPercentage",
        "totalMarginUsed",
        "crossMaintenanceMarginUsed",
        mode="before",
    )
    def convert_fields(cls, v):
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

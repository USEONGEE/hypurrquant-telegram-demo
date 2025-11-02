from typing import TypedDict
from datetime import datetime


class DexInforesponse(TypedDict):
    name: str
    protocol: str
    is_ve33: bool


class TokenInfo(TypedDict):
    ticker: str
    address: str


class CoreToken(TypedDict):
    wrapped: TokenInfo
    stable: TokenInfo


class PoolConfig(TypedDict):
    id: str
    chain: str
    dex_type: str
    pool_name: str
    fee: int
    token0_address: str
    token1_address: str
    address: str

    def get_token0_name(self) -> str:
        return self.pool_name.split("/")[0] if self.pool_name else ""

    def get_token1_name(self) -> str:
        return self.pool_name.split("/")[1] if self.pool_name else ""


class LpVaultWithConfigDict(TypedDict):
    id: str
    public_key: str
    pool_config_id: str
    range_pct: float
    created_at: datetime
    last_updated_at: datetime
    pool_config: PoolConfig


class LpvaultSettingsDict(TypedDict):
    public_key: str
    chain: str
    aggregator: str
    auto_claim: bool

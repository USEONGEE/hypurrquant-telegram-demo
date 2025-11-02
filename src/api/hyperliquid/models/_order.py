from pydantic import BaseModel
from typing import List


# ================================
# buy, sell에서 사용하는 응답 DTO
# ================================
class Filled(BaseModel):
    totalSz: float
    avgPx: float
    oid: int


class OrderData(BaseModel):
    """
    {
        "type": "order",
        "filled": [
            {
                "totalSz": 0.1,
                "avgPx": 100.0,
                "oid": 1
            }
        ]
    }
    """

    type: str
    filled: List[Filled]

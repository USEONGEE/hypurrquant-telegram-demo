from enum import Enum, auto


# ================================
# state
# ================================
class WalletState(Enum):
    SELECT_ACTION = auto()  # 전체매도/부분매도/종목선택 옵션 표시
    REFRESH = auto()


class ChangeState(Enum):
    CHANGE = auto()
    END = auto()


class CreateState(Enum):
    SET_NICKNAME = auto()
    END = auto()


class ImportState(Enum):
    IMPORT_KEY = auto()
    SET_NICKNAME = auto()
    END = auto()


class DeleteState(Enum):
    SELECT = auto()
    DELETE = auto()
    END = auto()


class ExportWallet(Enum):
    EXPORT = auto()
    END = auto()


class SpotToPerp(Enum):
    SPOT_TO_PERP = auto()
    END = auto()


class PerpToSpot(Enum):
    PERP_TO_SPOT = auto()
    END = auto()


class WalletRefresh(Enum):
    REFRESH = auto()
    END = auto()


class Authenticate(Enum):
    START = auto()

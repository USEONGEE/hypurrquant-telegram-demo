from enum import Enum


class DcaStates(Enum):
    SELECT_ACTION = "dca_start_select_action"


class DcaTimeSliceSpotStates(Enum):
    START = "dca_timeslice_spot_start"
    TYPING = "dca_timeslice_spot_typing"
    CONFIRM = "dca_timeslice_spot_confirm"


class DcaDeleteStates(Enum):
    START = "dca_delete_start"
    SELECT = "dca_delete_select"
    CONFIRM = "dca_delete_confirm"

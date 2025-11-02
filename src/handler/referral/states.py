from enum import Enum


class ReferralState(Enum):
    SELECT_ACTION = "referral_select_action"


class DetailState(Enum):
    START = "referral_detail_start"
    PAGE = "referral_detail_page"

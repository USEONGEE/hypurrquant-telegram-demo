from enum import Enum


class LpvaultState(Enum):
    START = "lpvault_start"
    SELECT_ACTION = "lpvault_start_select_action"


class LpvaultRegisterState(Enum):
    START = "lpvault_register_start"
    SELECT_DEX = "lpvault_register_select_dex"
    SELECT_POOL = "lpvault_register_select_pool"
    RANGE_PERCENTAGE = "lpvault_register_range_percentage"
    CUSTOM_RANGE_PERCENTAGE = "lpvault_register_custom_range_percentage"
    USE_EXISTING_SETTINGS = "lpvault_register_use_existing_settings"
    SELECT_AGGREGATOR = "lpvault_register_select_aggregator"
    AUTO_CLAIM = "lpvault_register_auto_claim"
    # IS_FARM = "lpvault_register_is_farm"
    # GOV_TOKEN_AUTO_SWAP = "lpvault_register_gov_token_auto_swap"
    SELECT_SWAP_TARGET_TOKEN = "lpvault_register_select_to_swap_token"
    CONFIRM = "lpvault_register_confirm"


class LpvaultManualMintState(Enum):
    START = "lpvault_manual_mint_start"
    SELECT_DEX = "lpvault_manual_mint_select_dex"
    SELECT_POOL = "lpvault_manual_mint_select_pool"
    RANGE_PERCENTAGE = "lpvault_manual_mint_range_percentage"
    CUSTOM_RANGE_PERCENTAGE = "lpvault_manual_mint_custom_range_percentage"
    USE_EXISTING_SETTINGS = "lpvault_manual_mint_use_existing_settings"
    SELECT_AGGREGATOR = "lpvault_manual_mint_select_aggregator"
    # IS_FARM = "lpvault_manual_mint_is_farm"
    CONFIRM = "lpvault_manual_mint_confirm"


class LpvaultUnregisterState(Enum):
    START = "lpvault_unregister_start"
    CONFIRM = "lpvault_unregister_confirm"
    CONFIRM2 = "lpvault_unregister_confirm2"


class LpvaultBridgeWrapState(Enum):
    START = "lpvault_bridge_wrap_start"
    SELECT = "lpvault_bridge_wrap_select"
    CONFIRM = "lpvault_bridge_wrap_confirm"


class LpvaultBridgeUnwrapState(Enum):
    START = "lpvault_bridge_unwrap_start"
    CONFIRM = "lpvault_bridge_unwrap_confirm"


class LpvaultRefreshState(Enum):
    START = "lpvault_refresh_start"


class LpvaultSwapState(Enum):
    START = "lpvault_swap_start"
    SELECT_IN_TICKER = "lpvault_swap_select_in_ticker"
    SELECT_OUT_TICKER = "lpvault_swap_select_out_ticker"
    SELECT_AMOUNT = "lpvault_swap_select_amount"
    SELECT_AGGREGATION = "lpvault_swap_select_aggregation"
    CONFIRM = "lpvault_swap_confirm"


class LpvaultSettingsState(Enum):
    START = "lpvault_settings_start"
    SELECT_ACTION = "lpvault_settings_select_action"
    AUTO_SWAP = "lpvault_settings_auto_swap"
    AUTO_FARM = "lpvault_settings_auto_farm"
    AUTO_CLAIM = "lpvault_settings_auto_claim"
    SELECT_AGGREGATOR = "lpvault_settings_select_aggregator"
    CONFIRM_AGGREGATOR = "lpvault_settings_confirm_aggregator"

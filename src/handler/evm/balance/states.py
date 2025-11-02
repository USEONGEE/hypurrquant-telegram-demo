from enum import Enum


class EvmBalanceState(Enum):
    START = "evm_balance_start"
    SELECT_ACTION = "evm_balance_start_select_action"


class SendState(Enum):
    START = "evm_balance_send_start"
    SELECT_ACCOUNT = "evm_balance_send_select_account"
    SELECT_TOKEN = "evm_balance_send_select_token"
    SELECT_AMOUNT = "evm_balance_send_select_amount"
    CONFIRM = "evm_balance_send_confirm"

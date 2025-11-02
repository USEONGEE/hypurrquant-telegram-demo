from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from handler.command import Command
from .wallet_change import wallet_change_start, change_state
from .wallet_delete import wallet_delete_start, delete_state
from .wallet_create import wallet_create_start, create_states
from .wallet_import import wallet_import_start, import_state
from .wallet_export import wallet_export_start
from .wallet_authenticate import authenticate_refresh_start
from .wallet_start import wallet_start
from .states import WalletState
from handler.start.states import StartStates
from handler.utils.cancel import cancel_handler
from handler.hyperliquid.start.states import HLCoreStartState

from handler.hyperliquid.balance.balance_send_usdc import (
    balance_send_usdc_start,
    send_usdc_state,
)
from handler.hyperliquid.balance.states import SendUsdcStates

# ================================
# ConversationHandler 등록
# ===============================
wallet_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.WALLET, wallet_start),
        CallbackQueryHandler(
            wallet_start,
            pattern=rf"^({StartStates.TRIGGER.value}|({HLCoreStartState.TRIGGER.value}))\|{Command.WALLET}",
        ),
    ],
    states={
        WalletState.SELECT_ACTION: [
            CallbackQueryHandler(wallet_change_start, pattern="^wallet_change"),
            CallbackQueryHandler(wallet_delete_start, pattern="^wallet_delete"),
            CallbackQueryHandler(wallet_create_start, pattern="^wallet_create"),
            CallbackQueryHandler(wallet_import_start, pattern="^wallet_import"),
            CallbackQueryHandler(wallet_export_start, pattern="^wallet_export"),
            CallbackQueryHandler(
                authenticate_refresh_start,
                pattern="^wallet_approve_builder_fee",
            ),
            CallbackQueryHandler(
                balance_send_usdc_start, pattern=f"^{SendUsdcStates.START.value}"
            ),
        ],
        **change_state,
        **create_states,
        **import_state,
        **delete_state,
        **send_usdc_state,
    },
    fallbacks=[cancel_handler],
    name=Command.WALLET,
    allow_reentry=True,
)

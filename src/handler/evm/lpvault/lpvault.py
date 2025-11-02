from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from handler.command import Command
from .lpvault_start import lpvault_command
from .lpvault_register import (
    lpvault_register_start,
    lpvault_register_states,
)
from .lpvault_unregister import (
    lpvault_unregister_start,
    unregister_states,
)
from .lpvault_bridge_wrap import (
    lpvault_bridge_wrap_start,
    lpvault_bridge_wrap_states,
)
from .lpvault_bridge_unwrap import (
    lpvault_bridge_unwrap_start,
    lpvault_bridge_unwrap_states,
)
from .lpvault_swap import (
    lpvault_swap_start,
    lpvault_swap_states,
)
from .lpvault_manual_mint import lpvault_manual_mint_start, manual_mint_states

from .lpvualt_settings import lpvault_settings_start, settings_states
from .lpvault_refresh import lpvault_refresh
from .cancel import cancel_handler
from .states import *

from handler.start.states import StartStates

from handler.wallet.wallet_change import wallet_change_start, change_state
from handler.wallet.states import ChangeState
from handler.utils.cancel import cancel_handler as common_cancel_handler

# ================================
# ConversationHandler 등록
# ===============================
lpvault_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.LPVAULT_AUTO, lpvault_command),
        CallbackQueryHandler(
            lpvault_command,
            pattern=rf"^{StartStates.TRIGGER.value}\|{Command.LPVAULT_AUTO}$",
        ),
    ],
    states={
        LpvaultState.SELECT_ACTION: [
            CallbackQueryHandler(
                lpvault_register_start,
                pattern=f"^{LpvaultRegisterState.START.value}",
            ),
            CallbackQueryHandler(
                lpvault_unregister_start,
                pattern=f"^{LpvaultUnregisterState.START.value}",
            ),
            CallbackQueryHandler(
                lpvault_bridge_wrap_start,
                pattern=f"^{LpvaultBridgeWrapState.START.value}",
            ),
            CallbackQueryHandler(
                lpvault_bridge_unwrap_start,
                pattern=f"^{LpvaultBridgeUnwrapState.START.value}",
            ),
            CallbackQueryHandler(
                lpvault_refresh,
                pattern=f"^{LpvaultRefreshState.START.value}",
            ),
            CallbackQueryHandler(
                lpvault_swap_start,
                pattern=f"^{LpvaultSwapState.START.value}",
            ),
            CallbackQueryHandler(
                lpvault_manual_mint_start,
                pattern=f"^{LpvaultManualMintState.START.value}",
            ),
            CallbackQueryHandler(
                lpvault_settings_start,
                pattern=f"^{LpvaultSettingsState.START.value}",
            ),
            # wallet
            CallbackQueryHandler(
                wallet_change_start,
                pattern=f"^{ChangeState.CHANGE.value}",
            ),
        ],
        **lpvault_register_states,
        **lpvault_bridge_wrap_states,
        **unregister_states,
        **lpvault_bridge_unwrap_states,
        **lpvault_swap_states,
        **settings_states,
        **manual_mint_states,
        # wallet
        **change_state,
    },
    fallbacks=[cancel_handler, common_cancel_handler],
    name=Command.LPVAULT_AUTO,
    allow_reentry=True,
)

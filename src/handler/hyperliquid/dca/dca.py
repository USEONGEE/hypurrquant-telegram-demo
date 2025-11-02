from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from handler.command import Command
from handler.utils.cancel import cancel_handler as common_cancel_handler
from .dca_start import dca_start
from .dca_spot import (
    dca_timeslice_spot_states,
    dca_spot_start,
)
from .dca_delete import (
    dca_delete_start,
    delete_states,
)
from .states import *
from .cancel import (
    cancel_handler as dca_cancel_handler,
)
from ..start.states import HLCoreStartState

# ================================
# ConversationHandler 등록
# ===============================
dca_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.DCA, dca_start),
        CallbackQueryHandler(
            dca_start,
            pattern=rf"^{HLCoreStartState.TRIGGER.value}\|{Command.DCA}$",
        ),
    ],
    states={
        DcaStates.SELECT_ACTION: [
            CallbackQueryHandler(
                dca_spot_start,
                pattern=f"^{DcaTimeSliceSpotStates.START.value}\\|(buy|sell)$",
            ),
            CallbackQueryHandler(
                dca_delete_start,
                pattern=f"^{DcaDeleteStates.START.value}$",
            ),
        ],
        **dca_timeslice_spot_states,
        **delete_states,
    },
    fallbacks=[dca_cancel_handler, common_cancel_handler],
    name=Command.DCA,
    allow_reentry=True,
)

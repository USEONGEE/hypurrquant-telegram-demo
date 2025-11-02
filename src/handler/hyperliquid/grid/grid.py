from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
)
from handler.command import Command
from handler.utils.cancel import cancel_handler as common_cancel_handler
from .grid_start import grid_start
from .states import *
from .cancel import (
    cancel_handler,
)
from .states import GridState, GridSpotBuyState
from .grid_spot_buy import (
    grid_spot_buy_start,
    grid_spot_buy_states,
)
from .grid_spot_sell import (
    grid_spot_sell_start,
    grid_spot_sell_states,
)
from .grid_cancel import (
    grid_cancel_start as grid_cancel_handler,
    grid_cancel_states,
)
from .grid_perp_open import (
    grid_perp_open_start,
    grid_perp_open_states,
)
from .grid_perp_close import (
    grid_perp_close_start,
    grid_perp_close_states,
)
from .grid_status import (
    grid_status_start,
)

from ..start.states import HLCoreStartState

# ================================
# ConversationHandler 등록
# ===============================
grid_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler(Command.GRID, grid_start),
        CallbackQueryHandler(
            grid_start,
            pattern=rf"^{HLCoreStartState.TRIGGER.value}\|{Command.GRID}$",
        ),
    ],
    states={
        GridState.SELECT_ACTION: [
            CallbackQueryHandler(
                grid_spot_buy_start,
                pattern=f"^{GridSpotBuyState.START.value}$",
            ),
            CallbackQueryHandler(
                grid_spot_sell_start,
                pattern=f"^{GridSpotSellState.START.value}$",
            ),
            CallbackQueryHandler(
                grid_cancel_handler,
                pattern=f"^{GridCancelState.START.value}$",
            ),
            CallbackQueryHandler(
                grid_perp_open_start,
                pattern=f"^{GridPerpOpenState.START.value}$",
            ),
            CallbackQueryHandler(
                grid_perp_close_start,
                pattern=f"^{GridPerpCloseState.START.value}$",
            ),
            CallbackQueryHandler(
                grid_status_start,
                pattern=f"^{GridStatusState.START.value}$",
            ),
        ],
        **grid_spot_buy_states,
        **grid_spot_sell_states,
        **grid_perp_open_states,
        **grid_cancel_states,
        **grid_perp_close_states,
    },
    fallbacks=[cancel_handler, common_cancel_handler],
    name=Command.GRID,
    allow_reentry=True,
)

from hypurrquant.logging_config import configure_logging
from handler.utils.utils import TimeUtils

logger = configure_logging(__name__)


def format_dca_spot_list(dca_spot_list):
    """
    Formats the DCA spot list into a message string.

    Args:
        dca_spot_list (list): List of DCA spot data.

    Returns:
        str: Formatted message string.
    """
    logger.debug(f"Formatting DCA spot list: {dca_spot_list}")

    text = "Spot DCA List: \n"

    message = ""
    for index, data in enumerate(dca_spot_list, start=1):
        if not data.get("symbol"):
            continue
        days, hours, minutes, _ = TimeUtils.remaining_time_from_iso(data["next_time"])
        days1, hours1, minutes1, _ = TimeUtils.seconds_to_dhms(data["interval_seconds"])
        message += (
            f"{index}. {'🟢' if data['is_buy'] else '🔴'} `{data['symbol']}` · "
            f"⏳`{days}d {hours}h {minutes}m` / 🔁`{days1}d {hours1}h {minutes1}m` · "
            f"💸`{data['amount']}` each · 🛒`{data['remaining_count']}` left\n"
        )

    if not message:
        message = "<Empty>\n"

    text += message
    text += "\n Please refer to the [documentation](https://docs.hypurrquant.com/bot_commands/tools/dca)"
    return text

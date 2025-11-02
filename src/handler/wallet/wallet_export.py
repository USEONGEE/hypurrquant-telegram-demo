from telegram import Update, Update
from telegram.ext import ContextTypes, CallbackContext, ConversationHandler

from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from handler.utils.utils import send_or_edit, answer
from api import AccountService

account_service = AccountService()

logger = configure_logging(__name__)


@force_coroutine_logging
async def wallet_export_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")

    async def delete_job(context: CallbackContext):
        job_data = context.job.data
        await context.bot.delete_message(
            chat_id=job_data["chat_id"], message_id=job_data["message_id"]
        )

    # 지갑 리스트들을 가져와서 선택할 수 있게 만들어주기
    await answer(update)
    private_key = await account_service.export_account(context._user_id)
    text = (
        "Export Wallet\n\n"
        "Here is your wallet address. Please keep it private and never share it with anyone to ensure the security of your assets.\n\n"
        "This message will be deleted in 20 seconds.\n"
        f"`{private_key}`"
    )

    message = await send_or_edit(update, context, text, parse_mode="Markdown")
    if message:
        context.application.job_queue.run_once(
            delete_job,
            when=20,
            data={"chat_id": message.chat_id, "message_id": message.message_id},
        )

    return ConversationHandler.END

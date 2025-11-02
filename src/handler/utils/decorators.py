from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from handler.utils.account_helpers import fetch_account_manager
from hypurrquant.models.account import Account


def require_builder_fee_approved(func):
    """
    래핑된 핸들러를 호출하기 전에
    active_account.is_approved_builder_fee를 검사합니다.
    False면 인증 안내 메시지 후 조기 리턴.
    """

    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # AccountManager 획득
        account_manager = await fetch_account_manager(context)
        account = await account_manager.get_active_account(force=True)
        # 승인 여부 체크
        if not account.is_approved_builder_fee:
            await update.effective_message.reply_text(
                "❗ Authentication is required.\n"
                "Please deposit USDC into your active wallet (or the account you're registering), then run /start to complete authentication before proceeding."
            )
            return  # 원래 핸들러 로직 실행 안 함
        # 승인된 경우 원래 핸들러 실행
        return await func(update, context)

    return wrapped

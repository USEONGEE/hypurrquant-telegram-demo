from hypurrquant.db import init_db, close_db
from hypurrquant.api.market_data import periodic_task as market_data_periodic_task2
from hypurrquant.logging_config import configure_logging

from api.hyperliquid import (
    MarketDataCache,
    PerpMarketDataCache,
    periodic_task as market_data_periodic_task,
)
from handler.command import Command
from handler.utils.exception_handler import exception_error_handler

from telegram.warnings import PTBUserWarning

from telegram import BotCommand
from telegram.ext import (
    Application,
    PicklePersistence,
)
from mongopersistence import MongoPersistence
from warnings import filterwarnings
import asyncio
import logging
import os


# Disable httpx _logger completely
logging.getLogger("httpx").disabled = True


filterwarnings(
    action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning
)

_logger = configure_logging(__name__)
perp_market_data_cache = PerpMarketDataCache()

# NOTE -> this values have been removed for security reasons.
username = os.getenv(...)
password = os.getenv(...)
ip = os.getenv(...)
port = os.getenv(...)
db_name = os.getenv(...)
bot_token = os.getenv(...)
profile = os.getenv(...)

_logger.info(f"bot_token: {bot_token}")
# MongoPersistence (prod 용)
persistence_prod = MongoPersistence(
    url=f"mongodb://{username}:{password}@{ip}:27017/",
    db_name=db_name,
    name_col_user_data="user-data",
    name_col_chat_data="chat-data",
    name_col_bot_data="bot-data",
    name_col_conversations_data="conversations",
    create_col_if_not_exist=True,
    ignore_general_data=["cache"],
)

# PicklePersistence (dev 용)
persistence_dev = PicklePersistence("bot_data.pickle")


async def common(application: Application) -> None:
    # 명령어 메뉴 설정

    from handler.start.start import start_handler
    from handler.hyperliquid.buy.buy import buy_conv_handler
    from handler.hyperliquid.buy_one.buy_one import buy_one_conv_handler
    from handler.hyperliquid.perp_one.perp_one import perp_one_conv_handler
    from handler.hyperliquid.sell.sell import sell_conv
    from handler.hyperliquid.close.close import close_conv
    from handler.hyperliquid.copytrading.copytrading import copytrading_conv_handler
    from handler.hyperliquid.dca.dca import dca_conv_handler
    from handler.hyperliquid.grid.grid import grid_conv_handler
    from handler.hyperliquid.delta.delta import delta_conv_handler
    from handler.hyperliquid.balance.balacne import balance_conv_handler
    from handler.hyperliquid.start.start import hyperliquid_core_start_handler
    from handler.evm.lpvault.lpvault import lpvault_conv_handler
    from handler.evm.balance.balance import (
        balance_conv_handler as evm_balance_conv_handler,
    )
    from handler.wallet.wallet import wallet_handler
    from handler.referral.referral import referral_conv_handler

    commands = [
        BotCommand(Command.START, "Start the bot"),
        # BotCommand(Command.BUY, "Buy spot assets using a strategy"),
        # BotCommand(Command.BUY_ONE, "Buy a spot asset"),
        # BotCommand(Command.SELL, "Sell spot assets"),
        # BotCommand(Command.PERP_ONE, "Open a perpetual position"),
        # BotCommand(Command.CLOSE, "Close perpetual positions."),
        # BotCommand(Command.WALLET, "Manage your wallet settings"),
        # BotCommand(Command.BALANCE, "View account balance and P&L summary"),
        # BotCommand(Command.REBALANCE, "PNL alarm features"),
        # BotCommand(
        #     Command.COPY_TRADING,
        #     "Execute copy traidng",
        # ),
        # BotCommand(Command.REFERRAL, "referral"),
    ]
    await application.bot.set_my_commands(commands)

    # 핸들러 등록
    application.add_handler(start_handler)
    # application.add_handler(buy_conv_handler)
    application.add_handler(buy_one_conv_handler)
    application.add_handler(perp_one_conv_handler)
    application.add_handler(sell_conv)
    application.add_handler(close_conv)
    application.add_handler(wallet_handler)
    application.add_handler(balance_conv_handler)
    application.add_handler(evm_balance_conv_handler)
    # application.add_handler(rebalance_conv_handler)
    application.add_handler(copytrading_conv_handler)
    application.add_handler(hyperliquid_core_start_handler)
    application.add_handler(referral_conv_handler)
    application.add_handler(dca_conv_handler)
    application.add_handler(grid_conv_handler)
    application.add_handler(delta_conv_handler)
    application.add_handler(lpvault_conv_handler)
    application.add_error_handler(exception_error_handler)


async def start_app_polling(application: Application) -> None:
    """
    Polling 방식으로 봇을 실행 (dev용).
    """
    await common(application)
    # 앱 시작
    await application.initialize()
    await application.start()
    try:
        # Polling 시작
        await application.updater.start_polling()
        # 무기한 대기
        await asyncio.Event().wait()
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


async def start_app_webhook(application: Application) -> None:
    """
    Webhook 방식으로 봇을 실행 (prod용) 예시.
    실제 운영 시에는 HTTPS, 도메인 등 설정이 필요.
    """
    await common(application)
    await application.initialize()

    # 여기서는 예시로 run_webhook 사용
    # 실제로는 SSL 인증서, 도메인 설정 등 필요
    await application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        webhook_url=f"https://YOUR_DOMAIN/bot{bot_token}",
    )
    # run_webhook가 종료되면 함수 끝 -> 종료 시그널 처리


async def main_async():
    init_db()
    try:
        fetch = MarketDataCache()

        async def combined_periodic_tasks():
            await asyncio.gather(
                market_data_periodic_task(fetch, 30),
                perp_market_data_cache.run(30),
                market_data_periodic_task2(30),
            )

        task = asyncio.create_task(combined_periodic_tasks())

        # 2) profile에 따른 Application & 실행
        if profile == "prod":
            # MongoPersistence 사용 (예시)
            application = (
                Application.builder()
                .token(bot_token)
                .persistence(persistence_prod)
                .build()
            )
            # Webhook 모드
            try:
                await start_app_webhook(application)
            finally:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logging.info("Periodic task cancelled.")
        else:
            # dev
            application = (
                Application.builder()
                .token(bot_token)
                .persistence(persistence_dev)
                .build()
            )

            _logger.debug("dev profile")
            try:
                await start_app_polling(application)
            finally:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logging.info("Periodic task cancelled.")
    finally:
        await close_db()


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from hypurrquant.models.market_data import MarketData
from handler.command import Command
from api.hyperliquid import StrategyService, StrategyMeta
from .settings import (
    BuySetting,
    StrategySetting,
)
from .states import (
    StrategyStates,
    MarketStrategyState,
    StockSelectStates,
)
from hypurrquant.logging_config import (
    configure_logging,
    force_coroutine_logging,
)
from handler.utils.utils import send_or_edit
from typing import Dict, List

strategyService = StrategyService()
logger = configure_logging(__name__)

CALLBACK_PREFIX = "BUY_STRATEGY_STATE"


# ================================
# 시작 - 원하는 장(상승, 하강)을 선택한 후
# ================================
@force_coroutine_logging
async def start_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await query.answer()
    user_data = context.user_data
    user_data["buy"]["strategy"] = StrategySetting()
    strategy_setting: StrategySetting = StrategySetting.get_setting(context)

    # 사용자가 선택한 장(상승, 하강 등) 가져오기
    selected_strategy = update.callback_query.data
    try:
        selected_strategy = MarketStrategyState(selected_strategy)
    except ValueError:
        raise ValueError(f"Invalid strategy type: {selected_strategy}")

    # 해당 장에 맞는 전략의 정보 가져오기
    _, strategy_key = selected_strategy.value.split("|", 1)
    all_strategies: Dict[str, StrategyMeta] = await strategyService.get_strategies(
        strategy_key
    )

    # 해당 전략이 없는 경우
    if not all_strategies:
        await update.callback_query.edit_message_text(
            "Failed to fetch strategy list from the server. Please try again."
        )
        return ConversationHandler.END

    strategy_setting.strategies = all_strategies

    # 전략 목록 표시
    keyboard = []
    for key in all_strategies.keys():
        keyboard.append(
            [InlineKeyboardButton(text=key, callback_data=f"{CALLBACK_PREFIX}|{key}")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "Select the strategy to execute\n\n", reply_markup=reply_markup
    )

    return StrategyStates.SELECTING_STRATEGY


# ================================
# 해당 장에서 원하는 전략 선택
# ================================
@force_coroutine_logging
async def pick_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    query = update.callback_query
    await query.answer()
    strategy_setting: StrategySetting = StrategySetting.get_setting(context)

    data = query.data  # ex) "pick_strategy|largecap"
    _, strategy_key = data.split("|", 1)
    strategies = strategy_setting.strategies

    if strategy_key not in strategies:
        await query.edit_message_text(
            text=f"The strategy does not exist. Please try again with /{Command.BUY}"
        )
        return ConversationHandler.END

    # 사용자가 선택한 전략
    strategy_setting.chosen_strategy_key = strategy_key
    chosen_meta = strategies[strategy_key]

    # default_params의 key 목록
    param_keys = list(chosen_meta.default_params.keys())
    strategy_setting.param_keys = param_keys
    strategy_setting.param_index = 0
    strategy_setting.collected_params = {}

    message = f"You have selected the '{strategy_key}' strategy.\n"
    await query.edit_message_text(text=message)

    # 만약 파라미터가 없다면 바로 실행
    if not param_keys:
        await query.message.reply_text(
            f"{message}\nNo parameters required. Executing..."
        )
        return await execute_strategy(update, context)

    # 파라미터가 있다면 첫 번째 파라미터부터 물어보기
    return await ask_next_param(update, context)


# ================================
# Parameter 입력 시작
# ================================
@force_coroutine_logging
async def ask_next_param(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    strategy_setting: StrategySetting = StrategySetting.get_setting(context)
    param_keys: List[str] = strategy_setting.param_keys
    param_index: int = strategy_setting.param_index

    if param_index >= len(param_keys):
        return await execute_strategy(update, context)

    current_param = param_keys[param_index]
    chosen_strategy_key = strategy_setting.chosen_strategy_key
    chosen_meta = strategy_setting.strategies[chosen_strategy_key]

    param_config = chosen_meta.default_params[current_param]
    default_val = param_config.default
    min_val = param_config.min
    max_val = param_config.max

    # ** 새로 추가된 label, description 가져오기 **
    label = param_config.label
    desc = param_config.description

    # 유저에게 보여줄 텍스트
    # 여기서는 Markdown을 안 쓰거나, 혹은 escape 처리해주는 편이 좋음
    # 예시는 간단히 HTML parse_mode로 가정
    ask_text = (
        f"<b>Parameter: {label}</b>\n"
        f"{desc}\n\n"
        f"Default: {default_val}\n"
        f"Range: {min_val} ~ {max_val}\n\n"
        "Please enter a value or click 'Use Default'."
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "Use Default",
                callback_data=f"strategy_parameter_use_default|{current_param}",
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_chat.send_message(
        text=ask_text, reply_markup=reply_markup, parse_mode="HTML"
    )

    return StrategyStates.ASKING_PARAMS


# ================================
# Parameter default 사용한 경우
# ================================
@force_coroutine_logging
async def use_default_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    사용자: '기본값 사용' 버튼 클릭 시
    """
    query = update.callback_query
    await query.answer()

    data = query.data  # ex: "strategy_parameter_use_default|marketcap_percentile"
    _, param_name = data.split("|", 1)

    strategy_setting: StrategySetting = StrategySetting.get_setting(context)
    chosen_strategy_key = strategy_setting.chosen_strategy_key
    chosen_meta = strategy_setting.strategies[chosen_strategy_key]

    param_config = chosen_meta.default_params[param_name]
    strategy_setting.collected_params[param_name] = param_config.default

    strategy_setting.param_index += 1
    return await ask_next_param(update, context)


# ================================
# Parameter를 직접 입력한 경우
# ================================
@force_coroutine_logging
async def on_param_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    사용자가 파라미터 값을 직접 입력(텍스트)
    """
    text_input = update.message.text.strip()
    strategy_setting = StrategySetting.get_setting(context)

    param_keys: List[str] = strategy_setting.param_keys
    param_index: int = strategy_setting.param_index

    if param_index >= len(param_keys):
        raise ValueError("Parameter index out of range.")

    current_param = param_keys[param_index]

    chosen_strategy_key = strategy_setting.chosen_strategy_key
    chosen_meta = strategy_setting.strategies[chosen_strategy_key]

    param_config = chosen_meta.default_params[current_param]
    min_val = param_config.min
    max_val = param_config.max

    # validation: 숫자만 허용
    try:
        value = float(text_input)
    except ValueError:
        await update.effective_message.reply_text(
            f"Invalid number. Try again. /{Command.BUY}"
        )
        return ConversationHandler.END

    # validation: 인자 범위 확인
    if not (min_val <= value <= max_val):
        await update.effective_message.reply_text(
            f"Please enter a number between {min_val} and {max_val}. Try again. /{Command.BUY}"
        )
        return ConversationHandler.END

    strategy_setting.collected_params[current_param] = value
    strategy_setting.param_index += 1
    return await ask_next_param(update, context)


# ================================
# Parameter 입력이 끝난 후 전략 실행
# ================================
@force_coroutine_logging
async def execute_strategy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"triggerred by user: {context._user_id}")
    """
    모든 파라미터 입력(또는 기본값 결정)이 끝났을 때 실제 전략을 호출
    """
    strategy_setting: StrategySetting = StrategySetting.get_setting(context)
    strategy_key = strategy_setting.chosen_strategy_key
    strategies: Dict[str, StrategyMeta] = strategy_setting.strategies

    chosen_meta = strategies[strategy_key]
    user_params = strategy_setting.collected_params

    # Pydantic StrategyMeta.update_params() 로 override
    chosen_meta.update_params(user_params)

    logger.debug(f"chosen_meta after update: {chosen_meta}")

    # 실제 API 호출
    market_data: List[MarketData] = await strategyService.execute_strategy(chosen_meta)
    buy_setting: BuySetting = BuySetting.get_setting(context)
    buy_setting.filterd_stocks = market_data

    keyboard = [[InlineKeyboardButton("Next", callback_data="GO_SELECT_STOCK")]]
    markup = InlineKeyboardMarkup(keyboard)

    await send_or_edit(
        update, context, "The strategy execution is complete.", reply_markup=markup
    )
    return StockSelectStates.START
    # if update.callback_query:
    #     await update.callback_query.edit_message_text(
    #         "The strategy execution is complete.",
    #         reply_markup=markup,
    #     )
    #     return StockSelectStates.START
    # elif update.message:
    #     await update.effective_message.reply_text(
    #         "The strategy execution is complete.",
    #         reply_markup=markup,
    #     )
    #     return StockSelectStates.START
    # else:
    #     return ConversationHandler.END


strategy_states = {
    StrategyStates.START: [
        CallbackQueryHandler(start_strategy, pattern="^BUY_STRATEGY_STATE")
    ],
    StrategyStates.SELECTING_STRATEGY: [
        CallbackQueryHandler(pick_strategy_callback, pattern=f"^{CALLBACK_PREFIX}")
    ],
    StrategyStates.ASKING_PARAMS: [
        CallbackQueryHandler(
            use_default_callback, pattern="^strategy_parameter_use_default\|"
        ),
        MessageHandler(filters.TEXT & ~filters.COMMAND, on_param_input),
    ],
}

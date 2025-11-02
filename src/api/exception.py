from typing import Any, Optional

from hypurrquant.exception import (
    PerpMarketDataException,
    PerpMetaException,
    AllMidsException,
    CandleDataException,
)
from hypurrquant.logging_config import configure_logging

_logger = configure_logging(__name__)


class ApiException(Exception):
    def __init__(
        self, message="An unexpected API error occurred. Please try again later."
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 사용자의 시크릿 키가 L1 체인에서 받아들일 수 없는 경우 -> 서비스 코드의 문제임
# ================================
class InvalidSecretKeyInL1ChainException(ApiException):
    def __init__(
        self,
        message="The provided secret key is invalid for the L1 chain. Please check your key and try again.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 사용자의 주문이 비어있는 경우
# ================================
class EmptyOrderException(ApiException):
    def __init__(
        self,
        message="The order is empty. Please add at least one item to the order and try again.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 슬리피지가 너무 높은 경우
# ================================
class TooHighSlippageException(ApiException):
    def __init__(
        self,
        message="The slippage value is too high. Please reduce the slippage and try again.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 슬리피지가 낮거나 음수인 경우
# ================================
class TooLowSlippageException(ApiException):
    def __init__(
        self,
        message="Some items could not be purchased due to the current slippage settings. The remaining items have been successfully purchased.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 주문서의 티커가 존재하지 않는 경우
# ================================
class NoSuchTickerException(ApiException):  # 서비스 에러
    def __init__(
        self,
        message="The requested ticker does not exist.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 다뤄지지 않은 Hyperliquid의 주문중 발생한 에러
# ================================
class HyperClientException(ApiException):
    def __init__(
        self,
        message="A client error occurred while placing the order. Please contack the developer.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# Hyperliquid의 서버에 에러가 발생한 경우
# ================================
class HyperServerException(ApiException):
    def __init__(
        self,
        message="An error occurred on the Hyperliquid server. Please try again later.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 백엔드 서버에서 다뤄지지 않은 예외
# ================================
class UnhandledErrorException(ApiException):  # 백엔드 에러
    def __init__(
        self,
        message="Something went wrong. Please try again later.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# Buy 주문 중 limit price가 너무 높거나 너무 많은 양의 금액을 주문한 경우
# ================================
class TooManySizeException(ApiException):
    def __init__(
        self,
        message="The limit price value is too high. Please use a smaller value and try again.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 서버에서 429에러가 발생한 경우 -> Hyperliquid에서 허용한 Limit rate를 서버가 넘긴 경우
# ================================
class ApiLimitExceededException(ApiException):
    def __init__(
        self,
        message="The API request limit has been exceeded. Try again!",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 사용자의 계정이 3개를 넘긴 경우
# ================================
class MaxAccountsReachedException(ApiException):
    def __init__(
        self,
        message="You can create up to 10 accounts only.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 사용자가 계좌 생성을 동일한 닉네임으로 지정한 경우
# ================================
class DuplicateNicknameException(ApiException):
    def __init__(
        self,
        message="Duplicate nicknames are not allowed. Please choose a unique nickname.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# telegramId, nickname으로 조회했는데 nickname이 존재하지 않는 경우
# ================================
class NoSuchAccountByProvidedNickNameException(ApiException):
    def __init__(
        self,
        message="No account exists with the provided nickname. Please contack the developer.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 주어진 텔레그램 게정이 존재하지 않는 경우
# ================================
class NoSuchAccountByProvidedTelegramIdException(ApiException):
    def __init__(
        self,
        message="No account exists with the provided telegram id. Please contack the developer.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 백엔드 서버에 올바르지 않은 형식으로 예외를 보냈을 경우
# ================================
class Api422Exception(ApiException):
    def __init__(
        self,
        message="422 Please contack the developer.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 주문량이 너무 작은 경우
# ================================
class TooSmallOrderAmountException(ApiException):
    def __init__(
        self,
        message="The order amount is too small. Please increase the order amount and try again.",
    ):
        self.message = message
        super().__init__(self.message)


class InsufficientMarginException(ApiException):
    def __init__(
        self,
        message="Insufficient margin for the order. Please check your account balance and try again.",
    ):
        self.message = message
        super().__init__(self.message)


class BuilderFeeNotApprovedException(ApiException):
    def __init__(
        self,
        message="The builder fee has not been approved. Please check your account settings.",
    ):
        self.message = message
        super().__init__(self.message)


class RecudeOnlyException(ApiException):
    def __init__(
        self,
        message="The order is a reduce-only order. Please check your order settings.",
    ):
        self.message = message
        super().__init__(self.message)


class TooManyCumulativeOrdersException(ApiException):
    def __init__(
        self,
        message="The cumulative order limit has been exceeded. Please reduce the number of orders and try again.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 잔고가 부족한 경우
# ================================
class InsufficientBalanceException(ApiException):
    def __init__(
        self,
        message="Insufficient balance for withdrawal.",
    ):
        self.message = message
        super().__init__(self.message)


class CannotAcquireLockException(ApiException):
    def __init__(
        self,
        message="Cannot acquire lock. Please try again later.",
    ):
        self.message = message
        super().__init__(self.message)


class SubscribeFailException(ApiException):
    def __init__(
        self,
        message="Failed to subscribe to the market data. Please try again.",
    ):
        self.message = message
        super().__init__(self.message)


class NoSuchSubscriptionException(ApiException):
    def __init__(
        self,
        message="No such subscription exists.",
    ):
        self.message = message
        super().__init__(self.message)


class CannotDeleteSubscriptionException(ApiException):
    def __init__(
        self,
        message="Cannot delete the subscription.",
    ):
        self.message = message
        super().__init__(self.message)


class NotCopyTradingAccountException(ApiException):
    def __init__(
        self,
        message="This account is not a copy trading account.",
    ):
        self.message = message
        super().__init__(self.message)


class MaxCopyReachException(ApiException):
    def __init__(
        self,
        message="Caanot copy this account. The maximum number of copy trading accounts has been reached.",
    ):
        self.message = message
        super().__init__(self.message)


class InvalidEthAddressException(ApiException):
    def __init__(
        self,
        message="The provided Ethereum address is invalid.",
    ):
        self.message = message
        super().__init__(self.message)


class MaxTargetReachedException(ApiException):
    def __init__(
        self,
        message="You can only subscribe to a maximum of 1 target.",
    ):
        self.message = message
        super().__init__(self.message)


class MaxSubscriptionReachedException(ApiException):
    def __init__(
        self,
        # 모든 구독 가능한
        message="Subscription limit reached. Please try again once other users have canceled their subscriptions",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 올바르지 않은 필터를
# ================================
class InvalidFilterException(ApiException):
    def __init__(
        self,
        message="This filter is invalid. Please contack the developer.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 올바르지 않은 주문량을 입력한 경우
# ================================
class MarketDataException(ApiException):
    def __init__(
        self,
        message="Market Data is empty",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 선택된 전략에 해당하는 데이터가 없을 경우
# ================================
class NoDataWihtFilter(ApiException):
    def __init__(
        self,
        message="No stocks were selected with the chosen strategy and parameters. Please try again with a different strategy or parameters.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 모든 계정을 삭제하려고 한 경우
# ================================
class CannotDeleteAllAccounts(ApiException):
    def __init__(
        self,
        message="At least one account must be maintained.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# Import 중 제공한 키가 유효하지 않을 경우
# ================================
class InvalidSecretKey(ApiException):
    def __init__(
        self,
        message="The provided secret key is invalid.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# USDC 송금에 실패한 경우
# ================================
class SendUsdcException(ApiException):
    def __init__(
        self,
        message="Failed to send USDC.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 서버 데이터베이스 접속에 문제가 있는 경우
# ================================
class PymongoException(ApiException):
    def __init__(
        self,
        message="There is an issue with the server. Please try again in a moment.",
    ):
        self.message = message
        super().__init__(self.message)


# ================================
# 외부 서버 aiohttp 에러
# ================================
class AioHttpServerExcpetion(ApiException):
    def __init__(
        self,
        message="There is an issue with the server. Please try again in a moment.",
    ):
        self.message = message
        super().__init__(self.message)


class InsufficientSpotBalanceException(ApiException):
    def __init__(
        self,
        message="Insufficient balance for spot trading.",
    ):
        self.message = message
        super().__init__(self.message)


class InvalidNonceException(ApiException):
    def __init__(
        self,
        message="Invalid nonce. Try again.",
    ):
        self.message = message
        super().__init__(self.message)


class NoSuchPositionException(ApiException):
    def __init__(
        self,
        message="No open position for the specified ticker. Please open a position first.",
    ):
        self.message = message
        super().__init__(self.message)


class InsufficientUsdcException(ApiException):
    def __init__(
        self,
        message="Insufficient USDC balance for the operation. Please deposit more USDC.",
    ):
        self.message = message
        super().__init__(self.message)


class UnsupportedDeltaNeutralSymbolError(ApiException):
    def __init__(
        self,
        message="Unsupported delta-neutral symbol. Please use a valid symbol.",
    ):
        self.message = message
        super().__init__(self.message)


class InsufficientPerpBalanceException(ApiException):
    def __init__(
        self,
        message="Insufficient balance for perpetual trading.",
    ):
        self.message = message
        super().__init__(self.message)


class NoSuchAccountByProvidedPublicKeyException(ApiException):
    def __init__(
        self,
        message="No account exists with the provided public key. Please contack the developer.",
    ):
        self.message = message
        super().__init__(self.message)


class RebalanceAccountAlreadyExistsException(ApiException):
    def __init__(
        self,
        message="Rebalance account already exists.",
    ):
        self.message = message
        super().__init__(self.message)


class ShouldBeTradingAcocuntException(ApiException):
    def __init__(
        self,
        message="This wallet is already registered for either alarm or copy trading purposes. Please try again with a different wallet.",
    ):
        self.message = message
        super().__init__(self.message)


class RebalanceAccountNotRegisteredException(ApiException):
    def __init__(
        self,
        message="Rebalance account is not registered.",
    ):
        self.message = message
        super().__init__(self.message)


class NoRebalanceDetailsException(ApiException):
    def __init__(
        self,
        message="No rebalance details for the account.",
    ):
        self.message = message
        super().__init__(self.message)


class AlreadyRegisteredAccountException(ApiException):
    def __init__(
        self,
        message="The account is already registered.",
    ):
        self.message = message
        super().__init__(self.message)


class CannotApproveBuilderFeeException(ApiException):
    def __init__(
        self,
        # 인증이 불가능합니다. USDC를 예치한 후 다시 시도해주세요
        message="Cannot authenticate. Please deposit USDC and try again.",
    ):
        self.message = message
        super().__init__(self.message)


class CannotFoundReferralCodeException(ApiException):
    def __init__(
        self,
        message="Cannot find referral code. Please try again.",
    ):
        self.message = message
        super().__init__(self.message)


class CannotAddReferralException(ApiException):
    def __init__(
        self,
        message="Cannot add referral. Please try again.",
    ):
        self.message = message
        super().__init__(self.message)


class NoSuchReferralCodeException(ApiException):
    def __init__(self, message="No such referral code exists. Please check the code"):
        self.message = message
        super().__init__(self.message)


class UsdTransferSmmllerThanFeeException(ApiException):
    def __init__(
        self,
        message="The account you’re sending funds to is being registered with Hyperliquid for the first time. Please send at least $2.",
    ):
        self.message = message
        super().__init__(self.message)


class ShouldBeDexLpVaultAccountException(ApiException):
    def __init__(
        self,
        message="This account is not a DEX LP Vault account. Please use a valid DEX LP Vault account.",
    ):
        self.message = message
        super().__init__(self.message)


class AccountTypeNotFoundException(ApiException):
    def __init__(
        self,
        message="The specified account type does not exist. Please check the account type and try again.",
    ):
        self.message = message
        super().__init__(self.message)


class DuplicationDcaException(ApiException):
    def __init__(
        self,
        # 한 개의 티커는 한 번에 한 개의 DCA 주문만 가능합니다.
        message=" A ticker can only have one DCA order at a time.",
    ):
        self.message = message
        super().__init__(self.message)


class CannotCreateMoreDcaException(ApiException):
    def __init__(
        self,
        message="You have reached the maximum limit orders.",
    ):
        self.message = message
        super().__init__(self.message)


class NoSuchDexException(ApiException):
    def __init__(
        self,
        message="The specified DEX does not exist. Please check the DEX and try again.",
    ):
        self.message = message
        super().__init__(self.message)


class NoSuchPoolException(ApiException):
    def __init__(
        self,
        message="The specified pool does not exist. Please check the pool and try again.",
    ):
        self.message = message
        super().__init__(self.message)


class NoLpVaultJobException(ApiException):
    def __init__(
        self,
        message="No LP Vault job found for the specified account. Please check the account and try again.",
    ):
        self.message = message
        super().__init__(self.message)


class NoSuchDexProtocolException(ApiException):
    def __init__(
        self,
        message="The specified DEX protocol is not supported. Please check the protocol and try again.",
    ):
        self.message = message
        super().__init__(self.message)


class DecreaseLiquidityException(ApiException):
    def __init__(
        self,
        message="Decrease liquidity failed. Please check the parameters and try again.",
    ):
        self.message = message
        super().__init__(self.message)


class RouteExpiredException(ApiException):
    def __init__(
        self,
        message="The route has expired. try again.",
    ):
        self.message = message
        super().__init__(self.message)


def get_exception_by_code(
    code: int, api_response: Optional[Any] = None
) -> ApiException:
    """
    에러 코드에 따라 적절한 예외를 반환하는 함수.

    Args:
        code (int): 상호 협의된 에러 코드.
        message (str): 에러 메시지.
        api_response (Optional[Any]): 관련된 추가 API 응답 데이터.

    Returns:
        ApiException: 적절한 예외 객체.
    """

    _logger.debug(f"API Error Code: {code}")

    exception_mapping = {
        422: Api422Exception,
        500: HyperClientException,
        501: HyperServerException,
        502: PymongoException,
        503: AioHttpServerExcpetion,
        # order server
        1000: InvalidSecretKeyInL1ChainException,
        1001: EmptyOrderException,
        1002: TooHighSlippageException,
        1003: TooLowSlippageException,
        1004: NoSuchTickerException,
        1005: TooSmallOrderAmountException,
        1006: InsufficientMarginException,
        1007: BuilderFeeNotApprovedException,
        1008: RecudeOnlyException,
        1009: TooManyCumulativeOrdersException,
        1010: TooManySizeException,
        1011: InsufficientSpotBalanceException,
        1012: InvalidNonceException,
        1013: NoSuchPositionException,
        1014: InsufficientUsdcException,
        1015: UnsupportedDeltaNeutralSymbolError,
        # account server
        3000: ApiLimitExceededException,
        3001: MaxAccountsReachedException,
        3002: DuplicateNicknameException,
        3003: NoSuchAccountByProvidedNickNameException,
        3004: NoSuchAccountByProvidedTelegramIdException,
        3005: CannotDeleteAllAccounts,
        3006: InvalidSecretKey,
        3007: SendUsdcException,
        3009: InsufficientPerpBalanceException,
        3010: NoSuchAccountByProvidedPublicKeyException,
        3011: RebalanceAccountAlreadyExistsException,
        3012: ShouldBeTradingAcocuntException,
        3013: RebalanceAccountNotRegisteredException,
        3014: NoRebalanceDetailsException,
        3015: AlreadyRegisteredAccountException,
        3016: CannotApproveBuilderFeeException,
        3017: CannotFoundReferralCodeException,
        3018: CannotAddReferralException,
        3019: NoSuchReferralCodeException,
        3020: UsdTransferSmmllerThanFeeException,
        3021: ShouldBeDexLpVaultAccountException,
        3022: AccountTypeNotFoundException,
        3100: InsufficientBalanceException,
        # copy trading server
        5000: CannotAcquireLockException,
        5001: SubscribeFailException,
        5002: NoSuchSubscriptionException,
        5003: CannotDeleteSubscriptionException,
        5004: NotCopyTradingAccountException,
        5005: MaxCopyReachException,
        5006: InvalidEthAddressException,
        5007: MaxTargetReachedException,
        5008: MaxSubscriptionReachedException,
        # dca server
        6000: DuplicationDcaException,
        6001: CannotCreateMoreDcaException,
        # strategy server
        7000: InvalidFilterException,
        # dex server
        8000: NoSuchPoolException,
        8001: NoSuchDexException,
        8002: NoLpVaultJobException,
        8003: NoSuchDexProtocolException,
        8004: DecreaseLiquidityException,
        8005: RouteExpiredException,
        # market data server
        9000: MarketDataException,
        9001: CandleDataException,
        9002: AllMidsException,
        9003: PerpMetaException,
        9004: PerpMarketDataException,
        9999: UnhandledErrorException,  # Unhandled error
    }

    exception_class = exception_mapping.get(
        code, UnhandledErrorException
    )  # 기본값은 UnhandledErrorException
    return exception_class()  # 메시지를 전달하여 예외 생성

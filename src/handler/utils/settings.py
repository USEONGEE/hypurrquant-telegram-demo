from typing import Callable, Type, TypeVar, Self
from telegram.ext import ContextTypes


class SettingMixin:
    """모든 Setting 클래스가 가져야 하는 인터페이스(정적 타입 보장용)."""

    @classmethod
    def get_setting(cls: type[Self], context: ContextTypes.DEFAULT_TYPE) -> Self: ...
    @classmethod
    def clear_setting(cls: type[Self], context: ContextTypes.DEFAULT_TYPE) -> None: ...

    @property
    def return_to(self) -> str:
        return getattr(self, "_return_to")

    @return_to.setter
    def return_to(self, value: str) -> None:
        setattr(self, "_return_to", value)


T = TypeVar("T", bound=SettingMixin)


def _get(context: ContextTypes.DEFAULT_TYPE, root: str, key: str, cls: Type[T]) -> T:
    bucket = context.user_data.setdefault(root, {})
    if key not in bucket:
        bucket[key] = cls()
    return bucket[key]


def _clear(context: ContextTypes.DEFAULT_TYPE, root: str, key: str) -> None:
    if root not in context.user_data:
        return

    if root == key:
        # root 전체 삭제
        context.user_data.pop(root, None)
    else:
        # root 하위 key만 삭제
        context.user_data[root].pop(key, None)
        if not context.user_data[root]:
            # root 밑이 비면 root도 삭제
            context.user_data.pop(root, None)


def setting_paths(root: str, key: str) -> Callable[[Type[T]], Type[T]]:
    """
    각 Setting 클래스에 get_setting/clear_setting 정적 메서드를 주입하는 데코레이터.
    """

    def decorator(cls: Type[T]) -> Type[T]:
        def _get_setting(inner_cls: Type[T], context: ContextTypes.DEFAULT_TYPE) -> T:
            # inner_cls = 주입받은 Setting 클래스
            return _get(context, root, key, inner_cls)

        def _clear_setting(
            inner_cls: Type[T], context: ContextTypes.DEFAULT_TYPE
        ) -> None:
            _clear(context, root, key)

        # 정적 메서드로 주입
        cls.get_setting = classmethod(_get_setting)  # type: ignore[attr-defined]
        cls.clear_setting = classmethod(_clear_setting)  # type: ignore[attr-defined]
        # 선택: 클래스에 키를 달아두고 싶으면
        setattr(cls, "__key__", key)
        return cls

    return decorator

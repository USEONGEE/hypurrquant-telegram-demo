from telegram.ext import (
    ContextTypes,
)
from handler.command import Command
from handler.utils.settings import SettingMixin, setting_paths
from typing import Optional


class _WalletSetting(SettingMixin):
    _return_to: str = Command.WALLET


@setting_paths("wallet", "wallet")
class WalletSetting(_WalletSetting):
    _return_to: str = Command.START


@setting_paths("wallet", "import")
class ImportSetting(_WalletSetting):
    private_key: Optional[str] = None
    nickname: Optional[str] = None


@setting_paths("wallet", "delete")
class DeleteSetting(_WalletSetting):
    nickname: Optional[str] = None


@setting_paths("wallet", "change")
class ChangeSetting(_WalletSetting):
    pass


@setting_paths("wallet", "create")
class CreateSetting(_WalletSetting):
    pass

from __future__ import annotations

from .api_types import LoginScreen
from .core.login import LoginImpl

class CoreApi:
    @staticmethod
    def CreateLoginScreen() -> LoginScreen:
        """
        Entry point for the GUI.

        """
        return LoginImpl()

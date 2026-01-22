from __future__ import annotations

from .api_types import TrainingSelectScreen, UserProfile, AuthResult
from .core.training_select_impl import TrainingSelectImpl
from .core.user import create_user, login

class CoreApi:
    @staticmethod
    def Start(user_profile: UserProfile | None = None) -> TrainingSelectScreen:
        """
        Entry point for the GUI.

        Returns the initial TrainingSelectScreen (ladder with all available
        trainings). The caller never needs to know about plugins directly,
        only about this screen and its view.
        """
        return TrainingSelectImpl.start(user_profile)

    @staticmethod
    def Login(name: str) -> AuthResult:
        """
        Login with the given user name.
        """
        return login(name)

    @staticmethod
    def CreateUser(name: str) -> AuthResult:
        """
        Create a new user with the given name.
        """
        return create_user(name)

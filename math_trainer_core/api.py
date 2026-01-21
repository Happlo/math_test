from __future__ import annotations

from .api_types import TrainingSelectScreen, UserProfile
from .core.training_select_impl import TrainingSelectImpl  # concrete implementation

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

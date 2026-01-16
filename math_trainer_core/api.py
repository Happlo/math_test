from __future__ import annotations

from typing import List

from .plugin_loader import load_plugin_factories
from .plugin_api import PluginInfo, EmojiIcon, FileIcon
from .api_types import (
    TrainingSelectScreen,
    TrainingSelectView,
    TrainingItemView,
)
from .core.training_select_impl import TrainingSelectImpl  # concrete implementation
from pathlib import Path

def _icon_to_text(info: PluginInfo) -> str:
    """
    Convert PluginInfo.icon (EmojiIcon | FileIcon) to a string that the GUI
    can render in TrainingItemView.icon_text.

    For now:
    - EmojiIcon -> its symbol (e.g. "➕")
    - FileIcon  -> the file path as string (Qt side can decide to load pixmap)
    """
    icon = info.icon
    if isinstance(icon, EmojiIcon):
        return icon.symbol
    if isinstance(icon, FileIcon):
        return str(icon.path)
    return "?"

class CoreApi:
    @staticmethod
    def Start() -> TrainingSelectScreen:
        """
        Entry point for the GUI.

        Loads all plugins and returns the initial TrainingSelectScreen
        (ladder with all available trainings). The caller never needs to
        know about plugins directly, only about this screen and its view.
        """
        plugins = load_plugin_factories()  # dict[id, LoadedPlugin]

        items: List[TrainingItemView] = []
        for loaded in plugins.values():
            info: PluginInfo = loaded.info
            items.append(
                TrainingItemView(
                    training_id=info.id,        # opaque id, only core cares
                    label=info.name,
                    description=info.description,
                    icon_text=_icon_to_text(info),
                )
            )

        view = TrainingSelectView(
            title="Choose training",
            items=items,
            selected_index=0,
        )

        # TrainingSelectImpl will keep 'plugins' internally, so later when the
        # user presses Enter, it can create the right plugin instance and
        # transition to a TrainingGridScreen.
        return TrainingSelectImpl(view=view, plugins=plugins)

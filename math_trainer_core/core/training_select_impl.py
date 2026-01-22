from __future__ import annotations

from ..api_types import (
    TrainingSelectScreen,
    TrainingSelectView,
    TrainingGridScreen,
    TrainingItemView,
    SelectMove,
    UserProfile,
)
from ..plugins.plugin_api import Plugin, PluginInfo, EmojiIcon, FileIcon
from ..plugins.plugin_loader import load_plugin_factories
from .training_grid_impl import TrainingGridImpl
from .user import load_user, StoredUserProfile


class TrainingSelectImpl(TrainingSelectScreen):
    @staticmethod
    def start(user_profile: UserProfile | None = None) -> TrainingSelectScreen:
        plugins = load_plugin_factories()  # dict[id, LoadedPlugin]
        name = user_profile.name if user_profile is not None else "Player"
        stored_profile = load_user(name)
        if stored_profile is None:
            stored_profile = StoredUserProfile(name=name, items={})

        items: list[TrainingItemView] = []
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
        return TrainingSelectImpl(view=view, plugins=plugins, user_profile=stored_profile)

    def __init__(self, view: TrainingSelectView, plugins, user_profile: StoredUserProfile):
        self._view = view
        self._plugins = plugins
        self._user_profile = user_profile

    @property
    def view(self) -> TrainingSelectView:
        return self._view

    def move(self, event: SelectMove) -> TrainingSelectScreen:
        if event == SelectMove.UP:
            self._view.selected_index = max(0, self._view.selected_index - 1)
        elif event == SelectMove.DOWN:
            self._view.selected_index = min(
                len(self._view.items) - 1,
                self._view.selected_index + 1
            )
        return self

    def enter(self):
        selected = self._view.items[self._view.selected_index]
        loaded = self._plugins[selected.training_id]
        factory = loaded.factory
        plugin = factory.CreatePlugin()
        info = factory.PluginInfo()
        return _make_initial_training_grid(
            plugin=plugin,
            selected=selected,
            info=info,
            parent_select=self,
            user_profile=self._user_profile,
        )


def _make_initial_training_grid(
    plugin: Plugin,
    selected: TrainingItemView,
    info: PluginInfo,
    parent_select: TrainingSelectScreen,
    user_profile: StoredUserProfile,
) -> TrainingGridScreen:
    return TrainingGridImpl(
        plugin=plugin,
        info=info,
        parent_select=parent_select,
        title=selected.label,
        user_profile=user_profile,
        training_id=selected.training_id,
    )


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

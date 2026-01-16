from __future__ import annotations

from ..api_types import (
    TrainingSelectScreen,
    TrainingSelectView,
    TrainingGridScreen,
    TrainingItemView,
    SelectMove,
)
from ..plugin_api import Plugin, PluginInfo
from .training_grid_impl import TrainingGridImpl


class TrainingSelectImpl(TrainingSelectScreen):
    def __init__(self, view: TrainingSelectView, plugins):
        self._view = view
        self._plugins = plugins

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
        )


def _make_initial_training_grid(
    plugin: Plugin,
    selected: TrainingItemView,
    info: PluginInfo,
    parent_select: TrainingSelectScreen,
) -> TrainingGridScreen:
    return TrainingGridImpl(
        plugin=plugin,
        info=info,
        parent_select=parent_select,
        title=selected.label,
    )

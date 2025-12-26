from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .plugin_loader import load_plugin_factories
from .core import MathTrainerCore
from .plugin_api import IRandom, PluginInfo


@dataclass(frozen=True)
class Mode:
    mode_id: str
    name: str
    description: str


class CoreApi:
    @staticmethod
    def Modes() -> list[Mode]:
        plugins = load_plugin_factories()
        return [
            Mode(p.info.plugin_id, p.info.name, p.info.description)
            for p in plugins.values()
        ]

    @staticmethod
    def DefaultConfig(mode_id: str) -> dict[str, Any]:
        plugins = load_plugin_factories()
        return dict(plugins[mode_id].factory.PluginConfig())

    @staticmethod
    def Create(mode_id: str, overrides: dict[str, Any]) -> MathTrainerCore:
        plugins = load_plugin_factories()
        loaded = plugins[mode_id]
        plugin_instance = loaded.factory.CreatePlugin(overrides)
        return MathTrainerCore(plugin=plugin_instance)

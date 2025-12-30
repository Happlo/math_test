from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol, Union
from enum import Enum, auto

from .plugin_loader import load_plugin_factories
from .plugin_api import PluginInfo
from .core import Start
from .api_types import Mode, TrainerConfig, QuestionState, State


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
    def Start(config: TrainerConfig, mode_id: str, overrides: dict[str, Any]) -> QuestionState:
        plugins = load_plugin_factories()
        loaded = plugins[mode_id]
        plugin_instance = loaded.factory.CreatePlugin(overrides)
        return Start(plugin=plugin_instance, config=config)

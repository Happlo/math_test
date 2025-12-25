from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Type, Protocol

from .plugin_api import PluginInfo, IOperatorPlugin


class IPluginFactory(Protocol):
    @staticmethod
    def PluginInfo() -> PluginInfo: ...

    @staticmethod
    def PluginConfig() -> dict[str, Any]: ...

    @staticmethod
    def CreatePlugin(config: Mapping[str, Any]) -> IOperatorPlugin: ...


@dataclass(frozen=True)
class LoadedPlugin:
    info: PluginInfo
    default_config: dict[str, Any]
    factory: Type[IPluginFactory]


def load_plugin_factories() -> Dict[str, LoadedPlugin]:
    plugins_pkg = "math_trainer_core.plugins"
    package = importlib.import_module(plugins_pkg)

    result: Dict[str, LoadedPlugin] = {}

    for mod in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{plugins_pkg}.{mod.name}")
        factory = getattr(module, "PLUGIN_FACTORY", None)
        if factory is None:
            continue

        info = factory.PluginInfo()
        cfg = factory.PluginConfig()

        result[info.plugin_id] = LoadedPlugin(
            info=info,
            default_config=dict(cfg),
            factory=factory,
        )

    return result

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from typing import Any, Dict, Type

from .plugin_api import PluginInfo, PluginFactory


@dataclass(frozen=True)
class LoadedPlugin:
    info: PluginInfo
    default_config: dict[str, Any]
    factory: Type[PluginFactory]


def load_plugin_factories() -> Dict[str, LoadedPlugin]:
    plugins_pkg = "math_trainer_core.plugins"
    package = importlib.import_module(plugins_pkg)

    result: Dict[str, LoadedPlugin] = {}

    for mod in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{plugins_pkg}.{mod.name}")
        factory : PluginFactory = getattr(module, "PLUGIN_FACTORY", None)
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

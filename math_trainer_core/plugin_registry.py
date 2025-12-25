from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from typing import Dict, Iterable

from .plugin_api import IOperatorPlugin, PluginInfo


@dataclass(frozen=True)
class PluginRegistry:
    _plugins: Dict[str, IOperatorPlugin]

    def list_infos(self) -> list[PluginInfo]:
        infos = [p.info() for p in self._plugins.values()]
        return sorted(infos, key=lambda i: i.plugin_id)

    def get(self, plugin_id: str) -> IOperatorPlugin:
        return self._plugins[plugin_id]


def load_plugins() -> PluginRegistry:
    plugins_pkg = "math_trainer_core.plugins"
    package = importlib.import_module(plugins_pkg)

    plugins: Dict[str, IOperatorPlugin] = {}
    for mod in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{plugins_pkg}.{mod.name}")
        plugin = getattr(module, "PLUGIN", None)
        if plugin is None:
            continue
        pid = plugin.info().plugin_id
        plugins[pid] = plugin

    return PluginRegistry(plugins)

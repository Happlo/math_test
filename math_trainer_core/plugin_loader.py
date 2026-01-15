from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from typing import Dict, Type

from .plugin_api import PluginInfo, PluginFactory


@dataclass(frozen=True)
class LoadedPlugin:
    info: PluginInfo
    factory: Type[PluginFactory]


def load_plugin_factories() -> Dict[str, LoadedPlugin]:
    """
    Discover plugins under math_trainer_core.plugins.*

    Expected layout per plugin:

        math_trainer_core/
          plugin_api.py
          plugins/
            addition/
              __init__.py  (can be empty)
              plugin.py    (defines PLUGIN_FACTORY)

    Each plugin package must expose a top-level `PLUGIN_FACTORY`
    in its `plugin.py` module.
    """
    plugins_pkg = "math_trainer_core.plugins"
    package = importlib.import_module(plugins_pkg)

    result: Dict[str, LoadedPlugin] = {}

    for mod in pkgutil.iter_modules(package.__path__):
        package_name = f"{plugins_pkg}.{mod.name}"

        # Prefer a submodule named "plugin" inside each plugin package
        # e.g. math_trainer_core.plugins.addition.plugin
        try_module_names = [
            f"{package_name}.plugin",  # preferred
            package_name,              # fallback if plugin.py not used
        ]

        module = None
        for module_name in try_module_names:
            try:
                module = importlib.import_module(module_name)
                break
            except ModuleNotFoundError:
                continue

        if module is None:
            continue

        factory = getattr(module, "PLUGIN_FACTORY", None)
        if factory is None:
            continue

        info: PluginInfo = factory.PluginInfo()

        # Use plugin id as key
        result[info.id] = LoadedPlugin(
            info=info,
            factory=factory,
        )

    return result

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
          plugins/
            plugin_api.py
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
        if not mod.ispkg:
            continue
        package_name = f"{plugins_pkg}.{mod.name}"

        # Only load subpackages that provide a plugin.py module
        module_name = f"{package_name}.plugin"
        module = importlib.import_module(module_name)

        factory = getattr(module, "PLUGIN_FACTORY", None)
        if factory is None:
            raise RuntimeError(
                f"Plugin module '{module_name}' must define a 'PLUGIN_FACTORY' variable."
            )

        info: PluginInfo = factory.PluginInfo()

        # Use plugin id as key
        result[info.id] = LoadedPlugin(
            info=info,
            factory=factory,
        )

    return result

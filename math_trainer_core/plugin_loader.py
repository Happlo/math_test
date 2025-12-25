from __future__ import annotations
import importlib
import pkgutil
from typing import Dict

from .ports import IOperatorPlugin

def load_operator_plugins() -> Dict[str, IOperatorPlugin]:
    plugins_pkg = "math_trainer_core.plugins"
    package = importlib.import_module(plugins_pkg)

    result: Dict[str, IOperatorPlugin] = {}
    for mod in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{plugins_pkg}.{mod.name}")

        plugin = getattr(module, "PLUGIN", None)
        if plugin is None:
            continue

        plugin_id = plugin.plugin_id()
        result[plugin_id] = plugin

    return result

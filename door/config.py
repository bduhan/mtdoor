import inspect, importlib
from configparser import ConfigParser

from loguru import logger as log

from .base_command import BaseCommand


def find_commands(settings: ConfigParser) -> list[BaseCommand]:
    """
    for each section of the config file,
    import by name and look for a subclass of BaseCommand
    """
    results: BaseCommand = []
    for section in settings.sections():
        # skip global settings
        if section == "global":
            continue

        # skip disabled
        enabled = settings.getboolean(section, "enabled", fallback=True)
        if not enabled:
            continue

        try:
            module = importlib.import_module(section)
        except:  # (ModuleNotFoundError, AttributeError):
            log.exception(f"Failed to import plugin '{section}'")

        try:
            # find the subclass of BaseCommand
            plugin_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj is BaseCommand:
                    continue

                if issubclass(obj, BaseCommand) and obj is not BaseCommand:
                    plugin_class = obj
                    break

            assert plugin_class is not None
        except:
            log.exception(f"Failed to find subclass of BaseCommand in '{section}'")
            continue

        results.append(plugin_class)
    return results

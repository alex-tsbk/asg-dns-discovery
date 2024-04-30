import json
import os
from typing import Any


def get_debug_root_path():
    """Returns absolute path to debug folder of the project (parent folder of utils.py - /debug on local machine) relative to this file"""
    current_folder = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.abspath(os.path.join(current_folder, "debug")))


def combine_paths(*paths: str) -> str:
    """Combines multiple paths into one

    Args:
        *paths (str): Paths to combine

    Returns:
        str: Combined path
    """
    return os.path.join(*paths)


def load_event(cloud_provider: str, event_family: str, event_name: str) -> dict[str, Any]:
    """Loads the event handler for the specified cloud provider, event family, and event name.

    Args:
        cloud_provider (str): The cloud provider to debug the application for.
        event_family (str): The event family to debug the application for.
        event_name (str): The event name to debug the application for.

    Returns:
        Any: The event handler for the specified cloud provider, event family, and event name.
    """
    root_path = get_debug_root_path()
    event_path = combine_paths(root_path, "events", f"{cloud_provider}.{event_family}.{event_name}.json")
    if not os.path.exists(event_path):
        raise Exception(f"Unable to load event: {event_path}")
    with open(event_path, "r") as file:
        return json.load(file)


def wrap(cloud_provider: str, wrapper_name: str, message: dict[str, Any]) -> dict[str, Any]:
    """Wraps the message with the specified wrapper.

    Args:
        cloud_provider (str): The cloud provider to debug the application for.
        wrapper_name (str): The wrapper to wrap event with.
        message (dict[str, Any]): The message to wrap.

    Raises:
        Exception: If unable to load wrapper for cloud provider.

    Returns:
        dict[str, Any]: The wrapped message.
    """
    root_path = get_debug_root_path()
    event_path = combine_paths(root_path, "events", f"{cloud_provider}.{wrapper_name}.json")
    wrapper_text = None
    if not os.path.exists(event_path):
        return message
    with open(event_path, "r") as file:
        wrapper_text = file.read().replace("\n", "")
    if not wrapper_text:
        raise Exception(f"Unable to load wrapper for cloud provider: {event_path}")
    return json.loads(wrapper_text.replace("{%MESSAGE%}", json.dumps(message).replace('"', '\\"')))


def str_replace(source: dict[str, Any], token: str, new_value: str) -> dict[str, Any]:
    """Performs string replacement on the source dictionary.

    Args:
        source (dict[str, Any]): Source dictionary that contains the string to replace.
        token (str): Token to replace.
        new_value (str): New value to replace the token with.

    Returns:
        dict[str, Any]: Original source dictionary with the token replaced with the new value.
    """
    source_str = json.dumps(source)
    new_str = source_str.replace(token, new_value)
    return json.loads(new_str)

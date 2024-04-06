import os


def try_get_value[T: (str, bool, int)](key: str, default: T) -> T:
    """Return the value of an environment variable or a default value if it is not set.

    Returns:
        T: Value of the environment variable or the default value
    """
    # Infer the type of the default value if it provided, or fall back to str being the default type
    # for environment variables.
    result = os.environ.get(key, None)
    if result is not None:
        return type(default)(result)
    return default

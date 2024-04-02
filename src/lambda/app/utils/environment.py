import os


def get[T](key: str, default: T = None) -> T:
    """Return the value of an environment variable or a default value if it is not set.

    Returns:
        T: Value of the environment variable or the default value
    """
    result = os.environ.get(key, default)
    if result is not None and default is not None:
        # cast to the type of the default value
        return type(default)(result)
    return result

import unicodedata


def normalized(text: str) -> str:
    """Normalizes the text for comparison.

    Args:
        text (str): Text to normalize.

    Returns:
        str: Normalized text.

    Remarks:
        Read more on unicode normalization here: https://www.unicode.org/reports/tr15/#Normalization_Forms_Table
    """
    return unicodedata.normalize("NFKD", str(text).casefold())


def alike(*args: str) -> bool:
    """Performs case-insensitive and normalized comparison of strings.

    Returns:
        bool: True if all the strings are alike, False otherwise.
    """
    if len(args) < 2:
        raise ValueError("At least two strings are required for comparison.")

    return all(normalized(args[0]) == normalized(arg) for arg in args[1:])

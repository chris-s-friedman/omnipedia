from dateutil.parser import parse


def to_bool(x):
    """
    Convert obvious values to either True, False, or None.

    :param x: Thing to convert
    :type x: bool, str, or None
    :raises ValueError: Raised if not a bool, str, or None
    :raises ValueError: Raise if str and not resolvable to false or true or None
    :return: X as a True, False, or None
    :rtype: bool or None
    """
    if isinstance(x, bool):
        return x
    elif x is None:
        return x
    elif isinstance(x, str):
        cleanx = x.strip().lower()
        if not cleanx:
            return None
        elif cleanx == "false":
            return False
        elif cleanx == "true":
            return True
        else:
            raise ValueError(
                f'String must resolve to "false" or "true" or be None. Got: "{x}"'  # noqa
            )
    else:
        raise ValueError("Expecting a bool, str, or None")


def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: string to check for date
    :type string: str
    :param fuzzy: ignore unknown tokens in string if True
    :type fuzzy: bool
    :return: result of trying to convert the string to a date
    :rtype: bool
    """
    try:
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False

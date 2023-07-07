from dateutil.parser import parse


def is_date(date_str, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    if date_str is None:
        return False
    try:
        parse(date_str, fuzzy=fuzzy)
        return True

    except ValueError:
        return False


def is_date_after(start_date, end_date):
    return parse(end_date) >= parse(start_date)

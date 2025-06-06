from datetime import datetime


def is_valid_future_date(date_string: str) -> bool:
    """
    Checks if the provided date string is in YYYY-MM-DD format and
    represents a date that is today or in the future.
    """
    try:
        parsed_date = datetime.strptime(date_string, "%Y-%m-%d").date()
        current_date = datetime.now().date()
        return parsed_date >= current_date
    except ValueError:
        return False

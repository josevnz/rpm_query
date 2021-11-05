__version__ = "0.0.1"


def __is_valid_limit__(limit: str) -> int:
    try:
        int_limit = int(limit)
        if int_limit <= 0:
            raise ValueError(f"Invalid limit!: {limit}")
        return int_limit
    except ValueError:
        raise

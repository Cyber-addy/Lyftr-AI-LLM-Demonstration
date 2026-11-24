ALLOWED_FAILURE_STATUSES = {
    429,
    500,
    502,
    503,
}


def parse_failure_header(header_value):
    """
    Parse X-Simulate-Failure.

    Examples:
        key_1=429
        key_1=429,key_2=500
        *=429

    Returns:
        {
            "key_1": 429,
            "key_2": 500
        }
    """

    failures = {}

    if not header_value:
        return failures

    parts = header_value.split(",")

    for part in parts:

        part = part.strip()

        if not part:
            continue

        if "=" not in part:
            continue

        key_id, status = part.split(
            "=",
            1
        )

        key_id = key_id.strip()
        status = status.strip()

        try:
            status = int(status)
        except ValueError:
            continue

        if status not in ALLOWED_FAILURE_STATUSES:
            continue

        failures[key_id] = status

    return failures


def get_simulated_failure(
    key_id,
    failures
):
    """
    Return simulated status code for key_id.

    '*' applies to every key.
    """

    if "*" in failures:
        return failures["*"]

    return failures.get(key_id)
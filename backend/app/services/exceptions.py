class NotFoundError(Exception):
    """A requested resource doesn't exist, or doesn't belong to the
    requesting user — the two are treated identically on purpose. Returning
    404 (not 403) for "exists but isn't yours" avoids confirming to a
    caller that a given resource ID exists at all.
    """


class ValidationError(Exception):
    """A domain rule was violated (e.g. an account_id that doesn't belong
    to the user). Distinct from Pydantic's schema-level validation, which
    only checks shape/type, not cross-row ownership.
    """

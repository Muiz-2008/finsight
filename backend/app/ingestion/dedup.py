import hashlib
import uuid
from datetime import date as date_
from decimal import Decimal


def compute_import_hash(
    account_id: uuid.UUID,
    date: date_,
    description: str,
    amount: Decimal,
    transaction_type: str,
) -> str:
    """A stable fingerprint for "is this the same transaction?".

    Used both by manual transaction creation and CSV import so the two
    paths can't create duplicates of each other — re-importing a CSV that
    contains a transaction you already entered by hand is correctly
    treated as a duplicate. Normalizing the description (casefold + strip)
    means trivial formatting differences ("Uber " vs "uber") still hash
    the same.
    """
    normalized = "|".join(
        [
            str(account_id),
            date.isoformat(),
            description.strip().casefold(),
            f"{amount:.2f}",
            transaction_type,
        ]
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

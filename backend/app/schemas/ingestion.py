from pydantic import BaseModel


class ImportReportRead(BaseModel):
    total_rows: int
    imported: int
    duplicates: int
    invalid: int
    errors: list[str]

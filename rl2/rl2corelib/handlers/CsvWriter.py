from csv import DictWriter
import io
from typing import List


class CsvWriter:
    def __init__(self, columns):
        self._fp = io.StringIO()
        self._writer = DictWriter(self._fp, fieldnames=columns)
        self._writer.writeheader()

    def put_row(self, row: dict):
        self._writer.writerow(row)

    def put_rows(self, rows: List[dict]):
        self._writer.writerows(rows)

    def get_csv(self):
        csv = self._fp.getvalue()
        self._fp.close()
        return csv

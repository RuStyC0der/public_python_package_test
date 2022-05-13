from typing import List
import sqlalchemy
from sqlalchemy.orm import Session

__version__ = '0.2'


class RedshiftDB:
    def __init__(self, host, user, passwd, database, engine_params: dict = None):
        self.db_name = database

        engine_params = {} if engine_params is None else engine_params
        self.engine = sqlalchemy.create_engine(
            'redshift+psycopg2://%s:%s@%s:5439/%s' % (user, passwd, host, database),
            **engine_params
        )
        self.session = Session(bind=self.engine)

    def fetch(self, sql: str, **kwargs) -> list:
        result = self.engine.execute(sql, **kwargs)
        rows = result.fetchall()
        result.close()
        return rows

    def execute(self, sql: str, **kwargs) -> int:
        result = self.engine.execute(sql, **kwargs)
        self.session.commit()
        rowcount = result.rowcount
        result.close()
        return rowcount

    def bulk_save_records(self, orm_model, records: List[dict]):
        self.session.bulk_insert_mappings(orm_model, records)
        self.session.commit()
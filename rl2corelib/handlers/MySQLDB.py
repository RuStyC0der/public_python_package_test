import sqlalchemy
from sqlalchemy import exc
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.sql import text
import logging

__version__ = '0.5'


class MySQLDB:
    def __init__(self, host, user, passwd, database, engine_params: dict = None, port=3306):
        self.db_name = database

        # prepare engine params
        default_engine_params = {
            'pool_pre_ping': True
        }
        engine_params_merged = default_engine_params if engine_params is None else {**default_engine_params,
                                                                                    **engine_params}
        # init engine
        self.engine = sqlalchemy.create_engine(
            'mysql://%s:%s@%s:%s/%s' % (user, passwd, host, port, database),
            **engine_params_merged
        )

        self.session = Session(bind=self.engine)

    def _execute(self, sql: str, **kwargs):
        try:
            return self.engine.execute(text(sql), **kwargs)
        except exc.OperationalError as e:
            log = logging.getLogger()
            log.exception(e)

    def fetch(self, sql: str, **kwargs) -> Optional[list]:
        result = self._execute(sql, **kwargs)
        if result is None:
            return
        rows = result.fetchall()
        result.close()
        return rows

    def execute(self, sql: str, **kwargs) -> Optional[int]:
        result = self._execute(sql, **kwargs)
        if result is None:
            return
        self.session.commit()
        rowcount = result.rowcount
        result.close()
        return rowcount

    def bulk_save_records(self, orm_model, records: List[dict]):
        self.session.bulk_insert_mappings(orm_model, records)
        self.session.commit()

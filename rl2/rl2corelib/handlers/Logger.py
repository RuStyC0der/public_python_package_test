import logging
from traceback import StackSummary, walk_stack

__version__ = '0.1'


class Logger:
    _log_levels = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR
    }

    def __init__(self, log_name, log_level: str = None, log_format=None, log_file_name: str = None):
        self._date_fmt = '%y-%m-%d %H:%M:%S'
        self._logger = logging.getLogger(log_name)
        self._logger.setLevel(logging.DEBUG)  # reset default level
        logging_level = self._convert_str_to_log_level(log_level)

        # Console settings
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging_level)
        if not log_format:
            log_format = '%(asctime)s %(levelname)s: %(message)s'
        c_format = logging.Formatter(log_format, datefmt=self._date_fmt)
        c_handler.setFormatter(c_format)
        self._logger.addHandler(c_handler)
        # Add file handler
        if log_file_name:
            f_handler = logging.FileHandler(log_file_name, mode='w+')
            f_handler.setLevel(logging_level)
            f_handler.setFormatter(c_format)
            self._logger.addHandler(f_handler)

    def _convert_str_to_log_level(self, level: str):
        if level is None:
            return logging.INFO
        elif level.lower() in self._log_levels:
            return self._log_levels[level.lower()]
        else:
            raise ValueError("Incorrect log level '%s'. Expected: %s" % (level, ','.join(self._log_levels)))

    def get_logger_object(self):
        return self._logger

    def enabled_errors_file(self, log_file_path: str, log_format=None, ):
        f_handler = logging.FileHandler(log_file_path)
        f_handler.setLevel(logging.WARNING)

        if not log_format:
            log_format = '%(asctime)s %(name)s %(levelname)s: %(message)s -> %(myfilename)s at line %(mylineno)s'

        f_format = logging.Formatter(log_format, datefmt=self._date_fmt)

        f_handler.setFormatter(f_format)
        self._logger.addHandler(f_handler)

    def debug(self, msg):
        self._logger.debug(msg)

    def info(self, msg):
        self._logger.info(msg)

    def warning(self, msg):
        tr = StackSummary.extract(walk_stack(None))[-1]
        self._logger.warning(msg, extra=dict(myfilename=tr.filename, mylineno=tr.lineno))

    def error(self, msg, exc_info=False):
        tr = StackSummary.extract(walk_stack(None))[-1]
        self._logger.error(msg, exc_info=exc_info, extra=dict(myfilename=tr.filename, mylineno=tr.lineno))

    def exception(self, msg):
        self._logger.exception(msg)

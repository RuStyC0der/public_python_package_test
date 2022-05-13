import time

__version__ = '1.0'


class MicroTime:
    last_ts = 0

    def __init__(self, unit='millisec'):
        self._unit = unit
        self.last_ts = self.get_current_microsecs()

    @staticmethod
    def get_current_microsecs():
        return int(round(time.time() * 1000))

    def get_time(self):
        ts = self.get_current_microsecs()
        runtime = ts - self.last_ts
        self.last_ts = ts

        koof = 1
        if self._unit == 'sec':
            koof = 1000
        elif self._unit == 'min':
            koof = 1000 * 60

        return runtime/koof

    def pr_time(self, return_as_str=False):
        time_str = 'Time = %0.3f %s' % (self.get_time(), self._unit)
        if return_as_str:
            return time_str
        print(time_str)

from dataclasses import dataclass
import datetime as dt

import sys
sys.path.append('.')

from models.Auxiliary.csv_timeseries_reader import CsvTimeseriesReader

@dataclass
class Temperature:
    start_time   : dt.datetime 
    csv_path     : str

    temperature : float = 20.0 # [°C]

    def __post_init__(self):
        self._current_time = self.start_time

        self._data_reader = CsvTimeseriesReader(csv_path=self.csv_path)

    def step(self, seconds_since_start: int):
        self._update_current_time(seconds_since_start)
        self._update_temperature()

    def _update_temperature(self):
        self.temperature = self._data_reader.get_value_at_or_before(self._current_time)

    def _update_current_time(self, seconds_since_start: int):
        self._current_time = self.start_time + dt.timedelta(seconds=seconds_since_start)
from dataclasses import dataclass
import datetime as dt

import sys
sys.path.append('.')

from models.Auxiliary.csv_timeseries_reader import CsvTimeseriesReader

@dataclass
class PvSystem:
    start_time   : dt.datetime #     start time of the simulation
    peak_power   : float       # [W] maximum power output under perfect conditions
    csv_path     : str

    power_output : float       = 0.0 # [W] current power output

    def __post_init__(self):
        self._current_time = self.start_time

        self._data_reader = CsvTimeseriesReader(csv_path=self.csv_path)

    def step(self, seconds_since_start: int):
        self._update_current_time(seconds_since_start)
        self._update_power_output()

    def _update_power_output(self):
        normalized_power = self._data_reader.get_value_at_or_before(self._current_time)
        scaled_power = normalized_power * -self.peak_power
        self.power_output = scaled_power

    def _update_current_time(self, seconds_since_start: int):
        self._current_time = self.start_time + dt.timedelta(seconds=seconds_since_start)
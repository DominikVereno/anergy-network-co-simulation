import datetime as dt
import pandas as pd

class CsvTimeseriesReader:
    def __init__(self, csv_path: str):
        self._data = self._read_data(csv_path)

    def _read_data(self, csv_path):
        return pd.read_csv(csv_path, index_col=0, parse_dates=True).iloc[:, 0]
    
    def get_value_at_or_before(self, time: dt.datetime) -> float:
        valid_times = self._data.index[self._data.index <= time]

        if valid_times.empty:
            raise ValueError("Invalid time")
        else:
            closest_time = valid_times[-1]
            return self._data.loc[closest_time]
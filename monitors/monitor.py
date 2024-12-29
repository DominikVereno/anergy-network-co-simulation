import collections

from datetime import datetime

class Monitor:
    def __init__(self, start_time:datetime):
        self._data = collections.defaultdict(lambda: collections.defaultdict(dict))
        self._start_time = start_time

    def save_data(self, data, time):
        for attr, values in data.items():
            for src, value in values.items():
                self._data[src][attr][time] = value

    def output_data(self):
        raise NotImplementedError("Override output_data() function.")
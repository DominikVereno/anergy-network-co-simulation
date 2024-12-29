from datetime import timedelta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from monitors.monitor import Monitor


class GraphicalMonitor(Monitor):
    def output_data(self):
        if self._data:
            self._plot_diagrams()
    
    def _plot_diagrams(self):
        num_entities = len(self._data)
        fig, axes = plt.subplots(num_entities, 1, figsize=(10, 5 + num_entities))

        if num_entities == 1:
            axes = [axes]

        for i, (eid, data) in enumerate(sorted(self._data.items())):
            for attr, values in sorted(data.items()):
                time_values = values.keys()
                time_array = [self._start_time + timedelta(seconds=seconds) for seconds in time_values]
                value_array = np.array(list(values.values()))
                axes[i].plot(time_array, value_array, label=attr)
            axes[i].set_xlabel("time")
            axes[i].set_ylabel("value")
            axes[i].legend()
            axes[i].grid(True)
            axes[i].set_title(f"Recorded values for {eid}")

            axes[i].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

        fig.tight_layout()
        fig.show()
        plt.waitforbuttonpress()

import pandas as pd
from monitors.monitor import Monitor

class CsvMonitor(Monitor):
    def output_data(self):
        self._save_data_to_csv()
    
    def _save_data_to_csv(self, filename="simulation_results/output.csv"):
        # Prepare a dictionary to organize data for MultiIndex DataFrame
        data_for_csv = {}

        for eid, data in self._data.items():
            for attr, values in data.items():
                # Combine entity ID and attribute as a tuple for MultiIndex columns
                column_key = (eid, attr)
                for time, value in values.items():
                    if time not in data_for_csv:
                        data_for_csv[time] = {}
                    data_for_csv[time][column_key] = value

        # Convert the nested dictionary to a DataFrame
        df = pd.DataFrame.from_dict(data_for_csv, orient="index")

        # Convert time (seconds since start) to datetime
        start_time = self._start_time  # Reference start time (datetime object)
        df.index = pd.to_timedelta(df.index, unit="s") + start_time

        # Rename index to 'Time'
        df.index.name = "Time"

        # Sort index and columns for clean structure
        df.sort_index(inplace=True)
        df.columns = pd.MultiIndex.from_tuples(df.columns, names=["Entity", "Attribute"])

        # Save to CSV
        df.to_csv(filename, float_format="%.2f")
        print(f"Data saved to {filename}")

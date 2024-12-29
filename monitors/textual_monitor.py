from monitors.monitor import Monitor

class TextualMonitor(Monitor):
    def output_data(self):
        self._print_data_to_console()
    
    def _print_data_to_console(self):
        for eid, data in sorted(self._data.items()):
            print(f"- {eid}:")
            for attr, values in sorted(data.items()):
                print(f"  - {attr}: ")
                for time, value in values.items():
                    print(f"{time}: {value:.2f}", end="; ")
import mosaik_api

from monitors.textual_monitor   import TextualMonitor
from monitors.graphical_monitor import GraphicalMonitor
from monitors.csv_monitor       import CsvMonitor

META = {
    'type': 'time-based',
    'models': {
        'TextualMonitor': {
            'public': True,
            'any_inputs': True,
            'params': ['start_time'],
            'attrs': []
        },
        'GraphicalMonitor': {
            'public': True,
            'any_inputs': True,
            'params': ['start_time'],
            'attrs': []
        },
        'CsvMonitor': {
            'public': True,
            'any_inputs': True,
            'params': ['start_time'],
            'attrs': []
        }
    }
}


class MonitorSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.eid = ModuleNotFoundError
        self.monitor_classes = {
            "TextualMonitor": TextualMonitor,
            "GraphicalMonitor": GraphicalMonitor,
            "CsvMonitor"      : CsvMonitor
        }
        self.monitors = {}
    
    def init(self, sid, step_size=1, time_resolution=1., **sim_params):
        self.step_size = step_size
        return self.meta
    
    def create(self, num, model, **kwargs):
        if model not in self.monitor_classes:
            raise ValueError(f"Invalid model name given: {model}.")
        
        next_eid = len(self.monitors)
        created_monitors = []

        for idx in range(next_eid, next_eid+num):
            entity = self.monitor_classes[model](**kwargs)
            
            eid = f"{model}{idx}"
            self.monitors[eid] = entity
            created_monitors.append({'eid': eid, 'type': model})

        return created_monitors
    
    def step(self, time, inputs, max_advance):
        for target_eid, data in inputs.items():
            monitor = self.monitors[target_eid]
            monitor.save_data(data, time)
        return time + self.step_size

    def finalize(self):
        for monitor in self.monitors.values():
            monitor.output_data()

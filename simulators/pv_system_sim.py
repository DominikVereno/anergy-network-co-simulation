from simulators.basic_simulators.basic_simulator import BasicSimulator
from models.pv_system import PvSystem

META = {
    'type': 'time-based',
    'models': {
        'PvSystem': {
            'public': True,
            'params': [
                'start_time',  # datetime
                'peak_power',  # [W]
                'csv_path',    # string
            ],
            'attrs': [
                'power_output' # [°C]
            ]
        }
    }
}

class PvSystemSim(BasicSimulator):
    def __init__(self):
        super().__init__(META, PvSystem)

    def step(self, time, inputs, max_advance):
        for eid, pv_system in self.entities.items():
            elapsed_seconds = time
            pv_system.step(elapsed_seconds)

        return time + self.step_size
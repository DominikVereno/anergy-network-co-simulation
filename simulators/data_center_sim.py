import datetime as dt

from simulators.basic_simulators.basic_simulator import BasicSimulator
from models.data_center import DataCenter

META = {
    'type': 'time-based',
    'models': {
        'DataCenter': {
            'public': True,
            'params': [
                'max_computing_power',       # [W]
                'max_cooling_power',         # [W]
                'cooling_threshold',         # [°C]
                'max_temperature',           # [°C]
                'heat_generation_efficiency' # [-]
            ],
            'attrs': [
                "outdoor_temperature",     # [°C]
                "pv_input",                # [W]
                "electricity_consumption", # [W]
                "total_heat_output",       # [W]
                "excess_heat"              # [W]
            ]
        }
    }
}

class DataCenterSim(BasicSimulator):
    def __init__(self):
        super().__init__(META, DataCenter)

    def step(self, time, inputs, max_advance):
        for eid, data_center in self.entities.items():
            # Update input parameters
            self.set_params_if_in_inputs(data_center, eid, inputs)

            data_center.step()

        return time + self.step_size

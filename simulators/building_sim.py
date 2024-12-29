import datetime as dt

from simulators.basic_simulators.basic_simulator import BasicSimulator
from models.building import Building

META = {
    'type': 'time-based',
    'models': {
        'Building': {
            'public': True,
            'params': [
                'thermal_capacity_building', # [Wh/K]
                'thermal_capacity_tank',     # [Wh/K]
                'heat_loss_coefficient',     # [W/K]
                'tank_to_building_transfer', # [W/k]
                'setpoint_temperature',      # [°C]
            ],
            'attrs': [
                "outdoor_temperature",  # [°C]
                "heat_input",           # [W]
                "building_temperature", # [°C]
                "tank_temperature"      # [°C]
            ]
        }
    }
}

class BuildingSim(BasicSimulator):
    def __init__(self):
        super().__init__(META, Building)

    def step(self, time, inputs, max_advance):
        for eid, building in self.entities.items():
            self.set_params_if_in_inputs(building, eid, inputs)

            time_step = dt.timedelta(seconds=self.step_size) 
            building.step(time_step)

        return time + self.step_size

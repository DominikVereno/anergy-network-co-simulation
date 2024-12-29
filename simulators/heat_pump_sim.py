from simulators.basic_simulators.basic_simulator import BasicSimulator
from models.heat_pump import HeatPump

META = {
    'type': 'time-based',
    'models': {
        'HeatPump': {
            'public': True,
            'params': [
                'cop_nominal',           # [-]
                'heat_capacity_nominal', # [W]
                'temp_min',              # [°C]
                'temp_max'               # [°C]
            ],
            'attrs': [
                "tank_temperature",       # [°C]
                "supply_temperature",     # [°C]
                "massflow",               # [kg/s]
                "heat_output",            # [W]
                "heat_consumption",       # [W]
                "electricity_consumption" # [W]
            ]
        }
    }
}

class HeatPumpSim(BasicSimulator):
    def __init__(self):
        super().__init__(META, HeatPump)

    def step(self, time, inputs, max_advance):
        for eid, heat_pump in self.entities.items():
            self.set_params_if_in_inputs(heat_pump, eid, inputs)
            heat_pump.step()

        return time+self.step_size    
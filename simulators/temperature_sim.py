from simulators.basic_simulators.basic_simulator import BasicSimulator
from models.temperature import Temperature

META = {
    'type': 'time-based',
    'models': {
        'Temperature': {
            'public': True,
            'params': [
                'start_time', # datetime
                'csv_path',   # str
            ],
            'attrs': [
                'temperature' # [°C]
            ]
        }
    }
}

class TemperatureSim(BasicSimulator):
    def __init__(self):
        super().__init__(META, Temperature)

    def step(self, time, inputs, max_advance):
        for eid, temp_model in self.entities.items():
            elapsed_seconds = time
            temp_model.step(elapsed_seconds)

        return time + self.step_size
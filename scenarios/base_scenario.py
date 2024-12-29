from datetime import timedelta, datetime

import mosaik
import mosaik.util

SIM_CONFIG = {
    "DHNetworkSim": {
        "python": "simulators.dh_network_sim:DHNetworkSim"
    },
    "PyPower": {
        "python": "simulators.pypower_sim:PyPowerSim"
    },
    'HeatPumpSim': {
        "python": "simulators.heat_pump_sim:HeatPumpSim"
    },
    'BuildingSim': {
        "python": "simulators.building_sim:BuildingSim"
    },
    'DataCenterSim': {
        "python": "simulators.data_center_sim:DataCenterSim"
    },
    'TemperatureSim': {
        "python": "simulators.temperature_sim:TemperatureSim"
    },
    'PvSystemSim': {
        "python": "simulators.pv_system_sim:PvSystemSim"
    },
    'MonitorSim': {
        "python": "simulators.monitor_sim:MonitorSim"
    },
}

class BasicScenario:
    def __init__(self, start_time: datetime, duration: timedelta, step_size: timedelta, electricity_grid_file: str, dh_network_file: str):
        self._start_time = start_time
        self._duration_in_seconds  = int(duration .total_seconds())
        self._step_size_in_seconds = int(step_size.total_seconds())

        self._electricity_grid_file = electricity_grid_file
        self._dh_network_file       = dh_network_file

        self.world = mosaik.World(SIM_CONFIG)

        self._start_simulators()
        self._instantiate_entities()
        self._connect_entities()

    def run(self):
        self.world.run(until=self._duration_in_seconds)

    def _start_simulators(self):
        self.dh_network_sim   = self.world.start("DHNetworkSim"  , step_size=self._step_size_in_seconds)
        self.power_grid_sim   = self.world.start("PyPower"       , step_size=self._step_size_in_seconds)
        self.heat_pump_sim    = self.world.start("HeatPumpSim"   , step_size=self._step_size_in_seconds)
        self.building_sim     = self.world.start("BuildingSim"   , step_size=self._step_size_in_seconds)
        self.data_center_sim  = self.world.start("DataCenterSim" , step_size=self._step_size_in_seconds)
        self.temperature_sim  = self.world.start("TemperatureSim", step_size=self._step_size_in_seconds)
        self.pv_sim           = self.world.start("PvSystemSim"   , step_size=self._step_size_in_seconds)

        self.monitor_sim      = self.world.start("MonitorSim"    , step_size=self._step_size_in_seconds)

    def _instantiate_entities(self):
        raise NotImplementedError(
            f"The _instantiate_entities() function must be implemented by the subclass of {self.__class__.__name__}"
        )

    def _connect_entities(self):
        raise NotImplementedError(
            f"The _connect_entities() function must be implemented by the subclass of {self.__class__.__name__}"
        )

    def _connect(self, *args, **kwargs):
        self.world.connect(*args, **kwargs)


class Grid():
    def __init__(self, grid_elements) -> None:
      self.grid_elements = grid_elements

    def __getitem__(self, key):
       return next(element for element in self.grid_elements if key in element.eid)

if __name__ == "__main__":
    print("This file is not meant to be executed directly. Run \"simulation.py\" instead.")
from datetime import timedelta, datetime

from scenarios.base_scenario import BasicScenario, Grid

class CompleteScenario(BasicScenario):
    def __init__(self, start_time: datetime, duration: timedelta, step_size: timedelta, electricity_grid_file: str, dh_network_file: str):
        super().__init__(
            start_time           =start_time,
            duration             =duration,
            step_size            =step_size,
            electricity_grid_file=electricity_grid_file,
            dh_network_file      =dh_network_file
        )

    def _instantiate_entities(self):
        self._instantiate_dh_network()
        self._instantiate_electricity_grid()
        self._instantiate_heat_pumps()
        self._instantiate_buildings()
        self._instantiate_data_centers()
        self._instantiate_pv_systems()
        self._instantiate_temperature()
        self._instantiate_monitors()

    def _instantiate_dh_network(self):
        self.dh_network = self.dh_network_sim.DHNetwork(
            network_definition_path = self._dh_network_file,
            num_channels = 3
        )
        self.heat_exchanger_ports = self.dh_network.children

    def _instantiate_electricity_grid(self):
        self.power_grid = Grid(self.power_grid_sim.Grid(gridfile=self._electricity_grid_file).children)

    def _instantiate_heat_pumps(self):
        self.heat_pump_1 = self.heat_pump_sim.HeatPump(
            cop_nominal          = 4.0, 
            heat_capacity_nominal=40.0e3,
            temp_min             =50.0,
            temp_max             =60.0
            )

        self.heat_pump_2 = self.heat_pump_sim.HeatPump(
            cop_nominal          = 4.2, 
            heat_capacity_nominal=80.0e3,
            temp_min             =40.0,
            temp_max             =50.0
            )

    def _instantiate_buildings(self):
        self.building_1 = self.building_sim.Building(
            thermal_capacity_building= 50.0e3, 
            heat_loss_coefficient    =  1.8e3, 
            setpoint_temperature     = 20.0, 
            thermal_capacity_tank    =  3.5e3, 
            tank_to_building_transfer=  8.0e3
            )
        
        self.building_2 = self.building_sim.Building(
            thermal_capacity_building=200.0e3, 
            heat_loss_coefficient    =  3.5e3, 
            setpoint_temperature     = 19.0, 
            thermal_capacity_tank    = 45.0e3, 
            tank_to_building_transfer=  8.0e3
            )

    def _instantiate_data_centers(self):
        self.data_center = self.data_center_sim.DataCenter(
            max_computing_power=50.0e3, 
            max_cooling_power  =50.0e3, 
            cooling_threshold  =10.0  , 
            max_temperature    =40.0  )

    def _instantiate_pv_systems(self):
        self.pv_system = self.pv_sim.PvSystem(start_time=self._start_time, peak_power=120e3, csv_path="data/pv_normalized.csv")

    def _instantiate_temperature(self):
        self.temperature = self.temperature_sim.Temperature(start_time=self._start_time, csv_path="data/temperature_munich_airport.csv")

    def _instantiate_monitors(self):
        self.textual_monitor   = self.monitor_sim.TextualMonitor  (start_time=self._start_time)
        self.graphical_monitor = self.monitor_sim.GraphicalMonitor(start_time=self._start_time)
        self.csv_monitor       = self.monitor_sim.CsvMonitor      (start_time=self._start_time)

    def _connect_entities(self):
        self._connect(self.temperature, self.building_1 , ("temperature", "outdoor_temperature"))
        self._connect(self.temperature, self.building_2 , ("temperature", "outdoor_temperature"))
        self._connect(self.temperature, self.data_center, ("temperature", "outdoor_temperature"))

        self._connect(self.pv_system, self.data_center, ("power_output", "pv_input"))

        self._connect(self.data_center, self.heat_exchanger_ports[0       ], ("total_heat_output"      , "heat_consumption"))
        self._connect(self.data_center, self.power_grid          ["bus_a2"], ("electricity_consumption", "P"               ))

        self._connect(self.building_1, self.heat_pump_1, "tank_temperature")
        self._connect(self.building_2, self.heat_pump_2, "tank_temperature")
        self._connect(self.heat_pump_1, self.building_1, ("heat_output", "heat_input"), time_shifted=True, initial_data={"heat_output": 0.0})
        self._connect(self.heat_pump_2, self.building_2, ("heat_output", "heat_input"), time_shifted=True, initial_data={"heat_output": 0.0})

        self._connect(self.heat_exchanger_ports[0], self.heat_pump_1, "supply_temperature")
        self._connect(self.heat_exchanger_ports[2], self.heat_pump_2, "supply_temperature")
        self._connect(self.heat_exchanger_ports[0], self.heat_pump_1, "massflow")
        self._connect(self.heat_exchanger_ports[2], self.heat_pump_2, "massflow")
        self._connect(self.heat_pump_1, self.heat_exchanger_ports[0], "heat_consumption", time_shifted=True, initial_data={"heat_consumption": 0.0})
        self._connect(self.heat_pump_2, self.heat_exchanger_ports[2], "heat_consumption", time_shifted=True, initial_data={"heat_consumption": 0.0})
        self._connect(self.heat_pump_1, self.power_grid["bus_a1"], ("electricity_consumption", "P"))
        self._connect(self.heat_pump_2, self.power_grid["bus_c" ], ("electricity_consumption", "P"))


        self._connect_entities_to_monitors()

    def _connect_entities_to_monitors(self):
        self._connect(self.temperature         , self.csv_monitor, "temperature")
        self._connect(self.dh_network          , self.csv_monitor, "grid_return_temperature")
        self._connect(self.power_grid["tr_pri"], self.csv_monitor, "P")
        self._connect(self.pv_system           , self.csv_monitor, "power_output")
        self._connect(self.data_center         , self.csv_monitor, "total_heat_output", "electricity_consumption", "excess_heat")
        self._connect(self.heat_pump_1         , self.csv_monitor, "heat_consumption", "electricity_consumption")
        self._connect(self.heat_pump_2         , self.csv_monitor, "heat_consumption", "electricity_consumption")
        self._connect(self.building_1         , self.graphical_monitor, "tank_temperature", "building_temperature")
        self._connect(self.building_2         , self.graphical_monitor, "tank_temperature", "building_temperature")
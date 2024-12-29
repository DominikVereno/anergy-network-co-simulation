from dataclasses import dataclass

@dataclass
class DataCenter:
    # Parameters
    max_computing_power       : float        # [W]  Maximum computing power demand
    max_cooling_power         : float        # [W]  Maximum cooling power demand
    cooling_threshold         : float        # [°C] Threshold temperature below which cooling starts
    max_temperature           : float        # [°C] Maximum outdoor temperature for which cooling is possible
    heat_generation_efficiency: float =  0.9 # [-]  Efficiency for converting excess PV to heat       

    # Inputs
    outdoor_temperature       : float = 20.0  # [°C] Outdoor temperature
    pv_input                  : float =  0.0  # [W]  Current photovoltaic power (negative = production)

    # Outputs
    electricity_consumption   : float = 0.0   # [W] Total grid electricity consumption
    waste_heat                : float = 0.0   # [W] Waste heat generated
    excess_heat               : float = 0.0   # [W] Heat generated from excess PV
    total_power_demand        : float = 0.0   # [W] Total demand for both computing and cooling

    def __post_init__(self):
        self._cooling_rate = self.max_cooling_power / (self.max_temperature - self.cooling_threshold)

    def step(self):
        self.total_power_demand      = self._compute_total_power_demand()
        self.electricity_consumption = self._compute_electricity_consumption()
        self.waste_heat              = self._compute_waste_heat()
        self.excess_heat             = self._compute_excess_heat()

    @property
    def total_heat_output(self) -> float:
        return self.waste_heat + self.excess_heat

    def _compute_cooling_demand(self):
        if self.outdoor_temperature < self.cooling_threshold:
            cooling_demand = 0.0
        else:
            temperature_difference = self.outdoor_temperature - self.cooling_threshold
            cooling_demand = self._cooling_rate * temperature_difference
            cooling_demand = min(cooling_demand, self.max_cooling_power)
            cooling_demand = max(cooling_demand, 0) 

        return cooling_demand

    def _compute_total_power_demand(self):
        return self.max_computing_power + self._compute_cooling_demand()

    def _compute_electricity_consumption(self):
        net_power_demand = self.total_power_demand + self.pv_input
        return max(0, net_power_demand)

    def _compute_waste_heat(self):
        return -self.total_power_demand * 0.5

    def _compute_excess_heat(self):
        excess_pv = max(0, -self.pv_input - self.total_power_demand)
        return -excess_pv * self.heat_generation_efficiency

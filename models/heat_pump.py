from dataclasses import dataclass

HEAT_CAPACITY_WATER = 4.18e3  # Specific heat capacity of water (J/kg°C)

@dataclass
class HeatPump:
    # Parameters
    cop_nominal          : float # [ ] Nominal Coefficient of Performance
    heat_capacity_nominal: float # [W] Nominal heating capacity in watts
    temp_min             : float # [°C] Minimum tank temperature to start modulating
    temp_max             : float # [°C] Maximum tank temperature to stop heating

    # Inputs
    supply_temperature: float = 25.0 # [°C]   Temperature from the anergy network
    massflow          : float =  7.5 # [kg/s] Mass flow from the anergy network
    tank_temperature  : float = 20.0 # [°C]   Current tank temperature of building

    # Outputs
    heat_output            : float = 0.0 # [W] Heat delivered to the tank
    heat_consumption       : float = 0.0 # [W] Heat taken from the thermal network
    electricity_consumption: float = 0.0 # [W] Electricity consumed by the heat pump

    def step(self):
        modulation_factor = self._compute_modulation_factor_based_on_tank_temperature()

        self._operate(modulation_factor)

    def _operate(self, modulation_factor: float):
        cop = self._compute_cop()
        
        self.heat_output = self._compute_heat_output(modulation_factor)

        self.electricity_consumption = self.heat_output / cop

        self.heat_consumption = self.heat_output - self.electricity_consumption

    def _compute_target_temperature(self):
        return self.temp_max + 10

    def _compute_cop(self):
        target_output_temperature = self._compute_target_temperature()

        temperature_lift = target_output_temperature - self.supply_temperature

        return max(self.cop_nominal - 0.05 * temperature_lift, 1.0) 

    def _compute_modulation_factor_based_on_tank_temperature(self):
        if self.tank_temperature < self.temp_min:
            return 1.0 
        elif self.tank_temperature > self.temp_max:
            return 0.0 
        else:
            return (self.temp_max - self.tank_temperature) / (self.temp_max - self.temp_min)
    
    def _maximum_heat_transfer_from_heat_network(self):
        #reference_temperature = self.tank_temperature
        reference_temperature = self.temp_max
        return self.massflow * HEAT_CAPACITY_WATER * (reference_temperature - self.supply_temperature)
    
    def _compute_heat_output(self, modulation_factor: float):
        max_heat_transfer = self._maximum_heat_transfer_from_heat_network()
        return min(self.heat_capacity_nominal * modulation_factor, max_heat_transfer)

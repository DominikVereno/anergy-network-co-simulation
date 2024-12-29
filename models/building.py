from dataclasses import dataclass
import datetime as dt

@dataclass
class Building:
    # Parameters
    thermal_capacity_building: float # [Wh/K] total heat capacity of the building
    thermal_capacity_tank    : float # [Wh/K] heat capactiy of the heat tank
    heat_loss_coefficient    : float # [W/K]  heat transfer between building and outside
    tank_to_building_transfer: float # [W/K]  maximum heat transfer between tank and building
    setpoint_temperature     : float # [°C]   desired indoor temperature

    # Inputs
    outdoor_temperature: float = 10 # [°C]
    heat_input         : float =  0 # [W] External heat input to the tank

    # State variables and outputs
    building_temperature: float = 15 # [°C] Interior building temperature
    tank_temperature    : float = 45 # [°C] Internal tank temperature 
    
    def __post_init__(self):
        self.building_temperature = self.setpoint_temperature

    def step(self, time_step: dt.timedelta):
        time_step_hours = time_step.total_seconds() / 3600

        heat_loss_to_outside = self._compute_heat_loss_to_outside()

        actual_heat_transfer_to_building = self._compute_actual_heat_transfer_to_building(heat_loss_to_outside)

        self._update_building_temperature(time_step_hours, actual_heat_transfer_to_building, heat_loss_to_outside)
        self._update_tank_temperature    (time_step_hours, actual_heat_transfer_to_building)

    def _compute_heat_loss_to_outside(self):
        temperature_difference = self.building_temperature - self.outdoor_temperature
        return self.heat_loss_coefficient * temperature_difference

    def _compute_actual_heat_transfer_to_building(self, heat_loss_to_outside: float):
        required_heat_to_maintain_temp = heat_loss_to_outside
        temperature_dependent_correction = 500 * (self.setpoint_temperature - self.building_temperature)

        required_heat_to_reach_setpoint = required_heat_to_maintain_temp + temperature_dependent_correction

        actual_heat_transfer_to_building = min(
            self.tank_to_building_transfer * (self.tank_temperature - self.building_temperature),
            required_heat_to_reach_setpoint
        )

        return max(actual_heat_transfer_to_building, 0.0) # no cooling by tank 
    
    def _update_building_temperature(self, time_step_hours, actual_heat_transfer_to_building, heat_loss_to_outside):
        heat_power_difference = actual_heat_transfer_to_building - heat_loss_to_outside
        temperature_change = heat_power_difference * time_step_hours / self.thermal_capacity_building

        self.building_temperature += temperature_change

    def _update_tank_temperature(self, time_step_hours, actual_heat_transfer_to_building):
        heat_power_difference = self.heat_input - actual_heat_transfer_to_building
        temperature_change = heat_power_difference * time_step_hours / self.thermal_capacity_tank

        self.tank_temperature += temperature_change
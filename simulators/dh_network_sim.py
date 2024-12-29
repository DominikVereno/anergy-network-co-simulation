from simulators.basic_simulators.basic_multicontroller_simulator import BasicMulticontrollerSimulator

from models.dh_network import DHNetwork

META = {
    'type': 'hybrid',
    'models': {
        'DHNetwork': {
            'public': True,
            'params': [
                "network_definition_path",
                "num_channels"
            ],
            'attrs': [
                "grid_return_temperature"   # Return temperature of ext. grid  [degC]
            ]
        },
        'HeatExchanger': {
            'public': True, 
            'params': [],
            'attrs': [
                # INPUT
                "heat_consumption",   # Heat consumption of consumer   [W]
                # OUTPUT
                "supply_temperature", # Supply temperature at consumer [degC]
                "massflow"            # Massflow at consumer           [kg/s]
            ],
            'persistent': ["heat_consumption", "supply_temperature", "massflow"]
        }
    }
}

class DHNetworkSim(BasicMulticontrollerSimulator):
    def __init__(self):
        super().__init__(META, DHNetwork)

    def step(self, time, inputs, max_advance):
        self.time = time

        inputs_by_controller = self._sort_inputs_by_controller(inputs)

        for controller_id, attributes in inputs_by_controller.items():
            controller = self.controllers[controller_id]

            for attribute, values in attributes.items():
                for consumer, value in values.items():
                    setattr(controller.controlled_systems[consumer], attribute, value)

            controller.step(time)

        return time+self.step_size
import sys
import json
from dataclasses import dataclass, field
import pandapipes as pp
import pandapipes.control as pp_control

if not sys.warnoptions:
    import warnings

ABSOLUTE_ZERO = -273.15 # [degC]

def celsius_to_kelvin(degree_celsius: float):
    return degree_celsius - ABSOLUTE_ZERO

def kelvin_to_celsius(degree_kelvin: float):
    return degree_kelvin + ABSOLUTE_ZERO

@dataclass
class Consumer:
    heat_consumption  : float # [W]
    supply_temperature: float # [degC]
    massflow          : float # [kg/s]

@dataclass
class DHNetwork:
    '''
    Model of the district-heating network building on pandapipes model. 
    '''
    # Variables
    grid_massflow: float = 5.0  # [kg/s] Mass flow injected by grid

    controlled_systems: dict = field(init=False) # Inputs and outputs for each consumer 

    grid_return_temperature: float = 25 # [degC]

    # Config
    network_definition_path: str = "" # path to JSON-based network defintion

    def step(self, time):
        self.sim_time = time
        
        self._update_inputs()
        self._run_computations()
        self._update_outputs()

    def __post_init__(self):
        self._load_network_data()
        self._create_network()

    def _load_network_data(self):
        with open(self.network_definition_path, "r") as file:
            self._network_data = json.load(file)

    def initialize_controlled_systems(self, consumers):
        self.controlled_systems = {}

        hex_names = [name for name, *_ in self._network_data["heat_exchangers"]]

        self.hex_to_consumer = dict(zip(hex_names, consumers))
        self.consumer_to_hex = dict(zip(consumers, hex_names))

        default_supply_temperature = self._network_data["external_grid"]["supply_temperature"]
        default_massflow = self.grid_massflow

        for hex_name, _, _, init_consumption in self._network_data["heat_exchangers"]:
            consumer = self.hex_to_consumer[hex_name]
            self.controlled_systems[consumer] = Consumer(
                heat_consumption=init_consumption,
                supply_temperature=default_supply_temperature,
                massflow=default_massflow
            )

    def _update_inputs(self):
        self._update_consumer_heat_consumption()

    def _update_consumer_heat_consumption(self):
        for consumer_name, consumer in self.controlled_systems.items():
            hex_name = self.consumer_to_hex[consumer_name]
            heat_consumption = consumer.heat_consumption

            self.network.heat_exchanger.loc[
                self.network.heat_exchanger['name'] == hex_name,
                "qext_w"
            ] = heat_consumption

    def _run_computations(self):
        self._run_hydraulic_control()
        self._run_static_pipeflow()

    def _run_hydraulic_control(self):
        try:
            pp_control.run_control(self.network, max_iter=100)
        except:
            warnings.warn("Controller not converged: maximum number of iterations per controller is reached", UserWarning, stacklevel=2)

    def _run_static_pipeflow(self):
        pp.pipeflow(
            self.network,
            transient=False,
            mode="all",
            max_iter=100,
            run_control=True,
            heat_transfer=True
        )

    def _update_outputs(self):
        self._update_heat_exchanger_temperature_and_massflow()
        self._update_grid_return_temperature()

    def _update_heat_exchanger_temperature_and_massflow(self):
        for consumer_name, consumer in self.controlled_systems.items():
            hex_name = self.consumer_to_hex[consumer_name]
            from_junction = self._get_from_junction_for_heat_exchanger(hex_name)

            consumer.supply_temperature = self._get_temperature_at_junction(from_junction)
            consumer.massflow = self._get_massflow_into_heat_exchanger(hex_name)

    def _get_from_junction_for_heat_exchanger(self, hex_name):
        return next(
            heat_exchanger[1] for heat_exchanger in self._network_data["heat_exchangers"] if heat_exchanger[0] == hex_name
            )

    def _update_grid_return_temperature(self):
        self.grid_return_temperature = self._get_temperature_at_junction(
            self._network_data["external_grid"]["sink_node"]
        )

    def _get_temperature_at_junction(self, junction_name):
        '''
        Retrieve computed temperature at specified junction in [degC]
        '''
        junctions = self.network.junction['name'].tolist()
        temperature_k = self.network.res_junction.at[junctions.index(junction_name), 't_k']

        return kelvin_to_celsius(temperature_k)
    
    def _get_massflow_into_heat_exchanger(self, hex_name):
        hex_names = self.network.heat_exchanger['name'].tolist()

        return self.network.res_heat_exchanger.at[hex_names.index(hex_name), 'mdot_from_kg_per_s']

    def _create_network(self):
        self._initialize_empty_network()

        self._set_water_as_fluid()

        self._create_junctions()
        self._create_external_grid()
        self._create_pipes()
        self._create_valves()
        self._create_heat_exchangers()

    def _initialize_empty_network(self):
        self.network = pp.create_empty_network("dh_network", add_stdtypes=False)

    def _set_water_as_fluid(self):
        pp.create_fluid_from_lib(self.network, 'water', overwrite=True)

    def _create_junctions(self):
        for name, geodata in self._network_data["junctions"]:
            geodata_as_tuple = tuple(geodata)
            self._create_junction(name, geodata_as_tuple)

    def _create_external_grid(self):
        external_grid = self._network_data["external_grid"]
        supply_temperature_kelvin = celsius_to_kelvin(external_grid["supply_temperature"])

        pp.create_ext_grid(
            self.network, 
            junction=self._get_junction_index(external_grid["junction"]),
            p_bar   =external_grid["pressure"],
            t_k     =supply_temperature_kelvin, 
            name    ="ext_grid",
            type    ="pt"
            )
        
        pp.create_sink(
            self.network,
            junction     =self._get_junction_index(external_grid["sink_node"]),
            mdot_kg_per_s=self.grid_massflow,
            name         ="sink_grid"
            )
        
        pp.create_source(
            self.network,
            junction     =self._get_junction_index(external_grid["sink_node"]),
            mdot_kg_per_s=0,
            name         ="source_grid"
            )

    def _create_pipes(self):
        for pipe_data in self._network_data["pipes"]:
            self._create_pipe(
                name          = pipe_data[0],
                from_junction = pipe_data[1],
                to_junction   = pipe_data[2],
                length_km     = pipe_data[3],
                sections      = pipe_data[4]
            )
    
    def _create_valves(self):
        for valve_data in self._network_data["valves"]:
            self._create_valve(
                name            =valve_data[0],
                from_junction   =valve_data[1],
                to_junction     =valve_data[2],
                loss_coefficient=valve_data[3]
            )

    def _create_heat_exchangers(self):
        for hex_data in self._network_data["heat_exchangers"]:
            self._create_heat_exchanger(
                name         =hex_data[0],
                from_junction=hex_data[1],
                to_junction  =hex_data[2],
                qext         =hex_data[3]
            )

    def _create_junction(self, name, geodata):
        external_grid_data = self._network_data["external_grid"]
        
        supply_temperature_C = external_grid_data["supply_temperature"]
        temperature_K = celsius_to_kelvin(supply_temperature_C) 

        pp.create_junction(
            self.network,
            pn_bar  =external_grid_data["pressure"],
            tfluid_k=temperature_K,
            name    =name, 
            geodata =geodata
        )

    def _create_pipe(self, name, from_junction, to_junction, length_km, sections, diameter_m=0.1, k_mm=0.01, alpha_w_per_m2k=1.5, text_k=None):
        if not text_k:
            ambient_temperature_C = self._network_data["external_grid"]["ambient_temperature"]
            text_k = celsius_to_kelvin(ambient_temperature_C)

        pp.create_pipe_from_parameters(
            self.network,
            from_junction   = self._get_junction_index(from_junction),
            to_junction     = self._get_junction_index(to_junction),
            length_km       = length_km,
            diameter_m      = diameter_m,
            k_mm            = k_mm,
            sections        = sections,
            alpha_w_per_m2k = alpha_w_per_m2k,
            text_k          = text_k,
            name            = name
        )

    def _create_valve(self, name, from_junction, to_junction, diameter_m=0.1, loss_coefficient=0, opened=True):
        pp.create_valve(
            self.network, 
            from_junction   =self._get_junction_index(from_junction),
            to_junction     =self._get_junction_index(to_junction),
            diameter_m      =diameter_m,
            loss_coefficient=loss_coefficient,
            opened          =opened,
            name            =name
        )
    
    def _create_heat_exchanger(self, name, from_junction, to_junction, qext, diameter_m=0.1):

        pp.create_heat_exchanger(
            self.network, 
            from_junction=self._get_junction_index(from_junction),
            to_junction  =self._get_junction_index(to_junction),
            diameter_m   =diameter_m,
            qext_w       =qext,
            name         =name
        )

    def _get_junction_index(self, junction_name):
        return self.network.junction[
            self.network.junction["name"] == junction_name
            ].index[0]
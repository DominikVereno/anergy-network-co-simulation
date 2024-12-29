import mosaik_api
import asyncio

from concurrent.futures import ThreadPoolExecutor


def reverse_dictionary_lookup(dictionary, value_to_find):
    key = next(key for key, value in dictionary.items() if value == value_to_find)
    return key


def run_async_in_thread(coroutine):
    with ThreadPoolExecutor() as executor:
        loop = asyncio.new_event_loop()
        future = executor.submit(loop.run_until_complete, coroutine)
        result = future.result()
        loop.close()
        return result


class BasicMulticontrollerSimulator(mosaik_api.Simulator):
    def __init__(self, meta, controller_class):
        super().__init__(meta)

        self.simulator_id = None
        self.time = 0

        self.controller_class = controller_class

        self._initialize_model_names()
        self._set_eid_fixes()

        self.controllers = {}
        self.controller_channels = {}
        self.channel_controllers = {}
        self.systems_channels_dict = {}

    def init(self, sid, step_size=1, time_resolution=1.0, **kwargs):
        if float(time_resolution) != 1.0:
            raise ValueError(
                f"{self.controller_model} simulator only supports time_resolution=1.0, but {time_resolution} was set."
            )
        
        self.simulator_id = sid
        self.step_size=step_size

        return self.meta

    def create(self, num, model, **model_params):
        self._validate_model_name_to_create(model)

        next_controller_index = len(self.controllers)
        created_entities = []

        for controller_index in range(next_controller_index, next_controller_index + num):
            controller_entity = self._create_controller_with_channels(
                controller_index, **model_params)

            created_entities.append(controller_entity)

        return created_entities

    def setup_done(self):
        self._create_system_to_channel_map()
        self._models_initialize_controlled_systems()

    def step(self, time, inputs, max_advance):
        raise NotImplementedError(
            f"The step() function must be implemented by the subclass of {self.__class__.__name__}"
        )

    def get_data(self, outputs):
        data = {'time': self.time}

        for entity_id, attributes in outputs.items():
            if self._is_controller(entity_id):
                self._get_data_from_controller(attributes, data, entity_id)

            elif self._is_channel(entity_id):
                self._get_data_from_channel(attributes, data, entity_id)

            else:
                raise RuntimeError(
                    f"The entity ID {entity_id} belongs to neither the controller ({self.controller_model}) "
                    f"nor the channel ({self.channel_model})"
                )

        return data

    def _validate_model_name_to_create(self, model_name):
        if model_name == self.channel_model:
            raise RuntimeError(
                f"Cannot instantiate {self.channel_model} directly. Create {self.controller_model} instead.")
        elif model_name != self.controller_model:
            raise ValueError(f"Invalid model name.")

    def _create_controller_with_channels(self, controller_index, **model_params):
        controller_id = self._make_controller_eid(controller_index)
        num_channels = model_params.pop('num_channels')
        channel_ids = self._create_channels_for_controller(num_channels, controller_id)

        self.controllers[controller_id] = self.controller_class(**model_params)

        return self._make_controller_entity(channel_ids, controller_id)

    def _initialize_model_names(self):
        models = self._extract_model_list_from_meta()

        self._validate_model_list_length(models)

        self.controller_model = models[0]
        self.channel_model = models[1]

    def _extract_model_list_from_meta(self):
        return list(self.meta['models'].keys())

    def _validate_model_list_length(self, models):
        if len(models) != 2:
            raise ValueError(
                f"{self.__class__.__name__} only works for simulators with exactly two models. "
                f"{len(models)} were specified."
            )

    def _set_eid_fixes(self):
        self.controller_eid_prefix = f"{self.controller_model}_"
        self.channel_eid_infix = f"_{self.channel_model}_"

    # -------------------------------------------------------------------------------------------------------------#
    def _is_controller(self, entity_id):
        return entity_id in self.controllers.keys()

    def _is_channel(self, entity_id):
        return entity_id in self.channel_controllers.keys()

    def _get_data_from_controller(self, attributes, data, controller_id):
        controller = self.controllers[controller_id]

        data[controller_id] = {}

        for attribute in attributes:
            if self._is_valid_controller_attribute(attribute):
                attribute_value = getattr(controller, attribute)
                if attribute_value is not None:
                    data[controller_id][attribute] = attribute_value

            else:
                raise ValueError(f"Unknown output attribute: {attribute}")

    def _is_valid_controller_attribute(self, attribute_name):
        return attribute_name in self.meta['models'][self.controller_model]['attrs']

    def _get_data_from_channel(self, attributes, data, channel_id):
        controller_id = self.channel_controllers[channel_id]
        controller = self.controllers[controller_id]

        data[channel_id] = {}

        for attribute in attributes:
            if self._is_valid_channel_attribute(attribute):
                system_id = reverse_dictionary_lookup(self.systems_channels_dict, channel_id)
                attribute_value = getattr(controller.controlled_systems[system_id], attribute)
                if attribute_value is not None:
                    data[channel_id][attribute] = attribute_value
            else:
                raise ValueError(f"Unknown output attribute: {attribute}")

    def _is_valid_channel_attribute(self, attribute_name):
        return attribute_name in self.meta['models'][self.channel_model]['attrs']

    def _make_controller_entity(self, channel_ids, controller_id):
        channels = []
        for channel_id in channel_ids:
            channels.append({'eid': channel_id, 'type': self.channel_model})

        entity = {
            'eid': controller_id,
            'type': self.controller_model,
            'children': channels
        }

        return entity

    @staticmethod
    def _map_channel_ids_to_thresholds(channel_ids, channel_thresholds):
        return {channel_id: {'threshold': threshold} for channel_id, threshold in
                zip(channel_ids, channel_thresholds)}

    def _create_channels_for_controller(self, num_channels, controller_id):
        channel_ids = self._make_channel_eids(controller_id, num_channels)
        self._register_channels_for_controller(channel_ids, controller_id)
        return channel_ids

    def _register_channels_for_controller(self, channel_ids, controller_id):
        self.controller_channels[controller_id] = channel_ids
        for channel_id in channel_ids:
            self.channel_controllers[channel_id] = controller_id

    def _make_controller_eid(self, controller_index):
        return f"{self.controller_eid_prefix}{controller_index}"

    def _make_channel_eids(self, controller_id, num_channels):
        return [f"{controller_id}{self.channel_eid_infix}{i}" for i in range(num_channels)]

    # -------------------------------------------------------------------------------------------------------------#

    def _sort_inputs_by_controller(self, inputs: dict):
        inputs_processed = {}

        for entity_id, values in inputs.items():
            if self._is_controller(entity_id):
                self._add_controller_attribute_to_processed_inputs(inputs_processed, entity_id, values)
            elif self._is_channel(entity_id):
                self._add_channel_attribute_to_processed_inputs(inputs_processed, entity_id, values)
        return inputs_processed

    def _add_controller_attribute_to_processed_inputs(self, inputs_processed, controller_id, values):
        self._ensure_field_exists(inputs_processed, controller_id)

        for attribute in values.keys():
            value = self._first_dict_value(values[attribute])
            inputs_processed[controller_id][attribute] = value

    def _add_channel_attribute_to_processed_inputs(self, inputs_processed, channel_id, values):
        channel_id = self.channel_controllers[channel_id]

        self._ensure_field_exists(inputs_processed, channel_id)

        for attribute in values.keys():
            source = self._first_dict_key(values[attribute])
            value = self._first_dict_value(values[attribute])
            self._ensure_field_exists(inputs_processed[channel_id], attribute)
            inputs_processed[channel_id][attribute][source] = value

    @staticmethod
    def _ensure_field_exists(dictionary: dict, key):
        if key not in dictionary:
            dictionary[key] = {}

    @staticmethod
    def _first_dict_value(dictionary: dict):
        return list(dictionary.values())[0]

    @staticmethod
    def _first_dict_key(dictionary: dict):
        return list(dictionary.keys())[0]

    def _create_system_to_channel_map(self):
        channels_formatted = [self.simulator_id + "." + channel for channels in self.controller_channels.values() for
                              channel in channels]
        channels_systems_dict = run_async_in_thread(self.mosaik.get_related_entities(channels_formatted))
        systems_channels_dict = {}
        for outer_key, inner_dict in channels_systems_dict.items():
            for inner_key in inner_dict.keys():
                relevant_part_of_outer_key = outer_key.split('.')[1]
                systems_channels_dict[inner_key] = relevant_part_of_outer_key

        self.systems_channels_dict = systems_channels_dict

    def _models_initialize_controlled_systems(self):
        for controller in self.controllers.values():
            controller.initialize_controlled_systems(self.systems_channels_dict.keys())

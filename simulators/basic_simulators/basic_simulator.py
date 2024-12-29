import mosaik_api


class BasicSimulator(mosaik_api.Simulator):
    def __init__(self, meta, model_class):
        super().__init__(meta)

        models = list(self.meta['models'].keys())
        if len(models) > 1:
            raise ValueError(
                f"{self.__class__.__name__} only works for single-model simulators. "
                f"{len(models)} models were specified."
            )

        self.model_class = model_class
        self.model = models[0]
        self.eid_prefix = f"{self.model}_"
        self.entities = {}
        self.time = 0
        self.sid = None
        self.step_size = None

    def init(self, sid, step_size=1, time_resolution=1.0, eid_prefix=None):
        if float(time_resolution) != 1.0:
            raise ValueError(f"{self.model} only supports time_resolution=1.0, but {time_resolution} was set.")

        self.sid = sid
        self.step_size = step_size

        if eid_prefix is not None:
            self.eid_prefix = eid_prefix

        return self.meta

    def create(self, num, model, **kwargs):
        if model != self.model:
            raise ValueError(f"The simulator can only instantiate entities of type {model}")

        next_eid = len(self.entities)
        created_entities = []

        for idx in range(next_eid, next_eid + num):
            entity = self.model_class(**kwargs)
            eid = f"{self.eid_prefix}{idx}"
            self.entities[eid] = entity
            created_entities.append({'eid': eid, 'type': model})

        return created_entities

    def step(self, time, inputs, max_advance):
        self.time = time

        for eid, entity in self.entities.items():
            self.set_params_if_in_inputs(entity, eid, inputs)
            entity.step(time)

        return self.next_simulation_time(max_advance)

    @staticmethod
    def set_params_if_in_inputs(entity, eid, inputs):
        if eid in inputs:
            input_data = inputs[eid]
            for attr, value in input_data.items():
                setattr(entity, attr, list(value.values())[0])

    def get_data(self, outputs):
        data = {'time': self.time}

        for eid, attributes in outputs.items():
            entity = self.entities[eid]
            data[eid] = {}

            for attribute in attributes:
                if attribute not in self.meta["models"][self.model]["attrs"]:
                    raise ValueError(f"Unknown output attribute {attribute}")

                attribute_value = getattr(entity, attribute)
                if attribute_value is not None:
                    data[eid][attribute] = attribute_value

        return data

    def next_simulation_time(self, max_advance):
        advance = min(self.step_size, max_advance) if max_advance else self.step_size

        return self.time + advance

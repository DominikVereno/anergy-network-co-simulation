"""
This module implements the mosaik API for `PYPOWER
<https://pypi.python.org/pypi/PYPOWER>`_.

"""
from __future__ import division
import logging
import os
import mosaik_api_v3

from models import pypower


logger = logging.getLogger('pypower.mosaik')

meta = {
    'type': 'time-based',
    'models': {
        'Grid': {
            'public': True,
            'params': [
                'gridfile',  # Name of the file containing the grid topology.
                'sheetnames',  # Mapping of Excel sheet names, optional.
            ],
            'attrs': [],
        },
        'RefBus': {
            'public': False,
            'params': [],
            'attrs': [
                'P',   # Active power [W]
                'Q',   # Reactive power [VAr]
                'Vl',  # Nominal bus voltage [V]
                'Vm',  # Voltage magnitude [V]
                'Va',  # Voltage angle [deg]
            ],
        },
        'PQBus': {
            'public': False,
            'params': [],
            'attrs': [
                'P',   # Active power [W]
                'Q',   # Reactive power [VAr]
                'Vl',  # Nominal bus voltage [V]
                'Vm',  # Voltage magnitude [V]
                'Va',  # Voltage angle [deg]
            ],
        },
        'Transformer': {
            'public': False,
            'params': [],
            'attrs': [
                'P_from',    # Active power at "from" side [W]
                'Q_from',    # Reactive power at "from" side [VAr]
                'P_to',      # Active power at "to" side [W]
                'Q_to',      # Reactive power at "to" side [VAr]
                'S_r',       # Rated apparent power [VA]
                'I_max_p',   # Maximum current on primary side [A]
                'I_max_s',   # Maximum current on secondary side [A]
                'P_loss',    # Active power loss [W]
                'U_p',       # Nominal primary voltage [V]
                'U_s',       # Nominal secondary voltage [V]
                'taps',      # Dict. of possible tap turns and their values
                'tap_turn',  # Currently active tap turn
            ],
        },
        'Branch': {
            'public': False,
            'params': [],
            'attrs': [
                'P_from',    # Active power at "from" side [W]
                'Q_from',    # Reactive power at "from" side [VAr]
                'P_to',      # Active power at "to" side [W]
                'Q_to',      # Reactive power at "to" side [VAr]
                'I_real',    # Branch current (real part) [A]
                'I_imag',    # Branch current (imaginary part) [A]
                'S_max',     # Maximum apparent power [VA]
                'I_max',     # Maximum current [A]
                'length',    # Line length [km]
                'R_per_km',  # Resistance per unit length [Ω/km]
                'X_per_km',  # Reactance per unit length [Ω/km]
                'C_per_km',  # Capactity per unit length [F/km]
                'online',    # Boolean flag (True|False)
            ],
        },
    },
}


class PyPowerSim(mosaik_api_v3.Simulator):
    def __init__(self):
        super(PyPowerSim, self).__init__(meta)
        self.step_size = None

        # In PYPOWER loads are positive numbers and feed-in is expressed via
        # negative numbers. "init()" will that this flag to "1" in this case.
        # If incoming values for loads are negative and feed-in is positive,
        # this attribute must be set to -1.
        self.pos_loads = None

        self._entities = {}
        self._relations = []  # List of pair-wise related entities (IDs)
        self._ppcs = []  # The pypower cases
        self._cache = {}  # Cache for load flow outputs

    def init(self, sid, time_resolution, step_size, pos_loads=True,
             converge_exception=False):
        logger.debug('Power flow will be computed every %d seconds.' %
                     step_size)
        signs = ('positive', 'negative')
        logger.debug('Loads will be %s numbers, feed-in %s numbers.' %
                     signs if pos_loads else tuple(reversed(signs)))

        self.step_size = step_size
        self.pos_loads = 1 if pos_loads else -1
        self._converge_exception = converge_exception

        return self.meta

    def create(self, num, modelname, gridfile, sheetnames=None):
        if modelname != 'Grid':
            raise ValueError('Unknown model: "%s"' % modelname)
        if not os.path.isfile(gridfile):
            raise ValueError('File "%s" does not exist!' % gridfile)

        if not sheetnames:
            sheetnames = {}

        grids = []
        for i in range(num):
            grid_idx = len(self._ppcs)
            ppc, entities = pypower.load_case(gridfile, grid_idx, sheetnames)
            self._ppcs.append(ppc)

            children = []
            for eid, attrs in sorted(entities.items()):
                assert eid not in self._entities
                self._entities[eid] = attrs

                # We'll only add relations from branches to nodes (and not from
                # nodes to branches) because this is sufficient for mosaik to
                # build the entity graph.
                relations = []
                if attrs['etype'] in ['Transformer', 'Branch']:
                    relations = attrs['related']

                children.append({
                    'eid': eid,
                    'type': attrs['etype'],
                    'rel': relations,
                })

            grids.append({
                'eid': pypower.make_eid('grid', grid_idx),
                'type': 'Grid',
                'rel': [],
                'children': children,
            })

        return grids

    def step(self, time, inputs, max_advance):
        for ppc in self._ppcs:
            pypower.reset_inputs(ppc)

        for eid, attrs in inputs.items():
            ppc = pypower.case_for_eid(eid, self._ppcs)
            idx = self._entities[eid]['idx']
            etype = self._entities[eid]['etype']
            static = self._entities[eid]['static']
            for name, values in attrs.items():
                # values is a dict of p/q values, sum them up
                attrs[name] = sum(float(v) for v in values.values())
                if name == 'P':
                    attrs[name] *= self.pos_loads

            pypower.set_inputs(ppc, etype, idx, attrs, static)

        res = []
        for ppc in self._ppcs:
            res.append(pypower.perform_powerflow(ppc))
            if self._converge_exception and not res[-1]['success']:
                raise RuntimeError(
                    'Loadflow did not converge for eid "%s" at time %i!' %
                    (eid, time))
        self._cache = pypower.get_cache_entries(res, self._entities)

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            for attr in attrs:
                try:
                    val = self._cache[eid][attr]
                    if attr == 'P':
                        val *= self.pos_loads
                except KeyError:
                    val = self._entities[eid]['static'][attr]
                data.setdefault(eid, {})[attr] = val

        return data


def main():
    mosaik_api_v3.start_simulation(PyPowerSim(), 'The mosaik-PYPOWER adapter')

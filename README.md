# Anergy Network Co-Simulation Repository

## Overview

This repository provides co-simulation setup for anergy networks and their interaction with electrical systems. It uses [Mosaik 3.0](https://mosaik.offis.de) as co-simulation framework, [pandapipes](https://www.pandapipes.org) for thermal network modeling, and [PYPOWER](https://github.com/rwl/PYPOWER) for power grid simulation.

## Requirements

- Suggested Python version: **3.10.0**
- Install dependencies using the following command:
  ```bash
  pip install -r requirements.txt
  ```

## Directory Structure

- `data/` : Contains auxiliary specification data, such as network topologies and time-series data.

- `models/` : Includes simulation models and logic for individual subsystems.

- `monitors/` : Provides modules for logging and visualizing simulation results.

- `scenarios/` : Configuration setups of entities and their connections.

- `simulators/` : Contains classes implementing the high-level Mosaik API to connect and manage simulation models within the framework.

- `simulation.py` : Instantiate and run a simulation scenario. 

## Citing this Work

TBD
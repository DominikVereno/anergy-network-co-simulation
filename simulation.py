import datetime as dt

from scenarios.complete_scenario import CompleteScenario

start_time = dt.datetime(year=2023, month=1, day=30, hour=0)
duration = dt.timedelta(days=10)

electricity_grid_file = "data/demo_grid.json"
dh_network_file       = "data/anergy_demo_network.json"

scenario = CompleteScenario(
    start_time           =start_time,
    duration             =duration, 
    step_size            =dt.timedelta(minutes=10),
    electricity_grid_file=electricity_grid_file,
    dh_network_file      =dh_network_file
    )

scenario.run()

from agent import *
from model import CityModel
from mesa.visualization import CanvasGrid, ModularServer, Slider, ChartModule


def agent_portrayal(agent):
    if agent is None: return
    
    portrayal = {"Shape": "rect",
                 "Filled": "true",
                 "Layer": 1,
                 "w": 1,
                 "h": 1
                 }

    if isinstance(agent, Road):
        portrayal["Color"] = "grey"
        portrayal["Layer"] = 0

    if isinstance(agent, Destination):
        portrayal["Color"] = "lightgreen"
        portrayal["Layer"] = 0

    if isinstance(agent, Traffic_Light):
        portrayal["Color"] = "red" if not agent.state else "green"
        portrayal["Layer"] = 0
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8

    if isinstance(agent, Obstacle):
        portrayal["Color"] = "cadetblue"
        portrayal["Layer"] = 0
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8

    if isinstance(agent, Car):
        portrayal["Color"] = agent.color
        portrayal["Layer"] = 1
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.5

    return portrayal

# Set grid size based on the map file
width = 0
height = 0

with open('../static/city_files/2024_base.txt') as baseFile:
    lines = baseFile.readlines()
    width = len(lines[0]) - 1
    height = len(lines)

# Create a CanvasGrid for visualization
grid = CanvasGrid(agent_portrayal, width, height, 500, 500)

agent_count_chart = ChartModule(
    [{"Label": "Cars in Grid", "Color": "blue"}],
    data_collector_name="datacollector"
)
arrived_chart = ChartModule(
    [{"Label": "Cars Reached Destination", "Color": "red"}],
    data_collector_name="datacollector"
)

# Set up the server with the bar chart and grid
server = ModularServer(CityModel, [grid, agent_count_chart, arrived_chart], "Traffic Simulation", {"N":0})
server.port = 8522  # The default port for Mesa
server.launch()
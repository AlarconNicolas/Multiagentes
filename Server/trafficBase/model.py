from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agent import *
import json
import random

class CityModel(Model):
    """
    Creates a model based on a city map.
    Args:
        N: Number of agents in the simulation
    """
    def __init__(self, N):
        # Ensure the Model superclass is initialized
        super().__init__()

        # Load the map dictionary
        dataDictionary = json.load(open("../static/city_files/mapDictionary.json"))
        self.traffic_lights = []
        self.destinations = []  # List to store all destination agents
        
        # Load the map file
        with open('../static/city_files/2022_base.txt') as baseFile:
            lines = baseFile.readlines()
            self.width = len(lines[0])-1
            self.height = len(lines)
            self.grid = MultiGrid(self.width, self.height, torus=False)
            self.schedule = RandomActivation(self)
            
            # Loop through the map and create agents
            for r, row in enumerate(lines):
                for c, col in enumerate(row):
                    if col in ["v", "^", ">", "<"]:
                        agent = Road(f"r_{r*self.width+c}", self, dataDictionary[col])
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                    elif col in ["S", "s"]:
                        agent = Traffic_Light(f"tl_{r*self.width+c}", self, False if col == "S" else True, int(dataDictionary[col]))
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        self.schedule.add(agent)
                        self.traffic_lights.append(agent)
                    elif col == "#":
                        agent = Obstacle(f"ob_{r*self.width+c}", self)
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                    elif col == "D":
                        agent = Destination(f"d_{r*self.width+c}", self)
                        pos = (c, self.height - r - 1)
                        self.grid.place_agent(agent, pos)
                        self.destinations.append(pos)  # Store the destination position
        
        # Create a car agent with a random destination
        if self.destinations:  
            car_destination = random.choice(self.destinations)
            car = Car("car_1", self, car_destination)
            
            self.grid.place_agent(car, (0, 0))
            self.schedule.add(car)
            print("Car position:", car.pos)
            print("Destination:", car_destination)
        
        self.num_agents = N
        self.running = True

    def step(self):
        '''Advance the model by one step.'''
        self.schedule.step()

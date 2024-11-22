from mesa import Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from .agent import *
import json
import random
import networkx as nx

class CityModel(Model):
    def __init__(self, N):
        super().__init__()
        self.reached_destination = 0
        self.in_grid = 0
        self.remaining_cars_to_spawn = N
        self.datacollector = DataCollector(
            model_reporters={
                "Cars in Grid": lambda m: m.in_grid,
                "Cars Reached Destination": lambda m: m.reached_destination,
                "Cars Waiting to Spawn": lambda m: m.remaining_cars_to_spawn
            }
        )
        
        # Load the map dictionary
        dataDictionary = json.load(open("./static/city_files/mapDictionary.json"))
        self.traffic_lights = []
        self.destinations = []
        self.corner_positions = []
        
        # Load the map file and create graph
        map_path = './static/city_files/2022_base.txt'
        with open(map_path) as baseFile:
            lines = baseFile.readlines()
            self.width = len(lines[0])-1
            self.height = len(lines)
            self.grid = MultiGrid(self.width, self.height, torus=False)
            self.schedule = RandomActivation(self)
            
            # Create basic grid structure (same as before)
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
                        self.destinations.append(pos)
        
        self.navigation_graph = self.create_city_graph(map_path)
        
        # Bottom-left corner
        self.corner_positions.append((0, 1))  
        self.corner_positions.append((0, 0))  
        # Top-left corner
        self.corner_positions.append((0, self.height - 1))  
        self.corner_positions.append((0, self.height - 2))  
        # Bottom-right corner
        self.corner_positions.append((self.width - 1, 0))  
        self.corner_positions.append((self.width - 1, 1))  
        # Top-right corner
        self.corner_positions.append((self.width - 1, self.height - 1)) 
        self.corner_positions.append((self.width - 1, self.height - 2))
        
        self.spawn_positions = [
            pos for pos in self.corner_positions
            if any(isinstance(agent, Road) for agent in self.grid.get_cell_list_contents([pos]))
        ]
        
        self.car_id_counter = 0
        self.num_agents = N
        self.running = True

    def create_city_graph(self, map_file_path):
        """
        Creates a directed graph representation of the city based on the map file.
        """
        with open(map_file_path, 'r') as file:
            lines = file.readlines()
            height = len(lines)
            width = len(lines[0].strip())
            
        city_graph = nx.DiGraph()
        cell_types = {}
        
        for y, line in enumerate(lines):
            for x, cell in enumerate(line.strip()):
                grid_y = height - y - 1
                cell_types[(x, grid_y)] = cell
                
        directions = {
            '>': [(1, 0)],   # Right
            '<': [(-1, 0)],  # Left
            '^': [(0, 1)],   # Up
            'v': [(0, -1)],  # Down
            's': [],         # Traffic light (horizontal)
            'S': [],         # Traffic light (vertical)
            '#': [],         # Obstacle
            'D': []          # Destination
        }
        
        for y, line in enumerate(lines):
            for x, cell in enumerate(line.strip()):
                grid_y = height - y - 1
                current_pos = (x, grid_y)
                
                if cell == '#':
                    continue
                    
                possible_moves = []
                
                if cell in ['>', '<', '^', 'v']:
                    possible_moves.extend(directions[cell])
                    
                    if cell in ['>', '<']:  # Horizontal road
                        possible_moves.extend([(0, 1), (0, -1)]) 
                    elif cell in ['^', 'v']:  # Vertical road
                        possible_moves.extend([(1, 0), (-1, 0)]) 
                        
                elif cell in ['s', 'S']:
                    if cell == 's':
                        possible_moves.extend([(1, 0), (-1, 0)])  # Left/right
                    else: 
                        possible_moves.extend([(0, 1), (0, -1)])  # Up/down
                        
                elif cell == 'D':
                    continue
                
                # Add edges to the graph for valid movements
                for dx, dy in possible_moves:
                    next_pos = (x + dx, grid_y + dy)
                    
                    if (0 <= next_pos[0] < width and 
                        0 <= next_pos[1] < height and 
                        next_pos in cell_types):
                        
                        if cell_types[next_pos] != '#':
                            city_graph.add_edge(current_pos, next_pos)
        
        return city_graph

    def find_path(self, start_pos, end_pos):
        """
        Finds the shortest path between two positions in the city.
        """
        try:
            return nx.shortest_path(self.navigation_graph, start_pos, end_pos)
        except nx.NetworkXNoPath:
            return None
    
    def try_spawn_car(self):
        """Attempts to spawn new cars at all available corner positions."""
        if self.remaining_cars_to_spawn <= 0:
            return False

        # Find all available corner positions
        available_positions = []

        for pos in self.corner_positions:
            cell_contents = self.grid.get_cell_list_contents([pos])
            has_car = any(isinstance(agent, Car) for agent in cell_contents)
            has_road = any(isinstance(agent, Road) for agent in cell_contents)

            if has_road and not has_car:
                available_positions.append(pos)

        for pos in available_positions:
            if self.remaining_cars_to_spawn <= 0:
                break

            # Create and place the car
            self.car_id_counter += 1
            car = Car(f"car_{self.car_id_counter}", self, random.choice(self.destinations))
            self.grid.place_agent(car, pos)
            print(f"Spawned car {car.unique_id} at position {pos}")  # Debug print
            self.schedule.add(car)
            self.in_grid += 1
            self.remaining_cars_to_spawn -= 1

        return len(available_positions) > 0
        
    def step(self):
        """Advance the model by one step and try to spawn new cars."""
        # Try to spawn new cars if there are any remaining
        self.try_spawn_car()
        self.datacollector.collect(self)
        self.schedule.step()
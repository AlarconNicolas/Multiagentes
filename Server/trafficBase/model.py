from mesa import Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agent import *
import json
import random
import networkx as nx

class CityModel(Model):
    def __init__(self, N):
        super().__init__()
        self.reached_destination = 0
        self.in_grid = 0
        self.corner_positions = []
        self.running = True
        self.datacollector = DataCollector(
            model_reporters={
                "Cars in Grid": lambda m: m.in_grid,
                "Cars Reached Destination": lambda m: m.reached_destination,
            }
        )
        
        # Load the map dictionary
        dataDictionary = json.load(open("../static/city_files/mapDictionary.json"))
        self.traffic_lights_S = []
        self.traffic_lights_s = []
        self.destinations = []
        self.corner_positions = []
        
        # Load the map file and create graph
        map_path = '../static/city_files/2022_base.txt'
        with open(map_path) as baseFile:
            lines = baseFile.readlines()
            self.width = len(lines[0])-1
            self.height = len(lines)
            self.grid = MultiGrid(self.width, self.height, torus=False)
            self.schedule = RandomActivation(self)
            
            # Create basic grid structure
            for r, row in enumerate(lines):
                for c, col in enumerate(row):
                    if col in ["v", "^", ">", "<"]:
                        agent = Road(f"r_{r*self.width+c}", self, dataDictionary[col])
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                    elif col in ["S", "s"]:
                        is_horizontal = (col == "s")
                        agent = Traffic_Light(f"tl_{r*self.width+c}", self, is_horizontal=is_horizontal)
                        self.grid.place_agent(agent, (c, self.height - r - 1))
                        self.schedule.add(agent)
                        if col == "S":
                            self.traffic_lights_S.append(agent)
                        else:
                            self.traffic_lights_s.append(agent)
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
        self.corner_positions.append((0, 0))  
        # Top-left corner
        self.corner_positions.append((0, self.height - 1))  
        # Bottom-right corner
        self.corner_positions.append((self.width - 1, 0))  
        # Top-right corner
        self.corner_positions.append((self.width - 1, self.height - 1)) 
        
        self.spawn_positions = [
            pos for pos in self.corner_positions
            if any(isinstance(agent, Road) for agent in self.grid.get_cell_list_contents([pos]))
        ]
        
        self.car_id_counter = 0
        self.num_agents = N
        self.remaining_cars_to_spawn = int(N * len(self.corner_positions))
        self.running = True
        self.light_timer = 0  
        self.light_cycle_duration = 10  

    def create_city_graph(self, map_file_path):
        """
        Creates a directed graph representation of the city based on the map file,
        ensuring all valid cells are included as nodes and edges are added for valid movements,
        respecting the directionality of roads and traffic lights.
        """
        with open(map_file_path, 'r') as file:
            lines = file.readlines()
            height = len(lines)
            width = len(lines[0].strip())

        city_graph = nx.DiGraph()  # Directed graph for city
        cell_types = {}

        # Define valid movement directions for each cell type
        directions = {
            '>': [(1, 0)],   # Right
            '<': [(-1, 0)],  # Left
            '^': [(0, 1)],   # Up
            'v': [(0, -1)],  # Down
            's': [],         # Horizontal traffic light (left/right)
            'S': [],         # Vertical traffic light (up/down)
            '#': [],         # Obstacle (no movement)
            'D': []          # Destination (no movement)
        }

        # Map cell types to their grid coordinates
        for y, line in enumerate(lines):
            for x, cell in enumerate(line.strip()):
                grid_y = height - y - 1  # Invert Y axis to align with the grid
                cell_types[(x, grid_y)] = cell

        # Add all valid cells to the graph as nodes
        for pos, cell in cell_types.items():
            if cell != '#':  # Skip obstacles
                city_graph.add_node(pos)

        # Add edges based on movement rules
        for pos, cell in cell_types.items():
            if cell == '#':  # Skip obstacles
                continue

            possible_moves = []

            # Handle roads and traffic lights
            if cell in ['>', '<', '^', 'v']:  # If it's a road
                possible_moves.extend(directions[cell])  # Add primary direction

                # Allow turns at corners if it's a road
                if cell in ['>', '<']:  # Horizontal roads
                    possible_moves.extend([(0, 1), (0, -1)])  # Up/Down movement
                elif cell in ['^', 'v']:  # Vertical roads
                    possible_moves.extend([(1, 0), (-1, 0)])  # Left/Right movement

            elif cell == 's':  # Horizontal traffic light (left/right)
                # Check next cells in left and right directions
                next_right_pos = (pos[0] + 1, pos[1])  # Move right
                next_left_pos = (pos[0] - 1, pos[1])  # Move left

                if next_right_pos in cell_types and cell_types[next_right_pos] in ['>', 's']:
                    possible_moves.append((1, 0))  # Right
                if next_left_pos in cell_types and cell_types[next_left_pos] in ['<', 's']:
                    possible_moves.append((-1, 0))  # Left

            elif cell == 'S':  # Vertical traffic light (up/down)
                # Check next cells in up and down directions
                next_up_pos = (pos[0], pos[1] + 1)  # Move up
                next_down_pos = (pos[0], pos[1] - 1)  # Move down

                if next_up_pos in cell_types and cell_types[next_up_pos] in ['^', 'S']:
                    possible_moves.append((0, 1))  # Up
                if next_down_pos in cell_types and cell_types[next_down_pos] in ['v', 'S']:
                    possible_moves.append((0, -1))  # Down


            # Add edges based on possible movements
            for dx, dy in possible_moves:
                next_pos = (pos[0] + dx, pos[1] + dy)
                if next_pos in cell_types and cell_types[next_pos] != '#':  # Ensure valid cell
                    # Add the edge to the graph
                    city_graph.add_edge(pos, next_pos)

        return city_graph

    def find_path(self, start_pos, end_pos, avoid_traffic=True):
        """
        Finds the shortest path between two positions using Dijkstra's algorithm.
        If avoid_traffic is True, considers positions occupied by other cars or obstacles
        by assigning a high cost to edges leading to those positions.
        """
        try:
            if avoid_traffic:
                def weight(u, v, d):
                    """
                    Custom weight function for Dijkstra's algorithm.
                    u: current node position
                    v: neighbor node position
                    d: edge data dictionary
                    """
                    # Check if the target position v is occupied by a Car or an Obstacle
                    cell_contents = self.grid.get_cell_list_contents([v])
                    if any(isinstance(agent, (Car, Obstacle)) for agent in cell_contents):
                        return float('inf')  # Effectively block this edge
                    else:
                        # Add random penalty to encourage route diversity
                        random_penalty = random.uniform(0.1, 0.5)
                        return 1 + random_penalty  # Base cost plus penalty

                # Use Dijkstra's algorithm with the custom weight function
                return nx.dijkstra_path(self.navigation_graph, start_pos, end_pos, weight=weight)
            else:
                # Standard shortest path without weights
                return nx.shortest_path(self.navigation_graph, start_pos, end_pos)
        except nx.NetworkXNoPath:
            return None  # No path found


    def try_spawn_car(self):
        """
        Attempts to spawn new cars at available corner positions based on the probability N (density).
        """
        if self.num_agents <= 0:  # If density is 0, no cars will spawn
            return False

        # Find all available corner positions
        available_positions = []

        for pos in self.corner_positions:
            cell_contents = self.grid.get_cell_list_contents([pos])
            has_car = any(isinstance(agent, Car) for agent in cell_contents)
            has_road = any(isinstance(agent, Road) for agent in cell_contents)

            if has_road and not has_car:
                available_positions.append(pos)

        # Spawn cars based on the density probability (self.num_agents)
        for pos in available_positions:
            if random.random() < self.num_agents:  # Compare random value to density probability
                # Create and place the car
                self.car_id_counter += 1
                car = Car(f"car_{self.car_id_counter}", self, random.choice(self.destinations))
                self.grid.place_agent(car, pos)
                self.schedule.add(car)
                self.in_grid += 1

        return len(available_positions) > 0
        
    def toggle_traffic_lights(self):
        """
        Toggles the state of all traffic lights such that S lights and s lights are synchronized.
        """
        if self.light_timer % self.light_cycle_duration == 0:
            for light in self.traffic_lights_S:
                light.state = True  # S lights green
            for light in self.traffic_lights_s:
                light.state = False  # s lights red
        elif self.light_timer % self.light_cycle_duration == self.light_cycle_duration // 2:
            for light in self.traffic_lights_S:
                light.state = False  # S lights red
            for light in self.traffic_lights_s:
                light.state = True  # s lights green
        self.light_timer += 1

    def step(self):
        """Advance the model by one step and try to spawn new cars."""
        # Toggle synchronized traffic lights
        self.toggle_traffic_lights()
        self.try_spawn_car()
        self.datacollector.collect(self)
        self.schedule.step()
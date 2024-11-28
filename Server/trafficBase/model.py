# Import necessary modules
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from .agent import *  # Ensure your agent classes (Car, Road, Traffic_Light, Destination, etc.) are correctly defined in this module
import json
import random
import networkx as nx  # For graph-based city navigation

# Define the main city simulation model
class CityModel(Model):
    def __init__(self, N):
        """
        Initialize the city simulation model.

        Parameters:
        - N: Number of cars to spawn initially (not directly used in this code).
        """
        super().__init__()
        self.reached_destination = 0  # Counter for cars that reached their destination
        self.in_grid = 0  # Counter for cars currently in the grid
        self.corner_positions = []  # Positions designated for spawning cars
        self.running = True  # Controls the simulation run state
        self.step_count = 0  # Step counter
        self.n = N  # Number of cars to potentially spawn

        # Initialize DataCollector to track model metrics
        self.datacollector = DataCollector(
            model_reporters={
                "Cars in Grid": lambda m: m.in_grid,
                "Cars Reached Destination": lambda m: m.reached_destination,
            }
        )

        # Load the map dictionary (provides additional map-related data if needed)
        with open("./static/city_files/mapDictionary.json") as f:
            dataDictionary = json.load(f)

        # Separate lists for traffic lights and destination positions
        self.traffic_lights_S = []  # Vertical traffic lights
        self.traffic_lights_s = []  # Horizontal traffic lights
        self.destinations = []  # Destination positions

        # Define arrow orientations for navigation
        self.arrow_orientations = {
            '>': (1, 0),    # Right
            '<': (-1, 0),   # Left
            '^': (0, 1),    # Up
            'v': (0, -1),   # Down
        }

        # Load the map file and create the grid
        map_path = './static/city_files/2024_base.txt'
        with open(map_path) as baseFile:
            lines = baseFile.readlines()
            self.width = len(lines[0].strip())  # Grid width
            self.height = len(lines)  # Grid height
            self.grid = MultiGrid(self.width, self.height, torus=False)  # Non-wrapping grid
            self.schedule = RandomActivation(self)  # Random activation schedule for agents

            # Create the grid structure by parsing the map file
            for r, row in enumerate(lines):
                for c, col in enumerate(row.strip('\n')):
                    pos = (c, self.height - r - 1)  # Align Y-axis correctly
                    unique_id = f"{col}_{r*self.width+c}"
                    if col in self.arrow_orientations:
                        # Create Road agent with appropriate direction
                        direction = tuple(self.arrow_orientations[col])
                        agent = Road(f"r_{r*self.width+c}", self, direction)
                        self.grid.place_agent(agent, pos)
                    elif col in ["S", "s"]:
                        # Create Traffic_Light agent and add to appropriate list
                        is_horizontal = (col == "s")
                        agent = Traffic_Light(f"tl_{r*self.width+c}", self, is_horizontal=is_horizontal)
                        self.grid.place_agent(agent, pos)
                        self.schedule.add(agent)
                        if col == "S":
                            self.traffic_lights_S.append(agent)
                        else:
                            self.traffic_lights_s.append(agent)
                    elif col == "#":
                        # Create Obstacle agent
                        agent = Obstacle(f"ob_{r*self.width+c}", self)
                        self.grid.place_agent(agent, pos)
                    elif col == "D":
                        # Create Destination agent and store its position
                        agent = Destination(f"d_{r*self.width+c}", self)
                        self.grid.place_agent(agent, pos)
                        self.destinations.append(pos)

        # Create the city navigation graph based on the map
        self.navigation_graph = self.create_city_graph(map_path)

        # Define corner positions for spawning cars
        self.corner_positions = [
            (0, 0),                          # Bottom-left corner
            (0, self.height - 1),            # Top-left corner
            (self.width - 1, 0),             # Bottom-right corner
            (self.width - 1, self.height - 1)  # Top-right corner
        ]

        self.car_id_counter = 0  # Unique ID counter for cars
        self.light_timer = 0  # Timer for traffic light toggling
        self.light_cycle_duration = 10  # Duration for each traffic light state

    def lateral_moves(self, direction):
        """
        Returns the lateral movement directions based on the forward direction.
        """
        if direction == (1, 0):  # Right
            return [(0, 1), (0, -1)]  # Up and Down
        elif direction == (-1, 0):  # Left
            return [(0, -1), (0, 1)]  # Down and Up
        elif direction == (0, 1):  # Up
            return [(-1, 0), (1, 0)]  # Left and Right
        elif direction == (0, -1):  # Down
            return [(1, 0), (-1, 0)]  # Right and Left
        else:
            return []

    def get_allowed_moves(self, cell_type):
        """
        Returns the list of allowed movement directions based on the cell type.
        """
        if cell_type in self.arrow_orientations:
            forward = self.arrow_orientations[cell_type]
            lateral_moves = self.lateral_moves(forward)
            return [forward] + lateral_moves
        elif cell_type == 's':
            return [(-1, 0), (1, 0)]  # Horizontal traffic light (left, right)
        elif cell_type == 'S':
            return [(0, -1), (0, 1)]  # Vertical traffic light (up, down)
        elif cell_type == 'D':
            return []  # Destination cells allow no outgoing movement
        else:
            return []

    def valid_movement(self, current_cell_type, next_cell_type, dx, dy):
        """
        Determines if movement between two cells is valid based on rules:
        - Movement allowed by current cell type.
        - No U-turns or contrary movement.
        """
        if next_cell_type == '#':  # Obstacles are impassable
            return False

        # Check allowed moves for current cell type
        allowed_moves = self.get_allowed_moves(current_cell_type)
        if (dx, dy) not in allowed_moves:
            return False

        # Prevent movement into a contrary arrow
        current_orientation = self.arrow_orientations.get(current_cell_type)
        next_orientation = self.arrow_orientations.get(next_cell_type)
        if next_orientation:
            if current_orientation and (current_orientation[0] == -next_orientation[0] and current_orientation[1] == -next_orientation[1]):
                return False

        # Prevent U-turns
        reverse_direction = (-dx, -dy)
        if current_orientation == reverse_direction:
            return False

        return True

    def create_city_graph(self, map_file_path):
        """
        Creates a directed graph representing the city layout based on the map file.
        """
        with open(map_file_path, 'r') as file:
            lines = file.readlines()
            height = len(lines)
            width = len(lines[0].strip())

        city_graph = nx.DiGraph()
        cell_types = {}

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
            if cell == '#' or cell == 'D':  # Skip obstacles and destinations
                continue

            # Determine allowed moves
            allowed_moves = self.get_allowed_moves(cell)
            for dx, dy in allowed_moves:
                next_pos = (pos[0] + dx, pos[1] + dy)
                if next_pos in cell_types:
                    next_cell = cell_types[next_pos]
                    if self.valid_movement(cell, next_cell, dx, dy):
                        city_graph.add_edge(pos, next_pos)

        return city_graph

    def is_neighbor(self, pos, reference_pos):
        """
        Checks if a position is a direct neighbor of another.
        """
        neighbors = self.grid.get_neighborhood(reference_pos, moore=True, include_center=False)
        return pos in neighbors

    def find_path(self, start_pos, end_pos, avoid_traffic=True):
        """
        Finds the shortest path between two positions using Dijkstra's algorithm.
        """
        try:
            allowed_nodes = set(self.navigation_graph.nodes)
            if start_pos in self.corner_positions:
                allowed_nodes -= set(self.corner_positions)
                allowed_nodes.add(start_pos)
            else:
                allowed_nodes -= set(self.corner_positions)

            other_destinations = set(self.destinations) - {end_pos}
            allowed_nodes -= other_destinations

            temp_graph = self.navigation_graph.subgraph(allowed_nodes)

            if avoid_traffic:
                def weight(u, v, d):
                    w = 1
                    cell_contents = self.grid.get_cell_list_contents([v])
                    if any(isinstance(agent, (Car, Obstacle)) for agent in cell_contents):
                        return float('inf')
                    for corner in self.corner_positions:
                        if self.is_neighbor(v, corner):
                            w += 30
                    return w

                path = nx.dijkstra_path(temp_graph, start_pos, end_pos, weight=weight)
                return path
            else:
                path = nx.shortest_path(temp_graph, start_pos, end_pos)
                return path
        except nx.NetworkXNoPath:
            return None

    def try_spawn_car(self):
        """
        Attempts to spawn up to 4 cars at corner positions if available.
        """
        if self.step_count % 1 != 0:
            return None

        available_positions = [
            pos for pos in self.corner_positions
            if not any(isinstance(agent, Car) for agent in self.grid.get_cell_list_contents([pos]))
        ]

        cars_to_spawn = min(4, len(available_positions))
        spawned_cars = []

        for i in range(cars_to_spawn):
            pos = available_positions[i]
            self.car_id_counter += 1
            destination = random.choice(self.destinations)
            car = Car(f"car_{self.car_id_counter}", self, destination)
            self.grid.place_agent(car, pos)
            self.schedule.add(car)
            self.in_grid += 1
            spawned_cars.append(car)

        return spawned_cars

    def toggle_traffic_lights(self):
        """
        Toggles the state of all traffic lights (synchronized for S and s).
        """
        if self.light_timer % self.light_cycle_duration == 0:
            for light in self.traffic_lights_S:
                light.state = True
            for light in self.traffic_lights_s:
                light.state = False
        elif self.light_timer % self.light_cycle_duration == self.light_cycle_duration // 2:
            for light in self.traffic_lights_S:
                light.state = False
            for light in self.traffic_lights_s:
                light.state = True
        self.light_timer += 1

    def step(self):
        """
        Advances the model by one step, toggles traffic lights, and spawns new cars.
        """
        self.step_count += 1
        self.toggle_traffic_lights()
        self.schedule.step()

        cars_spawned = self.try_spawn_car()

        if cars_spawned is not None and cars_spawned == []:
            self.running = False

        if not self.running:
            cars = [agent for agent in self.schedule.agents if isinstance(agent, Car)]
            for car in cars:
                self.grid.remove_agent(car)
                self.schedule.remove(car)
                self.in_grid -= 1

        self.datacollector.collect(self)
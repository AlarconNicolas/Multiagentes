from mesa import Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agent import *  # Ensure your agent classes are correctly defined in this module
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
        self.step_count = 0
        self.n = N

        # Initialize DataCollector
        self.datacollector = DataCollector(
            model_reporters={
                "Cars in Grid": lambda m: m.in_grid,
                "Cars Reached Destination": lambda m: m.reached_destination,
            }
        )

        # Load the map dictionary
        with open("../static/city_files/mapDictionary.json") as f:
            dataDictionary = json.load(f)

        self.traffic_lights_S = []
        self.traffic_lights_s = []
        self.destinations = []

        # Define arrow orientations
        self.arrow_orientations = {
            '>': (1, 0),    # Right
            '<': (-1, 0),   # Left
            '^': (0, 1),    # Up
            'v': (0, -1),   # Down
        }

        # Initialize an array to store traffic light directions
        # Each entry will be a dictionary with traffic light ID, position, and directions
        self.traffic_light_directions = []

        # Load the map file and create graph
        map_path = '../static/city_files/2024_base.txt'
        with open(map_path) as baseFile:
            lines = baseFile.readlines()
            self.width = len(lines[0].strip())
            self.height = len(lines)
            self.grid = MultiGrid(self.width, self.height, torus=False)
            self.schedule = RandomActivation(self)

            # Create basic grid structure
            for r, row in enumerate(lines):
                for c, col in enumerate(row.strip('\n')):
                    pos = (c, self.height - r - 1)  # Align Y-axis correctly
                    unique_id = f"{col}_{r*self.width + c}"
                    if col in self.arrow_orientations:
                        direction = tuple(self.arrow_orientations[col])
                        agent = Road(f"r_{r*self.width + c}", self, direction)
                        self.grid.place_agent(agent, pos)
                    elif col in ["S", "s"]:
                        is_horizontal = (col == "s")
                        agent = Traffic_Light(f"tl_{r*self.width + c}", self, is_horizontal=is_horizontal)
                        self.grid.place_agent(agent, pos)
                        self.schedule.add(agent)
                        if col == "S":
                            self.traffic_lights_S.append(agent)
                        else:
                            self.traffic_lights_s.append(agent)
                        
                        # Determine the directions this traffic light controls
                        directions = self.get_traffic_light_directions(col)
                        self.traffic_light_directions.append({
                            "id": agent.unique_id,
                            "position": pos,
                            "directions": directions
                        })
                    elif col == "#":
                        agent = Obstacle(f"ob_{r*self.width + c}", self)
                        self.grid.place_agent(agent, pos)
                    elif col == "D":
                        agent = Destination(f"d_{r*self.width + c}", self)
                        self.grid.place_agent(agent, pos)
                        self.destinations.append(pos)

        # Create the city navigation graph
        self.navigation_graph = self.create_city_graph(map_path)

        # Define corner positions for spawning cars
        self.corner_positions = [
            (0, 0),                          # Bottom-left corner
            (0, self.height - 1),            # Top-left corner
            (self.width - 1, 0),             # Bottom-right corner
            (self.width - 1, self.height - 1)  # Top-right corner
        ]

        self.car_id_counter = 0
        self.running = True
        self.light_timer = 0  
        self.light_cycle_duration = 7  

        print("Traffic Light Directions Array:")
        for tl_info in self.traffic_light_directions:
            print(f"ID: {tl_info['id']}, Position: {tl_info['position']}, Directions: {tl_info['directions']}")

    def get_traffic_light_directions(self, light_type):
        """
        Determines the controlled directions based on the traffic light type.
        'S' controls vertical (North-South) directions.
        's' controls horizontal (East-West) directions.
        """
        if light_type == "S":
            return ["North", "South"]
        elif light_type == "s":
            return ["East", "West"]
        else:
            return []

    def get_lateral_moves(self, direction):
        """Returns the lateral movement directions based on the forward direction."""
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
        For arrow cells, includes forward and lateral moves.
        For traffic lights, includes specified directions.
        """
        if cell_type in self.arrow_orientations:
            forward = self.arrow_orientations[cell_type]
            lateral_moves = self.get_lateral_moves(forward)
            return [forward] + lateral_moves
        elif cell_type == 's':
            # Horizontal traffic light allows left and right movement
            return [(-1, 0), (1, 0)]
        elif cell_type == 'S':
            # Vertical traffic light allows up and down movement
            return [(0, -1), (0, 1)]
        elif cell_type == 'D':
            # Destination cells can be entered from any direction but do not allow any exits
            return []
        else:
            return []

    def is_valid_movement(self, current_cell_type, next_cell_type, dx, dy):
        """
        Determines if movement from current_cell to next_cell in direction (dx, dy) is valid.
        - Movement is valid if:
            - current_cell allows movement in (dx, dy).
            - next_cell's arrow is not in contrary orientation to current_cell's arrow.
            - U-turns are not allowed.
        """
        if next_cell_type == '#':
            return False  # Can't move into an obstacle

        # Check if current cell allows movement in (dx, dy)
        allowed_moves = self.get_allowed_moves(current_cell_type)
        if (dx, dy) not in allowed_moves:
            return False  # Movement not allowed by current cell

        # Get arrow orientations of current cell and next cell
        current_orientation = self.arrow_orientations.get(current_cell_type)
        next_orientation = self.arrow_orientations.get(next_cell_type)

        if next_orientation:
            # If next cell has an arrow, check for contrary orientation
            if current_orientation and (current_orientation[0] == -next_orientation[0] and current_orientation[1] == -next_orientation[1]):
                return False  # Movement into a cell with contrary orientation is invalid

        # Prevent U-turns: Ensure that moving in the reverse direction is not allowed
        reverse_direction = (-dx, -dy)
        if current_orientation == reverse_direction:
            return False  # U-turns are not allowed

        return True  # Valid movement

    def create_city_graph(self, map_file_path):
        """
        Creates a directed graph representing the city layout based on the map file.
        Nodes represent cells, and edges represent valid movements.
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
            if cell == '#' or cell == 'D':
                continue  # Skip obstacles and destinations (no outgoing edges)

            # Possible movement directions from the current cell
            allowed_moves = self.get_allowed_moves(cell)

            for dx, dy in allowed_moves:
                next_pos = (pos[0] + dx, pos[1] + dy)
                if next_pos in cell_types:
                    next_cell = cell_types[next_pos]
                    if self.is_valid_movement(cell, next_cell, dx, dy):
                        city_graph.add_edge(pos, next_pos)

        return city_graph

    def find_path(self, start_pos, end_pos, avoid_traffic=True):
        """
        Finds the shortest path between two positions using Dijkstra's algorithm.
        Excludes corner positions and other destination cells from the path unless the start position is a corner.
        """
        try:
            # Start with all nodes in the navigation graph
            allowed_nodes = set(self.navigation_graph.nodes)

            # Exclude corner positions unless it's the start position
            if start_pos in self.corner_positions:
                allowed_nodes -= set(self.corner_positions)  # Remove all corners
                allowed_nodes.add(start_pos)  # Re-add the start corner
            else:
                allowed_nodes -= set(self.corner_positions)  # Remove all corners

            # Exclude all destination cells except the end_pos
            other_destinations = set(self.destinations) - {end_pos}
            allowed_nodes -= other_destinations  # Treat other destinations as obstacles

            # Create a subgraph with the allowed nodes
            temp_graph = self.navigation_graph.subgraph(allowed_nodes)

            if avoid_traffic:
                def weight(u, v, d):
                    """
                    Custom weight function for Dijkstra's algorithm.
                    Adds penalties for red traffic lights and blocked cells.
                    """
                    # Base weight
                    w = 1

                    # Check if the target position v is occupied by a Car or an Obstacle
                    cell_contents = self.grid.get_cell_list_contents([v])
                    if any(isinstance(agent, (Car, Obstacle)) for agent in cell_contents):
                        return float('inf')  # Block this edge

                    # Check if there's a traffic light at position v
                    for agent in cell_contents:
                        if isinstance(agent, Traffic_Light):
                            if not agent.state:
                                # Traffic light is red; add penalty
                                w += 10  # Penalty for red light

                    return w

                # Use Dijkstra's algorithm with the custom weight function on the temporary graph
                path = nx.dijkstra_path(temp_graph, start_pos, end_pos, weight=weight)
                return path
            else:
                # Use standard shortest path without weights
                path = nx.shortest_path(temp_graph, start_pos, end_pos)
                return path
        except nx.NetworkXNoPath:
            return None  # No path found

    def try_spawn_car(self):
        """
        Attempts to spawn up to 4 cars every step in designated spawn positions if available.
        Returns the number of cars spawned.
        """
        if self.step_count % 1 != 0:
            return None  # No spawn attempt this step

        # Find all available spawn positions (i.e., positions without a Car)
        available_positions = [
            pos for pos in self.corner_positions
            if not any(isinstance(agent, Car) for agent in self.grid.get_cell_list_contents([pos]))
        ]

        # Determine how many cars can be spawned (up to 4)
        cars_to_spawn = min(4, len(available_positions))
        spawned_cars = 0  # Counter for spawned cars

        # Spawn cars
        for i in range(cars_to_spawn):
            pos = available_positions[i]
            self.car_id_counter += 1
            destination = random.choice(self.destinations)
            car = Car(f"car_{self.car_id_counter}", self, destination)
            self.grid.place_agent(car, pos)
            self.schedule.add(car)
            self.in_grid += 1
            spawned_cars += 1  # Increment spawned cars count

        return spawned_cars

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
        self.step_count += 1  # Increment step counter
        self.schedule.step()

        # Toggle synchronized traffic lights
        self.toggle_traffic_lights()

        # Try spawning cars and capture the number spawned
        cars_spawned = self.try_spawn_car()

        if cars_spawned is not None:
            if cars_spawned <= 0:
                self.running = False

        # Collect data
        self.datacollector.collect(self)

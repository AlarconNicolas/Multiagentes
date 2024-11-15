from mesa import Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from agent import *
import json
import random
import networkx as nx

class CityModel(Model):
    """
    Creates a model based on a city map.
    Args:
        N: Number of agents in the simulation
    """
    def __init__(self, N):
        # Ensure the Model superclass is initialized
        super().__init__()
        self.reached_destination = 0  # Increment reached destination count
        self.in_grid = 0  # Decrease the count of cars in the grid
        self.datacollector = DataCollector(
            model_reporters={
                "Cars in Grid": lambda m: m.in_grid,
                "Cars Reached Destination": lambda m: m.reached_destination,
            }
        )
        
        # Load the map dictionary
        dataDictionary = json.load(open("../static/city_files/mapDictionary.json"))
        self.traffic_lights = []
        self.destinations = []  # List to store all destination agents
        
        # Load the map file and create graph
        map_path = '../static/city_files/2022_base.txt'
        with open(map_path) as baseFile:
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
                                
        # Create the navigation graph
        self.navigation_graph = self.create_city_graph(map_path)
        
        # Define edge corner positions
        edge_buffer = 2  # Number of positions to include from the edge
        corner_positions = [
            # Bottom-left corner
            (0, y) for y in range(edge_buffer)] + [
            # Top-left corner
            (0, y) for y in range(self.height - edge_buffer, self.height)] + [
            # Bottom-right corner
            (self.width - 1, y) for y in range(edge_buffer)] + [
            # Top-right corner
            (self.width - 1, y) for y in range(self.height - edge_buffer, self.height)]
        
        # Filter corner positions to only include valid road positions
        valid_corner_positions = [
            pos for pos in corner_positions
            if any(isinstance(agent, Road) for agent in self.grid.get_cell_list_contents([pos]))
        ]
        
        # Create a car agent with a random destination
        if self.destinations and valid_corner_positions:
            for i in range(N):
                car_destination = random.choice(self.destinations)
                start_pos = random.choice(valid_corner_positions)
                car = Car(f"car_{i+1}", self, car_destination)
                self.grid.place_agent(car, start_pos)
                self.schedule.add(car)
                self.in_grid += 1

        
        self.num_agents = N
        self.running = True

    def create_city_graph(self, map_file_path):
        """
        Creates a directed graph representation of the city where nodes are cell coordinates
        and edges represent possible movements between cells.
        """
        # Read the map file
        with open(map_file_path, 'r') as file:
            lines = file.readlines()
            height = len(lines)
            width = len(lines[0].strip())
            
        # Create a directed graph
        city_graph = nx.DiGraph()
        
        # Dictionary to store cell types for reference
        cell_types = {}
        
        # First pass: Store all cell types
        for y, line in enumerate(lines):
            for x, cell in enumerate(line.strip()):
                # Convert to grid coordinates (bottom-left origin)
                grid_y = height - y - 1
                cell_types[(x, grid_y)] = cell
                
        # Movement directions based on road type
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
        
        # Second pass: Create graph edges
        for y, line in enumerate(lines):
            for x, cell in enumerate(line.strip()):
                # Convert to grid coordinates (bottom-left origin)
                grid_y = height - y - 1
                current_pos = (x, grid_y)
                
                # Skip obstacles
                if cell == '#':
                    continue
                    
                # For each position, check possible movements based on cell type
                possible_moves = []
                
                # Handle road cells
                if cell in ['>', '<', '^', 'v']:
                    # Add movement in road direction
                    possible_moves.extend(directions[cell])
                    
                    # Add perpendicular movements based on road type
                    if cell in ['>', '<']:  # Horizontal road
                        possible_moves.extend([(0, 1), (0, -1)])  # Add up/down
                    elif cell in ['^', 'v']:  # Vertical road
                        possible_moves.extend([(1, 0), (-1, 0)])  # Add left/right
                        
                # Handle traffic lights
                elif cell in ['s', 'S']:
                    # For horizontal traffic lights
                    if cell == 's':
                        possible_moves.extend([(1, 0), (-1, 0)])  # Left/right
                    # For vertical traffic lights
                    else:  # cell == 'S'
                        possible_moves.extend([(0, 1), (0, -1)])  # Up/down
                        
                # Handle destinations
                elif cell == 'D':
                    # Destinations are endpoints, no outgoing edges needed
                    continue
                
                # Add edges to the graph for valid movements
                for dx, dy in possible_moves:
                    next_pos = (x + dx, grid_y + dy)
                    
                    # Check if the next position is within bounds
                    if (0 <= next_pos[0] < width and 
                        0 <= next_pos[1] < height and 
                        next_pos in cell_types):
                        
                        # Don't add edges to obstacles
                        if cell_types[next_pos] != '#':
                            city_graph.add_edge(current_pos, next_pos)
        
        return city_graph

    def get_valid_neighbors(self, current_pos):
        """
        Gets all valid neighboring positions that can be reached from the current position.
        
        Args:
            current_pos (tuple): Current position (x, y)
            
        Returns:
            list: List of valid neighbor positions (x, y)
        """
        return list(self.navigation_graph.neighbors(current_pos))

    def find_path(self, start_pos, end_pos):
        """
        Finds the shortest path between two positions in the city.
        
        Args:
            start_pos (tuple): Starting position (x, y)
            end_pos (tuple): Destination position (x, y)
            
        Returns:
            list: List of positions representing the path, or None if no path exists
        """
        try:
            return nx.shortest_path(self.navigation_graph, start_pos, end_pos)
        except nx.NetworkXNoPath:
            return None

    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.schedule.step()

    def get_next_move(self, current_pos, destination):
        """
        Gets the next move for an agent based on the shortest path to its destination.
        
        Args:
            current_pos (tuple): Current position (x, y)
            destination (tuple): Destination position (x, y)
            
        Returns:
            tuple: Next position to move to, or None if no path exists
        """
        path = self.find_path(current_pos, destination)
        if path and len(path) > 1:
            return path[1]  # Return the next position in the path
        return None
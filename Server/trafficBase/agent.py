# Imanol Santisteban 
# Nicolas Alarcón
# This code manages all of the agents and their qualitites and attributes
# 2024

from mesa import Agent
import random

# Define a palette of colors to randomly assign to cars for visualization
color_palette = ["red", "blue", "green", "orange", "purple", "yellow", "pink", "cyan"]

class Car(Agent):
    """
    Car agent representing vehicles in the simulation. Each car has a destination 
    and follows a calculated path while respecting traffic rules and avoiding obstacles.
    """

    def __init__(self, unique_id, model, destination):
        super().__init__(unique_id, model)
        self.destination = destination  # The target destination for the car
        self.current_path = None  # The path the car is currently following
        self.path_index = 0  # Tracks the car's position along the path
        self.stuck_counter = 0  # Counter to detect if the car is stuck
        self.direction = None  # Current movement direction of the car
        self.recalculate_path()  # Initial path calculation
        self.color = random.choice(color_palette)  # Assign a random color for visualization

    def recalculate_path(self):
        """
        Recalculates the shortest path to the destination using the model's pathfinding logic.
        Resets the path index and stuck counter.
        """
        if self.pos and self.destination:
            self.current_path = self.model.find_path(self.pos, self.destination, avoid_traffic=True)
            self.path_index = 0
            self.stuck_counter = 0

    def check_traffic_light(self, next_pos):
        """
        Checks if there is a traffic light at the next position and returns its state.
        Returns True if the light is green or if no light is present, False otherwise.
        """
        next_cell_contents = self.model.grid.get_cell_list_contents([next_pos])
        for agent in next_cell_contents:
            if isinstance(agent, Traffic_Light):
                return agent.state
        return True  # No traffic light means no restriction

    def check_for_obstacles(self, next_pos):
        """
        Checks if the next position is blocked by another car or an obstacle.
        Returns True if the position is clear, False otherwise.
        """
        next_cell_contents = self.model.grid.get_cell_list_contents([next_pos])
        for agent in next_cell_contents:
            if isinstance(agent, (Obstacle, Car)):  # Blocked by an obstacle or another car
                return False
        return True

    def get_next_position(self):
        """
        Retrieves the next position in the car's path.
        Returns None if the path is incomplete or the car is at its destination.
        """
        if not self.current_path or self.path_index >= len(self.current_path) - 1:
            return None
        return self.current_path[self.path_index + 1]

    def near_corner(self):
        """
        Checks if the car is near a corner cell and trying to move into it.
        Returns True if the car is near a corner and another car is blocking the corner.
        """
        for corner in self.model.corner_positions:
            next_pos = self.get_next_position()
            if next_pos == corner:
                if self.check_for_obstacles(next_pos):
                    continue  # Corner is clear
                else:
                    return True  # Corner is blocked
        return False

    def move(self):
        """
        Moves the car along its path, handling traffic lights, obstacles, and alternative routes.
        Recalculates the path if stuck for too long or avoids blocked cells when possible.
        """
        if self.near_corner():
            return  # Yield movement to avoid congestion near corners

        if self.pos == self.destination:
            # If the car reaches its destination, remove it from the grid and schedule
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.in_grid -= 1
            self.model.reached_destination += 1
            return

        next_pos = self.get_next_position()

        if not self.check_traffic_light(next_pos):
            self.stuck_counter += 1
            return  # Wait for the light to turn green

        if not next_pos or not self.check_for_obstacles(next_pos):
            self.stuck_counter += 1
            # Explore alternative cells if stuck
            neighborhood = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
            if self.stuck_counter == 1:
                current_cell_contents = self.model.grid.get_cell_list_contents([self.pos])
                current_cell_type = None

                # Identify the current cell's type
                for agent in current_cell_contents:
                    if isinstance(agent, Road):
                        current_cell_type = agent.direction

                for neighbor in neighborhood:
                    if not self.model.grid.out_of_bounds(neighbor):
                        neighbor_cell_contents = self.model.grid.get_cell_list_contents([neighbor])
                        neighbor_cell_type = None

                        # Check the neighbor cell's type
                        for agent in neighbor_cell_contents:
                            if isinstance(agent, Road):
                                neighbor_cell_type = agent.direction

                        # Attempt to move into a valid neighbor cell
                        if (current_cell_type and neighbor_cell_type and
                            self.model.valid_movement(current_cell_type, neighbor_cell_type,
                                                        neighbor[0] - self.pos[0], neighbor[1] - self.pos[1])):
                            if all(not isinstance(agent, (Car, Obstacle)) for agent in neighbor_cell_contents):
                                dx = neighbor[0] - self.pos[0]
                                dy = neighbor[1] - self.pos[1]
                                self.direction = (dx, dy)
                                self.model.grid.move_agent(self, neighbor)
                                self.stuck_counter = 0
                                self.recalculate_path()
                                return
            if self.stuck_counter == 3:  # Recalculate path if stuck for too long
                self.recalculate_path()
                self.stuck_counter = 0
            else:
                return
        else:
            # Move to the next position
            dx = next_pos[0] - self.pos[0]
            dy = next_pos[1] - self.pos[1]
            self.direction = (dx, dy)
            self.model.grid.move_agent(self, next_pos)
            self.path_index += 1
            self.stuck_counter = 0

    def step(self):
        """
        Executes the car's logic for a single simulation step.
        Recalculates its path if no valid path exists, then moves along the path.
        """
        if not self.current_path:
            self.recalculate_path()
            if not self.current_path:
                return
        self.move()


class Traffic_Light(Agent):
    """
    Traffic light agent, controlled by the model to toggle states.
    """
    def __init__(self, unique_id, model, is_horizontal=False):
        super().__init__(unique_id, model)
        self.state = False  # Default state: red
        self.is_horizontal = is_horizontal  # True for horizontal traffic lights, False for vertical
        self.facing_directions = []  # Unused, can represent the directions the light controls

    def step(self):
        pass  # Traffic lights are controlled by the CityModel


class Road(Agent):
    """
    Road agent defining the direction of traffic.
    """
    def __init__(self, unique_id, model, direction):
        super().__init__(unique_id, model)
        self.direction = direction  # The direction cars can move on this road

    def step(self):
        pass  # No independent behavior for roads


class Obstacle(Agent):
    """
    Obstacle agent representing a blocking element in the grid.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass  # Obstacles are static


class Destination(Agent):
    """
    Destination agent representing the target endpoint for cars.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        pass  # Destinations are static

from mesa import Agent
from collections import defaultdict

class Car(Agent):
    """
    Car agent that follows a calculated path to its destination while respecting traffic rules.
    """
    def __init__(self, unique_id, model, destination):
        super().__init__(unique_id, model)
        self.destination = destination
        self.current_path = None
        self.path_index = 0
        self.recalculate_path()

    def recalculate_path(self):
        """
        Calculates or recalculates the path to the destination.
        """
        if self.pos and self.destination:
            self.current_path = self.model.find_path(self.pos, self.destination)
            self.path_index = 0

    def check_traffic_light(self, next_pos):
        """
        Checks if there's a traffic light at the next position and returns its state.
        Returns True for green, False for red.
        """
        next_cell_contents = self.model.grid.get_cell_list_contents([next_pos])
        for agent in next_cell_contents:
            if isinstance(agent, Traffic_Light):
                return agent.state
        return True

    def check_for_obstacles(self, next_pos):
        """
        Checks if there are obstacles or other cars at the next position.
        Returns False if the position is blocked.
        """
        next_cell_contents = self.model.grid.get_cell_list_contents([next_pos])
        for agent in next_cell_contents:
            if isinstance(agent, (Obstacle, Car)):
                return False
        return True

    def get_next_position(self):
        """
        Gets the next position from the calculated path.
        Returns None if no valid next position is available.
        """
        if (not self.current_path or 
            self.path_index >= len(self.current_path) - 1):
            return None
            
        return self.current_path[self.path_index + 1]

    def move(self):
        """
        Moves the car along its calculated path while respecting traffic rules.
        """
        # Check if we've reached the destination
        if self.pos == self.destination:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.reached_destination += 1
            self.model.in_grid -= 1
            return

        # Get next position from path
        next_pos = self.get_next_position()
        if not next_pos:
            # If no next position, try to recalculate path
            self.recalculate_path()
            return

        # Check if next position is within grid bounds
        if (not (0 <= next_pos[0] < self.model.grid.width and
                0 <= next_pos[1] < self.model.grid.height)):
            self.recalculate_path()
            return

        # Check for obstacles and traffic lights
        if not self.check_for_obstacles(next_pos):
            # If blocked by obstacle/car, wait
            return

        if not self.check_traffic_light(next_pos):
            # If red light, wait
            return

        # Move to next position
        self.model.grid.move_agent(self, next_pos)
        self.path_index += 1

        # If we've completed the current path segment
        if self.path_index >= len(self.current_path) - 1:
            self.recalculate_path()

    def step(self):
        """
        Performs one step of the car's movement.
        """
        # If no path exists, try to calculate one
        if not self.current_path:
            self.recalculate_path()
            if not self.current_path:
                return

        self.move()

class Traffic_Light(Agent):
    """
    Traffic light agent that changes state (green or red) every few steps.
    """
    def __init__(self, unique_id, model, state=False, timeToChange=10):
        super().__init__(unique_id, model)
        self.state = state
        self.timeToChange = timeToChange
        
    def step(self):
        """
        Changes the state of the traffic light (green or red) after a certain number of steps.
        """
        if self.model.schedule.steps % self.timeToChange == 0:
            self.state = not self.state

class Road(Agent):
    """
    Road agent that determines the direction of traffic.
    """
    def __init__(self, unique_id, model, direction):
        super().__init__(unique_id, model)
        self.direction = direction
        
    def step(self):
        pass  # No specific behavior for roads in this case

class Obstacle(Agent):
    """
    Obstacle agent. Blocks cars from moving.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
    def step(self):
        pass  # No specific behavior for obstacles in this case

class Destination(Agent):
    """
    Destination agent. Represents the endpoint for the car to reach.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
    def step(self):
        pass  # No specific behavior for destination in this case
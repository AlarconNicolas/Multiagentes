from mesa import Agent
from collections import defaultdict

class Car(Agent):
    """
    Car agent that moves according to road rules, considering obstacles, traffic lights, and road directions.
    """
    def __init__(self, unique_id, model, destination):
        super().__init__(unique_id, model)
        self.direction = None
        self.last_direction = None 
        self.destination = destination

    def get_road_direction(self):
        """
        Gets the direction of the road the car is currently on.
        If no road is found, uses the last known direction.
        """
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        for agent in cell_contents:
            if isinstance(agent, Road):
                self.last_direction = agent.direction  # Update last direction
                return agent.direction
        return self.last_direction  # Return the last known direction if no road is found

    def check_traffic_light(self, next_pos):
        """
        Checks if there's a traffic light at the next position and returns its state (True for green, False for red).
        """
        next_cell_contents = self.model.grid.get_cell_list_contents([next_pos])
        for agent in next_cell_contents:
            if isinstance(agent, Traffic_Light):
                return agent.state  # True for green, False for red
        return True  # No traffic light, proceed as if green

    def check_for_obstacles(self, next_pos):
        """
        Checks if there are obstacles or other cars at the next position.
        Returns False if the car cannot move to the next position.
        """
        next_cell_contents = self.model.grid.get_cell_list_contents([next_pos])
        for agent in next_cell_contents:
            if isinstance(agent, (Obstacle, Car)):
                return False  # Cannot move if there's an obstacle or another car
        return True

    def move(self):
        """
        Moves the car according to road rules, considering traffic lights, obstacles, and road directions.
        """
        road_direction = self.get_road_direction()
        if road_direction is None:  # Return if no direction is available
            return
        
        direction_to_move = {
            "Up": (0, 1),
            "Down": (0, -1),
            "Left": (-1, 0),
            "Right": (1, 0),
            "^": (0, 1),
            "v": (0, -1),
            "<": (-1, 0),
            ">": (1, 0)
        }

        # Get the movement vector based on road direction
        movement = direction_to_move.get(road_direction)
        if movement:
            next_pos = (self.pos[0] + movement[0], self.pos[1] + movement[1])
            
            # Check if next position is within grid bounds
            if (0 <= next_pos[0] < self.model.grid.width and
                0 <= next_pos[1] < self.model.grid.height):
                
                # Check for obstacles
                if not self.check_for_obstacles(next_pos):
                    return  # If there's an obstacle, do not move
                
                # Check traffic light state
                if not self.check_traffic_light(next_pos):
                    return  # If the light is red, do not move
                
                # Move if there is a road or traffic light at the next position
                next_cell_contents = self.model.grid.get_cell_list_contents([next_pos])
                if any(isinstance(agent, (Road, Traffic_Light)) for agent in next_cell_contents):
                    self.model.grid.move_agent(self, next_pos)

    def step(self):
        """
        Determines the new direction and moves the car.
        """
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
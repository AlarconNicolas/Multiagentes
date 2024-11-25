from mesa import Agent

class Car(Agent):
    """
    Car agent that follows a calculated path to its destination while respecting traffic rules.
    Includes lane-changing behavior to avoid traffic and ensures valid lane changes considering road direction.
    """
    def __init__(self, unique_id, model, destination):
        super().__init__(unique_id, model)
        self.destination = destination
        self.current_path = None
        self.path_index = 0
        self.stuck_counter = 0  # Counter to track if the car is stuck
        self.recalculate_path()

    def recalculate_path(self):
        """
        Recalculates the path to the destination, adding random penalties to encourage route diversity.
        """
        if self.pos and self.destination:
            # Use a weighted pathfinding function with traffic-based penalties
            self.current_path = self.model.find_path(self.pos, self.destination, avoid_traffic=True)
            self.path_index = 0
            self.stuck_counter = 0  # Reset stuck counter

    def check_traffic_light(self, next_pos):
        """
        Checks if there's a traffic light at the next position and returns its state.
        Returns True for green, False for red.
        """
        next_cell_contents = self.model.grid.get_cell_list_contents([next_pos])
        for agent in next_cell_contents:
            if isinstance(agent, Traffic_Light):
                return agent.state
        return True  # If no traffic light, proceed

    def check_for_obstacles(self, next_pos):
        """
        Checks if there are obstacles or other cars at the next position.
        Returns False if the position is blocked.
        """
        next_cell_contents = self.model.grid.get_cell_list_contents([next_pos])
        for agent in next_cell_contents:
            if isinstance(agent, (Obstacle, Car)):  # Obstacle or another car
                return False
        return True

    def get_next_position(self):
        """
        Gets the next position from the calculated path.
        Returns None if no valid next position is available.
        """
        if (not self.current_path or 
            self.path_index >= len(self.current_path) - 1):
            return None  # No next position
        return self.current_path[self.path_index + 1]

    def get_current_road(self):
        """
        Gets the road agent at the car's current position.
        """
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        for agent in cell_contents:
            if isinstance(agent, Road):
                return agent
        return None

    def change_lane(self):
        """
        Attempts to change lanes if the car is stuck.
        Checks adjacent cells based on the current road direction.
        """
        current_road = self.get_current_road()
        if not current_road:
            return  # Can't find road at current position

        direction = current_road.direction

        # Define side offsets based on direction
        side_offsets = {
            'N': [(-1, 0), (1, 0)],  # Left: west, Right: east
            'S': [(1, 0), (-1, 0)],  # Left: east, Right: west
            'E': [(0, -1), (0, 1)],  # Left: north, Right: south
            'W': [(0, 1), (0, -1)]   # Left: south, Right: north
        }

        if direction not in side_offsets:
            return  # Unknown direction

        for offset in side_offsets[direction]:
            new_pos = (self.pos[0] + offset[0], self.pos[1] + offset[1])
            # Check if new_pos is within the grid bounds
            if not self.model.grid.out_of_bounds(new_pos):
                # Check if there is a road at new_pos
                cell_contents = self.model.grid.get_cell_list_contents([new_pos])
                road_found = False
                for agent in cell_contents:
                    if isinstance(agent, Road):
                        road_found = True
                        new_road = agent
                        break
                if road_found:
                    # Check if the new position is free of obstacles
                    if self.check_for_obstacles(new_pos):
                        # Move the car to the new position
                        self.model.grid.move_agent(self, new_pos)
                        self.stuck_counter = 0
                        self.recalculate_path()
                        return  # Successfully changed lanes

    def move(self):
        """
        Moves the car along its calculated path while respecting traffic rules.
        Includes periodic path recalculation to avoid congestion.
        """
        if self.pos == self.destination:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.in_grid -= 1
            return

        next_pos = self.get_next_position()
        if not next_pos or not self.check_for_obstacles(next_pos):
            self.stuck_counter += 1
            if self.stuck_counter >= 3:  # Threshold for being stuck
                self.change_lane()
            else:
                return
        elif not self.check_traffic_light(next_pos):
            # Can't move due to red light
            self.stuck_counter += 1
            if self.stuck_counter >= 3:
                self.change_lane()
            else:
                return
        else:
            # Move to the next position
            self.model.grid.move_agent(self, next_pos)
            self.path_index += 1
            self.stuck_counter = 0

        # Recalculate path every 5 steps for diversity
        if self.model.schedule.steps % 5 == 0:
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
    Traffic light agent controlled by the model's synchronized mechanism.
    """
    def __init__(self, unique_id, model, is_horizontal=False):
        super().__init__(unique_id, model)
        self.state = False  # Default to red
        self.is_horizontal = is_horizontal  # True for horizontal (s), False for vertical (S)

    def step(self):
        pass  # Behavior controlled by CityModel

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
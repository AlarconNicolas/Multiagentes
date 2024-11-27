from mesa import Agent

class Car(Agent):
    """
    Car agent that follows a calculated path to its destination while respecting traffic rules.
    Includes lane-changing behavior to avoid traffic and ensures valid lane changes considering road direction.
    Now includes refined courtesy behavior to yield only when approaching corner cells.
    """
    def __init__(self, unique_id, model, destination):
        super().__init__(unique_id, model)
        self.destination = destination
        self.current_path = None
        self.path_index = 0
        self.stuck_counter = 0  # Counter to track if the car is stuck
        self.direction = None  # Current movement direction
        self.recalculate_path()

    def recalculate_path(self):
        """
        Recalculates the path to the destination.
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

    def near_corner(self):
        """
        Checks if the car is adjacent to any corner cell and is attempting to move into it.
        Returns True if both conditions are met, else False.
        """
        # Get all corner positions from the model
        for corner in self.model.corner_positions:
            # Check if the next position is the corner
            next_pos = self.get_next_position()
            if next_pos == corner:
                # Check if the car is attempting to move into the corner
                if self.check_for_obstacles(next_pos):
                    # There's space to move into the corner (should not yield)
                    continue
                else:
                    # If there's a car already in the corner, yield
                    return True
        return False

    def find_alternative_move(self):
        """
        Tries to find an alternative valid move to adjacent cells without moving backward.
        Returns True if a move was made, False otherwise.
        """
        if not self.direction:
            # If direction is undefined, cannot determine forward movement
            return False

        # Define backward direction
        backward_direction = (-self.direction[0], -self.direction[1])

        # Get all possible adjacent positions (non-diagonal moves)
        adjacent_positions = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )

        # Prioritize forward movement and lane changes
        for pos in adjacent_positions:
            if not self.model.grid.out_of_bounds(pos):
                # Check if there is a road at pos
                cell_contents = self.model.grid.get_cell_list_contents([pos])
                road_found = False
                road_direction = None
                for agent in cell_contents:
                    if isinstance(agent, Road):
                        road_found = True
                        road_direction = agent.direction
                        break
                if road_found and self.check_for_obstacles(pos):
                    # Calculate the movement direction
                    dx = pos[0] - self.pos[0]
                    dy = pos[1] - self.pos[1]
                    move_direction = (dx, dy)

                    # Prevent backward movement
                    if move_direction == backward_direction:
                        continue  # Skip backward moves

                    # Optionally, ensure that the move aligns with the road's direction
                    if road_direction and move_direction != road_direction:
                        # Allow lane changes (perpendicular to road direction)
                        # For example, if road_direction is (1,0) or (-1,0), allow (0,1) or (0,-1)
                        if not ((road_direction[0] != 0 and move_direction[0] != 0) or 
                                (road_direction[1] != 0 and move_direction[1] != 0)):
                            pass  # Valid lane change
                        else:
                            continue  # Invalid movement direction

                    # Check if a path exists from pos to the destination
                    potential_path = self.model.find_path(pos, self.destination, avoid_traffic=True)
                    if potential_path:
                        # Move the car to the new position
                        self.model.grid.move_agent(self, pos)
                        self.stuck_counter = 0
                        self.current_path = potential_path
                        self.path_index = 0
                        # Update direction
                        self.direction = move_direction
                        return True  # Successfully moved
        return False  # No valid move found

    def move(self):
        """
        Moves the car along its calculated path while respecting traffic rules.
        Includes periodic path recalculation to avoid congestion and refined courtesy behavior.
        """
        # Refined Courtesy Behavior: Yield only if approaching a corner cell and a car is present in the corner
        if self.near_corner():
            return  # Yield movement to allow the newly spawned car to enter

        if self.pos == self.destination:
            # Car has reached its destination
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            self.model.in_grid -= 1
            self.model.reached_destination += 1
            return

        next_pos = self.get_next_position()
        if not next_pos or not self.check_for_obstacles(next_pos):
            # Next position is blocked or no path available
            self.stuck_counter += 1
            if self.stuck_counter >= 3:  # Threshold for being stuck
                if not self.find_alternative_move():
                    # If can't find alternative move, recalculate path
                    self.recalculate_path()
                    self.stuck_counter = 0
                else:
                    # Successfully moved to a new position
                    return
            else:
                return
        elif not self.check_traffic_light(next_pos):
            # Can't move due to red light
            self.stuck_counter += 1
            if self.stuck_counter >= 3:
                if not self.find_alternative_move():
                    # If can't find alternative move, recalculate path
                    self.recalculate_path()
                    self.stuck_counter = 0
                else:
                    # Successfully moved to a new position
                    return
            else:
                return
        else:
            # Determine the direction of movement
            dx = next_pos[0] - self.pos[0]
            dy = next_pos[1] - self.pos[1]
            self.direction = (dx, dy)
            
            # Move to the next position
            self.model.grid.move_agent(self, next_pos)
            self.path_index += 1
            self.stuck_counter = 0

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

# TC2008B. Sistemas Multiagentes y Gráficas Computacionales
# Python Flask server to interact with WebGL.
# Octavio Navarro. 2024

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from trafficBase.model import CityModel
from trafficBase.agent import Car, Traffic_Light, Obstacle

# Size of the board:
width = 28
height = 28
number_agents = 10
randomModel = None
currentStep = 0

# Flask app setup
app = Flask("Traffic Example")
cors = CORS(app, origins=['http://localhost'])

@app.route('/init', methods=['POST'])
@cross_origin()
def initModel():
    """Initialize the CityModel with parameters from the client."""
    global currentStep, randomModel, number_agents

    if request.method == 'POST':
        try:
            number_agents = int(request.json.get('NAgents'))
            currentStep = 0

            print(request.json)
            print(f"Model parameters: {number_agents}")

            # Initialize the model
            randomModel = CityModel(number_agents)
            if randomModel is None:
                print("MODEL NOT STARTED")
            elif randomModel is not None:
                print("MODEL STARTED CORRECTLY")
            return jsonify({"message": "Parametersss received, model initialized."})

        except Exception as e:
            print(e)
            return jsonify({"message": "Error initializing the model"}), 500

@app.route('/getAgents', methods=['GET'])
@cross_origin()
def getAgents():
    """Retrieve the positions of all cars in the model."""
    global randomModel

    if request.method == 'GET':
        print("REQUEST METHOD ACCEPTED")
        try:
            if randomModel and not any(isinstance(a, Car) for a, p in randomModel.grid.coord_iter()):
                test_car = Car("debug_car", randomModel, None)
                randomModel.grid.place_agent(test_car, (0, 0))
                randomModel.schedule.add(test_car)
                print("Manually placed a debug car at (0,0)")
            test_position=(0,0)
            placed_agent = randomModel.grid.get_cell_list_contents(test_position)[0]
            
            if test_car in randomModel.grid.get_cell_list_contents(test_position):
                print("Debug car successfully placed in the grid at", test_position)
            else:
                print("Debug car not found in the grid at", test_position)

            
            agentPositions = [
                {"id": a.unique_id, "x": pos[0], "y": 1, "z": 1}
                for a, pos in randomModel.grid.coord_iter()
                if isinstance(a, Car)
            ]
            car_instances = [
            (agent, pos) for agent, pos in randomModel.grid.coord_iter() if isinstance(agent, Car)
            ]
            if car_instances:
                print(f"Found {len(car_instances)} car instances in the map.")
            else:
                print("No car instances found in the map.")
            print("Agent Locations:", agentPositions)

            return jsonify({'positions': agentPositions})

        except Exception as e:
            print(e)
            return jsonify({"message": "Error retrieving agent positions"}), 500

@app.route('/getObstacles', methods=['GET'])
@cross_origin()
def getObstacles():
    """Retrieve the positions of all obstacles in the model."""
    global randomModel

    if request.method == 'GET':
        try:
            obstaclePositions = [
                {"id": a.unique_id, "x": pos[0], "y": 1, "z": pos[1]}
                for a, pos in randomModel.grid.coord_iter()
                if isinstance(a, Obstacle)
            ]
            return jsonify({'positions': obstaclePositions})

        except Exception as e:
            print(e)
            return jsonify({"message": "Error retrieving obstacle positions"}), 500

@app.route('/getLights', methods=['GET'])
@cross_origin()
def getLights():
    """Retrieve the positions and states of all traffic lights."""
    global randomModel

    if request.method == 'GET':
        try:
            lightPositions = [
                {"id": a.unique_id, "x": pos[0], "y": 1, "z": pos[1], "state": a.state}
                for a, pos in randomModel.grid.coord_iter()
                if isinstance(a, Traffic_Light)
            ]
            print("Light Locations:", lightPositions)
            return jsonify({'positions': lightPositions})

        except Exception as e:
            print(e)
            return jsonify({"message": "Error retrieving traffic light positions"}), 500

@app.route('/update', methods=['GET'])
@cross_origin()
def updateModel():
    """Advance the model by one step."""
    global currentStep, randomModel

    if request.method == 'GET':
        try:
            randomModel.step()
            currentStep += 1
            return jsonify({'message': f'Model updated to step {currentStep}.', 'currentStep': currentStep})

        except Exception as e:
            print(e)
            return jsonify({"message": "Error during model update."}), 500

if __name__ == '__main__':
    # Run the Flask server on port 8585
    app.run(host="localhost", port=8585, debug=True)

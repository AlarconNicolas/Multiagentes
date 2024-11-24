# TC2008B. Sistemas Multiagentes y Gráficas Computacionales
# Python Flask server to interact with WebGL.
# Octavio Navarro. 2024

from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from trafficBase.model import CityModel
from trafficBase.agent import Car, Traffic_Light, Obstacle,Road

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
        try:
            if not randomModel:
                return jsonify({"message": "Model not initialized"}), 400

            # Get car positions from the schedule instead
            car_positions = []
            for agents, pos in randomModel.grid.coord_iter():
            # for agent in randomModel.schedule.agents:
                for agent in agents:
                    if isinstance(agent, Car):
                        car_positions.append({
                            "id": agent.unique_id,
                            "x": agent.pos[0],
                            "y": 1,
                            "z": agent.pos[1]  # Using y coordinate as z for 3D
                        })
            
            print(f"Found {len(car_positions)} cars")
            for pos in car_positions:
                print(f"Car {pos['id']} at position ({pos['x']}, {pos['z']})")
                
            return jsonify({'positions': car_positions})

        except Exception as e:
            print(f"Error in getAgents: {str(e)}")
            return jsonify({"message": f"Error retrieving agent positions: {str(e)}"}), 500

@app.route('/getBuildings', methods=['GET'])
@cross_origin()
def getBuildings():
    """Retrieve the positions of all cars in the model."""
    global randomModel

    if request.method == 'GET':
        try:
            if not randomModel:
                return jsonify({"message": "Model not initialized"}), 400

            # Get car positions from the schedule instead
            obstacles_positions = []
            for agents, pos in randomModel.grid.coord_iter():
            # for agent in randomModel.schedule.agents:
                for agent in agents:
                    if isinstance(agent, Obstacle):
                        obstacles_positions.append({
                            "id": agent.unique_id,
                            "x": agent.pos[0],
                            "y": 1,
                            "z": agent.pos[1]  # Using y coordinate as z for 3D
                        })
            
            print(f"Found {len(obstacles_positions)} obstacles")
            for pos in obstacles_positions:
                print(f"Obstacle {pos['id']} at position ({pos['x']}, {pos['z']})")
                
            return jsonify({'positions': obstacles_positions})

        except Exception as e:
            print(f"Error in getObstacles: {str(e)}")
            return jsonify({"message": f"Error retrieving obstacles positions: {str(e)}"}), 500

@app.route('/getLights', methods=['GET'])
@cross_origin()
def getLights():
    """Retrieve the positions and states of all traffic lights."""
    global randomModel

    if request.method == 'GET':
        try:
            if not randomModel:
                return jsonify({"message": "Model not initialized"}), 400

            # Get car positions from the schedule instead
            light_positions = []
            for agent in randomModel.schedule.agents:
                if isinstance(agent, Traffic_Light):
                    light_positions.append({
                        "id": agent.unique_id,
                        "x": agent.pos[0],
                        "y": 2,
                        "z": agent.pos[1]  # Using y coordinate as z for 3D
                    })
            
            print(f"Found {len(light_positions)} Lights")
            for pos in light_positions:
                print(f"Light {pos['id']} at position ({pos['x']}, {pos['z']})")
                
            return jsonify({'positions': light_positions})

        except Exception as e:
            print(f"Error in getAgents: {str(e)}")
            return jsonify({"message": f"Error retrieving agent positions: {str(e)}"}), 500
        

@app.route('/getRoads', methods=['GET'])
@cross_origin()
def getRoads():
    """Retrieve the positions of all cars in the model."""
    global randomModel

    if request.method == 'GET':
        try:
            if not randomModel:
                return jsonify({"message": "Model not initialized"}), 400

            # Get car positions from the schedule instead
            Roads_positions = []
            for agents, pos in randomModel.grid.coord_iter():
            # for agent in randomModel.schedule.agents:
                for agent in agents:
                    if isinstance(agent,Road ) or isinstance(agent,Traffic_Light ) :
                        Roads_positions.append({
                            "id": agent.unique_id,
                            "x": agent.pos[0],
                            "y": 1,
                            "z": agent.pos[1]  # Using y coordinate as z for 3D
                        })
            
            print(f"Found {len(Roads_positions)} Roads")
            for pos in Roads_positions:
                print(f"Roads {pos['id']} at position ({pos['x']}, {pos['z']})")
                
            return jsonify({'positions': Roads_positions})

        except Exception as e:
            print(f"Error in getObstacles: {str(e)}")
            return jsonify({"message": f"Error retrieving obstacles positions: {str(e)}"}), 500

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

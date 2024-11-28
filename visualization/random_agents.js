'use strict';

import * as twgl from 'twgl.js';
import GUI from 'lil-gui';
import { typeOf } from 'mathjs';
import vsGLSL from './shaders/vs_phong.glsl?raw';
import fsGLSL from './shaders/fs_phong.glsl?raw';
// Define the vertex shader code, using GLSL 3.00

// Define the Building3D class to represent 3D objcetsCar
class Building3D {
  constructor(id, position=[0,0,0], rotation=[0,0,0], scale=[0.5,0.5,0.5]){
  this.id = id;
  this.position = position;
  this.rotation = rotation;
  this.scale = scale;
  this.matrix = twgl.m4.create();
  }
}
class Agent3D {
  constructor(id, position = [0, 0, 0], rotation = [0, 0, 0], scale = [1, 1, 1]) {
    this.id = id;
    this.position = position;
    this.currentPosition = [...position];      // Current interpolated position
    this.previousPosition = [...position];     // Position at last server update
    this.targetPosition = [...position];       // New position from server
    this.rotation = rotation;
    this.scale = scale;
    this.matrix = twgl.m4.create();
    this.heading = 0;
    this.isAtDestination = false;
    this.lastUpdateTime = performance.now();
    this.updateInterval = 100; // Time between updates in ms
  }
}

class TrafficLight3D {
  constructor(id, position=[1,1,3],state, rotation=[0,0,0], scale=[0.2,0.2,0.2]){
  this.id = id;
  this.position = position;
  this.rotation = rotation;
  this.scale = scale;
  this.matrix = twgl.m4.create();
  this.state = state
  }
}
class Road3D {
  constructor(id, position=[1,1,3],direction, rotation=[0,0,0], scale=[0.3,0.5,0.7]){
  this.id = id;
  this.position = position;
  this.rotation = rotation;
  this.scale = scale;
  this.matrix = twgl.m4.create();
  this.direction=direction;
  }
}


// Define the agent server URI
const agent_server_uri = "http://localhost:8585/";

// Initialize arrays to store agents and obstacles
const agents = [];
const Buildings = [];
const traficLights= [];
const Roads=[];
const Destinations=[];
const MAX_LIGHTS = 24;

const updateInterval = 100; // milliseconds
let lastUpdateTime = performance.now();
// Initialize WebGL-related variables
let gl, programInfo, agentArrays, agentsBufferInfo, agentsVao, BuildingVAO,Building2Buffer, Building2VAO,wheelVAO,wheelBufferInfo,TrafficLightArrays,TrafficLightBuffer,TrafficLightVAO,BuildingBuffer,RoadBuffer,RoadVAO,SubterraBuffer,SubterraVAO;

// Define the camera position
let cameraPosition = {x:0, y:9, z:9};
let numberofcars=0;
// Initialize the frame count
let frameCount = 0;
const data = {
  NAgents: 50,
  width: 29,
  height: 30
};
const lighting = {
  ambientLight: [0.2, 0.2, 0.2, 1.0],    // Ambient light color
  diffuseLight: [1.0, 1.0, 1.0, 1.0],    // Diffuse light color (white)
  specularLight: [1.0, 1.0, 1.0, 1.0],   // Specular light color (white)
  
  ambientColor: [1.0, 1.0, 1.0, 1.0],    // Material ambient color
  diffuseColor: [0.6, 0.6, 0.6, 1.0],    // Material diffuse color
  specularColor: [1.0, 1.0, 1.0, 1.0],   // Material specular color
  shininess: 32.0,                        // Material shininess
  
  lightWorldDirection: [0.5, 1.0, 0.5], // Directional light direction
  viewWorldPosition: [cameraPosition.x + data.width/2, cameraPosition.y, cameraPosition.z + data.height/2], // Camera position
  
  numTrafficLights: 0,
  trafficLightPositions: new Float32Array(MAX_LIGHTS * 3),
  trafficLightColors: new Float32Array(MAX_LIGHTS * 3),
  trafficLightDirections: new Float32Array(MAX_LIGHTS * 3),
  trafficLightCutoffs: new Float32Array(MAX_LIGHTS),
};

// Define the data object
const objcetsCar= {
  model: {
      transforms: {
          // Translation
          t: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in degrees
          rd: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in radians
          rr: {
              x: 0,
              y: 0,
              z: 0},
          // Scale
          s: {
              x: 1,
              y: 1,
              z: 1},
      },
      arrays: undefined,
      bufferInfo: undefined,
      vao: undefined,
  }
}
const objcetsTrafficLight = {
  model: {
      transforms: {
          // Translation
          t: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in degrees
          rd: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in radians
          rr: {
              x: 0,
              y: 0,
              z: 0},
          // Scale
          s: {
              x: 1,
              y: 1,
              z: 1},
      },
      arrays: undefined,
      bufferInfo: undefined,
      vao: undefined,
  }
}
const objcetsBuilding= {
  model: {
      transforms: {
          // Translation
          t: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in degrees
          rd: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in radians
          rr: {
              x: 0,
              y: 0,
              z: 0},
          // Scale
          s: {
              x: 1,
              y: 1,
              z: 1},
      },
      arrays: undefined,
      bufferInfo: undefined,
      vao: undefined,
  }
}
const objcetsBuilding2= {
  model: {
      transforms: {
          // Translation
          t: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in degrees
          rd: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in radians
          rr: {
              x: 0,
              y: 0,
              z: 0},
          // Scale
          s: {
              x: 1,
              y: 1,
              z: 1},
      },
      arrays: undefined,
      bufferInfo: undefined,
      vao: undefined,
  }
}
const objcetsRoads= {
  model: {
      transforms: {
          // Translation
          t: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in degrees
          rd: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in radians
          rr: {
              x: 0,
              y: 0,
              z: 0},
          // Scale
          s: {
              x: 1,
              y: 1,
              z: 1},
      },
      arrays: undefined,
      bufferInfo: undefined,
      vao: undefined,
  }
}
const objcetsRoads1= {
  model: {
      transforms: {
          // Translation
          t: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in degrees
          rd: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in radians
          rr: {
              x: 0,
              y: 0,
              z: 0},
          // Scale
          s: {
              x: 1,
              y: -1,
              z: 1},
      },
      arrays: undefined,
      bufferInfo: undefined,
      vao: undefined,
  }
}
const objectsZeppeling= {
  model: {
      transforms: {
          // Translation
          t: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in degrees
          rd: {
              x: 0,
              y: 0,
              z: 0},
          // Rotation in radians
          rr: {
              x: 0,
              y: 0,
              z: 0},
          // Scale
          s: {
              x: 1,
              y: -1,
              z: 1},
      },
      arrays: undefined,
      bufferInfo: undefined,
      vao: undefined,
  }
}
// Main function to initialize and run the application
async function main() {
  const canvas = document.querySelector('canvas');
  gl = canvas.getContext('webgl2');
  
  programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);
  

  //const newTrafficLight = new TrafficLight3D('trafficLight', [5, 0, 3]);
  //traficLights.push(newTrafficLight);

  const obj1 = await loadObj('./Figures/coche.obj',true,"Car");
  objcetsCar.model.arrays = obj1;

  const obj2 = await loadObj('./Figures/Semaforo2.obj',false,"TrafficLight");
  objcetsTrafficLight.model.arrays = obj2;

  const obj3 = await loadObj('./Figures/Building.obj',false,"Building");
  objcetsBuilding.model.arrays = obj3;

  const obj4 = await loadObj('./Figures/Building2.obj',false,"Building");
  objcetsBuilding2.model.arrays = obj4;

  const obj5 = await loadObj('./Figures/Road3.obj',false,"Road");
  objcetsRoads.model.arrays = obj5;
  
  const obj6 = await loadObj('./Figures/Subterra2.obj',false,"Road");
  objcetsRoads1.model.arrays = obj6;

  const obj7 = await loadObj('./Figures/Zeppeling.obj',false,"Road");
  objectsZeppeling.model.arrays = obj7;
  
  console.log("LightArray",objcetsTrafficLight.model.arrays )
  console.log("Car ARRAY:", objcetsCar.model.arrays);
  console.log("Building ARRAY:", objcetsBuilding.model.arrays);
  console.log("Road ARRAY:", objcetsRoads.model.arrays);
  
  //agentArrays = generateData(1);
  //obstacleArrays = generateObstacleData(1);
  
  // Create buffer infos
  //agentsBufferInfo = twgl.createBufferInfoFromArrays(gl, agentArrays);
  wheelBufferInfo = twgl.createBufferInfoFromArrays(gl, objcetsCar.model.arrays);
  TrafficLightBuffer = twgl.createBufferInfoFromArrays(gl, objcetsTrafficLight.model.arrays);
  BuildingBuffer = twgl.createBufferInfoFromArrays(gl, objcetsBuilding.model.arrays);
  Building2Buffer = twgl.createBufferInfoFromArrays(gl, objcetsBuilding2.model.arrays);
  RoadBuffer = twgl.createBufferInfoFromArrays(gl, objcetsRoads.model.arrays);
  SubterraBuffer = twgl.createBufferInfoFromArrays(gl, objcetsRoads1.model.arrays);
  //BuildingBuffer = twgl.createBufferInfoFromArrays(gl, obstacleArrays);
  
  // Create VAOs
  //agentsVao = twgl.createVAOFromBufferInfo(gl, programInfo, agentsBufferInfo);
  wheelVAO = twgl.createVAOFromBufferInfo(gl, programInfo, wheelBufferInfo);
  TrafficLightVAO = twgl.createVAOFromBufferInfo(gl, programInfo, TrafficLightBuffer);
  BuildingVAO = twgl.createVAOFromBufferInfo(gl, programInfo, BuildingBuffer);
  Building2VAO = twgl.createVAOFromBufferInfo(gl, programInfo, Building2Buffer);
  RoadVAO = twgl.createVAOFromBufferInfo(gl, programInfo, RoadBuffer);
  SubterraVAO = twgl.createVAOFromBufferInfo(gl, programInfo, SubterraBuffer);
  //BuildingVAO = twgl.createVAOFromBufferInfo(gl, programInfo, BuildingBuffer);
  
  setupUI();
  await initAgentsModel();
  await getLights();
  await getAgents();
  await getBuildings();
  await getRoads();
  await getDestinations();

  setLightingUniforms();
  // Pass parameters in the correct order
  await drawScene(gl, programInfo, wheelBufferInfo, wheelVAO, BuildingVAO, BuildingBuffer, TrafficLightBuffer, TrafficLightVAO,RoadVAO,RoadBuffer,SubterraVAO,SubterraBuffer);
}


/*
 * Initializes the agents model by sending a POST request to the agent server.
 */
async function initAgentsModel() {
  try {
    // Send a POST request to the agent server to initialize the model
    let response = await fetch(agent_server_uri + "init", {
      method: 'POST', 
      headers: { 'Content-Type':'application/json' },
      body: JSON.stringify(data)
    })

    // Check if the response was successful
    if(response.ok){
      // Parse the response as JSON and log the message
      let result = await response.json()
      console.log(result.message)
    }
      
  } catch (error) {
    console.log("model was not created correctlly")
    // Log any errors that occur during the request
    console.log(error)    
  }
}

/*
 * Retrieves the current positions of all agents from the agent server.
 */
async function getAgents() {
  try {
    let response = await fetch(agent_server_uri + "getAgents");
    if (response.ok) {
      let result = await response.json();

      for (const agentData of result.positions) {
        let agent = agents.find(a => a.id === agentData.id);

        if (agent) {
          // Update existing agent
          if (!agent.currentPosition) {
            agent.currentPosition = [...agent.previousPosition];
          }
          agent.previousPosition = [...agent.currentPosition];
          agent.targetPosition = [agentData.x, agentData.y, agentData.z];
          agent.lastUpdateTime = performance.now();
        } else {
          // Add new agent
          const newAgent = new Agent3D(agentData.id, [agentData.x, agentData.y, agentData.z]);
          agents.push(newAgent);
        }
      }
    }
  } catch (error) {
    console.log("Error fetching agents:", error);
  }
}





async function getLights() {
  try {
    let response = await fetch(agent_server_uri + "getLights");
    if (response.ok) {
      let result = await response.json();
      console.log("Light positions obtained")
      let positions = result.positions || result['Light positions']; // Check the correct key from JSON response

      console.log("Traffic light positions:", positions);

      if (traficLights.length === 0) {
        for (const light of positions) {
          const newLight = new TrafficLight3D(light.id, [light.x, light.y, light.z],light.state);
          traficLights.push(newLight);
        }
      } else {
        for (const light of positions) {
          const existingLight = traficLights.find(t => t.id === light.id);
          if (existingLight) {
            existingLight.position = [light.x, light.y, light.z];
            existingLight.state = light.state;
            console.log("NEW LIGHT STATE:", existingLight.state)
          }
        }
      }

      console.log("Updated traffic lights:", traficLights);
    }
  } catch (error) {
    console.error("Error fetching traffic lights:", error);
  }
}


/*
 * Retrieves the current positions of all obstacles from the agent server.
 */
async function getBuildings() {
  try {
    let response = await fetch(agent_server_uri + "getBuildings");
    if (response.ok) {
      let result = await response.json();
      for (const obstacle of result.positions) {
        const newObstacle = new Building3D(obstacle.id, [obstacle.x, obstacle.y, obstacle.z]);
        // Assign a random model index (1 or 2)
        newObstacle.modelIndex = Math.random() < 0.5 ? 1 : 2;
        Buildings.push(newObstacle);
      }
      console.log("Buildings:", Buildings);
    }
  } catch (error) {
    console.log(error);
  }
}

async function getRoads() {
  try {
    // Send a GET request to the agent server to retrieve the obstacle positions
    let response = await fetch(agent_server_uri + "getRoads") 

    // Check if the response was successful
    if(response.ok){
      // Parse the response as JSON
      let result = await response.json()

      // Create new obstacles and add them to the obstacles array
      for (const Road of result.positions) {
        const newRoad = new Road3D(Road.id, [Road.x, Road.y, Road.z],Road.direction)
        Roads.push(newRoad)
      }
      // Log the obstacles array
      console.log("Roads:", Roads)
    }

  } catch (error) {
    // Log any errors that occur during the request
    console.log(error) 
  }
}
async function getDestinations() {
  try {
    // Send a GET request to the agent server to retrieve the obstacle positions
    let response = await fetch(agent_server_uri + "getDestinations") 

    // Check if the response was successful
    if(response.ok){
      // Parse the response as JSON
      let result = await response.json()

      // Create new obstacles and add them to the obstacles array
      for (const Road of result.positions) {
        const newRoad = new Road3D(Road.id, [Road.x, Road.y, Road.z])
        Destinations.push(newRoad)
      }
      // Log the obstacles array
      console.log("Roads:", Destinations)
    }

  } catch (error) {
    // Log any errors that occur during the request
    console.log(error) 
  }
}

async function getModelStats() {
  try {
    let response = await fetch(agent_server_uri + "getStats");
    if (response.ok) {
      let stats = await response.json();

      // Update the UI with the fetched statistics
      updateStatsUI(stats);
    }
  } catch (error) {
    console.log("Error fetching model stats:", error);
  }
}

/*
 * Updates the agent positions by sending a request to the agent server.
 */
async function update() {
  try {
    let response = await fetch(agent_server_uri + "update");

    if (response.ok) {
      // Retrieve the updated agent positions
      await getAgents();
      await getLights();
      await getModelStats();
      console.log("Updated agents");
    }
  } catch (error) {
    console.log(error);
  }
}


/*
 * Draws the scene by rendering the agents and obstacles.
 * 
 * @param {WebGLRenderingContext} gl - The WebGL rendering context.
 * @param {Object} programInfo - The program information.
 * @param {WebGLVertexArrayObject} agentsVao - The vertex array object for agents.
 * @param {Object} agentsBufferInfo - The buffer information for agents.
 * @param {WebGLVertexArrayObject} BuildingVAO - The vertex array object for obstacles.
 * @param {Object} BuildingBuffer - The buffer information for obstacles.
 */
async function drawScene(gl, programInfo, wheelBufferInfo, wheelVAO, BuildingVAO, BuildingBuffer,TrafficLightBuffer,TrafficLightVAO,RoadVAO,RoadBuffer,SubterraVAO,SubterraBuffer) {
  twgl.resizeCanvasToDisplaySize(gl.canvas);
  gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
  gl.clearColor(0.2, 0.2, 0.2, 1);
  gl.enable(gl.DEPTH_TEST);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.useProgram(programInfo.program);
  setLightingUniforms();
  updateTrafficLightUniforms();
  twgl.setUniforms(programInfo, {
    u_viewWorldPosition: lighting.viewWorldPosition,
    u_numTrafficLights: lighting.numTrafficLights,
    u_trafficLightPositions: lighting.trafficLightPositions,
    u_trafficLightColors: lighting.trafficLightColors,
    u_trafficLightDirections: lighting.trafficLightDirections,
    u_trafficLightCutoffs: lighting.trafficLightCutoffs,
  });
  const viewProjectionMatrix = setupWorldView(gl);
  const distance = 1;

  // Pass wheelVAO and wheelBufferInfo instead of agentsVao and agentsBufferInfo
  drawSubterra(distance, SubterraVAO, SubterraBuffer, viewProjectionMatrix);
  drawAgents(distance, wheelVAO, wheelBufferInfo, viewProjectionMatrix); 
  drawTrafficLights(distance, TrafficLightVAO, TrafficLightBuffer, viewProjectionMatrix); 
  drawBuildings(distance, viewProjectionMatrix);
  drawRoads(distance, RoadVAO, RoadBuffer, viewProjectionMatrix);

  const currentTime = performance.now();
  if (currentTime - lastUpdateTime >= updateInterval) {
    lastUpdateTime = currentTime;
    await update();
  }

  // In your drawScene function, ensure all parameters are passed in the recursive call
requestAnimationFrame(() => drawScene(gl, programInfo, wheelBufferInfo, wheelVAO, BuildingVAO, BuildingBuffer, TrafficLightBuffer, TrafficLightVAO, RoadVAO, RoadBuffer, SubterraVAO, SubterraBuffer));

}


/*
 * Draws the agents.
 * 
 * @param {Number} distance - The distance for rendering.
 * @param {WebGLVertexArrayObject} agentsVao - The vertex array object for agents.
 * @param {Object} agentsBufferInfo - The buffer information for agents.
 * @param {Float32Array} viewProjectionMatrix - The view-projection matrix.
 */
function drawAgents(distance, agentsVao, agentsBufferInfo, viewProjectionMatrix) {
  gl.bindVertexArray(agentsVao);

  const currentTime = performance.now();

  for (const agent of agents) {
    if (agent.isAtDestination) continue; // Skip agents that have reached their destination

    const timeSinceLastUpdate = currentTime - agent.lastUpdateTime;
    const t = Math.min(timeSinceLastUpdate / agent.updateInterval, 1); // Clamp t between 0 and 1

    // Interpolate position
    const interpolatedPosition = [
      lerp(agent.previousPosition[0], agent.targetPosition[0], t),
      lerp(agent.previousPosition[1], agent.targetPosition[1], t),
      lerp(agent.previousPosition[2], agent.targetPosition[2], t),
    ];

    // Update the current position for the next frame
    agent.currentPosition = [...interpolatedPosition];

    // **Add this check to update isAtDestination**
    if (isAtDestination(agent.currentPosition, Destinations)) {
      agent.isAtDestination = true;
      console.log(`Agent ${agent.id} has reached its destination and will be removed.`);
      continue; // Skip rendering this agent
    }

    // Calculate heading based on movement direction
    const movementDirection = [
      agent.targetPosition[0] - agent.previousPosition[0],
      agent.targetPosition[1] - agent.previousPosition[1],
      agent.targetPosition[2] - agent.previousPosition[2],
    ];
    agent.heading = Math.atan2(-movementDirection[2], movementDirection[0]);

    // Rest of your drawing code remains the same
    const translation = twgl.v3.create(...interpolatedPosition);
    const scale = twgl.v3.create(...agent.scale);

    let modelMatrix = twgl.m4.identity();
    modelMatrix = twgl.m4.translate(modelMatrix, translation);
    modelMatrix = twgl.m4.rotateY(modelMatrix, agent.heading - Math.PI / 2);
    modelMatrix = twgl.m4.scale(modelMatrix, scale);

    const mvpMatrix = twgl.m4.multiply(viewProjectionMatrix, modelMatrix);
    const worldInverseTranspose = twgl.m4.transpose(twgl.m4.inverse(modelMatrix));

    twgl.setUniforms(programInfo, {
      u_world: modelMatrix,
      u_matrix: mvpMatrix,
      u_worldInverseTranspose: worldInverseTranspose,
      u_ambientColor: [1.0, 0.5, 0.0, 1.0],
      u_diffuseColor: [1.0, 0.5, 0.0, 1.0],
      u_specularColor: [1.0, 0.5, 0.0, 1.0],
    });

    twgl.drawBufferInfo(gl, agentsBufferInfo);
  }
}






function drawTrafficLights(distance, trafficLightVAO, trafficLightBufferInfo, viewProjectionMatrix) {
  gl.bindVertexArray(trafficLightVAO);
  
  traficLights.forEach(trafficLight => {
    const translation = twgl.v3.create(...trafficLight.position);
    const scale = twgl.v3.create(...trafficLight.scale);
    
    // Create model matrix
    let modelMatrix = twgl.m4.identity();
    modelMatrix = twgl.m4.translate(modelMatrix, translation);
    modelMatrix = twgl.m4.rotateX(modelMatrix, trafficLight.rotation[0]);
    modelMatrix = twgl.m4.rotateY(modelMatrix, trafficLight.rotation[1]);
    modelMatrix = twgl.m4.rotateZ(modelMatrix, trafficLight.rotation[2]);
    modelMatrix = twgl.m4.scale(modelMatrix, scale);
    
    // Compute the model-view-projection matrix
    const mvpMatrix = twgl.m4.multiply(viewProjectionMatrix, modelMatrix);
    
    // Compute the world inverse transpose matrix for normals
    const worldInverseTranspose = twgl.m4.transpose(twgl.m4.inverse(modelMatrix));

    let color;
    if (trafficLight.state) {
      // Red state
      color = [0.0, 1.0, 0.0, 1.0];
    } else {
      // Green state
      color = [1.0, 0.0, 0.0, 1.0];
    }
    
    // Optionally, add emissive color
    let emissiveColor = color;
    
    // Set uniforms for this traffic light
    twgl.setUniforms(programInfo, {
      u_world: modelMatrix,
      u_matrix: mvpMatrix,
      u_worldInverseTranspose: worldInverseTranspose,
      u_ambientColor: [1.0, 0.0, 0.5, 1.0],  // Pink color
      u_diffuseColor: [1.0, 0.0, 0.5, 1.0],
      u_specularColor: [1.0, 0.0, 0.5, 1.0],
      u_emissiveColor: emissiveColor,
    });
    
    // Draw the traffic light
    twgl.drawBufferInfo(gl, trafficLightBufferInfo);
  });
}


      
/*
 * Draws the obstacles.
 * 
 * @param {Number} distance - The distance for rendering.
 * @param {WebGLVertexArrayObject} BuildingVAO - The vertex array object for obstacles.
 * @param {Object} BuildingBuffer - The buffer information for obstacles.
 * @param {Float32Array} viewProjectionMatrix - The view-projection matrix.
 */
function drawBuildings(distance, viewProjectionMatrix) {
  Buildings.forEach(Building => {
    const translation = twgl.v3.create(...Building.position);
    const scale = twgl.v3.create(...Building.scale);

    // Create model matrix
    let modelMatrix = twgl.m4.identity();
    modelMatrix = twgl.m4.translate(modelMatrix, translation);
    modelMatrix = twgl.m4.rotateX(modelMatrix, Building.rotation[0]);
    modelMatrix = twgl.m4.rotateY(modelMatrix, Building.rotation[1]);
    modelMatrix = twgl.m4.rotateZ(modelMatrix, Building.rotation[2]);
    modelMatrix = twgl.m4.scale(modelMatrix, scale);

    // Compute matrices
    const mvpMatrix = twgl.m4.multiply(viewProjectionMatrix, modelMatrix);
    const worldInverseTranspose = twgl.m4.transpose(twgl.m4.inverse(modelMatrix));

    // Set uniforms
    twgl.setUniforms(programInfo, {
      u_world: modelMatrix,
      u_matrix: mvpMatrix,
      u_worldInverseTranspose: worldInverseTranspose,
      u_ambientColor: [0.0, 0.5, 0.5, 1.0],
      u_diffuseColor: [0.0, 0.5, 0.5, 1.0],
      u_specularColor: [0.0, 0.5, 0.5, 1.0],
      u_emissiveColor: [0.0, 0.0, 0.0, 1.0],
    });

    // Choose the VAO and buffer based on modelIndex
    let currentVAO, currentBufferInfo;
    if (Building.modelIndex === 1) {
      currentVAO = BuildingVAO;
      currentBufferInfo = BuildingBuffer;
    } else {
      currentVAO = Building2VAO;
      currentBufferInfo = Building2Buffer;
    }

    // Bind the VAO and draw the building
    gl.bindVertexArray(currentVAO);
    twgl.drawBufferInfo(gl, currentBufferInfo);
  });
}



function drawRoads(distance, RoadVAO, RoadBuffer, viewProjectionMatrix){
  gl.bindVertexArray(RoadVAO);

  Roads.forEach(Road => {
    const translation = twgl.v3.create(...Road.position);
    const scale = twgl.v3.create(...Road.scale);
    
    // Adjust rotation based on direction
    if (
      (Road.direction[0] === 0 && Road.direction[1] === 1) ||  // Matches (0, 1)
      (Road.direction[0] === 0 && Road.direction[1] === -1)   // Matches (0, -1)
    ) {
      Road.rotation[1] = 0;
    } else {
      Road.rotation[1] = Math.PI / 2; // 90 degrees in radians
    }
    
    // Create model matrix
    let modelMatrix = twgl.m4.identity();
    modelMatrix = twgl.m4.translate(modelMatrix, translation);
    modelMatrix = twgl.m4.rotateX(modelMatrix, Road.rotation[0]);
    modelMatrix = twgl.m4.rotateY(modelMatrix, Road.rotation[1]);
    modelMatrix = twgl.m4.rotateZ(modelMatrix, Road.rotation[2]);
    modelMatrix = twgl.m4.scale(modelMatrix, scale);
    
    // Compute the model-view-projection matrix
    const mvpMatrix = twgl.m4.multiply(viewProjectionMatrix, modelMatrix);
    
    // Compute the world inverse transpose matrix for normals
    const worldInverseTranspose = twgl.m4.transpose(twgl.m4.inverse(modelMatrix));
    
    // Set uniforms for this road
    twgl.setUniforms(programInfo, {
      u_world: modelMatrix,
      u_matrix: mvpMatrix,
      u_worldInverseTranspose: worldInverseTranspose,
      u_ambientColor: [1.0, 1.0, , 1.0],  // Dark gray color
      u_diffuseColor: [1.0, 1.0, , 1.0],
      u_specularColor: [1.0, 1.0, , 1.0],
      u_emissiveColor: [0.0,0.0,0.0,1.0],
    });
    
    // Draw the road
    twgl.drawBufferInfo(gl, RoadBuffer);
  });
}
function drawSubterra(distance, SubterraVAO, SubterraBuffer, viewProjectionMatrix) {
  gl.bindVertexArray(SubterraVAO);

  // Position the subterra at the center of the map and slightly below other objects
  const translation = twgl.v3.create(data.width / 2, 0.5, data.height / 2);

  // Scale the subterra to cover the entire map area
  const scale = twgl.v3.create(data.width, 1, data.height);

  // Create the model matrix
  let modelMatrix = twgl.m4.identity();
  modelMatrix = twgl.m4.translate(modelMatrix, translation);
  modelMatrix = twgl.m4.scale(modelMatrix, scale);

  // Compute matrices
  const mvpMatrix = twgl.m4.multiply(viewProjectionMatrix, modelMatrix);
  const worldInverseTranspose = twgl.m4.transpose(twgl.m4.inverse(modelMatrix));

  // Set uniforms
  twgl.setUniforms(programInfo, {
    u_world: modelMatrix,
    u_matrix: mvpMatrix,
    u_worldInverseTranspose: worldInverseTranspose,
    u_ambientColor: [0.5, 0.5, 0.5, 1.0], 
    u_diffuseColor: [0.5, 0.5, 0.5, 1.0],
    u_specularColor: [0.5, 0.5, 0.5, 1.0],  // Slight specular highlight
    u_emissiveColor: [0.0, 0.0, 0.0, 1.0],
  });

  // Draw the subterra
  twgl.drawBufferInfo(gl, SubterraBuffer);
}



function setLightingUniforms() {
  twgl.setUniforms(programInfo, {
    u_ambientLight: lighting.ambientLight,
    u_diffuseLight: lighting.diffuseLight,
    u_specularLight: lighting.specularLight,
    
    u_ambientColor: lighting.ambientColor,
    u_diffuseColor: lighting.diffuseColor,
    u_specularColor: lighting.specularColor,
    u_shininess: lighting.shininess,
    
    u_lightWorldDirection: lighting.lightWorldDirection,
    u_viewWorldPosition: lighting.viewWorldPosition,
    
  });
}

/*
 * Sets up the world view by creating the view-projection matrix.
 * 
 * @param {WebGLRenderingContext} gl - The WebGL rendering context.
 * @returns {Float32Array} The view-projection matrix.
 */
function setupWorldView(gl) {
    // Set the field of view (FOV) in radians
    const fov = 45 * Math.PI / 180;

    // Calculate the aspect ratio of the canvas
    const aspect = gl.canvas.clientWidth / gl.canvas.clientHeight;

    // Create the projection matrix
    const projectionMatrix = twgl.m4.perspective(fov, aspect, 1, 200);

    // Set the target position
    const target = [data.width/2, 0, data.height/2];

    // Set the up vector
    const up = [0, 1, 0];

    // Calculate the camera position
    const camPos = twgl.v3.create(cameraPosition.x + data.width/2, cameraPosition.y, cameraPosition.z+data.height/2)

    // Create the camera matrix
    const cameraMatrix = twgl.m4.lookAt(camPos, target, up);

    // Calculate the view matrix
    const viewMatrix = twgl.m4.inverse(cameraMatrix);

    // Calculate the view-projection matrix
    const viewProjectionMatrix = twgl.m4.multiply(projectionMatrix, viewMatrix);
    
    lighting.viewWorldPosition = camPos;
  
    // Return the view-projection matrix
    return viewProjectionMatrix;
}

/*
 * Sets up the user interface (UI) for the camera position.
 */
function setupUI() {
  const gui = new GUI();
  const posFolder = gui.addFolder('Camera Position');
  
  posFolder.add(cameraPosition, 'x', -50, 50).onChange(updateCameraPosition);
  posFolder.add(cameraPosition, 'y', -50, 50).onChange(updateCameraPosition);
  posFolder.add(cameraPosition, 'z', -50, 50).onChange(updateCameraPosition);

  const lightingFolder = gui.addFolder('Lighting');

  // Add color controls for light colors
  lightingFolder.addColor(lighting, 'ambientLight').name('Ambient Light').onChange(updateLighting);
  lightingFolder.addColor(lighting, 'diffuseLight').name('Diffuse Light').onChange(updateLighting);
  lightingFolder.addColor(lighting, 'specularLight').name('Specular Light').onChange(updateLighting);

  // Add color controls for material colors
  //lightingFolder.addColor(lighting, 'ambientColor').name('Ambient Color').onChange(updateLighting);
  //lightingFolder.addColor(lighting, 'diffuseColor').name('Diffuse Color').onChange(updateLighting);
  //lightingFolder.addColor(lighting, 'specularColor').name('Specular Color').onChange(updateLighting);

  // Add control for shininess
  lightingFolder.add(lighting, 'shininess', 0, 100).name('Shininess').onChange(updateLighting);

  // Add controls for light direction
  const lightDirFolder = lightingFolder.addFolder('Light Direction');
  lightDirFolder.add(lighting.lightWorldDirection, 0, -1, 1).name('X').onChange(updateLighting);
  lightDirFolder.add(lighting.lightWorldDirection, 1, -1, 1).name('Y').onChange(updateLighting);
  lightDirFolder.add(lighting.lightWorldDirection, 2, -1, 1).name('Z').onChange(updateLighting);
}


function updateCameraPosition() {
  // Recalculate the viewProjectionMatrix
  setupWorldView(gl);
  // Update the camera position in the lighting object
  lighting.viewWorldPosition = [cameraPosition.x + data.width/2, cameraPosition.y, cameraPosition.z+data.height/2];
  // Do not set the uniform here; it will be set in drawScene()
}
function updateLighting() {
  // Normalize the light direction vector
  twgl.v3.normalize(lighting.lightWorldDirection, lighting.lightWorldDirection);
}
function updateTrafficLightUniforms() {
  lighting.numTrafficLights = Math.min(traficLights.length, MAX_LIGHTS);
  for (let i = 0; i < lighting.numTrafficLights; i++) {
      const trafficLight = traficLights[i];
      const pos = trafficLight.position; 
      const color = trafficLight.state ? [0.0, 1.0, 0.0] : [1.0, 0.0, 0.0];

      lighting.trafficLightPositions.set(pos, i * 3);
      lighting.trafficLightColors.set(color, i * 3);
      lighting.trafficLightDirections.set([0, -1, 0], i * 3); 
      lighting.trafficLightCutoffs[i] = Math.cos(30 * Math.PI / 180); 
  }
}
function updateStatsUI(stats) {
  // Assuming you have elements with IDs 'cars-in-grid' and 'cars-reached-destination'
  document.getElementById('cars-in-grid').textContent = stats.in_grid;
  document.getElementById('cars-reached-destination').textContent = stats.reached_destination;
}
async function loadObj(route, shouldScaleSmall,type) {
  try {
      const response = await fetch(route);
      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.text();

      const structure = {
          a_position: { numComponents: 3, data: [] },
          a_color: { numComponents: 4, data: [] },
          a_normal: { numComponents: 3, data: [] },
          a_texCoord: { numComponents: 2, data: [] }
      };

      const vertices = [];
      const normals = [];

      const lines = data.split('\n');
      for (const line of lines) {
          const parts = line.trim().split(/\s+/);
          const prefix = parts[0];

          if (prefix === 'v') {
              // Vertex positions
              vertices.push([parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3])]);
          } else if (prefix === 'vn') {
              // Vertex normals
              normals.push([parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3])]);
          } else if (prefix === 'f') {
              for (let i = 1; i < parts.length; i++) {
                  const indices = parts[i].split('/').map(num => parseInt(num, 10) - 1);
                  const vertexIndex = indices[0];
                  const normalIndex = indices[2];
                  const vertex = vertices[vertexIndex];
                  const normal = normals[normalIndex];
                  const scale = shouldScaleSmall ? 0.01 : 0.5;
                  const scaledVertex = vertex.map(coord => coord * scale);

                  structure.a_position.data.push(...scaledVertex);
                  if(type=="Car"){structure.a_color.data.push(0.0, 0.0, 0.0, 1.0);}
                  else if (type=="TrafficLight"){structure.a_color.data.push(0.0, 0.0, 0.0, 1.0);}
                  else if (type=="Building"){structure.a_color.data.push(0.0, 0.0, 0.0, 1.0);}  // Fixed color for all vertices
                  else if (type=="Road"){structure.a_color.data.push(0.0, 0.0, 0.0, 1.0);}  // Fixed color for all vertices
                  structure.a_normal.data.push(...normal);
              }
          }
      }

      console.log("Structured Data:", structure);
      return structure;
  } catch (err) {
      console.error("Error loading OBJ file:", err);
  }
}

function calculateHeading(currentPos, previousPos) {
  // Calculate direction vector
  const dx = currentPos[0] - previousPos[0];
  const dz = currentPos[2] - previousPos[2]; // Using z instead of y for ground plane
  
  // Calculate angle in radians
  let angle = Math.atan2(-dz, dx);
  
  // Only update heading if there's significant movement
  if (Math.abs(dx) > 0.01 || Math.abs(dz) > 0.01) {
    return angle;
  }
  return null; // Return null if there's no significant movement
}

function isAtDestination(agentPosition, destinations, tolerance = 0.1) {
  return destinations.some(destination => 
    Math.abs(agentPosition[0] - destination.position[0]) <= tolerance &&
    Math.abs(agentPosition[2] - destination.position[2]) <= tolerance
  );
}

function lerp(start, end, t) {
  return start + (end - start) * t;
}



main()

'use strict';

import * as twgl from 'twgl.js';
import GUI from 'lil-gui';

// Define the vertex shader code, using GLSL 3.00
const vsGLSL = `#version 300 es
in vec4 a_position;
in vec4 a_color;

uniform mat4 u_transforms;
uniform mat4 u_matrix;

out vec4 v_color;

void main() {
gl_Position = u_matrix * a_position;
v_color = a_color;
}
`;

// Define the fragment shader code, using GLSL 3.00
const fsGLSL = `#version 300 es
precision highp float;

in vec4 v_color;

out vec4 outColor;

void main() {
outColor = v_color;
}
`;

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
  constructor(id, position=[0,0,0], rotation=[0,0,0], scale=[1,1,1]){
  this.id = id;
  this.position = position;
  this.rotation = rotation;
  this.scale = scale;
  this.matrix = twgl.m4.create();
  this.previousPosition = position; // Store previous position to calculate direction
  this.heading = 0;
  }
}
class TrafficLight3D {
  constructor(id, position=[1,1,3], rotation=[0,0,0], scale=[1,1,1]){
  this.id = id;
  this.position = position;
  this.rotation = rotation;
  this.scale = scale;
  this.matrix = twgl.m4.create();
  }
}

class Road3D {
  constructor(id, position=[1,1,3], rotation=[0,0,0], scale=[0.5,0.5,0.5]){
  this.id = id;
  this.position = position;
  this.rotation = rotation;
  this.scale = scale;
  this.matrix = twgl.m4.create();
  }
}

// Define the agent server URI
const agent_server_uri = "http://localhost:8585/";

// Initialize arrays to store agents and obstacles
const agents = [];
const Buildings = [];
const traficLights= [];
const Roads=[];

// Initialize WebGL-related variables
let gl, programInfo, agentArrays, agentsBufferInfo, agentsVao, BuildingVAO,wheelVAO,wheelBufferInfo,TrafficLightArrays,TrafficLightBuffer,TrafficLightVAO,BuildingBuffer,RoadBuffer,RoadVAO;

// Define the camera position
let cameraPosition = {x:0, y:9, z:9};

// Initialize the frame count
let frameCount = 0;

// Define the data object
const data = {
  NAgents: 5,
  width: 10,
  height: 10
};
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
// Main function to initialize and run the application
async function main() {
  const canvas = document.querySelector('canvas');
  gl = canvas.getContext('webgl2');
  
  programInfo = twgl.createProgramInfo(gl, [vsGLSL, fsGLSL]);
  

  //const newTrafficLight = new TrafficLight3D('trafficLight', [5, 0, 3]);
  //traficLights.push(newTrafficLight);

  const obj3 = await loadObj('./Figures/coche.obj',true,"Car");
  objcetsCar.model.arrays = obj3;

  const obj4 = await loadObj('./Figures/Semaforo.obj',false,"TrafficLight");
  objcetsTrafficLight.model.arrays = obj4;

  const obj5 = await loadObj('./Figures/Building.obj',false,"Building");
  objcetsBuilding.model.arrays = obj5;

  const obj6 = await loadObj('./Figures/Road.obj',false,"Road");
  objcetsRoads.model.arrays = obj6;
  
  
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
  RoadBuffer = twgl.createBufferInfoFromArrays(gl, objcetsRoads.model.arrays);
  //BuildingBuffer = twgl.createBufferInfoFromArrays(gl, obstacleArrays);
  
  // Create VAOs
  //agentsVao = twgl.createVAOFromBufferInfo(gl, programInfo, agentsBufferInfo);
  wheelVAO = twgl.createVAOFromBufferInfo(gl, programInfo, wheelBufferInfo);
  TrafficLightVAO = twgl.createVAOFromBufferInfo(gl, programInfo, TrafficLightBuffer);
  BuildingVAO = twgl.createVAOFromBufferInfo(gl, programInfo, BuildingBuffer);
  RoadVAO = twgl.createVAOFromBufferInfo(gl, programInfo, RoadBuffer);
  //BuildingVAO = twgl.createVAOFromBufferInfo(gl, programInfo, BuildingBuffer);
  
  setupUI();
  await initAgentsModel();
  await getLights();
  await getAgents();
  await getBuildings();
  await getRoads();
  
  // Pass parameters in the correct order
  await drawScene(gl, programInfo, wheelBufferInfo, wheelVAO, BuildingVAO, BuildingBuffer, TrafficLightBuffer, TrafficLightVAO,RoadVAO,RoadBuffer);
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
    if(response.ok){
      let result = await response.json();
      
      if(agents.length == 0){
        // Create new agents
        for (const agent of result.positions) {
          const newAgent = new Agent3D(agent.id, [agent.x, agent.y, agent.z]);
          agents.push(newAgent);
        }
      } else {
        // Update existing agents
        for (const agent of result.positions) {
          const current_agent = agents.find((Agent3D) => Agent3D.id == agent.id);
          
          if(current_agent != undefined){
            // Store previous position before updating
            current_agent.previousPosition = [...current_agent.position];
            // Update position
            current_agent.position = [agent.x, agent.y, agent.z];
            
            // Calculate new heading
            const newHeading = calculateHeading(current_agent.position, current_agent.previousPosition);
            if (newHeading !== null) {
              current_agent.heading = newHeading;
            }
          }
        }
      }
    }
  } catch (error) {
    console.log(error);
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
          const newLight = new TrafficLight3D(light.id, [light.x, light.y, light.z]);
          traficLights.push(newLight);
        }
      } else {
        for (const light of positions) {
          const existingLight = traficLights.find(t => t.id === light.id);
          if (existingLight) {
            existingLight.position = [light.x, light.y, light.z];
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
    // Send a GET request to the agent server to retrieve the obstacle positions
    let response = await fetch(agent_server_uri + "getBuildings") 

    // Check if the response was successful
    if(response.ok){
      // Parse the response as JSON
      let result = await response.json()

      // Create new obstacles and add them to the obstacles array
      for (const obstacle of result.positions) {
        const newObstacle = new Building3D(obstacle.id, [obstacle.x, obstacle.y, obstacle.z])
        Buildings.push(newObstacle)
      }
      // Log the obstacles array
      console.log("Obstacles:", obstacles)
    }

  } catch (error) {
    // Log any errors that occur during the request
    console.log(error) 
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
        const newRoad = new Building3D(Road.id, [Road.x, Road.y, Road.z])
        Roads.push(newRoad)
      }
      // Log the obstacles array
      console.log("Roads:", Road)
    }

  } catch (error) {
    // Log any errors that occur during the request
    console.log(error) 
  }
}

/*
 * Updates the agent positions by sending a request to the agent server.
 */
async function update() {
  try {
    // Send a request to the agent server to update the agent positions
    let response = await fetch(agent_server_uri + "update") 

    // Check if the response was successful
    if(response.ok){
      // Retrieve the updated agent positions
      await getAgents()
      // Log a message indicating that the agents have been updated
      console.log("Updated agents")
    }

  } catch (error) {
    // Log any errors that occur during the request
    console.log(error) 
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
async function drawScene(gl, programInfo, wheelBufferInfo, wheelVAO, BuildingVAO, BuildingBuffer,TrafficLightBuffer,TrafficLightVAO,RoadVAO,RoadBuffer) {
  twgl.resizeCanvasToDisplaySize(gl.canvas);
  gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);
  gl.clearColor(0.2, 0.2, 0.2, 1);
  gl.enable(gl.DEPTH_TEST);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.useProgram(programInfo.program);

  const viewProjectionMatrix = setupWorldView(gl);
  const distance = 1;

  // Pass wheelVAO and wheelBufferInfo instead of agentsVao and agentsBufferInfo
  drawAgents(distance, wheelVAO, wheelBufferInfo, viewProjectionMatrix); 
  drawTrafficLights(distance, TrafficLightVAO, TrafficLightBuffer, viewProjectionMatrix); 
  drawBuildings(distance, BuildingVAO, BuildingBuffer, viewProjectionMatrix);
  drawRoads(distance, RoadVAO, RoadBuffer, viewProjectionMatrix);

  frameCount++;

  if(frameCount%30 == 0){
      frameCount = 0;
      await update();
  } 

  requestAnimationFrame(() => drawScene(gl, programInfo, wheelBufferInfo, wheelVAO, BuildingVAO, BuildingBuffer,TrafficLightBuffer,TrafficLightVAO,RoadVAO,RoadBuffer));
}


/*
 * Draws the agents.
 * 
 * @param {Number} distance - The distance for rendering.
 * @param {WebGLVertexArrayObject} agentsVao - The vertex array object for agents.
 * @param {Object} agentsBufferInfo - The buffer information for agents.
 * @param {Float32Array} viewProjectionMatrix - The view-projection matrix.
 */
function drawAgents(distance, agentsVao, agentsBufferInfo, viewProjectionMatrix){
  gl.bindVertexArray(agentsVao);
  
  for(const agent of agents){
    const cube_trans = twgl.v3.create(...agent.position);
    const cube_scale = twgl.v3.create(...agent.scale);
    
    // Start with view projection matrix
    agent.matrix = twgl.m4.translate(viewProjectionMatrix, cube_trans);
    
    // Apply Y-axis rotation based on heading
    agent.matrix = twgl.m4.rotateY(agent.matrix, agent.heading);
    
    // Apply any additional rotations if needed
    agent.matrix = twgl.m4.rotateX(agent.matrix, agent.rotation[0]);
    agent.matrix = twgl.m4.rotateZ(agent.matrix, agent.rotation[2]);
    
    // Apply scale
    agent.matrix = twgl.m4.scale(agent.matrix, cube_scale);
    
    let uniforms = {
      u_matrix: agent.matrix,
    };
    
    twgl.setUniforms(programInfo, uniforms);
    twgl.drawBufferInfo(gl, agentsBufferInfo);
  }
}

function drawTrafficLights(distance, trafficLightVAO, trafficLightBufferInfo, viewProjectionMatrix) {
  // Bind the vertex array object for traffic lights
  gl.bindVertexArray(trafficLightVAO);
  console.log("TraffiLights Array",traficLights)
  // Iterate over the traffic lights
  traficLights.forEach(trafficLight => {
      console.log("TYPE OF TRAF LIGHT", trafficLight)
      // Calculate the traffic light's position
      let x = trafficLight.position[0] * distance, y = trafficLight.position[1] * distance, z = trafficLight.position[2];

      // Create the traffic light's transformation matrix
      const light_trans = twgl.v3.create(x, y, z);
      const light_scale = twgl.v3.create(0.5, 0.5, 0.5);;

      // Calculate the traffic light's matrix
      trafficLight.matrix = twgl.m4.translate(viewProjectionMatrix, light_trans);
      trafficLight.matrix = twgl.m4.rotateX(trafficLight.matrix, trafficLight.rotation[0]);
      trafficLight.matrix = twgl.m4.rotateY(trafficLight.matrix, trafficLight.rotation[1]);
      trafficLight.matrix = twgl.m4.rotateZ(trafficLight.matrix, trafficLight.rotation[2]);
      trafficLight.matrix = twgl.m4.scale(trafficLight.matrix, light_scale);

      // Set the uniforms for the traffic light
      let uniforms = {
          u_matrix: trafficLight.matrix,
      };

      // Set the uniforms and draw the traffic light
      twgl.setUniforms(programInfo, uniforms);
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
function drawBuildings(distance, BuildingVAO, BuildingBuffer, viewProjectionMatrix){
    // Bind the vertex array object for obstacles
    gl.bindVertexArray(BuildingVAO);

    // Iterate over the obstacles
    for(const Building of Buildings){
      // Create the obstacle's transformation matrix
      const cube_trans = twgl.v3.create(...Building.position);
      const cube_scale = twgl.v3.create(...Building.scale);

      // Calculate the obstacle's matrix
      Building.matrix = twgl.m4.translate(viewProjectionMatrix, cube_trans);
      Building.matrix = twgl.m4.rotateX(Building.matrix, Building.rotation[0]);
      Building.matrix = twgl.m4.rotateY(Building.matrix, Building.rotation[1]);
      Building.matrix = twgl.m4.rotateZ(Building.matrix, Building.rotation[2]);
      Building.matrix = twgl.m4.scale(Building.matrix, cube_scale);

      // Set the uniforms for the obstacle
      let uniforms = {
          u_matrix: Building.matrix,
      }

      // Set the uniforms and draw the obstacle
      twgl.setUniforms(programInfo, uniforms);
      twgl.drawBufferInfo(gl, BuildingBuffer);
      
    }
}

function drawRoads(distance, RoadVAO, RoadBuffer, viewProjectionMatrix){
  // Bind the vertex array object for obstacles
  gl.bindVertexArray(RoadVAO);

  // Iterate over the obstacles
  for(const Road of Roads){
    // Create the obstacle's transformation matrix
    const Road_trans = twgl.v3.create(...Road.position);
    const Road_scale = twgl.v3.create(...Road.scale);

    // Calculate the obstacle's matrix
    Road.matrix = twgl.m4.translate(viewProjectionMatrix, Road_trans);
    Road.matrix = twgl.m4.rotateX(Road.matrix, Road.rotation[0]);
    Road.matrix = twgl.m4.rotateY(Road.matrix,Road.rotation[1]);
    Road.matrix = twgl.m4.rotateZ(Road.matrix, Road.rotation[2]);
    Road.matrix = twgl.m4.scale(Road.matrix, Road_scale);

    // Set the uniforms for the obstacle
    let uniforms = {
        u_matrix: Road.matrix,
    }

    // Set the uniforms and draw the obstacle
    twgl.setUniforms(programInfo, uniforms);
    twgl.drawBufferInfo(gl, RoadBuffer);
    
  }
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

    // Return the view-projection matrix
    return viewProjectionMatrix;
}

/*
 * Sets up the user interface (UI) for the camera position.
 */
function setupUI() {
    // Create a new GUI instance
    const gui = new GUI();

    // Create a folder for the camera position
    const posFolder = gui.addFolder('Position:')

    // Add a slider for the x-axis
    posFolder.add(cameraPosition, 'x', -50, 50)
        .onChange( value => {
            // Update the camera position when the slider value changes
            cameraPosition.x = value
        });

    // Add a slider for the y-axis
    posFolder.add( cameraPosition, 'y', -50, 50)
        .onChange( value => {
            // Update the camera position when the slider value changes
            cameraPosition.y = value
        });

    // Add a slider for the z-axis
    posFolder.add( cameraPosition, 'z', -50, 50)
        .onChange( value => {
            // Update the camera position when the slider value changes
            cameraPosition.z = value
        });
}

function generateData(size) {
    let arrays =
    {
        a_position: {
                numComponents: 3,
                data: [
                  // Front Face
                  -0.5, -0.5,  0.5,
                  0.5, -0.5,  0.5,
                  0.5,  0.5,  0.5,
                 -0.5,  0.5,  0.5,

                 // Back face
                 -0.5, -0.5, -0.5,
                 -0.5,  0.5, -0.5,
                  0.5,  0.5, -0.5,
                  0.5, -0.5, -0.5,

                 // Top face
                 -0.5,  0.5, -0.5,
                 -0.5,  0.5,  0.5,
                  0.5,  0.5,  0.5,
                  0.5,  0.5, -0.5,

                 // Bottom face
                 -0.5, -0.5, -0.5,
                  0.5, -0.5, -0.5,
                  0.5, -0.5,  0.5,
                 -0.5, -0.5,  0.5,

                 // Right face
                  0.5, -0.5, -0.5,
                  0.5,  0.5, -0.5,
                  0.5,  0.5,  0.5,
                  0.5, -0.5,  0.5,

                 // Left face
                 -0.5, -0.5, -0.5,
                 -0.5, -0.5,  0.5,
                 -0.5,  0.5,  0.5,
                 -0.5,  0.5, -0.5
                ].map(e => size * e)
            },
        a_color: {
                numComponents: 4,
                data: [
                  // Front face
                    1, 0, 0, 1, // v_1
                    1, 0, 0, 1, // v_1
                    1, 0, 0, 1, // v_1
                    1, 0, 0, 1, // v_1
                  // Back Face
                    0, 1, 0, 1, // v_2
                    0, 1, 0, 1, // v_2
                    0, 1, 0, 1, // v_2
                    0, 1, 0, 1, // v_2
                  // Top Face
                    0, 0, 1, 1, // v_3
                    0, 0, 1, 1, // v_3
                    0, 0, 1, 1, // v_3
                    0, 0, 1, 1, // v_3
                  // Bottom Face
                    1, 1, 0, 1, // v_4
                    1, 1, 0, 1, // v_4
                    1, 1, 0, 1, // v_4
                    1, 1, 0, 1, // v_4
                  // Right Face
                    0, 1, 1, 1, // v_5
                    0, 1, 1, 1, // v_5
                    0, 1, 1, 1, // v_5
                    0, 1, 1, 1, // v_5
                  // Left Face
                    1, 0, 1, 1, // v_6
                    1, 0, 1, 1, // v_6
                    1, 0, 1, 1, // v_6
                    1, 0, 1, 1, // v_6
                ]
            },
        indices: {
                numComponents: 3,
                data: [
                  0, 1, 2,      0, 2, 3,    // Front face
                  4, 5, 6,      4, 6, 7,    // Back face
                  8, 9, 10,     8, 10, 11,  // Top face
                  12, 13, 14,   12, 14, 15, // Bottom face
                  16, 17, 18,   16, 18, 19, // Right face
                  20, 21, 22,   20, 22, 23  // Left face
                ]
            }
    };

    return arrays;
}

function generateObstacleData(size){

    let arrays =
    {
        a_position: {
                numComponents: 3,
                data: [
                  // Front Face
                  -0.5, -0.5,  0.5,
                  0.5, -0.5,  0.5,
                  0.5,  0.5,  0.5,
                 -0.5,  0.5,  0.5,

                 // Back face
                 -0.5, -0.5, -0.5,
                 -0.5,  0.5, -0.5,
                  0.5,  0.5, -0.5,
                  0.5, -0.5, -0.5,

                 // Top face
                 -0.5,  0.5, -0.5,
                 -0.5,  0.5,  0.5,
                  0.5,  0.5,  0.5,
                  0.5,  0.5, -0.5,

                 // Bottom face
                 -0.5, -0.5, -0.5,
                  0.5, -0.5, -0.5,
                  0.5, -0.5,  0.5,
                 -0.5, -0.5,  0.5,

                 // Right face
                  0.5, -0.5, -0.5,
                  0.5,  0.5, -0.5,
                  0.5,  0.5,  0.5,
                  0.5, -0.5,  0.5,

                 // Left face
                 -0.5, -0.5, -0.5,
                 -0.5, -0.5,  0.5,
                 -0.5,  0.5,  0.5,
                 -0.5,  0.5, -0.5
                ].map(e => size * e)
            },
        a_color: {
                numComponents: 4,
                data: [
                  // Front face
                    0, 0, 0, 1, // v_1
                    0, 0, 0, 1, // v_1
                    0, 0, 0, 1, // v_1
                    0, 0, 0, 1, // v_1
                  // Back Face
                    0.333, 0.333, 0.333, 1, // v_2
                    0.333, 0.333, 0.333, 1, // v_2
                    0.333, 0.333, 0.333, 1, // v_2
                    0.333, 0.333, 0.333, 1, // v_2
                  // Top Face
                    0.5, 0.5, 0.5, 1, // v_3
                    0.5, 0.5, 0.5, 1, // v_3
                    0.5, 0.5, 0.5, 1, // v_3
                    0.5, 0.5, 0.5, 1, // v_3
                  // Bottom Face
                    0.666, 0.666, 0.666, 1, // v_4
                    0.666, 0.666, 0.666, 1, // v_4
                    0.666, 0.666, 0.666, 1, // v_4
                    0.666, 0.666, 0.666, 1, // v_4
                  // Right Face
                    0.833, 0.833, 0.833, 1, // v_5
                    0.833, 0.833, 0.833, 1, // v_5
                    0.833, 0.833, 0.833, 1, // v_5
                    0.833, 0.833, 0.833, 1, // v_5
                  // Left Face
                    1, 1, 1, 1, // v_6
                    1, 1, 1, 1, // v_6
                    1, 1, 1, 1, // v_6
                    1, 1, 1, 1, // v_6
                ]
            },
        indices: {
                numComponents: 3,
                data: [
                  0, 1, 2,      0, 2, 3,    // Front face
                  4, 5, 6,      4, 6, 7,    // Back face
                  8, 9, 10,     8, 10, 11,  // Top face
                  12, 13, 14,   12, 14, 15, // Bottom face
                  16, 17, 18,   16, 18, 19, // Right face
                  20, 21, 22,   20, 22, 23  // Left face
                ]
            }
    };
    return arrays;
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
                  if(type=="Car"){structure.a_color.data.push(1.0, 0.5, 0.0, 1.0);}
                  else if (type=="TrafficLight"){structure.a_color.data.push(1.0, 0.0, 0.5, 1.0);}
                  else if (type=="Building"){structure.a_color.data.push(0.0, 0.5, 0.5, 1.0);}  // Fixed color for all vertices
                  else if (type=="Road"){structure.a_color.data.push(1.0, 1.0, 1.0, 1.0);}  // Fixed color for all vertices
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
  let angle = Math.atan2(dx, dz);
  
  // Only update heading if there's significant movement
  if (Math.abs(dx) > 0.01 || Math.abs(dz) > 0.01) {
    return angle;
  }
  return null; // Return null if there's no significant movement
}




main()

#version 300 es
precision highp float;

// Attributes from the buffer
in vec4 a_position;
in vec4 a_color;
in vec3 a_normal;

// Uniforms
uniform mat4 u_matrix;
uniform mat4 u_worldInverseTranspose;

// Varyings to pass to fragment shader
out vec4 v_color;
out vec3 v_normal;
out vec3 v_position;

void main() {
    gl_Position = u_matrix * a_position;
    v_color = a_color;
    // Transform the normal to world space
    v_normal = mat3(u_worldInverseTranspose) * a_normal;
    // Calculate world position of the vertex
    v_position = (u_matrix * a_position).xyz;
}

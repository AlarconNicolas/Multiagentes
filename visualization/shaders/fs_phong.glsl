#version 300 es
precision highp float;

// Varyings from the vertex shader
in vec4 v_color;
in vec3 v_normal;
in vec3 v_position;

// Uniforms for lighting
uniform vec3 u_lightWorldDirection; // Directional light direction
uniform vec4 u_ambientLight;
uniform vec4 u_diffuseLight;
uniform vec4 u_specularLight;

// Uniforms for material properties
uniform vec4 u_ambientColor;
uniform vec4 u_diffuseColor;
uniform vec4 u_specularColor;
uniform float u_shininess;

// Uniform for camera position
uniform vec3 u_viewWorldPosition;

// Output color
out vec4 outColor;

void main() {
    // Normalize the normal vector
    vec3 normal = normalize(v_normal);
    
    // Normalize the light direction
    vec3 lightDir = normalize(u_lightWorldDirection);
    
    // Calculate the view direction
    vec3 viewDir = normalize(u_viewWorldPosition - v_position);
    
    // Calculate the reflection direction
    vec3 reflectDir = reflect(-lightDir, normal);
    
    // Ambient component
    vec4 ambient = u_ambientLight * u_ambientColor;
    
    // Diffuse component
    float lambert = max(dot(normal, lightDir), 0.0);
    vec4 diffuse = u_diffuseLight * u_diffuseColor * lambert;
    
    // Specular component
    float spec = 0.0;
    if (lambert > 0.0) {
        spec = pow(max(dot(viewDir, reflectDir), 0.0), u_shininess);
    }
    vec4 specular = u_specularLight * u_specularColor * spec;
    
    // Combine all components
    outColor = ambient + diffuse + specular;
}

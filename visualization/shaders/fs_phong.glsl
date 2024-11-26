#version 300 es
precision highp float;

in vec3 v_normal;
in vec3 v_position;
in vec4 v_color;

uniform mat4 u_worldInverseTranspose;

uniform vec4 u_ambientLight;
uniform vec4 u_diffuseLight;
uniform vec4 u_specularLight;

uniform vec4 u_ambientColor;
uniform vec4 u_diffuseColor;
uniform vec4 u_specularColor;
uniform float u_shininess;

uniform vec4 u_emissiveColor; // New uniform for emissive color

uniform vec3 u_lightWorldDirection; // Directional light direction
uniform vec3 u_viewWorldPosition; // Camera position

out vec4 outColor;

void main() {
    // Normalize normal
    vec3 normal = normalize(v_normal);

    // Calculate ambient
    vec4 ambient = u_ambientLight * u_ambientColor;

    // Calculate diffuse
    float diffuseFactor = max(dot(normal, normalize(u_lightWorldDirection)), 0.0);
    vec4 diffuse = u_diffuseLight * u_diffuseColor * diffuseFactor;

    // Calculate specular
    vec3 viewDir = normalize(u_viewWorldPosition - v_position);
    vec3 reflectDir = reflect(-normalize(u_lightWorldDirection), normal);
    float specFactor = pow(max(dot(viewDir, reflectDir), 0.0), u_shininess);
    vec4 specular = u_specularLight * u_specularColor * specFactor;

    // Calculate emissive
    vec4 emissive = u_emissiveColor;

    // Combine all components
    outColor = ambient + diffuse + specular + emissive;
}

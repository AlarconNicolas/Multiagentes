#version 300 es
precision highp float;

in vec3 v_normal;
in vec3 v_position;
in vec4 v_color;

uniform vec4 u_ambientLight;
uniform vec4 u_diffuseLight;
uniform vec4 u_specularLight;

uniform vec4 u_ambientColor;
uniform vec4 u_diffuseColor;
uniform vec4 u_specularColor;
uniform float u_shininess;

uniform vec4 u_emissiveColor;          // Emissive color
uniform vec3 u_lightWorldDirection;    // Directional light direction
uniform vec3 u_viewWorldPosition;      // Camera position

// Traffic light uniforms
const int MAX_LIGHTS = 24;             // Adjust as needed
uniform int u_numTrafficLights;
uniform vec3 u_trafficLightPositions[MAX_LIGHTS];
uniform vec3 u_trafficLightColors[MAX_LIGHTS];
uniform vec3 u_trafficLightDirections[MAX_LIGHTS];
uniform float u_trafficLightCutoffs[MAX_LIGHTS];

out vec4 outColor;

void main() {
    // Normalize normal
    vec3 normal = normalize(v_normal);

    // Calculate ambient
    vec4 ambient = u_ambientLight * u_ambientColor;

    // Calculate directional light diffuse
    vec3 lightDir = normalize(u_lightWorldDirection);
    float diffuseFactor = max(dot(normal, lightDir), 0.0);
    vec4 diffuse = u_diffuseLight * u_diffuseColor * diffuseFactor;

    // Calculate specular for directional light
    vec3 viewDir = normalize(u_viewWorldPosition - v_position);
    vec3 reflectDir = reflect(-lightDir, normal);
    float specFactor = pow(max(dot(viewDir, reflectDir), 0.0), u_shininess);
    vec4 specular = u_specularLight * u_specularColor * specFactor;

    // Initialize total light with existing lighting
    vec3 totalLight = (ambient + diffuse + specular + u_emissiveColor).rgb;

    // Traffic light contributions
    for (int i = 0; i < MAX_LIGHTS; i++) {
        if (i >= u_numTrafficLights) break;

        vec3 lightPos = u_trafficLightPositions[i];
        vec3 lightColor = u_trafficLightColors[i];
        vec3 spotDir = normalize(u_trafficLightDirections[i]);
        float cutoff = u_trafficLightCutoffs[i];

        vec3 L = normalize(lightPos - v_position);
        float spotEffect = dot(L, -spotDir);

        if (spotEffect > cutoff) {
            // Diffuse component
            float lambertian = max(dot(normal, L), 0.0);
            // Attenuation based on distance (optional)
            float distance = length(lightPos - v_position);
            float attenuation = 1.0 / (distance * distance);

            vec3 diffuseTL = lambertian * lightColor * attenuation * spotEffect;

            // Specular component
            vec3 R = reflect(-L, normal);
            float specAngle = max(dot(R, viewDir), 0.0);
            float specularTL = pow(specAngle, u_shininess) * spotEffect * attenuation;

            totalLight += diffuseTL + specularTL * lightColor;
        }
    }

    outColor = vec4(totalLight, 1.0);
}

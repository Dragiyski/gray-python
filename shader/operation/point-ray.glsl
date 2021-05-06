#version 460

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(rgba32f, binding = 0) uniform image2DArray image_ray;

uniform ivec2 screenSize;
uniform vec2 viewSize;
uniform vec3 screenCenter;
uniform vec3 cameraOrigin;
uniform vec3 cameraDirection;
uniform vec3 cameraUp;
uniform vec3 cameraLeft;

void main() {
    vec3 relCoord = vec2(gl_WorkGroupID.xy) / vec2(screenSize);
    vec2 rectCoord = relCoord * viewSize * 2.0 - viewSize;
}
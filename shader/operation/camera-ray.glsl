#version 460

precision highp float;
precision highp int;

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(rgba32f, binding = 0) uniform image2DArray image_ray;

uniform ivec2 screen_size;
uniform vec2 view_size;
uniform vec3 screen_center;
uniform vec3 camera_position;
uniform vec3 camera_up;
uniform vec3 camera_right;

void main() {
    vec2 halfScreen = vec2(screen_size) * 0.5;
    vec2 relCoord = (vec2(gl_WorkGroupID.xy) - halfScreen) / halfScreen; // [-1; +1] range coordinates
    vec2 rectCoord = relCoord * view_size;
    vec3 rectPoint = screen_center + rectCoord.x * camera_right + rectCoord.y * camera_up;
    vec3 rayDirection = normalize(rectPoint - camera_position);
    imageStore(image_ray, ivec3(gl_WorkGroupID.xy, 0), vec4(camera_position, 1.0));
    imageStore(image_ray, ivec3(gl_WorkGroupID.xy, 1), vec4(rayDirection, 1.0));
}
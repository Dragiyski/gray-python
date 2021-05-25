#version 460

precision highp float;
precision highp int;

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(rgba32f, binding = 0) uniform image2DArray image_raytrace;
layout(rgba32f, binding = 1) uniform image2DRect image_screen;

void main() {
    float inf = uintBitsToFloat(0x7f800000);
    imageStore(image_raytrace, ivec3(gl_WorkGroupID.xy, 0), vec4(0.0, 0.0, 0.0, 0.0));
    imageStore(image_raytrace, ivec3(gl_WorkGroupID.xy, 1), vec4(0.0, 0.0, 0.0, 0.0));
    imageStore(image_raytrace, ivec3(gl_WorkGroupID.xy, 2), vec4(0.0, 0.0, 0.0, inf));
    imageStore(image_raytrace, ivec3(gl_WorkGroupID.xy, 3), vec4(0.0, 0.0, 0.0, 0.0));
    imageStore(image_screen, ivec2(gl_WorkGroupID.xy), vec4(0.0, 0.0, 0.0, 0.0));
}

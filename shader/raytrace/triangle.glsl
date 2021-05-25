#version 460

precision highp float;
precision highp int;

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(rgba32f, binding = 0) uniform image2DArray image_ray;
layout(rgba32f, binding = 1) uniform image2DArray image_trace;

struct Vertex {
    vec3 location;
    vec3 normal;
    vec2 uv;
};

layout(std430, binding = 2) buffer vertexArray {
    Vertex vertices[];
}

layout(std430, binding = 3) buffer indexArray {
    uvec3 indices[];
}

vec3 triangleInterpolate(vec3 point) {
    return normalize(
        vec3(
            length(point - triangle[0].location),
            length(point - triangle[1].location),
            length(point - triangle[2].location)
        )
    );
}

vec3 interpolate3(vec3 item0, vec3 item1, vec3 item2, vec3 coordinates) {
    return coordinates.x * item0 + coordinates.y * item1 + coordinates * item2;
}

void main() {
    vec3 rayOrigin = imageLoad(image_ray, ivec3(gl_WorkGroupID.xy, 0)).xyz;
    vec3 rayDirection = imageLoad(image_ray, ivec3(gl_WorkGroupID.xy, 1)).xyz;
    uvec3 triangle = indices[gl_WorkGroupID.z];
    Vertex va = vertices[triangle[0]]
    Vertex vb = vertices[triangle[1]]
    Vertex vc = vertices[triangle[2]]
    vec3 a = va.location;
    vec3 b = vb.location;
    vec3 c = vc.location;
    vec3 N = normalize(cross(c - a, c - b))
    float ND = dot(N, rayDirection)
    if (ND > 0) {
        ND = -ND;
        N = -N;
    }
    // The plane A * x + B * y + C * z = D, where [A, B, C] = N (the normal to that plane)
    // To find D, replace [x, y, z] with any known point (they all should produce the same result)
    // We know at least 3 points (from the triangle)
    float d = dot(N, c)

    // Intesect the plane and the ray, receiving the distance from the origin to the plane.
    float t = (d - dot(N, rayOrigin)) / ND;

    // If by any chance we are parallel to the plane, or the intersection is behind the camera, abandon now...
    if (isinf(t) || isnan(t) || t < 0.0) {
        return;
    }

    // Otherwise, we must check if we are withing the boundaries of the plane, to do that, we get the intersecton point X:
    vec3 x = rayOrigin + t * rayDirection;

    // Next we retrieve the triangle coordinates: this is done using the fact that within the same half space, the dot-cross product
    // (tripple product) would have the same sign...


    // Step 1: Compute the intersection between the triangle's plane and the ray:
    // A plane is pre-computed on the CPU (for now, although it is possible to run additional compute shader for that).
    // A plane formula is a * x + b * y + c * z = d
    // Where N = (a, b, c) is the normal to the plane
    // and X = (x, y, z) is a point from that plane
    // and d is used to get concrete plane, as there are infinite number of planes with the same normal
    // This can be rewritten as dot(N, X) = d
    // If X belongs to the ray it is also true that X = O + t * D for some distance t.
    float ND = dot(plane.xyz, rayDirection);
    float t = (plane.w - dot(plane.xyz, rayOrigin)) / ND;

    // In case the ray is parallel to the plane, we won't find any intersection point.
    if (isinf(t) || isnan(t) || t < 0.0) {
        return;
    }

    // Now p is an intersection point to the plane.
    vec3 x = rayOrigin + t * rayDirection;

    vec3 barycentric = vec3(
        dot(cross(b - a, x - a), N) / dot(cross(b - a, c - a), N),
        dot(cross(c - b, x - b), N) / dot(cross(c - b, a - b), N),
        1.0
    );
    barycentric.z = 1.0 - barycentric.x - barycentric.y;

    if (barycentric.x < 0.0 || barycentric.y < 0.0 || barycentric.z < 0.0) {
        return;
    }

    float current_t = imageLoad(image_trace, ivec3(gl_WorkGroupID.xy, 2)).w;

    // Check the depth buffer, if another entry exists that is closer, ignore current match
    if (t > current_t) {
        return;
    }

    triangleCoords = normalize(triangleCoords);
    imageStore(image_trace, ivec3(gl_WorkGroupID.xy, 0), vec4(1.0, 1.0, 1.0, 1.0));
    imageStore(image_trace, ivec3(gl_WorkGroupID.xy, 1), vec4(plane.xyz * 0.5 + 0.5, 1.0));
    imageStore(image_trace, ivec3(gl_WorkGroupID.xy, 2), vec4(x, t));
    imageStore(image_trace, ivec3(gl_WorkGroupID.xy, 3), vec4(-rayDirection, 1.0));
}

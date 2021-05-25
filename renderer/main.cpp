#include <Python.h>
#include <numpy/ndarraytypes.h>
#include <SDL2/SDL_surface.h>
#include <stdio.h>
#include <array>
#include <cmath>
#include <limits>
#include "array-math.h"

static PyObject *python_renderer(PyObject *self, PyObject *const *args, Py_ssize_t nargs);

PyMODINIT_FUNC PyInit_renderer(void) {
    static PyMethodDef methods[] = {
        {"render", (PyCFunction)python_renderer, METH_FASTCALL, nullptr},
        {nullptr, nullptr, 0, nullptr}
    };
    static struct PyModuleDef renderer_module = {
        .m_base = PyModuleDef_HEAD_INIT,
        .m_name = "renderer",
        .m_doc = nullptr,
        .m_size = -1,
        .m_methods = methods
    };
    auto python_module = PyModule_Create(&renderer_module);
    return python_module;
}

typedef struct {
    std::array<float, 3> position;
    std::array<float, 3> normal;
    std::array<float, 2> uv;
} Vertex;

typedef std::array<Vertex, 3> Triangle;

PyObject *python_renderer(PyObject *self, PyObject *const args[], Py_ssize_t nargs) {
    auto surface = (SDL_Surface *)PyLong_AsVoidPtr(args[1]);
    auto x = PyLong_AsLong(args[2]);
    auto y = PyLong_AsLong(args[3]);
    float (&texture_ray)[2][surface->h][surface->w][4] = *(float(*)[2][surface->h][surface->w][4])PyArray_DATA((PyArrayObject *)PyObject_GetAttrString(args[0], "_ray_texture"));
    float (&texture_raytrace)[4][surface->h][surface->w][4] = *(float(*)[4][surface->h][surface->w][4])PyArray_DATA((PyArrayObject *)PyObject_GetAttrString(args[0], "_raytrace_texture"));
    auto& camera_position = reinterpret_cast<std::array<float, 3>&>(*(float(*)[3])PyArray_DATA((PyArrayObject *)PyObject_GetAttrString(args[0], "_camera_position")));
    auto& view_size = reinterpret_cast<std::array<float, 2>&>(*(float(*)[2])PyArray_DATA((PyArrayObject *)PyObject_GetAttrString(args[0], "_view_size")));
    auto& screen_center = reinterpret_cast<std::array<float, 3>&>(*(float(*)[3])PyArray_DATA((PyArrayObject *)PyObject_GetAttrString(args[0], "_screen_center")));
    auto& camera_right = reinterpret_cast<std::array<float, 3>&>(*(float(*)[3])PyArray_DATA((PyArrayObject *)PyObject_GetAttrString(args[0], "_camera_right")));
    auto& camera_up = reinterpret_cast<std::array<float, 3>&>(*(float(*)[3])PyArray_DATA((PyArrayObject *)PyObject_GetAttrString(args[0], "_camera_up")));
    auto half_screen = vec2(float(surface->w), float(surface->h)) * 0.5;
    std::array<float, 2> rel_coords = {
        (x - half_screen[0]) / half_screen[0],
        (surface->h - y - half_screen[1]) / half_screen[1]
    };
    auto rect_coords = rel_coords * view_size;
    auto rect_point = screen_center + rect_coords[0] * camera_right + rect_coords[1] * camera_up;
    auto ray_direction = normalize(rect_point - camera_position);
    uint8_t (&pixelData)[surface->h][surface->w][surface->format->BytesPerPixel] = *(uint8_t (*)[surface->h][surface->w][surface->format->BytesPerPixel])surface->pixels;
    for (int i = 0; i < 3; ++i) {
        texture_ray[0][y][x][i] = camera_position[i];
        texture_ray[1][y][x][i] = ray_direction[i];
        texture_raytrace[0][y][x][i] = 0.0f;
    }
    texture_raytrace[2][y][x][3] = std::numeric_limits<std::decay_t<decltype(texture_raytrace[2][y][0][3])>>::infinity();
    auto py_cube_vertices = (PyArrayObject *)PyObject_GetAttrString(args[0], "_cube_vertices");
    auto py_cube_indices = (PyArrayObject *)PyObject_GetAttrString(args[0], "_cube_indices");
    auto cube_vertices_shape = PyArray_SHAPE(py_cube_vertices);
    auto cube_indices_shape = PyArray_SHAPE(py_cube_indices);
    auto triangle_count = cube_indices_shape[0] / 3;
    Vertex (&cube_vertices)[cube_vertices_shape[0] / 8] = *(Vertex (*)[cube_vertices_shape[0] / 8])PyArray_DATA(py_cube_vertices);
    uint8_t (&cube_indices)[triangle_count][3] = *(uint8_t (*)[triangle_count][3])PyArray_DATA(py_cube_indices);
    for (auto i = 0; i < triangle_count; ++i) {
        auto& ray_origin = camera_position;
        Triangle triangle = { cube_vertices[cube_indices[i][0]], cube_vertices[cube_indices[i][1]], cube_vertices[cube_indices[i][2]] };
        auto v0 = triangle[0].position;
        auto v1 = triangle[1].position;
        auto v2 = triangle[2].position;
        auto e1 = v1 - v0;
        auto e2 = v2 - v0;
        auto h = cross(ray_direction, e2);
        auto a = dot(e1, h);
        if (a > -std::numeric_limits<decltype(a)>::epsilon() && a < std::numeric_limits<decltype(a)>::epsilon()) {
            continue;
        }
        float f = 1.0 / a;
        auto s = ray_origin - v0;
        auto u = f * dot(s, h);
        if (u < 0.0 || u > 1.0) {
            continue;
        }
        auto q = cross(s, e1);
        auto v = f * dot(ray_direction, q);
        if (v < 0.0 || u + v > 1.0) {
            continue;
        }
        auto t = f * dot(e2, q);
        if (t < std::numeric_limits<decltype(t)>::epsilon() || t > texture_raytrace[2][y][x][3]) {
            continue;
        }
        auto P = ray_origin + t * ray_direction;
        for (auto i = 0; i < 4; ++i) {
            texture_raytrace[0][y][x][i] = 1.0f;
        }
        auto N = normalize(cross(e1, e2));
        for (auto i = 0; i < 3; ++i) {
            texture_raytrace[1][y][x][i] = N[i];
            texture_raytrace[2][y][x][i] = P[i];
            texture_raytrace[3][y][x][i] = -ray_direction[i];
        }
        texture_raytrace[1][y][x][3] = 1.0;
        texture_raytrace[2][y][x][3] = t;
        texture_raytrace[3][y][x][3] = 1.0;
    }
    auto color = vec4(0.0, 0.0, 0.0, 1.0);
    for (auto i = 0; i < 3; ++i) {
        if (texture_raytrace[1][y][x][3] > 0.5) {
            color[i] = (texture_raytrace[0][y][x][i]) * 255.0;
        }
    }
    for (auto i = 0; i < 4; ++i) {
        pixelData[y][x][i] = static_cast<uint8_t>(color[i]);
    }
    Py_INCREF(Py_None);
    return Py_None;
}
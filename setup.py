from distutils.core import setup, Extension
import numpy

render_module = Extension(
    'renderer',
    sources=['renderer/main.cpp'],
    extra_compile_args=['-std=c++17'],
    define_macros=[
        ('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')
    ]
)

setup(
    name='GrayPython_Renderer',
    version='1.0',
    description='C++ pixel renderer for CPU raytracing',
    ext_modules=[render_module],
    include_dirs=[numpy.get_include()],
)

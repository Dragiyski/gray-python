#include <array>

template<size_t ... Indices>
std::array<float, sizeof...(Indices)> plus_vector_number(const std::array<float, sizeof...(Indices)> &vector, float number, std::index_sequence<Indices...>) {
    return {(vector[Indices] + number)...};
}

template<size_t ... Indices>
std::array<float, sizeof...(Indices)> plus_vector_vector(const std::array<float, sizeof...(Indices)> &a, const std::array<float, sizeof...(Indices)> &b, std::index_sequence<Indices...>) {
    return {(a[Indices] + b[Indices])...};
}

template<size_t ... Indices>
constexpr std::array<float, sizeof...(Indices)> minus_vector_number(const std::array<float, sizeof...(Indices)> &vector, float number, std::index_sequence<Indices...>) {
    return {(vector[Indices] - number)...};
}

template<size_t ... Indices>
constexpr std::array<float, sizeof...(Indices)> minus_vector_vector(const std::array<float, sizeof...(Indices)> &a, const std::array<float, sizeof...(Indices)> &b, std::index_sequence<Indices...>) {
    return {(a[Indices] - b[Indices])...};
}

template<size_t ... Indices>
constexpr std::array<float, sizeof...(Indices)> multiplies_vector_number(const std::array<float, sizeof...(Indices)> &vector, float number, std::index_sequence<Indices...>) {
    return {(vector[Indices] * number)...};
}

template<size_t ... Indices>
constexpr std::array<float, sizeof...(Indices)> multiplies_vector_vector(const std::array<float, sizeof...(Indices)> &a, const std::array<float, sizeof...(Indices)> &b, std::index_sequence<Indices...>) {
    return {(a[Indices] * b[Indices])...};
}

template<size_t ... Indices>
constexpr std::array<float, sizeof...(Indices)> divides_vector_number(const std::array<float, sizeof...(Indices)> &vector, float number, std::index_sequence<Indices...>) {
    return {(vector[Indices] / number)...};
}

template<size_t ... Indices>
constexpr std::array<float, sizeof...(Indices)> divides_vector_vector(const std::array<float, sizeof...(Indices)> &a, const std::array<float, sizeof...(Indices)> &b, std::index_sequence<Indices...>) {
    return {(a[Indices] / b[Indices])...};
}

template<size_t N>
std::array<float, N> operator +(const std::array<float, N> &vector, float number) {
    return plus_vector_number(vector, number, std::make_index_sequence<N>{});
}

template<size_t N>
std::array<float, N> operator +(float number, const std::array<float, N> &vector) {
    return plus_vector_number(vector, number, std::make_index_sequence<N>{});
}

template<size_t N>
std::array<float, N> operator +(const std::array<float, N> &a, const std::array<float, N> &b) {
    return plus_vector_vector(a, b, std::make_index_sequence<N>{});
}

template<size_t N>
std::array<float, N> operator -(const std::array<float, N> &vector, float number) {
    return minus_vector_number(vector, number, std::make_index_sequence<N>{});
}

template<size_t N>
std::array<float, N> operator -(float number, const std::array<float, N> &vector) {
    return minus_vector_number(vector, number, std::make_index_sequence<N>{});
}

template<size_t N>
std::array<float, N> operator -(const std::array<float, N> &a, const std::array<float, N> &b) {
    return minus_vector_vector(a, b, std::make_index_sequence<N>{});
}

template<size_t N>
std::array<float, N> operator *(const std::array<float, N> &vector, float number) {
    return multiplies_vector_number(vector, number, std::make_index_sequence<N>{});
}

template<size_t N>
std::array<float, N> operator *(float number, const std::array<float, N> &vector) {
    return multiplies_vector_number(vector, number, std::make_index_sequence<N>{});
}

template<size_t N>
std::array<float, N> operator *(const std::array<float, N> &a, const std::array<float, N> &b) {
    return multiplies_vector_vector(a, b, std::make_index_sequence<N>{});
}

template<size_t N>
std::array<float, N> operator /(const std::array<float, N> &vector, float number) {
    return divides_vector_number(vector, number, std::make_index_sequence<N>{});
}

template<size_t N>
std::array<float, N> operator /(float number, const std::array<float, N> &vector) {
    return divides_vector_number(vector, number, std::make_index_sequence<N>{});
}

template<size_t N>
std::array<float, N> operator /(const std::array<float, N> &a, const std::array<float, N> &b) {
    return divides_vector_vector(a, b, std::make_index_sequence<N>{});
}

namespace {
    template<size_t O, size_t N, size_t S, size_t ... I>
    constexpr void assign_array_function_fold(std::array<float, N> target, std::array<float, S> source, std::index_sequence<I...>) {
        ((target[O + I] = source[I]), ...);
    }

    template<size_t O, size_t N, size_t S, typename I = std::index_sequence<S>>
    constexpr void assign_array_function(std::array<float, N> target, std::array<float, S> source) {
        assign_array_function_fold<O>(target, source, I{});
    }

    template<size_t N, size_t O, typename ... Args>
    struct assign_array {};

    template<size_t N, size_t O, size_t S, typename ... Args>
    struct assign_array<N, O, std::array<float, S>, Args...> {
        static constexpr void assign(std::array<float, N> &target, std::array<float, S> &source, Args ... args) {
            assign_array_function<O>(target, source);
            assign_array<N, O + S, Args...>::assign(target, args...);
        }
    };

    template<size_t N, size_t O, typename ... Args>
    struct assign_array<N, O, float, Args...> {
        static constexpr void assign(std::array<float, N> &target, float source, Args ... args) {
            target[O] = source;
            assign_array<N, O + 1, Args...>::assign(target, args...);
        }
    };

    template<size_t N, size_t O, typename ... Args>
    struct assign_array<N, O, double, Args...> {
        static constexpr void assign(std::array<float, N> &target, double source, Args ... args) {
            target[O] = float(source);
            assign_array<N, O + 1, Args...>::assign(target, args...);
        }
    };

    template<size_t N, size_t O>
    struct assign_array<N, O> {
        static constexpr void assign(std::array<float, N> &target) {
            static_assert(N == O);
        }
    };

    template<size_t N, typename ... Args>
    constexpr std::array<float, N> make_vector(Args... args) {
        std::array<float, N> target {};
        assign_array<N, 0, Args...>::assign(target, args...);
        return target;
    }

    template<size_t ... Indices>
    constexpr float array_element_sum(std::array<float, sizeof...(Indices)> array, std::index_sequence<Indices...>) {
        return ((array[Indices]) + ...);
    }
}

template<typename ... Args>
constexpr std::array<float, 2> vec2(Args... args) {
    return make_vector<2, Args...>(args...);
}

template<typename ... Args>
constexpr std::array<float, 3> vec3(Args... args) {
    return make_vector<3, Args...>(args...);
}

template<typename ... Args>
constexpr std::array<float, 4> vec4(Args... args) {
    return make_vector<4, Args...>(args...);
}

template<size_t N>
constexpr float length(const std::array<float, N> &array) {
    return std::sqrt(array_element_sum(array * array, std::make_index_sequence<N>{}));
}

template<size_t N>
constexpr std::array<float, N> normalize(const std::array<float, N>& array) {
    return array / length(array);
}

template<size_t N>
constexpr float dot(const std::array<float, N> a, const std::array<float, N> b) {
    return array_element_sum(a * b, std::make_index_sequence<N>{});
}

constexpr std::array<float, 3> cross(const std::array<float, 3> a, const std::array<float, 3> b) {
    return {
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    };
}

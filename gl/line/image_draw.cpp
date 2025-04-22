/*
<%
import pybind11
setup_pybind11(cfg)
%>
*/

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <thread>
#include <vector>
#include <queue>
#include <tuple>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <future>

namespace py = pybind11;

// 单条线的绘制函数（Bresenham算法）
void draw_line(uint8_t* img, int width, int height, int channel, int x0, int y0, int x1, int y1, uint8_t* color) {
    int dx = std::abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -std::abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy, e2;

    while (true) {
        if (x0 >= 0 && x0 < width && y0 >= 0 && y0 < height) {
            for (int i = 0; i < channel; i++) {
                img[y0 * width * channel + x0 * channel + i] = color[i];
            }
        }
        if (x0 == x1 && y0 == y1) break;
        e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
    }
}

void draw_lines(py::array_t<uint8_t>& img_array, std::vector<std::tuple<int, int, int, int>>& lines, py::array_t<uint8_t> &color_array) {
    auto buf = img_array.request();
    uint8_t* img = static_cast<uint8_t*>(buf.ptr);

    auto color_bur = color_array.request();
    uint8_t* color = static_cast<uint8_t*>(color_bur.ptr);
    
    int width = buf.shape[1];
    int height = buf.shape[0];
    int channel = 1;
    
    if (buf.ndim == 3) {
        channel = buf.shape[2];
    }

    size_t num_lines = lines.size();

    for (size_t i = 0; i < num_lines; i += 1) {
        int x0, y0, x1, y1;
        std::tie(x0, y0, x1, y1) = lines[i];
        draw_line(img, width, height, channel, x0, y0, x1, y1, color);
    }

}


// 将函数暴露给 Python
PYBIND11_MODULE(image_draw, m) {
    m.def("draw_lines", &draw_lines, "Draw lines using a single thread",
          py::arg("img_array"), py::arg("lines"), py::arg("color"));
}

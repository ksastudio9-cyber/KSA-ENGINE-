#include "ksa_engine/native_editor.hpp"

#ifdef KSA_NATIVE_EDITOR

#include <SDL.h>
#include <SDL_opengl.h>

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdio>
#include <memory>
#include <string>
#include <vector>

namespace ksa_engine {
namespace {

constexpr double pi = 3.14159265358979323846;

void draw_cube(const Entity& entity, const Material& material, bool selected) {
    const Vec3 p = entity.transform.position;
    const Vec3 s = entity.transform.scale;
    glPushMatrix();
    glTranslated(p.x, p.y, p.z);
    glRotated(entity.transform.rotation.x * 180.0 / pi, 1.0, 0.0, 0.0);
    glRotated(entity.transform.rotation.y * 180.0 / pi, 0.0, 1.0, 0.0);
    glRotated(entity.transform.rotation.z * 180.0 / pi, 0.0, 0.0, 1.0);
    glScaled(s.x, s.y, s.z);
    const double red = static_cast<double>(material.red) / 255.0;
    const double green = static_cast<double>(material.green) / 255.0;
    const double blue = static_cast<double>(material.blue) / 255.0;
    glColor3d(selected ? 1.0 : red, selected ? 0.8 : green, selected ? 0.2 : blue);
    glBegin(GL_QUADS);
    glNormal3d(0, 1, 0); glVertex3d(-1, 1, -1); glVertex3d(1, 1, -1); glVertex3d(1, 1, 1); glVertex3d(-1, 1, 1);
    glNormal3d(0, -1, 0); glVertex3d(-1, -1, 1); glVertex3d(1, -1, 1); glVertex3d(1, -1, -1); glVertex3d(-1, -1, -1);
    glNormal3d(0, 0, 1); glVertex3d(-1, -1, 1); glVertex3d(-1, 1, 1); glVertex3d(1, 1, 1); glVertex3d(1, -1, 1);
    glNormal3d(0, 0, -1); glVertex3d(1, -1, -1); glVertex3d(1, 1, -1); glVertex3d(-1, 1, -1); glVertex3d(-1, -1, -1);
    glNormal3d(1, 0, 0); glVertex3d(1, -1, 1); glVertex3d(1, 1, 1); glVertex3d(1, 1, -1); glVertex3d(1, -1, -1);
    glNormal3d(-1, 0, 0); glVertex3d(-1, -1, -1); glVertex3d(-1, 1, -1); glVertex3d(-1, 1, 1); glVertex3d(-1, -1, 1);
    glEnd();
    glPopMatrix();
}

void draw_ground() {
    glColor3d(0.34, 0.24, 0.14);
    glNormal3d(0, 1, 0);
    glBegin(GL_QUADS);
    glVertex3d(-80, 0, -80); glVertex3d(80, 0, -80); glVertex3d(80, 0, 80); glVertex3d(-80, 0, 80);
    glEnd();
    glDisable(GL_LIGHTING);
    glColor3d(0.5, 0.38, 0.23);
    glBegin(GL_LINES);
    for (int index = -40; index <= 40; ++index) {
        glVertex3d(index * 2.0, 0.01, -80); glVertex3d(index * 2.0, 0.01, 80);
        glVertex3d(-80, 0.01, index * 2.0); glVertex3d(80, 0.01, index * 2.0);
    }
    glEnd();
    glEnable(GL_LIGHTING);
}

void set_projection(int width, int height) {
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    const double aspect = static_cast<double>(width) / static_cast<double>(std::max(1, height));
    const double half_height = std::tan(30.0 * pi / 180.0) * 0.1;
    glFrustum(-half_height * aspect, half_height * aspect, -half_height, half_height, 0.1, 300.0);
    glMatrixMode(GL_MODELVIEW);
}

}  // namespace

int run_native_editor(Scene& scene) {
    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        std::fprintf(stderr, "KSA editor: SDL initialization failed: %s\n", SDL_GetError());
        return 1;
    }
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 2);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 1);
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
    SDL_Window* window = SDL_CreateWindow("KSA Engine Native 3D Editor", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, 1280, 720, SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE);
    if (!window) {
        std::fprintf(stderr, "KSA editor: window creation failed: %s\n", SDL_GetError());
        SDL_Quit();
        return 1;
    }
    SDL_GLContext context = SDL_GL_CreateContext(window);
    if (!context) {
        std::fprintf(stderr, "KSA editor: OpenGL context creation failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    SDL_GL_SetSwapInterval(1);
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_CULL_FACE);
    glEnable(GL_COLOR_MATERIAL);
    glEnable(GL_LIGHTING);
    glEnable(GL_LIGHT0);
    const GLfloat light_position[] = {-18.0F, 30.0F, 12.0F, 0.0F};
    const GLfloat light_color[] = {1.0F, 0.88F, 0.62F, 1.0F};
    const GLfloat ambient[] = {0.28F, 0.32F, 0.38F, 1.0F};
    glLightfv(GL_LIGHT0, GL_POSITION, light_position);
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_color);
    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient);

    std::vector<std::uint64_t> editable;
    for (const auto& [id, entity] : scene.entities()) if (entity.mesh && entity.kind != "static") editable.push_back(id);
    std::sort(editable.begin(), editable.end());
    std::size_t selected_index = 0;
    double yaw = 35.0;
    double pitch = -24.0;
    double distance = 20.0;
    Vec3 camera_target{0.0, 1.0, 0.0};
    bool running = true;
    bool right_drag = false;
    int last_mouse_x = 0;
    int last_mouse_y = 0;
    char mode = 'g';
    std::uint64_t next_id = scene.entities().size() + 1;
    std::uint64_t last_ticks = SDL_GetTicks();

    while (running) {
        SDL_Event event{};
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) running = false;
            if (event.type == SDL_WINDOWEVENT && event.window.event == SDL_WINDOWEVENT_SIZE_CHANGED) set_projection(event.window.data1, event.window.data2);
            if (event.type == SDL_MOUSEBUTTONDOWN && event.button.button == SDL_BUTTON_RIGHT) { right_drag = true; last_mouse_x = event.button.x; last_mouse_y = event.button.y; }
            if (event.type == SDL_MOUSEBUTTONUP && event.button.button == SDL_BUTTON_RIGHT) right_drag = false;
            if (event.type == SDL_MOUSEMOTION && right_drag) { yaw += (event.motion.x - last_mouse_x) * 0.35; pitch = std::clamp(pitch + (event.motion.y - last_mouse_y) * 0.35, -85.0, 5.0); last_mouse_x = event.motion.x; last_mouse_y = event.motion.y; }
            if (event.type == SDL_MOUSEWHEEL) distance = std::clamp(distance - event.wheel.y, 4.0, 80.0);
            if (event.type == SDL_KEYDOWN && !event.key.repeat) {
                if (event.key.keysym.sym == SDLK_ESCAPE) running = false;
                if (event.key.keysym.sym == SDLK_1) mode = 'g';
                if (event.key.keysym.sym == SDLK_2) mode = 'r';
                if (event.key.keysym.sym == SDLK_3) mode = 's';
                if (event.key.keysym.sym == SDLK_TAB && !editable.empty()) selected_index = (selected_index + 1) % editable.size();
                if (event.key.keysym.sym == SDLK_b) {
                    auto& block = scene.create_entity("Block " + std::to_string(next_id++), "mesh", {{0.0, 1.0, 0.0}, {}, {1.0, 1.0, 1.0}, 0});
                    block.mesh = std::make_unique<MeshComponent>(); block.material = std::make_unique<Material>();
                    block.material->red = 205; block.material->green = 150; block.material->blue = 55;
                    editable.push_back(block.id); selected_index = editable.size() - 1;
                }
                if (event.key.keysym.sym == SDLK_DELETE && !editable.empty()) { scene.destroy_entity(editable[selected_index]); editable.erase(editable.begin() + static_cast<std::ptrdiff_t>(selected_index)); if (!editable.empty()) selected_index %= editable.size(); }
            }
        }
        const std::uint64_t ticks = SDL_GetTicks();
        const double delta = std::min(0.05, static_cast<double>(ticks - last_ticks) / 1000.0); last_ticks = ticks;
        const std::uint8_t* keys = SDL_GetKeyboardState(nullptr);
        const double speed = keys[SDL_SCANCODE_LSHIFT] ? 12.0 : 6.0;
        const double radians = yaw * pi / 180.0;
        const Vec3 forward{-std::sin(radians), 0.0, -std::cos(radians)};
        const Vec3 right{std::cos(radians), 0.0, -std::sin(radians)};
        if (keys[SDL_SCANCODE_W]) camera_target += forward * (speed * delta);
        if (keys[SDL_SCANCODE_S]) camera_target += forward * (-speed * delta);
        if (keys[SDL_SCANCODE_A]) camera_target += right * (-speed * delta);
        if (keys[SDL_SCANCODE_D]) camera_target += right * (speed * delta);
        if (!editable.empty()) {
            Entity* selected = scene.find(editable[selected_index]);
            if (selected) {
                const double amount = (keys[SDL_SCANCODE_LSHIFT] ? 3.0 : 1.0) * delta;
                if (mode == 'g') { if (keys[SDL_SCANCODE_UP]) selected->transform.position += forward * amount; if (keys[SDL_SCANCODE_DOWN]) selected->transform.position += forward * (-amount); if (keys[SDL_SCANCODE_LEFT]) selected->transform.position += right * (-amount); if (keys[SDL_SCANCODE_RIGHT]) selected->transform.position += right * amount; }
                if (mode == 'r') { if (keys[SDL_SCANCODE_LEFT]) selected->transform.rotation.y -= amount * 2.0; if (keys[SDL_SCANCODE_RIGHT]) selected->transform.rotation.y += amount * 2.0; }
                if (mode == 's') { if (keys[SDL_SCANCODE_UP]) selected->transform.scale += Vec3{amount, amount, amount}; if (keys[SDL_SCANCODE_DOWN]) selected->transform.scale = selected->transform.scale - Vec3{amount, amount, amount}; }
            }
        }
        glClearColor(0.28F, 0.48F, 0.58F, 1.0F); glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
        int width = 0; int height = 0; SDL_GetWindowSize(window, &width, &height); set_projection(width, height);
        glLoadIdentity();
        glRotated(-pitch, 1, 0, 0); glRotated(-yaw, 0, 1, 0); glTranslated(-camera_target.x, -camera_target.y - 3.0, -camera_target.z - distance);
        draw_ground();
        for (const auto& [id, entity] : scene.entities()) if (entity.mesh && entity.active && entity.kind != "camera" && entity.kind != "light") draw_cube(entity, entity.material ? *entity.material : Material{}, !editable.empty() && id == editable[selected_index]);
        SDL_GL_SwapWindow(window);
    }
    SDL_GL_DeleteContext(context); SDL_DestroyWindow(window); SDL_Quit();
    return 0;
}

}  // namespace ksa_engine

#endif

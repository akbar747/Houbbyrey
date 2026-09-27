/*
 * 视觉震撼的 Windows C 语言烟花秀
 * 编译：gcc fireworks.c -O2 -std=c11 -o fireworks.exe -lgdi32 -luser32 -lm -mwindows
 *
 * 操作：
 *   鼠标左键  : 在鼠标位置放一朵烟花
 *   空格      : 同时发射三枚烟花
 *   ESC       : 退出
 *
 * 特点：
 *   - 纯 Win32 API，不需要 SDL、OpenGL 或图片资源
 *   - 拖尾辉光、冲击波、烟花的上升尾迹
 *   - 牡丹、光环、爱心、五角星、柳树、双重环六种爆炸
 *   - 星空、月亮、城市剪影和江面倒影
 */
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0601
#include <windows.h>
#include <windowsx.h>
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>

#define WIDTH 1280
#define HEIGHT 800
#define MAX_PARTICLES 12000
#define MAX_ROCKETS 64
#define MAX_WAVES 48
#define MAX_BUILDINGS 40
#define PI_F 3.14159265358979323846f

typedef struct {
    float x, y;
    float vx, vy;
    float life, max_life;
    float size;
    float drag;
    float gravity;
    float phase;
    unsigned char r, g, b;
} Particle;

typedef struct {
    float x, y;
    float sx, sy, tx, ty;
    float t, speed;
    float wobble, phase;
    unsigned char r, g, b;
} Rocket;

typedef struct {
    float x, y, radius, life, max_life;
    unsigned char r, g, b;
} ShockWave;

typedef struct {
    int x, w, h;
    int seed;
} Building;

static Particle particles[MAX_PARTICLES];
static int particle_count = 0;
static Rocket rockets[MAX_ROCKETS];
static int rocket_count = 0;
static ShockWave waves[MAX_WAVES];
static int wave_count = 0;
static Building buildings[MAX_BUILDINGS];
static int building_count = 0;
static uint32_t *pixels = NULL;
static int running = 1;
static int frame_no = 0;
static int next_launch = 25;
static HWND g_hwnd = NULL;

static const unsigned char COLORS[12][3] = {
    {255, 60, 70},  {255, 145, 45}, {255, 225, 65}, {120, 255, 90},
    {55, 255, 190}, {55, 190, 255}, {90, 110, 255}, {205, 80, 255},
    {255, 85, 185}, {255, 255, 235}, {130, 255, 255}, {255, 180, 120}
};

static inline float frand(void) { return (float)rand() / (float)RAND_MAX; }
static inline float fclamp(float v, float a, float b) { return v < a ? a : (v > b ? b : v); }
static inline int iclamp(int v, int a, int b) { return v < a ? a : (v > b ? b : v); }

static inline uint32_t rgb_pack(int r, int g, int b) {
    return ((uint32_t)iclamp(r, 0, 255) << 16) |
           ((uint32_t)iclamp(g, 0, 255) << 8) |
           (uint32_t)iclamp(b, 0, 255);
}

static inline void add_pixel(int x, int y, int r, int g, int b, int alpha) {
    if ((unsigned)x >= WIDTH || (unsigned)y >= HEIGHT || alpha <= 0) return;
    if (alpha > 255) alpha = 255;
    uint32_t p = pixels[y * WIDTH + x];
    int dr = (p >> 16) & 255;
    int dg = (p >> 8) & 255;
    int db = p & 255;
    dr += (r * alpha) >> 8;
    dg += (g * alpha) >> 8;
    db += (b * alpha) >> 8;
    pixels[y * WIDTH + x] = rgb_pack(dr, dg, db);
}

static inline void blend_pixel(int x, int y, int r, int g, int b, int alpha) {
    if ((unsigned)x >= WIDTH || (unsigned)y >= HEIGHT || alpha <= 0) return;
    if (alpha > 255) alpha = 255;
    uint32_t p = pixels[y * WIDTH + x];
    int dr = (p >> 16) & 255;
    int dg = (p >> 8) & 255;
    int db = p & 255;
    int inv = 255 - alpha;
    dr = (dr * inv + r * alpha) >> 8;
    dg = (dg * inv + g * alpha) >> 8;
    db = (db * inv + b * alpha) >> 8;
    pixels[y * WIDTH + x] = rgb_pack(dr, dg, db);
}

static void blend_rect(int x0, int y0, int w, int h, int r, int g, int b, int a) {
    int x1 = x0 + w, y1 = y0 + h;
    if (x0 < 0) x0 = 0;
    if (y0 < 0) y0 = 0;
    if (x1 > WIDTH) x1 = WIDTH;
    if (y1 > HEIGHT) y1 = HEIGHT;
    for (int y = y0; y < y1; ++y)
        for (int x = x0; x < x1; ++x)
            blend_pixel(x, y, r, g, b, a);
}

static void draw_glow(float x, float y, float radius,
                      int r, int g, int b, float intensity) {
    if (radius < 0.6f) radius = 0.6f;
    int cx = (int)x, cy = (int)y;
    int rr = (int)(radius + 0.5f);
    float rr2 = radius * radius;
    for (int dy = -rr; dy <= rr; ++dy) {
        for (int dx = -rr; dx <= rr; ++dx) {
            float d2 = (float)(dx * dx + dy * dy);
            if (d2 > rr2) continue;
            float t = 1.0f - d2 / rr2;
            int a = (int)(255.0f * intensity * t * t);
            add_pixel(cx + dx, cy + dy, r, g, b, a);
        }
    }
    add_pixel(cx, cy, 255, 255, 255, (int)(220.0f * intensity));
}

static void add_particle(float x, float y, float vx, float vy,
                         float life, float size, float drag, float gravity,
                         int r, int g, int b) {
    if (particle_count >= MAX_PARTICLES) return;
    Particle *p = &particles[particle_count++];
    p->x = x; p->y = y;
    p->vx = vx; p->vy = vy;
    p->life = life; p->max_life = life;
    p->size = size;
    p->drag = drag;
    p->gravity = gravity;
    p->phase = frand() * 100.0f;
    p->r = (unsigned char)iclamp(r, 0, 255);
    p->g = (unsigned char)iclamp(g, 0, 255);
    p->b = (unsigned char)iclamp(b, 0, 255);
}

static void add_wave(float x, float y, int r, int g, int b) {
    if (wave_count >= MAX_WAVES) return;
    ShockWave *w = &waves[wave_count++];
    w->x = x; w->y = y;
    w->radius = 4.0f;
    w->life = w->max_life = 34.0f;
    w->r = (unsigned char)r;
    w->g = (unsigned char)g;
    w->b = (unsigned char)b;
}

static void explode(float x, float y) {
    int c1 = rand() % 12;
    int c2 = rand() % 12;
    if (c2 == c1) c2 = (c2 + 5) % 12;
    int pattern = rand() % 6;
    int count = 430 + rand() % 310;

    for (int i = 0; i < count; ++i) {
        float a = (2.0f * PI_F * (float)i) / (float)count;
        float ex = cosf(a), ey = sinf(a);
        float speed = 2.6f + frand() * 2.6f;
        float life = 55.0f + frand() * 45.0f;
        float gravity = 0.030f;
        float drag = 0.982f;

        if (pattern == 1) {
            speed = 3.7f + frand() * 0.55f;
            life = 62.0f + frand() * 30.0f;
        } else if (pattern == 2) {
            float hx = 16.0f * sinf(a) * sinf(a) * sinf(a);
            float hy = -(13.0f * cosf(a) - 5.0f * cosf(2.0f * a)
                         - 2.0f * cosf(3.0f * a) - cosf(4.0f * a));
            float inv = 1.0f / fmaxf(0.001f, sqrtf(hx * hx + hy * hy));
            ex = hx * inv;
            ey = hy * inv;
            speed = 3.9f + frand() * 0.45f;
            life = 75.0f + frand() * 30.0f;
        } else if (pattern == 3) {
            float star_r = 0.55f + 0.45f * cosf(5.0f * a);
            ex = cosf(a) * star_r;
            ey = sinf(a) * star_r;
            float inv = 1.0f / fmaxf(0.001f, sqrtf(ex * ex + ey * ey));
            ex *= inv; ey *= inv;
            speed = 3.9f + frand() * 0.8f;
            life = 65.0f + frand() * 35.0f;
        } else if (pattern == 4) {
            ex = cosf(a) * (0.60f + frand() * 0.65f);
            ey = -0.45f - 0.95f * fabsf(sinf(a)) + frand() * 0.35f;
            speed = 2.0f + frand() * 2.0f;
            life = 105.0f + frand() * 45.0f;
            gravity = 0.070f;
            drag = 0.990f;
        } else if (pattern == 5) {
            float ring = (i & 1) ? 4.7f : 2.6f;
            speed = ring + frand() * 0.45f;
            life = 60.0f + frand() * 40.0f;
        }

        float jitter = 0.88f + frand() * 0.28f;
        int use_second = (pattern == 4 || (pattern == 5 && (i & 1))) ^ (i % 7 == 0);
        int ci = use_second ? c2 : c1;
        add_particle(x, y,
                     ex * speed * jitter + (frand() - 0.5f) * 0.35f,
                     ey * speed * jitter + (frand() - 0.5f) * 0.35f,
                     life,
                     1.25f + frand() * 1.85f,
                     drag, gravity,
                     COLORS[ci][0], COLORS[ci][1], COLORS[ci][2]);
    }

    /* 亮色细碎星尘，让爆炸边缘更丰富。 */
    for (int i = 0; i < 130; ++i) {
        float a = frand() * 2.0f * PI_F;
        float s = 0.6f + frand() * 5.2f;
        int ci = (i & 1) ? c1 : c2;
        add_particle(x, y, cosf(a) * s, sinf(a) * s,
                     35.0f + frand() * 55.0f,
                     0.8f + frand() * 1.2f,
                     0.975f, 0.020f,
                     COLORS[ci][0], COLORS[ci][1], COLORS[ci][2]);
    }

    add_wave(x, y, COLORS[c1][0], COLORS[c1][1], COLORS[c1][2]);
    if (pattern == 4 || pattern == 5) {
        add_wave(x, y, COLORS[c2][0], COLORS[c2][1], COLORS[c2][2]);
    }
}

static void launch_rocket(float tx, float ty, int fast) {
    if (rocket_count >= MAX_ROCKETS) return;
    Rocket *r = &rockets[rocket_count++];
    r->sx = tx + (frand() - 0.5f) * 80.0f;
    r->sy = (float)(HEIGHT - 40 - rand() % 55);
    r->x = r->sx; r->y = r->sy;
    r->tx = fclamp(tx, 80.0f, WIDTH - 80.0f);
    r->ty = fclamp(ty, 90.0f, HEIGHT * 0.62f);
    r->t = 0.0f;
    r->speed = fast ? (0.030f + frand() * 0.010f) : (0.012f + frand() * 0.010f);
    r->wobble = 4.0f + frand() * 13.0f;
    r->phase = frand() * 10.0f;
    int ci = rand() % 12;
    r->r = COLORS[ci][0]; r->g = COLORS[ci][1]; r->b = COLORS[ci][2];
}

static void init_buildings(void) {
    building_count = 0;
    int x = -20;
    while (x < WIDTH + 20 && building_count < MAX_BUILDINGS) {
        Building *b = &buildings[building_count++];
        b->x = x;
        b->w = 34 + rand() % 62;
        b->h = 65 + rand() % 145;
        b->seed = rand();
        x += b->w - (rand() % 10);
    }
}

static void update_particles(void) {
    for (int i = 0; i < particle_count; ) {
        Particle *p = &particles[i];
        p->vy += p->gravity;
        p->vx *= p->drag;
        p->vy *= p->drag;
        p->x += p->vx;
        p->y += p->vy;
        p->life -= 1.0f;
        if (p->life <= 0.0f || p->y > HEIGHT + 80.0f) {
            particles[i] = particles[--particle_count];
        } else {
            ++i;
        }
    }
}

static void update_rockets(void) {
    for (int i = 0; i < rocket_count; ) {
        Rocket *r = &rockets[i];
        r->t += r->speed;
        float t = fclamp(r->t, 0.0f, 1.0f);
        float ease = t * (2.0f - t);
        r->x = r->sx + (r->tx - r->sx) * ease +
               sinf(t * 9.0f + r->phase) * r->wobble * (1.0f - t);
        r->y = r->sy + (r->ty - r->sy) * ease;

        for (int k = 0; k < 2; ++k) {
            add_particle(r->x + (frand() - 0.5f) * 4.0f,
                         r->y + 4.0f + frand() * 7.0f,
                         (frand() - 0.5f) * 0.65f,
                         0.45f + frand() * 1.0f,
                         12.0f + frand() * 15.0f,
                         1.0f + frand() * 1.4f,
                         0.955f, 0.005f,
                         255, 185 + rand() % 70, 80 + rand() % 100);
        }

        if (r->t >= 1.0f) {
            explode(r->tx, r->ty);
            rockets[i] = rockets[--rocket_count];
        } else {
            ++i;
        }
    }
}

static void update_waves(void) {
    for (int i = 0; i < wave_count; ) {
        ShockWave *w = &waves[i];
        w->radius += 5.8f;
        w->life -= 1.0f;
        if (w->life <= 0.0f) {
            waves[i] = waves[--wave_count];
        } else {
            ++i;
        }
    }
}

static void draw_background(void) {
    int ground_y = HEIGHT - 168;

    /* 星空。星星每帧叠加，配合画面衰减形成闪烁。 */
    for (int i = 0; i < 170; ++i) {
        int x = (i * 97 + 31) % WIDTH;
        int y = (i * 53 + 17) % ground_y;
        float tw = 0.45f + 0.55f * sinf(frame_no * 0.035f + i * 1.7f);
        int a = (int)(18.0f + 48.0f * tw);
        add_pixel(x, y, 180, 210, 255, a);
        if ((i % 13) == 0) add_pixel(x + 1, y, 110, 160, 255, a / 2);
    }

    /* 月亮。 */
    draw_glow(WIDTH * 0.84f, 112.0f, 76.0f, 70, 120, 190, 0.34f);
    draw_glow(WIDTH * 0.84f, 112.0f, 29.0f, 205, 225, 255, 0.68f);

    /* 江面深色底色。 */
    for (int y = ground_y; y < HEIGHT; y += 2) {
        float t = (float)(y - ground_y) / (float)(HEIGHT - ground_y);
        blend_rect(0, y, WIDTH, 2, 3, 10, 25, (int)(100 + 60 * t));
    }

    /* 城市剪影和窗户灯光。 */
    for (int i = 0; i < building_count; ++i) {
        Building *b = &buildings[i];
        int top = ground_y - b->h;
        blend_rect(b->x, top, b->w, b->h, 4, 10, 24, 220);
        blend_rect(b->x + 2, top, b->w - 4, 3, 32, 55, 82, 180);
        for (int wy = top + 12; wy < ground_y - 8; wy += 13) {
            for (int wx = b->x + 7; wx < b->x + b->w - 7; wx += 12) {
                int v = (wx * 17 + wy * 31 + b->seed) & 31;
                if (v < 8) {
                    int warm = (v & 1);
                    add_pixel(wx, wy, warm ? 255 : 120,
                              warm ? 180 : 210,
                              warm ? 70 : 255, 75 + (v * 4));
                }
            }
        }
    }

    /* 水面反光线。 */
    for (int y = ground_y + 17; y < HEIGHT; y += 19) {
        int len = 80 + ((y * 37 + frame_no) % 240);
        int x = (y * 71) % (WIDTH - len);
        blend_rect(x, y, len, 1, 40, 100, 150, 30);
    }
}

static void draw_waves(void) {
    for (int i = 0; i < wave_count; ++i) {
        ShockWave *w = &waves[i];
        float life = w->life / w->max_life;
        int alpha = (int)(95.0f * life * life);
        int steps = 150;
        for (int k = 0; k < steps; ++k) {
            float a = 2.0f * PI_F * (float)k / (float)steps;
            int x = (int)(w->x + cosf(a) * w->radius);
            int y = (int)(w->y + sinf(a) * w->radius);
            add_pixel(x, y, w->r, w->g, w->b, alpha);
        }
    }
}

static void draw_rockets(void) {
    for (int i = 0; i < rocket_count; ++i) {
        Rocket *r = &rockets[i];
        draw_glow(r->x, r->y, 11.0f, r->r, r->g, r->b, 0.82f);
        draw_glow(r->x, r->y + 7.0f, 7.0f, 255, 180, 80, 0.70f);
        for (int k = 1; k <= 5; ++k) {
            int a = 80 - k * 13;
            if (a > 0) add_pixel((int)r->x, (int)r->y + k * 4,
                                 255, 170 + k * 8, 65, a);
        }
    }
}

static void draw_particles(void) {
    for (int i = 0; i < particle_count; ++i) {
        Particle *p = &particles[i];
        float ratio = p->life / p->max_life;
        float twinkle = 0.74f + 0.26f * sinf(frame_no * 0.35f + p->phase);
        float intensity = (0.22f + 0.90f * ratio) * twinkle;
        float radius = p->size * (0.85f + ratio * 1.15f);
        draw_glow(p->x, p->y, radius, p->r, p->g, p->b, intensity);
    }
}

static void update_scene(void) {
    ++frame_no;

    if (--next_launch <= 0) {
        int count = 1;
        if ((rand() % 9) == 0) count = 2;
        for (int i = 0; i < count; ++i) {
            float tx = 120.0f + frand() * (WIDTH - 240.0f);
            float ty = 85.0f + frand() * 290.0f;
            launch_rocket(tx, ty, 0);
        }
        next_launch = 28 + rand() % 45;
    }

    update_rockets();
    update_particles();
    update_waves();
}

static void render_scene(void) {
    /* 微微衰减而不是彻底清屏，形成漂亮的光轨。 */
    for (int i = 0; i < WIDTH * HEIGHT; ++i) {
        uint32_t p = pixels[i] & 0x00FFFFFFu;
        pixels[i] = p - ((p >> 3) & 0x001F1F1Fu);
    }

    draw_background();
    draw_waves();
    draw_rockets();
    draw_particles();
}

static void present(HDC hdc) {
    BITMAPINFO bmi;
    ZeroMemory(&bmi, sizeof(bmi));
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = WIDTH;
    bmi.bmiHeader.biHeight = -HEIGHT;
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;
    StretchDIBits(hdc, 0, 0, WIDTH, HEIGHT,
                  0, 0, WIDTH, HEIGHT,
                  pixels, &bmi, DIB_RGB_COLORS, SRCCOPY);
}

static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    switch (msg) {
    case WM_CREATE:
        g_hwnd = hwnd;
        SetTimer(hwnd, 1, 16, NULL);
        return 0;
    case WM_ERASEBKGND:
        return 1;
    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        present(hdc);
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_TIMER:
        update_scene();
        render_scene();
        InvalidateRect(hwnd, NULL, FALSE);
        return 0;
    case WM_LBUTTONDOWN: {
        int x = GET_X_LPARAM(lp);
        int y = GET_Y_LPARAM(lp);
        launch_rocket((float)x, (float)y, 1);
        return 0;
    }
    case WM_KEYDOWN:
        if (wp == VK_ESCAPE) DestroyWindow(hwnd);
        if (wp == VK_SPACE) {
            for (int i = 0; i < 3; ++i)
                launch_rocket(180.0f + frand() * (WIDTH - 360.0f),
                              80.0f + frand() * 320.0f, 1);
        }
        return 0;
    case WM_DESTROY:
        KillTimer(hwnd, 1);
        PostQuitMessage(0);
        return 0;
    default:
        return DefWindowProc(hwnd, msg, wp, lp);
    }
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance,
                   LPSTR lpCmdLine, int nCmdShow) {
    (void)hPrevInstance;
    (void)lpCmdLine;

    SetProcessDPIAware();
    srand((unsigned)time(NULL) ^ (unsigned)GetTickCount());
    init_buildings();

    WNDCLASSEXA wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)GetStockObject(BLACK_BRUSH);
    wc.lpszClassName = "FireworksWindowsClass";
    if (!RegisterClassExA(&wc)) return 1;

    RECT rect = {0, 0, WIDTH, HEIGHT};
    AdjustWindowRect(&rect, WS_OVERLAPPEDWINDOW & ~WS_THICKFRAME & ~WS_MAXIMIZEBOX, FALSE);
    int win_w = rect.right - rect.left;
    int win_h = rect.bottom - rect.top;
    int win_x = (GetSystemMetrics(SM_CXSCREEN) - win_w) / 2;
    int win_y = (GetSystemMetrics(SM_CYSCREEN) - win_h) / 2;

    HWND hwnd = CreateWindowExA(
        0, wc.lpszClassName, "C Fireworks - Click to launch - ESC to quit",
        WS_OVERLAPPEDWINDOW & ~WS_THICKFRAME & ~WS_MAXIMIZEBOX,
        win_x, win_y, win_w, win_h,
        NULL, NULL, hInstance, NULL);
    if (!hwnd) return 1;

    HDC screen_dc = GetDC(hwnd);
    BITMAPINFO bmi;
    ZeroMemory(&bmi, sizeof(bmi));
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER);
    bmi.bmiHeader.biWidth = WIDTH;
    bmi.bmiHeader.biHeight = -HEIGHT;
    bmi.bmiHeader.biPlanes = 1;
    bmi.bmiHeader.biBitCount = 32;
    bmi.bmiHeader.biCompression = BI_RGB;
    HBITMAP bitmap = CreateDIBSection(screen_dc, &bmi, DIB_RGB_COLORS,
                                      (void **)&pixels, NULL, 0);
    ReleaseDC(hwnd, screen_dc);
    if (!bitmap || !pixels) {
        if (bitmap) DeleteObject(bitmap);
        return 1;
    }
    for (int i = 0; i < WIDTH * HEIGHT; ++i) pixels[i] = 0;

    ShowWindow(hwnd, nCmdShow);
    UpdateWindow(hwnd);

    MSG msg;
    while (running) {
        while (PeekMessage(&msg, NULL, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) running = 0;
            TranslateMessage(&msg);
            DispatchMessage(&msg);
        }
        if (!running) break;
        Sleep(1);
    }

    DeleteObject(bitmap);
    return (int)msg.wParam;
}
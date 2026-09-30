#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0601
#include <windows.h>
#include <windowsx.h>
#include <wchar.h>
#include <wctype.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <errno.h>
#include <limits.h>

#define APP_TITLE L"C语言数学工具箱"
#define MAX_PAGE_CONTROLS 80
#define PAGE_COUNT 6

#define COLOR_BG RGB(13, 17, 27)
#define COLOR_PANEL RGB(24, 31, 47)
#define COLOR_EDIT RGB(8, 12, 21)
#define COLOR_TEXT RGB(238, 243, 250)
#define COLOR_MUTED RGB(145, 160, 184)
#define COLOR_ACCENT RGB(255, 148, 64)
#define COLOR_BLUE RGB(70, 170, 255)
#define COLOR_GREEN RGB(56, 205, 128)
#define COLOR_RED RGB(245, 82, 92)
#define COLOR_BUTTON RGB(39, 49, 68)
#define COLOR_BUTTON2 RGB(52, 66, 92)

#define ID_NAV_BASE 100
#define ID_CALC_DIGIT_BASE 200
#define ID_CALC_DOT 210
#define ID_CALC_DIV 211
#define ID_CALC_MUL 212
#define ID_CALC_SUB 213
#define ID_CALC_ADD 214
#define ID_CALC_LPAREN 215
#define ID_CALC_RPAREN 216
#define ID_CALC_CLEAR 217
#define ID_CALC_BACK 218
#define ID_CALC_EQUAL 219
#define ID_PRIME_CHECK 300
#define ID_PRIME_LIST 301
#define ID_NARC_CALC 310
#define ID_GCD_CALC 320
#define ID_FIB_NTH 330
#define ID_FIB_LIST 331

static HINSTANCE g_instance;
static HWND g_hwnd;
static HWND g_nav[PAGE_COUNT];
static HWND g_page_controls[PAGE_COUNT][MAX_PAGE_CONTROLS];
static int g_page_count[PAGE_COUNT];
static int g_current_page = 0;
static HFONT g_font;
static HFONT g_font_small;
static HFONT g_font_title;
static HBRUSH g_bg_brush;
static HBRUSH g_panel_brush;
static HBRUSH g_edit_brush;

static HWND g_calc_display;
static HWND g_calc_status;
static wchar_t g_calc_expr[512] = L"";

static HWND g_prime_input;
static HWND g_prime_result;
static HWND g_narc_start;
static HWND g_narc_end;
static HWND g_narc_result;
static HWND g_gcd_a;
static HWND g_gcd_b;
static HWND g_gcd_result;
static HWND g_fib_n;
static HWND g_fib_result;

static void switch_page(int page);

static void add_page_control(int page, HWND hwnd) {
    if (page < 0 || page >= PAGE_COUNT || !hwnd) return;
    if (g_page_count[page] < MAX_PAGE_CONTROLS)
        g_page_controls[page][g_page_count[page]++] = hwnd;
}

static HWND make_control(int page, LPCWSTR cls, LPCWSTR text, DWORD style,
                         int x, int y, int w, int h, int id) {
    HWND hwnd = CreateWindowExW(
        0, cls, text, WS_CHILD | style,
        x, y, w, h, g_hwnd, (HMENU)(INT_PTR)id, g_instance, NULL);
    if (hwnd) {
        SendMessageW(hwnd, WM_SETFONT, (WPARAM)g_font, TRUE);
        add_page_control(page, hwnd);
    }
    return hwnd;
}

static HWND make_button(int page, LPCWSTR text, int x, int y, int w, int h, int id) {
    return make_control(page, L"BUTTON", text, WS_TABSTOP | BS_OWNERDRAW,
                        x, y, w, h, id);
}

static HWND make_label(int page, LPCWSTR text, int x, int y, int w, int h) {
    return make_control(page, L"STATIC", text, SS_LEFT | SS_NOPREFIX,
                        x, y, w, h, 0);
}

static HWND make_input(int page, int x, int y, int w, int h, int id) {
    return make_control(page, L"EDIT", L"",
                        WS_TABSTOP | WS_BORDER | ES_AUTOHSCROLL,
                        x, y, w, h, id);
}

static HWND make_result(int page, int x, int y, int w, int h) {
    return make_control(page, L"EDIT", L"结果会显示在这里。",
                        WS_VSCROLL | WS_BORDER | ES_MULTILINE |
                        ES_AUTOVSCROLL | ES_READONLY,
                        x, y, w, h, 0);
}

static void center_window(HWND hwnd, int width, int height) {
    RECT rc = {0, 0, width, height};
    AdjustWindowRectEx(&rc, WS_OVERLAPPEDWINDOW & ~WS_THICKFRAME & ~WS_MAXIMIZEBOX,
                       FALSE, 0);
    int w = rc.right - rc.left;
    int h = rc.bottom - rc.top;
    int x = (GetSystemMetrics(SM_CXSCREEN) - w) / 2;
    int y = (GetSystemMetrics(SM_CYSCREEN) - h) / 2;
    SetWindowPos(hwnd, NULL, x, y, w, h, SWP_NOZORDER | SWP_NOACTIVATE);
}

static void set_result(HWND edit, const wchar_t *text) {
    SetWindowTextW(edit, text && *text ? text : L"");
    SendMessageW(edit, EM_SETSEL, 0, 0);
    SendMessageW(edit, EM_SCROLLCARET, 0, 0);
}

static BOOL appendf(wchar_t *buf, size_t cap, size_t *len,
                    const wchar_t *fmt, ...) {
    if (!buf || !len || *len >= cap - 1) return FALSE;
    va_list ap;
    va_start(ap, fmt);
    int n = vswprintf(buf + *len, cap - *len, fmt, ap);
    va_end(ap);
    if (n < 0) return FALSE;
    size_t add = (size_t)n;
    if (add > cap - 1 - *len) add = cap - 1 - *len;
    *len += add;
    buf[*len] = L'\0';
    return TRUE;
}

static BOOL parse_ull(const wchar_t *text, unsigned long long *out) {
    if (!text || !out) return FALSE;
    while (*text && iswspace(*text)) ++text;
    if (!*text) return FALSE;
    errno = 0;
    wchar_t *end = NULL;
    unsigned long long v = wcstoull(text, &end, 10);
    while (end && *end && iswspace(*end)) ++end;
    if (end == text || !end || *end || errno == ERANGE) return FALSE;
    *out = v;
    return TRUE;
}

static BOOL parse_ll(const wchar_t *text, long long *out) {
    if (!text || !out) return FALSE;
    while (*text && iswspace(*text)) ++text;
    if (!*text) return FALSE;
    errno = 0;
    wchar_t *end = NULL;
    long long v = wcstoll(text, &end, 10);
    while (end && *end && iswspace(*end)) ++end;
    if (end == text || !end || *end || errno == ERANGE) return FALSE;
    *out = v;
    return TRUE;
}

static void get_control_text(HWND hwnd, wchar_t *buf, int cap) {
    if (!buf || cap <= 0) return;
    buf[0] = L'\0';
    if (hwnd) GetWindowTextW(hwnd, buf, cap);
}

/* -------------------- 表达式计算器 -------------------- */
typedef struct {
    const wchar_t *s;
    int pos;
    int error; /* 1 语法错误，2 除数为零 */
} Parser;

static void parser_skip(Parser *p) {
    while (p->s[p->pos] && iswspace(p->s[p->pos])) ++p->pos;
}

static double parse_expression(Parser *p);

static double parse_number(Parser *p) {
    parser_skip(p);
    BOOL has_digit = FALSE;
    double value = 0.0;
    while (iswdigit(p->s[p->pos])) {
        has_digit = TRUE;
        value = value * 10.0 + (p->s[p->pos] - L'0');
        ++p->pos;
    }
    if (p->s[p->pos] == L'.') {
        ++p->pos;
        double scale = 0.1;
        while (iswdigit(p->s[p->pos])) {
            has_digit = TRUE;
            value += (p->s[p->pos] - L'0') * scale;
            scale *= 0.1;
            ++p->pos;
        }
    }
    if (!has_digit) {
        p->error = 1;
        return 0.0;
    }
    return value;
}

static double parse_factor(Parser *p) {
    parser_skip(p);
    if (p->s[p->pos] == L'+') {
        ++p->pos;
        return parse_factor(p);
    }
    if (p->s[p->pos] == L'-') {
        ++p->pos;
        return -parse_factor(p);
    }
    if (p->s[p->pos] == L'(') {
        ++p->pos;
        double v = parse_expression(p);
        parser_skip(p);
        if (p->s[p->pos] != L')') {
            p->error = 1;
            return 0.0;
        }
        ++p->pos;
        return v;
    }
    return parse_number(p);
}

static double parse_term(Parser *p) {
    double value = parse_factor(p);
    for (;;) {
        parser_skip(p);
        wchar_t op = p->s[p->pos];
        if (op != L'*' && op != L'/' && op != L'×' && op != L'÷') break;
        ++p->pos;
        double rhs = parse_factor(p);
        if (p->error) return 0.0;
        if ((op == L'/' || op == L'÷') && fabs(rhs) < 1e-15) {
            p->error = 2;
            return 0.0;
        }
        if (op == L'*' || op == L'×') value *= rhs;
        else value /= rhs;
    }
    return value;
}

static double parse_expression(Parser *p) {
    double value = parse_term(p);
    for (;;) {
        parser_skip(p);
        wchar_t op = p->s[p->pos];
        if (op != L'+' && op != L'-') break;
        ++p->pos;
        double rhs = parse_term(p);
        if (p->error) return 0.0;
        if (op == L'+') value += rhs;
        else value -= rhs;
    }
    return value;
}

static void update_calc_display(void) {
    wchar_t view[600];
    size_t j = 0;
    for (size_t i = 0; g_calc_expr[i] && j + 2 < sizeof(view) / sizeof(view[0]); ++i) {
        wchar_t c = g_calc_expr[i];
        if (c == L'*') c = L'×';
        else if (c == L'/') c = L'÷';
        view[j++] = c;
    }
    view[j] = L'\0';
    SetWindowTextW(g_calc_display, view);
}

static void calc_append(wchar_t c) {
    size_t n = wcslen(g_calc_expr);
    if (n + 1 >= sizeof(g_calc_expr) / sizeof(g_calc_expr[0])) return;
    g_calc_expr[n] = c;
    g_calc_expr[n + 1] = L'\0';
    update_calc_display();
    SetWindowTextW(g_calc_status, L"");
}

static void calc_clear(void) {
    g_calc_expr[0] = L'\0';
    update_calc_display();
    SetWindowTextW(g_calc_status, L"已清空");
}

static void calc_backspace(void) {
    size_t n = wcslen(g_calc_expr);
    if (n > 0) g_calc_expr[n - 1] = L'\0';
    update_calc_display();
}

static void calc_equal(void) {
    Parser p = {g_calc_expr, 0, 0};
    if (!g_calc_expr[0]) return;
    double value = parse_expression(&p);
    parser_skip(&p);
    if (p.error == 2) {
        SetWindowTextW(g_calc_status, L"错误：除数不能为 0");
        return;
    }
    if (p.error || g_calc_expr[p.pos] != L'\0' || !isfinite(value)) {
        SetWindowTextW(g_calc_status, L"错误：表达式不正确");
        return;
    }
    wchar_t result[128];
    swprintf(result, sizeof(result) / sizeof(result[0]), L"%.12g", value);
    SetWindowTextW(g_calc_status, result);
    wcsncpy(g_calc_expr, result, sizeof(g_calc_expr) / sizeof(g_calc_expr[0]) - 1);
    g_calc_expr[sizeof(g_calc_expr) / sizeof(g_calc_expr[0]) - 1] = L'\0';
    update_calc_display();
}

/* -------------------- 数学算法 -------------------- */
static BOOL is_prime_ull(unsigned long long n) {
    if (n < 2) return FALSE;
    if (n == 2) return TRUE;
    if (n % 2 == 0) return FALSE;
    for (unsigned long long d = 3; d <= n / d; d += 2)
        if (n % d == 0) return FALSE;
    return TRUE;
}

static void prime_check(void) {
    wchar_t text[128];
    get_control_text(g_prime_input, text, 128);
    unsigned long long n;
    if (!parse_ull(text, &n) || n < 1 || n > 1000000ULL) {
        set_result(g_prime_result, L"输入错误：请输入 1～1000000 范围内的整数。");
        return;
    }
    wchar_t out[256];
    swprintf(out, 256, L"%llu %ls素数。", n, is_prime_ull(n) ? L"是" : L"不是");
    set_result(g_prime_result, out);
}

static void prime_list(void) {
    wchar_t text[128];
    get_control_text(g_prime_input, text, 128);
    unsigned long long n;
    if (!parse_ull(text, &n) || n < 1 || n > 1000000ULL) {
        set_result(g_prime_result, L"输入错误：请输入 1～1000000 范围内的整数。");
        return;
    }
    if (n < 2) {
        set_result(g_prime_result, L"该范围内没有素数。");
        return;
    }
    size_t cap = 1400000;
    wchar_t *out = (wchar_t *)malloc(cap * sizeof(wchar_t));
    unsigned char *sieve = (unsigned char *)malloc(n + 1);
    if (!out || !sieve) {
        free(out); free(sieve);
        set_result(g_prime_result, L"内存不足，无法列出素数。");
        return;
    }
    memset(sieve, 1, n + 1);
    sieve[0] = sieve[1] = 0;
    for (unsigned long long p = 2; p <= n / p; ++p)
        if (sieve[p])
            for (unsigned long long k = p * p; k <= n; k += p) sieve[k] = 0;

    size_t len = 0;
    unsigned long long count = 0;
    out[0] = L'\0';
    appendf(out, cap, &len, L"范围 1～%llu 内的素数：\r\n\r\n", n);
    for (unsigned long long i = 2; i <= n; ++i) {
        if (!sieve[i]) continue;
        ++count;
        if (!appendf(out, cap, &len, L"%llu", i)) break;
        if (i < n) appendf(out, cap, &len, L"%ls", (count % 12 == 0) ? L"\r\n" : L"、");
    }
    while (len > 0 && (out[len - 1] == L'、' || iswspace(out[len - 1])))
        out[--len] = L'\0';
    appendf(out, cap, &len, L"\r\n\r\n共 %llu 个素数。", count);
    set_result(g_prime_result, out);
    free(out);
    free(sieve);
}

static int digit_count(unsigned long long n) {
    int c = 0;
    do { ++c; n /= 10; } while (n);
    return c;
}

static unsigned long long ipow_ull(unsigned long long base, int exp) {
    unsigned long long r = 1;
    while (exp-- > 0) r *= base;
    return r;
}

static BOOL is_narcissistic(unsigned long long n) {
    int digits = digit_count(n);
    unsigned long long x = n, sum = 0;
    while (x) {
        unsigned long long d = x % 10;
        sum += ipow_ull(d, digits);
        x /= 10;
    }
    return sum == n;
}

static void narcissistic_calc(void) {
    wchar_t a[64], b[64];
    get_control_text(g_narc_start, a, 64);
    get_control_text(g_narc_end, b, 64);
    unsigned long long start, end;
    if (!parse_ull(a, &start) || !parse_ull(b, &end) ||
        start > end || end > 1000000ULL) {
        set_result(g_narc_result, L"输入错误：请输入 0～1000000，并确保起点不大于终点。");
        return;
    }
    size_t cap = 400000;
    wchar_t *out = (wchar_t *)malloc(cap * sizeof(wchar_t));
    if (!out) {
        set_result(g_narc_result, L"内存不足。");
        return;
    }
    size_t len = 0;
    unsigned long long count = 0;
    appendf(out, cap, &len, L"水仙花数：\r\n");
    for (unsigned long long i = start; i <= end; ++i) {
        if (is_narcissistic(i)) {
            ++count;
            appendf(out, cap, &len, L"%llu", i);
            appendf(out, cap, &len, L"%ls", L"、");
        }
    }
    if (count == 0) appendf(out, cap, &len, L"没有找到。");
    else if (len && out[len - 1] == L'、') out[--len] = L'\0';
    appendf(out, cap, &len, L"\r\n\r\n共 %llu 个。", count);
    set_result(g_narc_result, out);
    free(out);
}

static unsigned long long gcd_ull(unsigned long long a, unsigned long long b) {
    while (b) {
        unsigned long long t = a % b;
        a = b;
        b = t;
    }
    return a;
}

static void gcd_lcm_calc(void) {
    wchar_t a[64], b[64];
    get_control_text(g_gcd_a, a, 64);
    get_control_text(g_gcd_b, b, 64);
    long long x, y;
    if (!parse_ll(a, &x) || !parse_ll(b, &y) || x == LLONG_MIN || y == LLONG_MIN) {
        set_result(g_gcd_result, L"输入错误：请输入两个有效整数。");
        return;
    }
    unsigned long long ux = (unsigned long long)(x < 0 ? -x : x);
    unsigned long long uy = (unsigned long long)(y < 0 ? -y : y);
    unsigned long long g = gcd_ull(ux, uy);
    unsigned long long l = 0;
    if (ux == 0 || uy == 0) {
        l = 0;
    } else {
        unsigned long long q = ux / g;
        if (uy > ULLONG_MAX / q) {
            wchar_t out[256];
            swprintf(out, 256, L"最大公约数：%llu\r\n最小公倍数：溢出（超出 64 位整数范围）", g);
            set_result(g_gcd_result, out);
            return;
        }
        l = q * uy;
    }
    wchar_t out[256];
    swprintf(out, 256, L"最大公约数：%llu\r\n最小公倍数：%llu", g, l);
    set_result(g_gcd_result, out);
}

static unsigned long long fibonacci_ull(unsigned n) {
    if (n == 0) return 0;
    unsigned long long a = 0, b = 1;
    for (unsigned i = 2; i <= n; ++i) {
        unsigned long long c = a + b;
        a = b;
        b = c;
    }
    return b;
}

static BOOL fib_read_n(unsigned *n) {
    wchar_t text[64];
    get_control_text(g_fib_n, text, 64);
    unsigned long long v;
    if (!parse_ull(text, &v) || v > 92) return FALSE;
    *n = (unsigned)v;
    return TRUE;
}

static void fib_nth(void) {
    unsigned n;
    if (!fib_read_n(&n)) {
        set_result(g_fib_result, L"输入错误：n 必须是 0～92 的整数。");
        return;
    }
    wchar_t out[128];
    swprintf(out, 128, L"斐波那契数列第 %u 项：%llu", n, fibonacci_ull(n));
    set_result(g_fib_result, out);
}

static void fib_list(void) {
    unsigned n;
    if (!fib_read_n(&n)) {
        set_result(g_fib_result, L"输入错误：n 必须是 0～92 的整数。");
        return;
    }
    if (n == 0) {
        set_result(g_fib_result, L"前 0 项为空。");
        return;
    }
    size_t cap = 4096;
    wchar_t *out = (wchar_t *)malloc(cap * sizeof(wchar_t));
    if (!out) return;
    size_t len = 0;
    appendf(out, cap, &len, L"斐波那契数列前 %u 项：\r\n", n);
    unsigned long long a = 0, b = 1;
    for (unsigned i = 0; i < n; ++i) {
        unsigned long long value = (i == 0) ? 0 : (i == 1 ? 1 : a + b);
        if (i > 1) { a = b; b = value; }
        appendf(out, cap, &len, L"%llu%ls", value, (i + 1 == n) ? L"" : L"、");
    }
    set_result(g_fib_result, out);
    free(out);
}

/* -------------------- 页面创建 -------------------- */
static void create_page_calculator(void) {
    HWND title = make_label(0, L"普通计算器", 230, 28, 500, 42);
    SendMessageW(title, WM_SETFONT, (WPARAM)g_font_title, TRUE);
    g_calc_display = make_control(0, L"EDIT", L"",
        WS_BORDER | ES_RIGHT | ES_READONLY | ES_AUTOHSCROLL,
        230, 88, 850, 62, 0);
    SendMessageW(g_calc_display, WM_SETFONT, (WPARAM)g_font_title, TRUE);
    g_calc_status = make_label(0, L"支持 + - × ÷ 和括号，例如 (2+3)*4",
                               230, 158, 850, 30);

    const wchar_t *labels[20] = {
        L"C", L"(", L")", L"÷",
        L"7", L"8", L"9", L"×",
        L"4", L"5", L"6", L"-",
        L"1", L"2", L"3", L"+",
        L"0", L".", L"←", L"="
    };
    int ids[20] = {
        ID_CALC_CLEAR, ID_CALC_LPAREN, ID_CALC_RPAREN, ID_CALC_DIV,
        ID_CALC_DIGIT_BASE + 7, ID_CALC_DIGIT_BASE + 8, ID_CALC_DIGIT_BASE + 9, ID_CALC_MUL,
        ID_CALC_DIGIT_BASE + 4, ID_CALC_DIGIT_BASE + 5, ID_CALC_DIGIT_BASE + 6, ID_CALC_SUB,
        ID_CALC_DIGIT_BASE + 1, ID_CALC_DIGIT_BASE + 2, ID_CALC_DIGIT_BASE + 3, ID_CALC_ADD,
        ID_CALC_DIGIT_BASE, ID_CALC_DOT, ID_CALC_BACK, ID_CALC_EQUAL
    };
    int x0 = 230, y0 = 205, bw = 198, bh = 68, gap = 14;
    for (int i = 0; i < 20; ++i) {
        int row = i / 4, col = i % 4;
        make_button(0, labels[i], x0 + col * (bw + gap),
                    y0 + row * (bh + gap), bw, bh, ids[i]);
    }
}

static void create_page_prime(void) {
    HWND title = make_label(1, L"素数工具", 230, 28, 500, 42);
    SendMessageW(title, WM_SETFONT, (WPARAM)g_font_title, TRUE);
    make_label(1, L"输入整数 N（1～1000000）：", 230, 101, 300, 34);
    g_prime_input = make_input(1, 530, 94, 220, 40, 0);
    make_button(1, L"判断素数", 775, 90, 145, 48, ID_PRIME_CHECK);
    make_button(1, L"列出 2～N", 930, 90, 145, 48, ID_PRIME_LIST);
    g_prime_result = make_result(1, 230, 165, 850, 520);
    SendMessageW(g_prime_result, WM_SETFONT, (WPARAM)g_font, TRUE);
    SetWindowTextW(g_prime_input, L"97");
}

static void create_page_narcissistic(void) {
    HWND title = make_label(2, L"水仙花数", 230, 28, 500, 42);
    SendMessageW(title, WM_SETFONT, (WPARAM)g_font_title, TRUE);
    make_label(2, L"起点：", 230, 105, 80, 34);
    g_narc_start = make_input(2, 300, 98, 180, 40, 0);
    make_label(2, L"终点：", 510, 105, 80, 34);
    g_narc_end = make_input(2, 580, 98, 180, 40, 0);
    make_button(2, L"开始计算", 790, 94, 280, 48, ID_NARC_CALC);
    g_narc_result = make_result(2, 230, 165, 850, 520);
    SendMessageW(g_narc_result, WM_SETFONT, (WPARAM)g_font, TRUE);
    SetWindowTextW(g_narc_start, L"100");
    SetWindowTextW(g_narc_end, L"999");
}

static void create_page_gcd(void) {
    HWND title = make_label(3, L"最大公约数与最小公倍数", 230, 28, 700, 42);
    SendMessageW(title, WM_SETFONT, (WPARAM)g_font_title, TRUE);
    make_label(3, L"第一个整数：", 230, 105, 180, 34);
    g_gcd_a = make_input(3, 390, 98, 220, 40, 0);
    make_label(3, L"第二个整数：", 640, 105, 180, 34);
    g_gcd_b = make_input(3, 800, 98, 180, 40, 0);
    make_button(3, L"开始计算", 1000, 94, 75, 48, ID_GCD_CALC);
    g_gcd_result = make_result(3, 230, 165, 850, 520);
    SendMessageW(g_gcd_result, WM_SETFONT, (WPARAM)g_font, TRUE);
    SetWindowTextW(g_gcd_a, L"48");
    SetWindowTextW(g_gcd_b, L"18");
}

static void create_page_fib(void) {
    HWND title = make_label(4, L"斐波那契数列", 230, 28, 500, 42);
    SendMessageW(title, WM_SETFONT, (WPARAM)g_font_title, TRUE);
    make_label(4, L"项数 n（0～92）：", 230, 105, 280, 34);
    g_fib_n = make_input(4, 500, 98, 180, 40, 0);
    make_button(4, L"求第 n 项", 710, 94, 160, 48, ID_FIB_NTH);
    make_button(4, L"列出前 n 项", 885, 94, 190, 48, ID_FIB_LIST);
    g_fib_result = make_result(4, 230, 165, 850, 520);
    SendMessageW(g_fib_result, WM_SETFONT, (WPARAM)g_font, TRUE);
    SetWindowTextW(g_fib_n, L"10");
}

static void create_page_help(void) {
    HWND title = make_label(5, L"使用说明", 230, 28, 500, 42);
    SendMessageW(title, WM_SETFONT, (WPARAM)g_font_title, TRUE);
    HWND help = make_result(5, 230, 90, 850, 600);
    SendMessageW(help, WM_SETFONT, (WPARAM)g_font, TRUE);
    SetWindowTextW(help,
        L"C语言数学工具箱使用说明\r\n\r\n"
        L"1. 普通计算器\r\n"
        L"   支持 + - × ÷、括号和小数，例如 (2+3)*4。\r\n"
        L"   点击 C 清空，点击 ← 删除最后一个字符。\r\n\r\n"
        L"2. 素数工具\r\n"
        L"   输入 1～1000000 之间的整数，可以判断单个数，也可以列出范围内的全部素数。\r\n\r\n"
        L"3. 水仙花数\r\n"
        L"   默认范围 100～999，也可以输入其他范围。每位数字的位数次方之和等于原数的数会被列出。\r\n\r\n"
        L"4. 最大公约数与最小公倍数\r\n"
        L"   输入两个整数，使用欧几里得算法计算。\r\n\r\n"
        L"5. 斐波那契数列\r\n"
        L"   支持范围 0～92。第 93 项超出 64 位整数范围，因此会提示错误。\r\n\r\n"
        L"提示：所有计算都在本机完成，不需要联网。");
}

static void create_ui(void) {
    const wchar_t *nav_text[PAGE_COUNT] = {
        L"计算器", L"素数工具", L"水仙花数",
        L"最大公约数", L"斐波那契", L"使用说明"
    };
    for (int i = 0; i < PAGE_COUNT; ++i) {
        g_nav[i] = CreateWindowExW(
            0, L"BUTTON", nav_text[i], WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_OWNERDRAW,
            18, 28 + i * 64, 176, 50, g_hwnd,
            (HMENU)(INT_PTR)(ID_NAV_BASE + i), g_instance, NULL);
        SendMessageW(g_nav[i], WM_SETFONT, (WPARAM)g_font, TRUE);
    }
    create_page_calculator();
    create_page_prime();
    create_page_narcissistic();
    create_page_gcd();
    create_page_fib();
    create_page_help();
    switch_page(0);
}

static void switch_page(int page) {
    if (page < 0 || page >= PAGE_COUNT) return;
    g_current_page = page;
    for (int p = 0; p < PAGE_COUNT; ++p)
        for (int i = 0; i < g_page_count[p]; ++i)
            ShowWindow(g_page_controls[p][i], p == page ? SW_SHOW : SW_HIDE);
    for (int i = 0; i < PAGE_COUNT; ++i) {
        InvalidateRect(g_nav[i], NULL, TRUE);
        UpdateWindow(g_nav[i]);
    }
}


static COLORREF blend_color(COLORREF a, COLORREF b, int amount) {
    if (amount < 0) amount = 0;
    if (amount > 255) amount = 255;
    int inv = 255 - amount;
    return RGB((GetRValue(a) * inv + GetRValue(b) * amount) / 255,
               (GetGValue(a) * inv + GetGValue(b) * amount) / 255,
               (GetBValue(a) * inv + GetBValue(b) * amount) / 255);
}

static void draw_soft_circle(HDC hdc, int cx, int cy, int radius,
                             COLORREF glow, int strength) {
    HPEN old_pen = (HPEN)SelectObject(hdc, GetStockObject(NULL_PEN));
    for (int r = radius; r > 0; r -= 8) {
        float t = 1.0f - (float)r / (float)radius;
        int alpha = (int)(strength * t * t);
        HBRUSH brush = CreateSolidBrush(blend_color(COLOR_BG, glow, alpha));
        HBRUSH old_brush = (HBRUSH)SelectObject(hdc, brush);
        Ellipse(hdc, cx - r, cy - r, cx + r, cy + r);
        SelectObject(hdc, old_brush);
        DeleteObject(brush);
    }
    SelectObject(hdc, old_pen);
}

static void paint_background(HWND hwnd, HDC target) {
    RECT rc;
    GetClientRect(hwnd, &rc);
    int width = rc.right - rc.left;
    int height = rc.bottom - rc.top;

    HDC mem = CreateCompatibleDC(target);
    HBITMAP bitmap = CreateCompatibleBitmap(target, width, height);
    HBITMAP old_bitmap = (HBITMAP)SelectObject(mem, bitmap);

    COLORREF top = RGB(8, 13, 25);
    COLORREF mid = RGB(20, 31, 57);
    COLORREF bottom = RGB(9, 14, 28);
    for (int y = 0; y < height; ++y) {
        COLORREF c;
        if (y < height / 2)
            c = blend_color(top, mid, y * 255 / (height / 2 + 1));
        else
            c = blend_color(mid, bottom, (y - height / 2) * 255 / (height - height / 2 + 1));
        HBRUSH brush = CreateSolidBrush(c);
        RECT line = {0, y, width, y + 1};
        FillRect(mem, &line, brush);
        DeleteObject(brush);
    }

    draw_soft_circle(mem, width - 145, 95, 220, RGB(48, 130, 235), 80);
    draw_soft_circle(mem, 90, height - 105, 180, RGB(210, 66, 155), 52);

    HPEN grid = CreatePen(PS_SOLID, 1, RGB(28, 43, 68));
    HPEN old_pen = (HPEN)SelectObject(mem, grid);
    for (int x = 210; x < width; x += 42)
        MoveToEx(mem, x, 0, NULL), LineTo(mem, x, height);
    for (int y = 0; y < height; y += 42)
        MoveToEx(mem, 210, y, NULL), LineTo(mem, width, y);
    SelectObject(mem, old_pen);
    DeleteObject(grid);

    HBRUSH side = CreateSolidBrush(RGB(12, 17, 29));
    RECT side_rc = {0, 0, 210, height};
    FillRect(mem, &side_rc, side);
    DeleteObject(side);

    HPEN side_line = CreatePen(PS_SOLID, 2, RGB(75, 98, 135));
    old_pen = (HPEN)SelectObject(mem, side_line);
    MoveToEx(mem, 210, 0, NULL); LineTo(mem, 210, height);
    SelectObject(mem, old_pen);
    DeleteObject(side_line);

    SetBkMode(mem, TRANSPARENT);
    SetTextColor(mem, RGB(36, 56, 86));
    HFONT old_font = (HFONT)SelectObject(mem, g_font_title);
    TextOutW(mem, width - 330, 130, L"∑", 1);
    TextOutW(mem, width - 245, 210, L"√", 1);
    TextOutW(mem, width - 115, 80, L"π", 1);
    TextOutW(mem, 260, height - 145, L"f(x)", 4);
    TextOutW(mem, 520, height - 74, L"gcd(a,b)", 8);
    SelectObject(mem, old_font);

    HPEN glow = CreatePen(PS_SOLID, 3, RGB(255, 151, 73));
    old_pen = (HPEN)SelectObject(mem, glow);
    MoveToEx(mem, 0, 2, NULL); LineTo(mem, width, 2);
    SelectObject(mem, old_pen);
    DeleteObject(glow);

    BitBlt(target, 0, 0, width, height, mem, 0, 0, SRCCOPY);
    SelectObject(mem, old_bitmap);
    DeleteObject(bitmap);
    DeleteDC(mem);
}

static void draw_button(const DRAWITEMSTRUCT *di) {
    int id = (int)di->CtlID;
    BOOL pressed = (di->itemState & ODS_SELECTED) != 0;
    BOOL disabled = (di->itemState & ODS_DISABLED) != 0;
    COLORREF bg = COLOR_BUTTON;

    if (id >= ID_NAV_BASE && id < ID_NAV_BASE + PAGE_COUNT) {
        bg = (id == ID_NAV_BASE + g_current_page) ? COLOR_ACCENT : COLOR_PANEL;
    } else if (id >= ID_CALC_DIGIT_BASE && id <= ID_CALC_DIGIT_BASE + 9) {
        bg = COLOR_BUTTON2;
    } else if (id == ID_CALC_DOT || id == ID_CALC_LPAREN || id == ID_CALC_RPAREN) {
        bg = COLOR_BUTTON;
    } else if (id == ID_CALC_EQUAL) {
        bg = COLOR_GREEN;
    } else if (id == ID_CALC_CLEAR || id == ID_CALC_BACK) {
        bg = RGB(82, 54, 72);
    } else if (id >= ID_CALC_DIV && id <= ID_CALC_ADD) {
        bg = COLOR_ACCENT;
    } else if (id == ID_PRIME_CHECK || id == ID_PRIME_LIST ||
               id == ID_NARC_CALC || id == ID_GCD_CALC ||
               id == ID_FIB_NTH || id == ID_FIB_LIST) {
        bg = COLOR_BLUE;
    }
    if (pressed) {
        bg = RGB((GetRValue(bg) * 75) / 100,
                 (GetGValue(bg) * 75) / 100,
                 (GetBValue(bg) * 75) / 100);
    }
    if (disabled) bg = RGB(55, 60, 72);

    HBRUSH brush = CreateSolidBrush(bg);
    FillRect(di->hDC, &di->rcItem, brush);
    DeleteObject(brush);

    HPEN border = CreatePen(PS_SOLID, 1,
        (id == ID_NAV_BASE + g_current_page) ? RGB(255, 195, 125) : RGB(75, 88, 112));
    HPEN old_pen = (HPEN)SelectObject(di->hDC, border);
    HBRUSH old_brush = (HBRUSH)SelectObject(di->hDC, GetStockObject(NULL_BRUSH));
    Rectangle(di->hDC, di->rcItem.left, di->rcItem.top,
              di->rcItem.right, di->rcItem.bottom);
    SelectObject(di->hDC, old_brush);
    SelectObject(di->hDC, old_pen);
    DeleteObject(border);

    wchar_t text[64];
    GetWindowTextW(di->CtlID ? GetDlgItem(g_hwnd, id) : di->hwndItem, text, 64);
    SetBkMode(di->hDC, TRANSPARENT);
    SetTextColor(di->hDC, disabled ? RGB(120,120,125) : COLOR_TEXT);
    RECT rc = di->rcItem;
    DrawTextW(di->hDC, text, -1, &rc, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
}

static LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp) {
    switch (msg) {
    case WM_CREATE:
        g_hwnd = hwnd;
        create_ui();
        return 0;

    case WM_COMMAND: {
        int id = LOWORD(wp);
        if (id >= ID_NAV_BASE && id < ID_NAV_BASE + PAGE_COUNT) {
            switch_page(id - ID_NAV_BASE);
            return 0;
        }
        if (id >= ID_CALC_DIGIT_BASE && id <= ID_CALC_DIGIT_BASE + 9) {
            calc_append((wchar_t)(L'0' + (id - ID_CALC_DIGIT_BASE)));
            return 0;
        }
        switch (id) {
        case ID_CALC_DOT: calc_append(L'.'); return 0;
        case ID_CALC_DIV: calc_append(L'/'); return 0;
        case ID_CALC_MUL: calc_append(L'*'); return 0;
        case ID_CALC_SUB: calc_append(L'-'); return 0;
        case ID_CALC_ADD: calc_append(L'+'); return 0;
        case ID_CALC_LPAREN: calc_append(L'('); return 0;
        case ID_CALC_RPAREN: calc_append(L')'); return 0;
        case ID_CALC_CLEAR: calc_clear(); return 0;
        case ID_CALC_BACK: calc_backspace(); return 0;
        case ID_CALC_EQUAL: calc_equal(); return 0;
        case ID_PRIME_CHECK: prime_check(); return 0;
        case ID_PRIME_LIST: prime_list(); return 0;
        case ID_NARC_CALC: narcissistic_calc(); return 0;
        case ID_GCD_CALC: gcd_lcm_calc(); return 0;
        case ID_FIB_NTH: fib_nth(); return 0;
        case ID_FIB_LIST: fib_list(); return 0;
        default: break;
        }
        break;
    }

    case WM_DRAWITEM:
        draw_button((const DRAWITEMSTRUCT *)lp);
        return TRUE;

    case WM_ERASEBKGND:
        return 1;

    case WM_PAINT: {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hwnd, &ps);
        paint_background(hwnd, hdc);
        SetBkMode(hdc, TRANSPARENT);
        SetTextColor(hdc, RGB(118, 142, 175));
        HFONT old = (HFONT)SelectObject(hdc, g_font_small);
        TextOutW(hdc, 30, 690, L"C Math Toolbox", 14);
        SelectObject(hdc, old);
        EndPaint(hwnd, &ps);
        return 0;
    }

    case WM_CTLCOLORSTATIC: {
        HDC hdc = (HDC)wp;
        wchar_t cls[32] = L"";
        GetClassNameW((HWND)lp, cls, 32);
        if (_wcsicmp(cls, L"Edit") == 0) {
            SetBkColor(hdc, COLOR_EDIT);
            SetTextColor(hdc, COLOR_TEXT);
            return (LRESULT)g_edit_brush;
        }
        SetBkMode(hdc, TRANSPARENT);
        SetTextColor(hdc, COLOR_TEXT);
        return (LRESULT)GetStockObject(HOLLOW_BRUSH);
    }

    case WM_CTLCOLOREDIT: {
        HDC hdc = (HDC)wp;
        SetBkColor(hdc, COLOR_EDIT);
        SetTextColor(hdc, COLOR_TEXT);
        return (LRESULT)g_edit_brush;
    }

    case WM_DESTROY:
        if (g_font) DeleteObject(g_font);
        if (g_font_small) DeleteObject(g_font_small);
        if (g_font_title) DeleteObject(g_font_title);
        if (g_bg_brush) DeleteObject(g_bg_brush);
        if (g_panel_brush) DeleteObject(g_panel_brush);
        if (g_edit_brush) DeleteObject(g_edit_brush);
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, msg, wp, lp);
}

#ifndef MATH_TOOLBOX_TEST
int WINAPI wWinMain(HINSTANCE instance, HINSTANCE prev, LPWSTR cmd, int show) {
    (void)prev; (void)cmd;
    g_instance = instance;
    SetProcessDPIAware();

    g_bg_brush = CreateSolidBrush(COLOR_BG);
    g_panel_brush = CreateSolidBrush(COLOR_PANEL);
    g_edit_brush = CreateSolidBrush(COLOR_EDIT);
    g_font = CreateFontW(-22, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
        DEFAULT_PITCH | FF_DONTCARE, L"Microsoft YaHei UI");
    g_font_small = CreateFontW(-16, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
        DEFAULT_PITCH | FF_DONTCARE, L"Microsoft YaHei UI");
    g_font_title = CreateFontW(-32, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE,
        DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
        DEFAULT_PITCH | FF_DONTCARE, L"Microsoft YaHei UI");

    WNDCLASSEXW wc;
    ZeroMemory(&wc, sizeof(wc));
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = WndProc;
    wc.hInstance = instance;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = g_bg_brush;
    wc.lpszClassName = L"MathToolboxWindowClass";
    if (!RegisterClassExW(&wc)) return 1;

    HWND hwnd = CreateWindowExW(
        0, wc.lpszClassName, APP_TITLE,
        WS_OVERLAPPEDWINDOW & ~WS_THICKFRAME & ~WS_MAXIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT, 1140, 790,
        NULL, NULL, instance, NULL);
    if (!hwnd) return 1;

    center_window(hwnd, 1140, 790);
    ShowWindow(hwnd, show);
    UpdateWindow(hwnd);

    MSG msg;
    while (GetMessageW(&msg, NULL, 0, 0) > 0) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return (int)msg.wParam;
}
#else
#include <stdio.h>

static int check_true(const char *name, int value) {
    if (value) {
        printf("[PASS] %s\n", name);
        return 0;
    }
    printf("[FAIL] %s\n", name);
    return 1;
}

int wmain(void) {
    int failures = 0;
    Parser p1 = {L"2+3*4", 0, 0};
    double v1 = parse_expression(&p1);
    failures += check_true("calculator 2+3*4", p1.error == 0 && v1 == 14.0);

    Parser p2 = {L"(2+3)*4", 0, 0};
    double v2 = parse_expression(&p2);
    failures += check_true("calculator (2+3)*4", p2.error == 0 && v2 == 20.0);

    Parser p3 = {L"8/0", 0, 0};
    (void)parse_expression(&p3);
    failures += check_true("divide by zero", p3.error == 2);
    failures += check_true("prime 97", is_prime_ull(97));
    failures += check_true("not prime 1", !is_prime_ull(1));
    failures += check_true("narcissistic 153", is_narcissistic(153));
    failures += check_true("narcissistic 370", is_narcissistic(370));
    failures += check_true("narcissistic 371", is_narcissistic(371));
    failures += check_true("narcissistic 407", is_narcissistic(407));
    failures += check_true("gcd 48,18", gcd_ull(48, 18) == 6);
    failures += check_true("fib 10", fibonacci_ull(10) == 55);
    failures += check_true("fib 92", fibonacci_ull(92) == 7540113804746346429ULL);
    printf("failures=%d\n", failures);
    return failures ? 1 : 0;
}
#endif

"""
坦克大战 - Python + Pygame 坦克对战游戏（城市版）
运行: pip install pygame  然后  python 坦克大战.py
操作: WASD移动 | 鼠标瞄准 | 左键机枪 | 空格重炮 | R重开 | ESC退出
"""

import sys, math, random, pygame

# ═══════════════ 常量 ═══════════════
W, H = 960, 640
HUD_H = 52
FPS = 60

C_BG       = (26, 30, 40)
C_HUD      = (18, 20, 28)
C_RED      = (231, 76, 60)
C_GREEN    = (46, 204, 113)
C_BLUE     = (52, 152, 219)
C_YELLOW   = (241, 196, 15)
C_WHITE    = (236, 240, 241)
C_GRAY     = (127, 140, 141)
C_DARK     = (22, 26, 34)
C_ORANGE   = (230, 140, 30)

# 坦克配色
C_P_HULL     = (68, 95, 68)
C_P_HULL2    = (55, 78, 55)
C_P_TRACK    = (48, 48, 52)
C_P_TRACK2   = (38, 38, 42)
C_P_TURRET   = (58, 85, 58)
C_P_BARREL   = (62, 68, 62)
C_P_DETAIL   = (80, 108, 80)

C_E_SCOUT    = (110, 100, 65)
C_E_SCOUT2   = (90, 82, 52)
C_E_MEDIUM   = (120, 95, 60)
C_E_MEDIUM2  = (100, 78, 48)
C_E_HEAVY    = (75, 75, 80)
C_E_HEAVY2   = (60, 60, 65)
C_E_TRACK    = (45, 42, 40)
C_E_TRACK2   = (35, 32, 30)
C_E_BARREL   = (65, 62, 58)

# ── 城市背景色 ──
C_ROAD       = (58, 58, 62)
C_ROAD_LINE  = (200, 190, 80)
C_SIDEWALK   = (140, 135, 128)
C_SIDEWALK2  = (125, 120, 114)
C_GRASS      = (65, 110, 55)
C_GRASS2     = (55, 95, 45)
C_LANE_DASH  = (220, 210, 90)
C_CROSSWALK  = (230, 230, 225)
C_MANHOLE    = (45, 45, 48)
C_TREE_TRUNK = (90, 65, 35)
C_TREE_LEAF  = (50, 120, 45)
C_TREE_LEAF2 = (60, 135, 55)
C_CAR_COLORS = [
    (180, 40, 40), (40, 80, 170), (220, 220, 220),
    (40, 40, 45), (200, 170, 50), (50, 160, 80),
    (180, 100, 40), (100, 50, 140),
]

ENEMY_CFG = {
    'scout':  {'hp': 30,  'spd': 1.8, 'score': 100,  'dmg': 6,  'ai': 'zigzag',
               'scale': 0.65, 'hull_c': C_E_SCOUT, 'hull2_c': C_E_SCOUT2,
               'turret_c': (100, 90, 58), 'shoot_cd': 150, 'shell_dmg': 6, 'shell_spd': 3.0},
    'medium': {'hp': 55,  'spd': 1.1, 'score': 200,  'dmg': 12, 'ai': 'chase',
               'scale': 0.85, 'hull_c': C_E_MEDIUM, 'hull2_c': C_E_MEDIUM2,
               'turret_c': (110, 88, 55), 'shoot_cd': 110, 'shell_dmg': 10, 'shell_spd': 3.5},
    'heavy':  {'hp': 180, 'spd': 0.6, 'score': 500,  'dmg': 22, 'ai': 'chase',
               'scale': 1.25, 'hull_c': C_E_HEAVY, 'hull2_c': C_E_HEAVY2,
               'turret_c': (70, 70, 75), 'shoot_cd': 70, 'shell_dmg': 18, 'shell_spd': 4.0},
    'boss':   {'hp': 400, 'spd': 0.5, 'score': 1500, 'dmg': 30, 'ai': 'chase',
               'scale': 1.6, 'hull_c': (90, 40, 40), 'hull2_c': (72, 30, 30),
               'turret_c': (80, 35, 35), 'shoot_cd': 50, 'shell_dmg': 22, 'shell_spd': 4.5},
}


# ═══════════════ 工具函数 ═══════════════
def clamp(v, lo, hi): return max(lo, min(hi, v))
def dist(a, b): return math.hypot(a[0]-b[0], a[1]-b[1])
def norm(v):
    l = math.hypot(*v)
    return (v[0]/l, v[1]/l) if l > 0 else (0, 0)
def angle_to(a, b): return math.atan2(b[1]-a[1], b[0]-a[0])
def darken(c, f=0.6): return tuple(int(x*f) for x in c[:3])
def brighten(c, f=1.3): return tuple(min(255, int(x*f)) for x in c[:3])
def lerp_color(c1, c2, t):
    return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))
def font(sz):
    try:
        # 优先尝试加载 Windows 微软雅黑
        return pygame.font.Font("C:\\Windows\\Fonts\\msyh.ttc", sz)
    except:
        try:
            # 找不到就尝试黑体
            return pygame.font.Font("C:\\Windows\\Fonts\\simhei.ttf", sz)
        except:
            # 终极保底：使用 pygame 默认字体
            return pygame.font.Font(None, sz)


# ═══════════════ 建筑物 ═══════════════
class Building:
    """城市中的建筑物：俯视图，有碰撞体和视觉表现"""

    # 建筑配色方案
    STYLES = [
        {'wall': (160, 155, 148), 'wall2': (140, 135, 128), 'roof': (120, 115, 110),
         'accent': (100, 95, 88), 'name': 'office_grey'},
        {'wall': (175, 145, 120), 'wall2': (155, 125, 100), 'roof': (135, 110, 85),
         'accent': (110, 85, 65), 'name': 'brick_brown'},
        {'wall': (130, 145, 160), 'wall2': (110, 125, 140), 'roof': (95, 108, 120),
         'accent': (75, 88, 100), 'name': 'blue_glass'},
        {'wall': (155, 150, 145), 'wall2': (135, 130, 125), 'roof': (115, 110, 105),
         'accent': (95, 90, 85), 'name': 'concrete'},
        {'wall': (170, 130, 130), 'wall2': (150, 110, 110), 'roof': (130, 90, 90),
         'accent': (110, 70, 70), 'name': 'red_brick'},
        {'wall': (145, 155, 140), 'wall2': (125, 135, 120), 'roof': (105, 115, 100),
         'accent': (85, 95, 80), 'name': 'green_tint'},
    ]

    def __init__(self, x, y, w, h, style_idx, floors, has_helipad=False):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.cx = x + w / 2
        self.cy = y + h / 2
        self.style = self.STYLES[style_idx % len(self.STYLES)]
        self.floors = floors
        self.has_helipad = has_helipad
        self.hp = 80 + floors * 15  # 血量与楼层挂钩
        self.max_hp = self.hp
        self.damaged = False
        self.destroyed = False
        self.dmg_flash = 0
        self._prerender()

    def _prerender(self):
        """预渲染建筑到 Surface"""
        margin = 6
        self._surf = pygame.Surface((self.w + margin * 2, self.h + margin * 2), pygame.SRCALPHA)
        self._ox = margin
        self._oy = margin
        s = self._surf
        ox, oy = margin, margin
        st = self.style
        r = random.Random(int(self.x * 31 + self.y * 17))

        # 阴影
        pygame.draw.rect(s, (20, 20, 25, 80),
                         (ox + 3, oy + 3, self.w, self.h), border_radius=2)

        # 建筑外墙
        pygame.draw.rect(s, st['wall'], (ox, oy, self.w, self.h), border_radius=2)
        # 外墙边框
        pygame.draw.rect(s, st['wall2'], (ox, oy, self.w, self.h), 2, border_radius=2)

        # 屋顶
        roof_inset = 3
        pygame.draw.rect(s, st['roof'],
                         (ox + roof_inset, oy + roof_inset,
                          self.w - roof_inset * 2, self.h - roof_inset * 2),
                         border_radius=1)

        # 窗户网格
        win_w = max(4, min(8, self.w // 8))
        win_h = max(4, min(8, self.h // 8))
        win_gap_x = win_w + max(3, self.w // 12)
        win_gap_y = win_h + max(3, self.h // 12)
        start_x = ox + roof_inset + 4
        start_y = oy + roof_inset + 4

        for wy in range(start_y, oy + self.h - roof_inset - win_h - 2, win_gap_y):
            for wx in range(start_x, ox + self.w - roof_inset - win_w - 2, win_gap_x):
                # 窗户颜色随机
                lit = r.random() < 0.3
                if lit:
                    wc = r.choice([(220, 210, 140), (180, 200, 220), (200, 180, 120)])
                    alpha = r.randint(120, 200)
                    pygame.draw.rect(s, (*wc[:3], alpha), (wx, wy, win_w, win_h))
                else:
                    wc = darken(st['accent'], r.uniform(0.6, 0.9))
                    pygame.draw.rect(s, wc, (wx, wy, win_w, win_h))

        # 屋顶细节
        if self.has_helipad and self.w > 40 and self.h > 40:
            # 直升机停机坪
            cx_h = ox + self.w // 2
            cy_h = oy + self.h // 2
            hr = min(self.w, self.h) // 4
            pygame.draw.circle(s, (80, 80, 75), (cx_h, cy_h), hr)
            pygame.draw.circle(s, C_WHITE, (cx_h, cy_h), hr, 2)
            pygame.draw.circle(s, C_WHITE, (cx_h, cy_h), hr - 3, 1)
            # H 标记
            hft = font(max(8, hr))
            hs = hft.render('H', True, C_WHITE)
            s.blit(hs, (cx_h - hs.get_width() // 2, cy_h - hs.get_height() // 2))

        # 空调外机（小方块）
        if self.floors >= 3 and self.w > 30:
            for _ in range(r.randint(1, 3)):
                acx = ox + r.randint(roof_inset + 2, self.w - roof_inset - 8)
                acy = oy + r.randint(roof_inset + 2, self.h - roof_inset - 6)
                pygame.draw.rect(s, (100, 100, 95), (acx, acy, 6, 4))

        # 天线（高层建筑）
        if self.floors >= 8 and self.w > 25:
            ax = ox + self.w // 2
            ay = oy + roof_inset + 2
            pygame.draw.line(s, (180, 180, 175), (ax, ay), (ax, ay - 8), 1)
            pygame.draw.circle(s, C_RED, (ax, ay - 8), 2)

    def take_damage(self, dmg, fx=None):
        """建筑受到攻击"""
        if self.destroyed:
            return
        self.hp -= dmg
        self.dmg_flash = 6
        if self.hp <= self.max_hp * 0.6:
            self.damaged = True
        if self.hp <= 0:
            self.destroyed = True
            self._render_destroyed()
            if fx:
                fx.explosion(self.cx, self.cy, 20)
        return self.destroyed

    def _render_destroyed(self):
        """渲染被摧毁的建筑（废墟）"""
        margin = 6
        self._surf = pygame.Surface((self.w + margin * 2, self.h + margin * 2), pygame.SRCALPHA)
        self._ox = margin
        self._oy = margin
        s = self._surf
        ox, oy = margin, margin
        r = random.Random(int(self.x * 7 + self.y * 13))

        # 废墟底座
        pygame.draw.rect(s, (60, 55, 50), (ox, oy, self.w, self.h), border_radius=1)
        # 碎石
        for _ in range(r.randint(5, 12)):
            rx = ox + r.randint(2, self.w - 4)
            ry = oy + r.randint(2, self.h - 4)
            rw = r.randint(3, 8)
            rh = r.randint(3, 6)
            rc = r.choice([(80, 75, 70), (95, 90, 85), (70, 65, 60)])
            pygame.draw.rect(s, rc, (rx, ry, rw, rh))
        # 烟尘
        for _ in range(r.randint(3, 6)):
            sx = ox + r.randint(4, self.w - 4)
            sy = oy + r.randint(4, self.h - 4)
            sr = r.randint(4, 10)
            dust_surf = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(dust_surf, (80, 80, 75, 60), (sr, sr), sr)
            s.blit(dust_surf, (sx - sr, sy - sr))

    def draw(self, surf):
        if self.dmg_flash > 0:
            self.dmg_flash -= 1
        # 绘制预渲染
        surf.blit(self._surf, (self.x - self._ox, self.y - self._oy))
        # 受伤闪烁
        if self.dmg_flash > 0:
            flash_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            flash_surf.fill((255, 100, 50, 80))
            surf.blit(flash_surf, (self.x, self.y))
        # 受损状态：裂纹叠加
        if self.damaged and not self.destroyed:
            crack_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            r = random.Random(int(self.x * 3 + self.y * 5))
            for _ in range(2):
                sx = r.randint(2, self.w - 2)
                sy = r.randint(2, self.h - 2)
                for step in range(4):
                    ex = sx + r.randint(-8, 8)
                    ey = sy + r.randint(-8, 8)
                    pygame.draw.line(crack_surf, (40, 35, 30, 150), (sx, sy), (ex, ey), 1)
                    sx, sy = ex, ey
            surf.blit(crack_surf, (self.x, self.y))

    def collide_point(self, px, py, r=0):
        """检测点/圆是否在建筑内"""
        if self.destroyed:
            return False
        return (px + r > self.x and px - r < self.x + self.w and
                py + r > self.y and py - r < self.y + self.h)

    def push_out(self, px, py, r):
        """将圆形实体推出建筑，返回修正后的 (px, py)"""
        if self.destroyed:
            return px, py
        # 找最近的边推出
        dx_left = (self.x) - (px + r)
        dx_right = (px - r) - (self.x + self.w)
        dy_top = (self.y) - (py + r)
        dy_bottom = (py - r) - (self.y + self.h)

        # 计算各方向穿透深度
        pen_left = (px + r) - self.x
        pen_right = (self.x + self.w) - (px - r)
        pen_top = (py + r) - self.y
        pen_bottom = (self.y + self.h) - (py - r)

        if pen_left <= 0 or pen_right <= 0 or pen_top <= 0 or pen_bottom <= 0:
            return px, py

        min_pen = min(pen_left, pen_right, pen_top, pen_bottom)
        if min_pen == pen_left:
            px = self.x - r
        elif min_pen == pen_right:
            px = self.x + self.w + r
        elif min_pen == pen_top:
            py = self.y - r
        else:
            py = self.y + self.h + r
        return px, py


# ═══════════════ 城市背景 ═══════════════
class CityBackground:
    """大城市俯视背景：道路网格 + 建筑群 + 街景装饰"""

    def __init__(self):
        self.rng = random.Random(42)
        self.buildings = []
        self.static_layer = pygame.Surface((W, H), pygame.SRCALPHA)
        self.trees = []
        self.cars = []
        self.street_lamps = []
        self.particles = []  # 飘落的树叶等

        self._generate_city()
        self._render_static()

        # 动态粒子（落叶）
        for _ in range(15):
            self.particles.append({
                'x': random.uniform(0, W),
                'y': random.uniform(HUD_H, H),
                'vx': random.uniform(-0.3, 0.3),
                'vy': random.uniform(0.2, 0.5),
                'rot': random.uniform(0, 360),
                'vr': random.uniform(-2, 2),
                'sz': random.uniform(2, 4),
                'color': random.choice([(120, 140, 50), (180, 140, 40), (160, 80, 30)]),
            })

        self.tick_count = 0

    def _generate_city(self):
        r = self.rng
        # 道路参数
        road_w = 52       # 主路宽
        lane_mark = 2     # 车道线宽
        sidewalk_w = 10   # 人行道宽

        # 街区网格（block = 一个街区方块，包含建筑+人行道）
        block_size = 160
        play_top = HUD_H + 10
        play_bot = H - 10

        # 主路位置（水平和垂直各一条主路，其余为小路）
        main_h_y = H // 2 - road_w // 2   # 水平主路
        main_v_x = W // 2 - road_w // 2   # 垂直主路

        # ── 放置建筑 ──
        # 将地图分为四个象限，每个象限内放置建筑群
        quadrants = [
            (10, play_top, W // 2 - road_w // 2 - 10, main_h_y - play_top - 10),   # 左上
            (W // 2 + road_w // 2 + 10, play_top, W - W // 2 - road_w // 2 - 20, main_h_y - play_top - 10),  # 右上
            (10, main_h_y + road_w + 10, W // 2 - road_w // 2 - 10, H - main_h_y - road_w - 20),  # 左下
            (W // 2 + road_w // 2 + 10, main_h_y + road_w + 10, W - W // 2 - road_w // 2 - 20, H - main_h_y - road_w - 20),  # 右下
        ]

        for qx, qy, qw, qh in quadrants:
            if qw < 40 or qh < 40:
                continue
            # 在象限内放置 2~5 栋建筑
            n_buildings = r.randint(2, 5)
            placed = []
            for _ in range(n_buildings * 3):  # 多次尝试
                if len(placed) >= n_buildings:
                    break
                bw = r.randint(30, min(70, qw - 10))
                bh = r.randint(30, min(70, qh - 10))
                bx = qx + r.randint(5, max(5, qw - bw - 5))
                by = qy + r.randint(5, max(5, qh - bh - 5))

                # 检查不与已放置建筑重叠
                overlap = False
                for px, py, pw, ph in placed:
                    if (bx < px + pw + 8 and bx + bw + 8 > px and
                            by < py + ph + 8 and by + bh + 8 > py):
                        overlap = True
                        break
                if overlap:
                    continue

                floors = r.randint(2, 12)
                style_idx = r.randint(0, len(Building.STYLES) - 1)
                has_helipad = floors >= 10 and bw > 40 and bh > 40 and r.random() < 0.4
                bldg = Building(bx, by, bw, bh, style_idx, floors, has_helipad)
                self.buildings.append(bldg)
                placed.append((bx, by, bw, bh))

        # ── 树木 ──
        for _ in range(20):
            tx = r.randint(15, W - 15)
            ty = r.randint(play_top + 10, play_bot - 10)
            # 检查不在建筑内也不在主路上
            ok = True
            for b in self.buildings:
                if b.collide_point(tx, ty, 12):
                    ok = False
                    break
            if ok and main_h_y - 5 < ty < main_h_y + road_w + 5:
                ok = False
            if ok and main_v_x - 5 < tx < main_v_x + road_w + 5:
                ok = False
            if ok:
                self.trees.append({
                    'x': tx, 'y': ty,
                    'r': r.randint(8, 14),
                    'color': r.choice([C_TREE_LEAF, C_TREE_LEAF2, (55, 105, 40)]),
                })

        # ── 停放车辆 ──
        for _ in range(8):
            side = r.randint(0, 3)
            if side == 0:  # 水平主路上侧
                cx = r.randint(30, W - 60)
                cy = main_h_y - 14
            elif side == 1:  # 水平主路下侧
                cx = r.randint(30, W - 60)
                cy = main_h_y + road_w + 4
            elif side == 2:  # 垂直主路左侧
                cx = main_v_x - 14
                cy = r.randint(play_top + 30, play_bot - 50)
            else:
                cx = main_v_x + road_w + 4
                cy = r.randint(play_top + 30, play_bot - 50)

            # 检查不在建筑内
            ok = True
            for b in self.buildings:
                if b.collide_point(cx + 8, cy + 5, 10):
                    ok = False
                    break
            if ok:
                horizontal = side < 2
                self.cars.append({
                    'x': cx, 'y': cy,
                    'w': 22 if horizontal else 12,
                    'h': 10 if horizontal else 22,
                    'color': r.choice(C_CAR_COLORS),
                    'horizontal': horizontal,
                })

        # ── 路灯 ──
        # 沿主路放置
        for x in range(30, W - 30, 80):
            self.street_lamps.append({'x': x, 'y': main_h_y - 8})
            self.street_lamps.append({'x': x, 'y': main_h_y + road_w + 3})
        for y in range(play_top + 20, play_bot - 20, 80):
            self.street_lamps.append({'x': main_v_x - 8, 'y': y})
            self.street_lamps.append({'x': main_v_x + road_w + 3, 'y': y})

    def _render_static(self):
        s = self.static_layer
        r = self.rng
        play_top = HUD_H
        road_w = 52
        main_h_y = H // 2 - road_w // 2
        main_v_x = W // 2 - road_w // 2

        # ── 地面：草地底色 ──
        s.fill(C_GRASS)
        # 草地纹理
        for _ in range(600):
            gx = r.randint(0, W - 1)
            gy = r.randint(play_top, H - 1)
            gc = r.choice([C_GRASS, C_GRASS2, (60, 105, 50), (70, 115, 55)])
            s.set_at((gx, gy), gc)

        # ── 人行道区域 ──
        # 沿主路两侧画人行道
        sw = 10
        for y in range(play_top, H):
            # 水平主路上下人行道
            if main_h_y - sw <= y < main_h_y:
                for x in range(W):
                    c = C_SIDEWALK if (x // 8 + y // 8) % 2 == 0 else C_SIDEWALK2
                    s.set_at((x, y), c)
            if main_h_y + road_w <= y < main_h_y + road_w + sw:
                for x in range(W):
                    c = C_SIDEWALK if (x // 8 + y // 8) % 2 == 0 else C_SIDEWALK2
                    s.set_at((x, y), c)
        for x in range(W):
            # 垂直主路左右人行道
            if main_v_x - sw <= x < main_v_x:
                for y in range(play_top, H):
                    c = C_SIDEWALK if (x // 8 + y // 8) % 2 == 0 else C_SIDEWALK2
                    s.set_at((x, y), c)
            if main_v_x + road_w <= x < main_v_x + road_w + sw:
                for y in range(play_top, H):
                    c = C_SIDEWALK if (x // 8 + y // 8) % 2 == 0 else C_SIDEWALK2
                    s.set_at((x, y), c)

        # ── 主路 ──
        # 水平主路
        pygame.draw.rect(s, C_ROAD, (0, main_h_y, W, road_w))
        # 垂直主路
        pygame.draw.rect(s, C_ROAD, (main_v_x, play_top, road_w, H - play_top))

        # 道路纹理
        for _ in range(300):
            rx = r.randint(0, W - 1)
            ry = r.randint(play_top, H - 1)
            # 只在路上
            on_h_road = main_h_y <= ry < main_h_y + road_w
            on_v_road = main_v_x <= rx < main_v_x + road_w
            if on_h_road or on_v_road:
                rc = r.choice([C_ROAD, (55, 55, 60), (62, 62, 66)])
                s.set_at((rx, ry), rc)

        # 路缘石
        curb_color = (160, 155, 148)
        pygame.draw.line(s, curb_color, (0, main_h_y), (W, main_h_y), 2)
        pygame.draw.line(s, curb_color, (0, main_h_y + road_w), (W, main_h_y + road_w), 2)
        pygame.draw.line(s, curb_color, (main_v_x, play_top), (main_v_x, H), 2)
        pygame.draw.line(s, curb_color, (main_v_x + road_w, play_top), (main_v_x + road_w, H), 2)

        # ── 车道中线（黄色虚线） ──
        dash_len = 16
        gap_len = 12
        # 水平主路中线
        cy = main_h_y + road_w // 2
        x = 0
        while x < W:
            pygame.draw.rect(s, C_LANE_DASH, (x, cy - 1, dash_len, 2))
            x += dash_len + gap_len
        # 垂直主路中线
        cx = main_v_x + road_w // 2
        y = play_top
        while y < H:
            pygame.draw.rect(s, C_LANE_DASH, (cx - 1, y, 2, dash_len))
            y += dash_len + gap_len

        # ── 斑马线（十字路口） ──
        cross_points = [
            (main_v_x, main_h_y),  # 路口中心参考
        ]
        for cpx, cpy in cross_points:
            # 上方斑马线
            for i in range(0, road_w, 6):
                pygame.draw.rect(s, C_CROSSWALK, (cpx + i, cpy - 12, 4, 10))
            # 下方
            for i in range(0, road_w, 6):
                pygame.draw.rect(s, C_CROSSWALK, (cpx + i, cpy + road_w + 2, 4, 10))
            # 左侧
            for i in range(0, road_w, 6):
                pygame.draw.rect(s, C_CROSSWALK, (cpx - 12, cpy + i, 10, 4))
            # 右侧
            for i in range(0, road_w, 6):
                pygame.draw.rect(s, C_CROSSWALK, (cpx + road_w + 2, cpy + i, 10, 4))

        # ── 小路（连接建筑区域） ──
        # 在四个象限内画几条小路
        small_road_w = 24
        paths = [
            # 左上象限横路
            (10, play_top + 70, main_v_x - 10 - 10, small_road_w),
            (10, main_h_y - 50, main_v_x - 10 - 10, small_road_w),
            # 右上象限
            (main_v_x + road_w + 10, play_top + 70, W - main_v_x - road_w - 20, small_road_w),
            (main_v_x + road_w + 10, main_h_y - 50, W - main_v_x - road_w - 20, small_road_w),
            # 左下
            (10, main_h_y + road_w + 50, main_v_x - 10 - 10, small_road_w),
            # 右下
            (main_v_x + road_w + 10, main_h_y + road_w + 50, W - main_v_x - road_w - 20, small_road_w),
            # 竖路
            (100, play_top, small_road_w, main_h_y - play_top),
            (W - 120, play_top, small_road_w, main_h_y - play_top),
            (100, main_h_y + road_w, small_road_w, H - main_h_y - road_w),
            (W - 120, main_h_y + road_w, small_road_w, H - main_h_y - road_w),
        ]
        for px, py, pw, ph in paths:
            if pw > 0 and ph > 0:
                pygame.draw.rect(s, (50, 50, 54), (px, py, pw, ph))
                # 小路路缘
                pygame.draw.rect(s, curb_color, (px, py, pw, ph), 1)

        # ── 井盖 ──
        for _ in range(6):
            mx = r.randint(20, W - 20)
            my = r.randint(play_top + 20, H - 20)
            pygame.draw.circle(s, C_MANHOLE, (mx, my), 4)
            pygame.draw.circle(s, (55, 55, 58), (mx, my), 4, 1)

        # ── 停放车辆（静态） ──
        for car in self.cars:
            self._draw_car_static(s, car)

        # ── 树木 ──
        for tree in self.trees:
            # 树干阴影
            pygame.draw.circle(s, (20, 20, 20, 40), (tree['x'] + 2, tree['y'] + 2), tree['r'])
            # 树干
            pygame.draw.circle(s, C_TREE_TRUNK, (tree['x'], tree['y']), 3)
            # 树冠
            pygame.draw.circle(s, tree['color'], (tree['x'], tree['y']), tree['r'])
            pygame.draw.circle(s, brighten(tree['color'], 1.15),
                               (tree['x'] - 2, tree['y'] - 2), tree['r'] - 3)

    def _draw_car_static(self, s, car):
        cx, cy, cw, ch = car['x'], car['y'], car['w'], car['h']
        col = car['color']
        # 车身阴影
        pygame.draw.rect(s, (20, 20, 20, 50), (cx + 1, cy + 1, cw, ch), border_radius=3)
        # 车身
        pygame.draw.rect(s, col, (cx, cy, cw, ch), border_radius=3)
        pygame.draw.rect(s, darken(col, 0.7), (cx, cy, cw, ch), 1, border_radius=3)
        # 车窗
        if car['horizontal']:
            win_x = cx + 4
            win_w = cw - 8
            pygame.draw.rect(s, (140, 180, 220, 150), (win_x, cy + 2, win_w, ch - 4), border_radius=2)
            # 前后灯
            pygame.draw.rect(s, (220, 220, 180), (cx + 1, cy + 1, 2, 3))
            pygame.draw.rect(s, (220, 220, 180), (cx + 1, cy + ch - 4, 2, 3))
            pygame.draw.rect(s, (200, 50, 50), (cx + cw - 3, cy + 1, 2, 3))
            pygame.draw.rect(s, (200, 50, 50), (cx + cw - 3, cy + ch - 4, 2, 3))
        else:
            win_y = cy + 4
            win_h = ch - 8
            pygame.draw.rect(s, (140, 180, 220, 150), (cx + 2, win_y, cw - 4, win_h), border_radius=2)
            pygame.draw.rect(s, (220, 220, 180), (cx + 1, cy + 1, 3, 2))
            pygame.draw.rect(s, (220, 220, 180), (cx + cw - 4, cy + 1, 3, 2))
            pygame.draw.rect(s, (200, 50, 50), (cx + 1, cy + ch - 3, 3, 2))
            pygame.draw.rect(s, (200, 50, 50), (cx + cw - 4, cy + ch - 3, 3, 2))

    def draw(self, surf):
        """绘制完整背景"""
        surf.blit(self.static_layer, (0, 0))

        # 动态：路灯闪烁
        self.tick_count += 1
        for lamp in self.street_lamps:
            flicker = 0.85 + 0.15 * math.sin(self.tick_count * 0.05 + lamp['x'] * 0.1)
            glow_r = int(18 * flicker)
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 240, 180, int(50 * flicker)),
                               (glow_r, glow_r), glow_r)
            pygame.draw.circle(glow_surf, (255, 250, 220, int(120 * flicker)),
                               (glow_r, glow_r), max(1, glow_r // 3))
            surf.blit(glow_surf, (lamp['x'] - glow_r, lamp['y'] - glow_r))

        # 动态：建筑物
        for b in self.buildings:
            b.draw(surf)

        # 动态：落叶粒子
        for p in self.particles:
            p['x'] += p['x'] * 0.001 + p['vx']
            p['y'] += p['vy']
            p['rot'] += p['vr']
            if p['y'] > H:
                p['y'] = HUD_H
                p['x'] = random.uniform(0, W)
            # 绘制叶子
            leaf_surf = pygame.Surface((int(p['sz'] * 2) + 2, int(p['sz']) + 2), pygame.SRCALPHA)
            pygame.draw.ellipse(leaf_surf, (*p['color'][:3], 180),
                                (0, 0, int(p['sz'] * 2), int(p['sz'])))
            rot_leaf = pygame.transform.rotate(leaf_surf, p['rot'])
            surf.blit(rot_leaf, (int(p['x']), int(p['y'])))

    def check_building_collision(self, x, y, r):
        """检测圆形实体与建筑的碰撞，返回 (collided, new_x, new_y, building)"""
        for b in self.buildings:
            if b.collide_point(x, y, r):
                new_x, new_y = b.push_out(x, y, r)
                return True, new_x, new_y, b
        return False, x, y, None


# ═══════════════ 坦克绘制系统 ═══════════════
def draw_tank(surf, x, y, body_angle, turret_angle,
              hull_color, hull_color2, turret_color, track_color, track_color2,
              barrel_color, scale=1.0, hit_flash=False, muzzle_flash=0):
    """绘制一辆精细坦克：履带+车体+炮塔+炮管+细节"""
    sc = scale
    flash = hit_flash

    # 创建足够大的绘制面（考虑对角线）
    sz = int(72 * sc) + 24
    ts = pygame.Surface((sz, sz), pygame.SRCALPHA)
    cx, cy = sz // 2, sz // 2

    # ── 履带（按车体方向） ──
    body_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    bcx, bcy = sz // 2, sz // 2

    tl = int(30 * sc)   # 履带半长
    tw = int(7 * sc)     # 履带半宽
    gap = int(13 * sc)   # 履带间距

    for side in (-1, 1):
        ty_off = side * gap
        track_rect = (bcx - tl, bcy + ty_off - tw, tl * 2, tw * 2)
        pygame.draw.rect(body_surf, track_color, track_rect, border_radius=int(3 * sc))
        inner_rect = (bcx - tl + 2, bcy + ty_off - tw + 2, tl * 2 - 4, tw * 2 - 4)
        pygame.draw.rect(body_surf, track_color2, inner_rect, border_radius=int(2 * sc))

        n_segments = max(4, int(8 * sc))
        seg_w = (tl * 2 - 4) / n_segments
        for i in range(n_segments):
            sx = bcx - tl + 2 + int(i * seg_w)
            pygame.draw.line(body_surf, (55, 55, 58),
                             (sx, bcy + ty_off - tw + 2),
                             (sx, bcy + ty_off + tw - 2), 1)

        n_wheels = max(2, int(4 * sc))
        wheel_r = max(2, int(3 * sc))
        for i in range(n_wheels):
            wx = bcx - tl + int((i + 0.5) * (tl * 2) / n_wheels)
            pygame.draw.circle(body_surf, (58, 58, 62), (wx, bcy + ty_off), wheel_r)
            pygame.draw.circle(body_surf, (45, 45, 48), (wx, bcy + ty_off),
                               max(1, wheel_r - 1))
            pygame.draw.circle(body_surf, (65, 65, 70), (wx, bcy + ty_off),
                               max(1, wheel_r // 2))

        drive_r = max(2, int(4 * sc))
        for dx in (-tl + 2, tl - 2):
            pygame.draw.circle(body_surf, (62, 62, 66), (bcx + dx, bcy + ty_off), drive_r)
            for a in range(0, 360, 60):
                ar = math.radians(a)
                ex = bcx + dx + int(math.cos(ar) * (drive_r - 1))
                ey = bcy + ty_off + int(math.sin(ar) * (drive_r - 1))
                pygame.draw.line(body_surf, (50, 50, 54),
                                 (bcx + dx, bcy + ty_off), (ex, ey), 1)

    rot_body = pygame.transform.rotate(body_surf, -math.degrees(body_angle))
    br = rot_body.get_rect(center=(cx, cy))
    ts.blit(rot_body, br)

    # ── 车体装甲 ──
    hull_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    hcx, hcy = sz // 2, sz // 2
    hl = int(22 * sc)
    hw = int(11 * sc)
    hc = C_WHITE if flash else hull_color
    hc2 = C_WHITE if flash else hull_color2

    hull_pts = [
        (hcx - hl, hcy - hw + int(3 * sc)),
        (hcx - hl + int(3 * sc), hcy - hw),
        (hcx + hl - int(5 * sc), hcy - hw),
        (hcx + hl, hcy - hw + int(4 * sc)),
        (hcx + hl + int(2 * sc), hcy),
        (hcx + hl, hcy + hw - int(4 * sc)),
        (hcx + hl - int(5 * sc), hcy + hw),
        (hcx - hl + int(3 * sc), hcy + hw),
        (hcx - hl, hcy + hw - int(3 * sc)),
    ]
    pygame.draw.polygon(hull_surf, hc, hull_pts)
    pygame.draw.polygon(hull_surf, hc2, hull_pts, max(1, int(2 * sc)))

    fx = hcx + hl - int(5 * sc)
    pygame.draw.line(hull_surf, hc2, (fx, hcy - hw + 2), (fx, hcy + hw - 2),
                     max(1, int(2 * sc)))

    eng_x = hcx - hl + int(4 * sc)
    eng_w = int(8 * sc)
    eng_rect = (eng_x, hcy - hw + int(2 * sc), eng_w, int(2 * sc) * 2 - 4)
    ec = darken(hull_color, 0.75) if not flash else (200, 200, 200)
    pygame.draw.rect(hull_surf, ec, eng_rect, border_radius=1)
    for i in range(3):
        gx = eng_x + 2 + i * max(1, int(2 * sc))
        pygame.draw.line(hull_surf, darken(hull_color, 0.5) if not flash else (180, 180, 180),
                         (gx, hcy - hw + int(3 * sc)),
                         (gx, hcy + hw - int(3 * sc)), 1)

    if not flash:
        for frac in (0.35, 0.65):
            lx = hcx - hl + int(frac * hl * 2)
            pygame.draw.line(hull_surf, darken(hull_color, 0.8),
                             (lx, hcy - hw + int(2 * sc)),
                             (lx, hcy + hw - int(2 * sc)), 1)
        rivet_color = brighten(hull_color, 1.2)
        for frac_x in (0.15, 0.5, 0.85):
            for frac_y in (0.2, 0.8):
                rx = hcx - hl + int(frac_x * hl * 2)
                ry = hcy - hw + int(frac_y * hw * 2)
                pygame.draw.circle(hull_surf, rivet_color, (rx, ry), max(1, int(sc)))

    rot_hull = pygame.transform.rotate(hull_surf, -math.degrees(body_angle))
    hr = rot_hull.get_rect(center=(cx, cy))
    ts.blit(rot_hull, hr)

    # ── 炮塔 ──
    turr_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    tcx, tcy = sz // 2, sz // 2
    tr = int(10 * sc)
    turr_c = C_WHITE if flash else turret_color

    pygame.draw.circle(turr_surf, (0, 0, 0, 40), (tcx + 1, tcy + 1), tr + 2)

    turr_pts = []
    for i in range(6):
        a = i * math.pi / 3 - math.pi / 6
        r_mod = tr * (0.85 if abs(math.cos(a)) > 0.5 and math.cos(a) > 0 else 1.0)
        turr_pts.append((tcx + int(r_mod * math.cos(a) * 1.1),
                         tcy + int(r_mod * math.sin(a))))
    pygame.draw.polygon(turr_surf, turr_c, turr_pts)
    pygame.draw.polygon(turr_surf, darken(turret_color, 0.7) if not flash else (180, 180, 180),
                        turr_pts, max(1, int(1.5 * sc)))

    if not flash:
        hl_s = pygame.Surface((tr, tr), pygame.SRCALPHA)
        pygame.draw.circle(hl_s, (255, 255, 255, 25), (tr // 2, tr // 2), tr // 2)
        turr_surf.blit(hl_s, (tcx - tr // 2, tcy - tr // 2))

    cup_r = max(2, int(3.5 * sc))
    cup_x = tcx - int(3 * sc)
    pygame.draw.circle(turr_surf, darken(turret_color, 0.85) if not flash else (170, 170, 170),
                       (cup_x, tcy), cup_r)
    pygame.draw.circle(turr_surf, darken(turret_color, 0.7) if not flash else (150, 150, 150),
                       (cup_x, tcy), cup_r, 1)

    if not flash:
        ant_x = tcx - int(5 * sc)
        ant_y = tcy - int(3 * sc)
        pygame.draw.line(turr_surf, (100, 100, 110),
                         (ant_x, ant_y), (ant_x - int(4 * sc), ant_y - int(12 * sc)), 1)
        pygame.draw.circle(turr_surf, C_RED,
                           (ant_x - int(4 * sc), ant_y - int(12 * sc)), max(1, int(sc)))

    rot_turr = pygame.transform.rotate(turr_surf, -math.degrees(turret_angle))
    tr_rect = rot_turr.get_rect(center=(cx, cy))
    ts.blit(rot_turr, tr_rect)

    # ── 炮管 ──
    gun_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
    gcx, gcy = sz // 2, sz // 2
    barrel_len = int(30 * sc)
    barrel_w = max(2, int(3.5 * sc))
    bc = C_WHITE if flash else barrel_color

    pygame.draw.line(gun_surf, bc, (gcx, gcy), (gcx + barrel_len, gcy), barrel_w)
    pygame.draw.line(gun_surf, darken(barrel_color, 0.7) if not flash else (180, 180, 180),
                     (gcx, gcy + barrel_w // 2),
                     (gcx + barrel_len, gcy + barrel_w // 2), 1)

    mb_w = max(3, int(5 * sc))
    mb_h = max(3, int(5 * sc))
    pygame.draw.rect(gun_surf, darken(barrel_color, 0.85) if not flash else (160, 160, 160),
                     (gcx + barrel_len - mb_w // 2, gcy - mb_h // 2, mb_w, mb_h),
                     border_radius=1)

    shield_w = max(3, int(5 * sc))
    shield_h = max(4, int(7 * sc))
    pygame.draw.ellipse(gun_surf, darken(turret_color, 0.8) if not flash else (160, 160, 160),
                        (gcx - 2, gcy - shield_h // 2, shield_w, shield_h))

    rot_gun = pygame.transform.rotate(gun_surf, -math.degrees(turret_angle))
    gr = rot_gun.get_rect(center=(cx, cy))
    ts.blit(rot_gun, gr)

    # ── 开火闪光 ──
    if muzzle_flash > 0:
        flash_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
        fcx, fcy = sz // 2, sz // 2
        muzzle_dist = int(30 * sc) + 4
        mx = fcx + int(math.cos(0) * muzzle_dist)
        my = fcy + int(math.sin(0) * muzzle_dist)
        flash_r = int(8 * sc * (muzzle_flash / 8))
        for ri in range(3):
            r = flash_r - ri * 2
            a = max(1, 200 - ri * 60)
            c = (255, 220 - ri * 30, 50 + ri * 20, a)
            if r > 0:
                pygame.draw.circle(flash_surf, c, (mx, my), r)
        rot_flash = pygame.transform.rotate(flash_surf, -math.degrees(turret_angle))
        fr = rot_flash.get_rect(center=(cx, cy))
        ts.blit(rot_flash, fr)

    surf.blit(ts, (int(x) - cx, int(y) - cy))


# ═══════════════ 粒子系统 ═══════════════
class Particle:
    __slots__ = ['x','y','vx','vy','color','life','ml','sz','grav','drag']
    def __init__(self, x, y, vx, vy, color, life=30, sz=4, grav=0, drag=0.96):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.color, self.life, self.ml = color, life, life
        self.sz, self.grav, self.drag = sz, grav, drag
    def tick(self):
        self.x += self.vx; self.y += self.vy
        self.vy += self.grav; self.vx *= self.drag; self.vy *= self.drag
        self.life -= 1; return self.life > 0
    def draw(self, surf):
        a = self.life / self.ml; s = max(1, int(self.sz * a))
        c = tuple(int(v*a) for v in self.color)
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), s)

class FloatText:
    def __init__(self, x, y, text, color, sz=18):
        self.x, self.y, self.text, self.color = x, y, text, color
        self.life, self.ml = 45, 45; self.ft = font(sz)
    def tick(self):
        self.y -= 0.8; self.life -= 1; return self.life > 0
    def draw(self, surf):
        a = self.life / self.ml
        s = self.ft.render(self.text, True, self.color); s.set_alpha(int(255*a))
        surf.blit(s, (int(self.x)-s.get_width()//2, int(self.y)))

class Particles:
    def __init__(self): self.parts = []; self.texts = []
    def burst(self, x, y, color, n=12, spd=4, life=28, sz=4):
        for _ in range(n):
            a = random.uniform(0, math.tau); s = random.uniform(spd*0.3, spd)
            self.parts.append(Particle(x,y,math.cos(a)*s,math.sin(a)*s,color,
                                       random.randint(life//2,life),random.uniform(sz*0.5,sz),0.08))
    def explosion(self, x, y, n=25):
        for _ in range(n):
            a = random.uniform(0, math.tau); s = random.uniform(1, 6)
            c = random.choice([C_RED, C_ORANGE, C_YELLOW, (200,200,200)])
            self.parts.append(Particle(x,y,math.cos(a)*s,math.sin(a)*s,c,
                                       random.randint(20,50),random.uniform(3,8),0.1))
        for _ in range(10):
            a = random.uniform(0, math.tau); s = random.uniform(0.5, 2)
            self.parts.append(Particle(x,y,math.cos(a)*s,math.sin(a)*s,
                                       (100,100,100),random.randint(40,80),random.uniform(5,12),0.02,0.98))
    def spark(self, x, y, color, n=6):
        for _ in range(n):
            a = random.uniform(0, math.tau); s = random.uniform(2, 5)
            self.parts.append(Particle(x,y,math.cos(a)*s,math.sin(a)*s,color,
                                       random.randint(8,16),random.uniform(2,3)))
    def damage(self, x, y, dmg): self.texts.append(FloatText(x,y-15,str(dmg),C_YELLOW,20))
    def heal(self, x, y, amt): self.texts.append(FloatText(x,y-15,f'+{amt}',C_GREEN,18))
    def tick(self):
        self.parts = [p for p in self.parts if p.tick()]
        self.texts = [t for t in self.texts if t.tick()]
    def draw(self, surf):
        for p in self.parts: p.draw(surf)
        for t in self.texts: t.draw(surf)


# ═══════════════ 炮弹 ═══════════════
class Shell:
    def __init__(self, x, y, angle, dmg=12, spd=7, friendly=True, heavy=False):
        self.x, self.y = x, y
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd
        self.dmg, self.spd = dmg, spd
        self.r = 6 if heavy else 4
        self.friendly = friendly
        self.heavy = heavy
        self.life = 120 if heavy else 80
        self.trail = []
        self.angle = angle
        self.hit_building = False  # 标记是否命中建筑

    def tick(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > (10 if self.heavy else 5): self.trail.pop(0)
        self.x += self.vx; self.y += self.vy
        self.life -= 1
        return self.life > 0 and -20 < self.x < W+20 and -20 < self.y < H+20

    def draw(self, surf):
        tc = (200, 180, 80) if self.friendly else (200, 80, 60)
        for i, (tx, ty) in enumerate(self.trail):
            a = (i+1) / max(1, len(self.trail)) * 0.5
            s = max(1, int(self.r * a * 0.7))
            c = tuple(int(v*a) for v in tc)
            pygame.draw.circle(surf, c, (int(tx), int(ty)), s)
        sc = int(self.r * 1.5)
        shell_s = pygame.Surface((sc*2+4, sc*2+4), pygame.SRCALPHA)
        scx, scy = sc+2, sc+2
        pts = [(scx+sc, scy), (scx-sc//2, scy-sc//2), (scx-sc, scy-sc//3),
               (scx-sc, scy+sc//3), (scx-sc//2, scy+sc//2)]
        bc = C_YELLOW if self.friendly else C_RED
        pygame.draw.polygon(shell_s, bc, pts)
        pygame.draw.polygon(shell_s, darken(bc, 0.7), pts, 1)
        rot_s = pygame.transform.rotate(shell_s, -math.degrees(self.angle))
        surf.blit(rot_s, (int(self.x)-rot_s.get_width()//2, int(self.y)-rot_s.get_height()//2))
        glow = pygame.Surface((self.r*6, self.r*6), pygame.SRCALPHA)
        gc = (*C_YELLOW[:3], 30) if self.friendly else (*C_RED[:3], 30)
        pygame.draw.circle(glow, gc, (self.r*3, self.r*3), self.r*3)
        surf.blit(glow, (int(self.x)-self.r*3, int(self.y)-self.r*3))


# ═══════════════ 玩家 ═══════════════
class Player:
    def __init__(self):
        self.x, self.y = W//2, H//2
        self.r = 18
        self.spd = 2.8
        self.hp, self.maxhp = 120, 120
        self.body_angle = 0
        self.turret_angle = 0
        self.shoot_cd = 0
        self.shell_cd = 0
        self.muzzle_flash = 0
        self.invincible = 0
        self.alive = True
        self.bob = 0
        self.bldg_dmg_cd = 0  # 撞楼伤害冷却

    def tick(self, keys, mouse_pos, shells, enemies, fx, shake, bg):
        if not self.alive: return
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:   dy =  1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:   dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:  dx =  1
        self.moving = dx != 0 or dy != 0
        if self.moving:
            dx, dy = norm((dx, dy))
            target_angle = math.atan2(dy, dx)
            diff = target_angle - self.body_angle
            while diff > math.pi: diff -= math.tau
            while diff < -math.pi: diff += math.tau
            self.body_angle += diff * 0.15
            # 尝试移动，检测建筑碰撞
            new_x = clamp(self.x + dx*self.spd, self.r+4, W-self.r-4)
            new_y = clamp(self.y + dy*self.spd, HUD_H+self.r+4, H-self.r-4)

            # X 轴移动
            test_x = clamp(self.x + dx*self.spd, self.r+4, W-self.r-4)
            hit, nx, ny, bldg = bg.check_building_collision(test_x, self.y, self.r)
            if hit:
                self.x = nx
                # 撞楼掉血
                if self.bldg_dmg_cd <= 0:
                    self.hp -= 3
                    self.bldg_dmg_cd = 30  # 0.5秒冷却
                    bldg.take_damage(2, fx)
                    fx.spark(self.x + dx * self.r, self.y, C_ORANGE, 6)
                    fx.damage(self.x, self.y - 20, 3)
                    shake.add(3)
            else:
                self.x = test_x

            # Y 轴移动
            test_y = clamp(self.y + dy*self.spd, HUD_H+self.r+4, H-self.r-4)
            hit, nx, ny, bldg = bg.check_building_collision(self.x, test_y, self.r)
            if hit:
                self.y = ny
                if self.bldg_dmg_cd <= 0:
                    self.hp -= 3
                    self.bldg_dmg_cd = 30
                    bldg.take_damage(2, fx)
                    fx.spark(self.x, self.y + dy * self.r, C_ORANGE, 6)
                    fx.damage(self.x, self.y - 20, 3)
                    shake.add(3)
            else:
                self.y = test_y

            if self.bldg_dmg_cd > 0:
                self.bldg_dmg_cd -= 1
            self.bob += 0.25

        # 面向鼠标
        self.turret_angle = angle_to((self.x, self.y), mouse_pos)

        if self.shoot_cd > 0: self.shoot_cd -= 1
        if self.shell_cd > 0: self.shell_cd -= 1
        if self.muzzle_flash > 0: self.muzzle_flash -= 1
        if self.invincible > 0: self.invincible -= 1
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            fx.explosion(self.x, self.y, 35)

    def shoot(self, shells):
        if self.shoot_cd > 0 or not self.alive: return
        bx = self.x + math.cos(self.turret_angle) * (self.r + 6)
        by = self.y + math.sin(self.turret_angle) * (self.r + 6)
        shells.append(Shell(bx, by, self.turret_angle, dmg=12, spd=8))
        self.shoot_cd = 12
        self.muzzle_flash = 6

    def heavy_shell(self, shells, fx, shake):
        if self.shell_cd > 0 or not self.alive: return
        bx = self.x + math.cos(self.turret_angle) * (self.r + 8)
        by = self.y + math.sin(self.turret_angle) * (self.r + 8)
        shells.append(Shell(bx, by, self.turret_angle, dmg=40, spd=6, heavy=True))
        self.shell_cd = 60
        self.muzzle_flash = 8
        shake.add(4)

    def hurt(self, dmg, fx, shake):
        if self.invincible > 0: return
        self.hp -= dmg
        self.invincible = 30
        fx.spark(self.x, self.y, C_ORANGE, 8)
        shake.add(5)
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            fx.explosion(self.x, self.y, 35)
            shake.add(12)

    def draw(self, surf):
        if not self.alive: return
        if self.invincible > 0 and self.invincible % 6 < 3: return
        draw_tank(surf, self.x, self.y, self.body_angle, self.turret_angle,
                  C_P_HULL, C_P_HULL2, C_P_TURRET, C_P_TRACK, C_P_TRACK2,
                  C_P_BARREL, scale=1.0, hit_flash=False,
                  muzzle_flash=self.muzzle_flash)
        # 血条
        bw = 36; bx = int(self.x) - bw//2; by = int(self.y) - 32
        pygame.draw.rect(surf, C_DARK, (bx-1,by-1,bw+2,6), border_radius=2)
        fill = int(bw * self.hp / self.maxhp)
        hc = C_GREEN if self.hp > 60 else C_YELLOW if self.hp > 30 else C_RED
        if fill > 0: pygame.draw.rect(surf, hc, (bx,by,fill,4), border_radius=2)


# ═══════════════ 敌方坦克 ═══════════════
class EnemyTank:
    def __init__(self, etype, x, y):
        cfg = ENEMY_CFG[etype]
        self.etype = etype
        self.x, self.y = x, y
        self.r = int(18 * cfg['scale'])
        self.hp, self.maxhp = cfg['hp'], cfg['hp']
        self.spd = cfg['spd']
        self.score_val = cfg['score']
        self.dmg = cfg['dmg']
        self.ai = cfg['ai']
        self.scale = cfg['scale']
        self.hull_c = cfg['hull_c']
        self.hull2_c = cfg['hull2_c']
        self.turret_c = cfg['turret_c']
        self.shoot_interval = cfg['shoot_cd']
        self.shell_dmg = cfg['shell_dmg']
        self.shell_spd = cfg['shell_spd']
        self.alive = True
        self.hit_flash = 0
        self.atk_cd = 0
        self.shoot_timer = random.randint(30, self.shoot_interval)
        self.phase = random.uniform(0, math.tau)
        self.tick_count = 0
        self.body_angle = random.uniform(0, math.tau)
        self.turret_angle = 0
        self.muzzle_flash = 0
        self.bldg_dmg_cd = 0

    def tick(self, player, shells, fx, shake, bg):
        if not self.alive: return
        self.tick_count += 1
        if self.hit_flash > 0: self.hit_flash -= 1
        if self.atk_cd > 0: self.atk_cd -= 1
        if self.muzzle_flash > 0: self.muzzle_flash -= 1
        if self.bldg_dmg_cd > 0: self.bldg_dmg_cd -= 1
        self.shoot_timer -= 1

        a = angle_to((self.x, self.y), (player.x, player.y))
        diff = a - self.turret_angle
        while diff > math.pi: diff -= math.tau
        while diff < -math.pi: diff += math.tau
        self.turret_angle += diff * 0.08

        if self.ai == 'chase':
            target_angle = a
            diff2 = target_angle - self.body_angle
            while diff2 > math.pi: diff2 -= math.tau
            while diff2 < -math.pi: diff2 += math.tau
            self.body_angle += diff2 * 0.1
            # 尝试移动 + 碰撞检测
            new_x = clamp(self.x + math.cos(a)*self.spd, self.r+4, W-self.r-4)
            new_y = clamp(self.y + math.sin(a)*self.spd, HUD_H+self.r+4, H-self.r-4)
            # X
            hit, nx, ny, bldg = bg.check_building_collision(new_x, self.y, self.r)
            if hit:
                self.x = nx
                if self.bldg_dmg_cd <= 0:
                    self.hp -= 2; self.bldg_dmg_cd = 40
                    bldg.take_damage(1, fx)
                    fx.spark(nx, self.y, C_ORANGE, 4)
            else:
                self.x = new_x
            # Y
            hit, nx, ny, bldg = bg.check_building_collision(self.x, new_y, self.r)
            if hit:
                self.y = ny
                if self.bldg_dmg_cd <= 0:
                    self.hp -= 2; self.bldg_dmg_cd = 40
                    bldg.take_damage(1, fx)
                    fx.spark(self.x, ny, C_ORANGE, 4)
            else:
                self.y = new_y

        elif self.ai == 'zigzag':
            self.phase += 0.08
            side = math.sin(self.phase) * 2.5
            perp = a + math.pi/2
            mx = math.cos(a)*self.spd + math.cos(perp)*side*0.4
            my = math.sin(a)*self.spd + math.sin(perp)*side*0.4
            target_angle = math.atan2(my, mx)
            diff2 = target_angle - self.body_angle
            while diff2 > math.pi: diff2 -= math.tau
            while diff2 < -math.pi: diff2 += math.tau
            self.body_angle += diff2 * 0.12
            new_x = clamp(self.x + mx, self.r+4, W-self.r-4)
            new_y = clamp(self.y + my, HUD_H+self.r+4, H-self.r-4)
            hit, nx, ny, bldg = bg.check_building_collision(new_x, self.y, self.r)
            if hit:
                self.x = nx
            else:
                self.x = new_x
            hit, nx, ny, bldg = bg.check_building_collision(self.x, new_y, self.r)
            if hit:
                self.y = ny
            else:
                self.y = new_y

        # 检查撞楼死亡
        if self.hp <= 0:
            self.alive = False
            fx.explosion(self.x, self.y, 20)

        # Boss 多发炮弹
        if self.etype == 'boss' and self.tick_count % 80 == 0:
            for i in range(3):
                ba = a + (i - 1) * 0.2
                bx = self.x + math.cos(ba) * (self.r + 15)
                by = self.y + math.sin(ba) * (self.r + 15)
                shells.append(Shell(bx, by, ba, dmg=self.shell_dmg,
                                    spd=self.shell_spd, friendly=False, heavy=True))
                self.muzzle_flash = 6

        # 普通开火
        if self.shoot_timer <= 0 and self.etype != 'boss':
            self.shoot_timer = self.shoot_interval + random.randint(-10, 10)
            bx = self.x + math.cos(self.turret_angle) * (self.r + 12)
            by = self.y + math.sin(self.turret_angle) * (self.r + 12)
            shells.append(Shell(bx, by, self.turret_angle, dmg=self.shell_dmg,
                                spd=self.shell_spd, friendly=False))
            self.muzzle_flash = 5

        # 碰撞玩家
        if dist((self.x,self.y),(player.x,player.y)) < self.r + player.r:
            if self.atk_cd <= 0:
                player.hurt(self.dmg, fx, shake)
                self.atk_cd = 60

    def hurt(self, dmg, fx):
        self.hp -= dmg; self.hit_flash = 6
        fx.damage(self.x, self.y, dmg)
        if self.hp <= 0: self.alive = False

    def draw(self, surf):
        if not self.alive: return
        draw_tank(surf, self.x, self.y, self.body_angle, self.turret_angle,
                  self.hull_c, self.hull2_c, self.turret_c,
                  C_E_TRACK, C_E_TRACK2, C_E_BARREL,
                  scale=self.scale, hit_flash=self.hit_flash > 0,
                  muzzle_flash=self.muzzle_flash)
        if self.hp < self.maxhp:
            bw = int(self.r * 2.5); bx = int(self.x) - bw//2
            by = int(self.y) - self.r - 16
            pygame.draw.rect(surf, C_DARK, (bx-1,by-1,bw+2,5), border_radius=2)
            fill = int(bw * self.hp / self.maxhp)
            hc = C_RED if self.etype == 'boss' else C_GREEN
            if fill > 0: pygame.draw.rect(surf, hc, (bx,by,fill,3), border_radius=2)
        if self.etype == 'boss':
            ft = font(14)
            t = ft.render('重型坦克', True, C_RED)
            surf.blit(t, (int(self.x)-t.get_width()//2, int(self.y)-self.r-28))


# ═══════════════ 屏幕震动 ═══════════════
class ScreenShake:
    def __init__(self): self.amount = 0
    def add(self, a): self.amount = max(self.amount, a)
    def get(self):
        if self.amount < 0.5: return (0,0)
        ox = random.uniform(-self.amount, self.amount)
        oy = random.uniform(-self.amount, self.amount)
        self.amount *= 0.85; return (int(ox), int(oy))


# ═══════════════ UI ═══════════════
def draw_vignette(surf):
    vg = pygame.Surface((W, H), pygame.SRCALPHA)
    for i in range(80, 0, -1):
        a = int(0.9*(80-i))
        pygame.draw.rect(vg, (0,0,0,a), (i,i,W-2*i,H-2*i), 1)
    surf.blit(vg, (0,0))

def draw_hud(surf, player, wave, score, enemy_count):
    for i in range(HUD_H):
        pygame.draw.line(surf, (18+i//4,20+i//4,28+i//4), (0,i), (W,i))
    pygame.draw.line(surf, (60,65,78), (0,HUD_H-1), (W,HUD_H-1), 2)
    f = font(18); fb = font(20)

    surf.blit(f.render('装甲', True, C_WHITE), (10, 16))
    bw = 140; bx = 55
    pygame.draw.rect(surf, C_DARK, (bx,16,bw,18), border_radius=4)
    fill = int(bw * player.hp / player.maxhp)
    hc = C_GREEN if player.hp > 60 else C_YELLOW if player.hp > 30 else C_RED
    if fill > 0: pygame.draw.rect(surf, hc, (bx,16,fill,18), border_radius=4)
    hl = pygame.Surface((bw,9), pygame.SRCALPHA)
    pygame.draw.rect(hl, (255,255,255,30), (0,0,bw,9), border_radius=4)
    surf.blit(hl, (bx,16))
    surf.blit(f.render(f'{player.hp}/{player.maxhp}', True, C_WHITE), (bx+bw+6, 16))

    shell_ready = player.shell_cd <= 0
    sc = C_GREEN if shell_ready else C_GRAY
    st = '重炮: 就绪' if shell_ready else f'重炮: {player.shell_cd//60+1}s'
    surf.blit(f.render(st, True, sc), (10, 36))

    surf.blit(fb.render(f'第 {wave} 波', True, C_BLUE), (W//2-40, 14))
    surf.blit(f.render(f'击毁: {score}', True, C_YELLOW), (W-180, 8))
    surf.blit(f.render(f'剩余: {enemy_count} 辆', True, C_RED), (W-180, 30))

    # 撞楼提示
    if player.bldg_dmg_cd > 0:
        warn_ft = font(14)
        warn = warn_ft.render('⚠ 撞击建筑', True, C_ORANGE)
        surf.blit(warn, (W//2 - warn.get_width()//2, HUD_H + 4))

def draw_menu(surf, bg):
    bg.draw(surf)
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0,0,0,150))
    surf.blit(overlay, (0,0))
    ft = font(56); fs = font(22)
    title_sh = ft.render('坦克大战', True, (0,0,0))
    surf.blit(title_sh, (W//2-title_sh.get_width()//2+3, H//2-93))
    title = ft.render('坦克大战', True, C_YELLOW)
    surf.blit(title, (W//2-title.get_width()//2, H//2-96))
    sub = fs.render('WASD移动 | 鼠标瞄准 | 左键机枪 | 空格重炮', True, C_GRAY)
    surf.blit(sub, (W//2-sub.get_width()//2, H//2-20))
    tip = fs.render('注意：撞击建筑会掉血！炮弹可摧毁建筑', True, C_ORANGE)
    surf.blit(tip, (W//2-tip.get_width()//2, H//2+10))
    blink = abs(math.sin(pygame.time.get_ticks()*0.003))
    start = fs.render('— 点击任意处开始 —', True, lerp_color(C_GRAY, C_WHITE, blink))
    surf.blit(start, (W//2-start.get_width()//2, H//2+50))
    draw_vignette(surf)
    pygame.display.flip()

def draw_gameover(surf, score, wave):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0,0,0,170)); surf.blit(overlay, (0,0))
    ft = font(48); fs = font(24)
    t1 = ft.render('坦克被击毁', True, C_RED)
    t2 = fs.render(f'击毁积分: {score}', True, C_YELLOW)
    t3 = fs.render(f'存活到第 {wave} 波', True, C_WHITE)
    t4 = fs.render('按 R 重新出击 | ESC 退出', True, C_GRAY)
    surf.blit(t1, (W//2-t1.get_width()//2, H//2-80))
    surf.blit(t2, (W//2-t2.get_width()//2, H//2-20))
    surf.blit(t3, (W//2-t3.get_width()//2, H//2+15))
    surf.blit(t4, (W//2-t4.get_width()//2, H//2+60))


# ═══════════════ 波次管理 ═══════════════
def spawn_wave(wave, bg):
    enemies = []
    n_scout = 2 + wave
    n_medium = max(0, wave - 2) * 2
    n_heavy = max(0, wave - 4)
    has_boss = wave % 5 == 0 and wave > 0
    cfgs = [('scout', n_scout), ('medium', n_medium), ('heavy', n_heavy)]
    if has_boss: cfgs += [('boss', 1)]
    for etype, count in cfgs:
        for _ in range(count):
            # 尝试多次找到不撞建筑的出生点
            for attempt in range(30):
                side = random.randint(0, 3)
                if side == 0:   ex, ey = random.randint(60,W-60), HUD_H+50
                elif side == 1: ex, ey = random.randint(60,W-60), H-50
                elif side == 2: ex, ey = 50, random.randint(HUD_H+60,H-60)
                else:           ex, ey = W-50, random.randint(HUD_H+60,H-60)
                # 检查不在建筑内
                in_bldg = False
                for b in bg.buildings:
                    if b.collide_point(ex, ey, 25):
                        in_bldg = True
                        break
                if not in_bldg:
                    enemies.append(EnemyTank(etype, ex, ey))
                    break
    return enemies


# ═══════════════ 主游戏 ═══════════════
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption('坦克大战 - 城市版')
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'menu'
        self.bg = CityBackground()
        self.reset()

    def reset(self):
        self.player = Player()
        # 确保玩家不在建筑内
        for b in self.bg.buildings:
            if b.collide_point(self.player.x, self.player.y, self.player.r):
                self.player.x, self.player.y = b.push_out(
                    self.player.x, self.player.y, self.player.r)
        self.enemies = []
        self.shells = []
        self.fx = Particles()
        self.shake = ScreenShake()
        self.wave = 0; self.score = 0; self.wave_timer = 0
        self.next_wave()

    def next_wave(self):
        self.wave += 1
        self.enemies = spawn_wave(self.wave, self.bg)
        self.wave_timer = 120

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False; return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.running = False; return
                if event.key == pygame.K_r and self.state == 'over':
                    self.reset(); self.state = 'play'
                if event.key == pygame.K_SPACE and self.state == 'play':
                    self.player.heavy_shell(self.shells, self.fx, self.shake)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == 'menu': self.state = 'play'
        if self.state == 'play':
            keys = pygame.key.get_pressed()
            self.player.tick(keys, mouse_pos, self.shells, self.enemies,
                             self.fx, self.shake, self.bg)
            if mouse_down: self.player.shoot(self.shells)

    def update(self):
        self.bg.tick_count += 1
        if self.state != 'play': return
        if self.wave_timer > 0: self.wave_timer -= 1
        for e in self.enemies:
            e.tick(self.player, self.shells, self.fx, self.shake, self.bg)
        self.shells = [s for s in self.shells if s.tick()]

        # 炮弹碰撞检测
        for s in list(self.shells):
            # 先检测建筑碰撞
            building_hit = False
            for b in self.bg.buildings:
                if not b.destroyed and b.collide_point(s.x, s.y, s.r):
                    b.take_damage(s.dmg, self.fx)
                    self.fx.spark(s.x, s.y, C_GRAY, 8)
                    self.shake.add(2)
                    if s.heavy:
                        self.fx.explosion(s.x, s.y, 12)
                        self.shake.add(4)
                    if s in self.shells: self.shells.remove(s)
                    building_hit = True
                    break
            if building_hit:
                continue

            if s.friendly:
                for e in self.enemies:
                    if e.alive and dist((s.x,s.y),(e.x,e.y)) < s.r + e.r:
                        e.hurt(s.dmg, self.fx)
                        self.fx.spark(s.x, s.y, C_ORANGE, 8)
                        self.shake.add(3)
                        if s.heavy:
                            self.fx.explosion(s.x, s.y, 15)
                            self.shake.add(5)
                        if s in self.shells: self.shells.remove(s)
                        break
            else:
                if self.player.alive and dist((s.x,s.y),(self.player.x,self.player.y)) < s.r + self.player.r:
                    self.player.hurt(s.dmg, self.fx, self.shake)
                    if s.heavy: self.fx.explosion(s.x, s.y, 12)
                    if s in self.shells: self.shells.remove(s)

        for e in list(self.enemies):
            if not e.alive:
                self.score += e.score_val
                self.fx.explosion(e.x, e.y, 30)
                self.shake.add(6)
                if random.random() < 0.2:
                    heal = 15
                    self.player.hp = min(self.player.maxhp, self.player.hp + heal)
                    self.fx.heal(self.player.x, self.player.y, heal)
        self.enemies = [e for e in self.enemies if e.alive]
        self.fx.tick()
        if len(self.enemies) == 0 and self.wave_timer <= 0: self.next_wave()
        if not self.player.alive: self.state = 'over'

    def draw(self):
        if self.state == 'menu': draw_menu(self.screen, self.bg); return
        ox, oy = self.shake.get()
        render = pygame.Surface((W, H))
        self.bg.draw(render)
        for e in self.enemies: e.draw(render)
        self.player.draw(render)
        for s in self.shells: s.draw(render)
        self.fx.draw(render)
        draw_vignette(render)
        draw_hud(render, self.player, self.wave, self.score, len(self.enemies))
        if self.wave_timer > 60:
            ft = font(36)
            t = ft.render(f'— 第 {self.wave} 波 —', True, C_YELLOW)
            t.set_alpha(int(255*(self.wave_timer-60)/60))
            render.blit(t, (W//2-t.get_width()//2, H//2-50))
        if self.state == 'over': draw_gameover(render, self.score, self.wave)
        self.screen.blit(render, (ox, oy))
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events(); self.update(); self.draw()
            self.clock.tick(FPS)
        pygame.quit(); sys.exit()


if __name__ == '__main__':
    Game().run()

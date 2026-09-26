"""
坦克大战 · 霓虹漂移版 - Python + Pygame
运行：pip install pygame
Python 3.14 如安装卡住，请改用：pip install pygame-ce
然后：python tank_battle_ultra_drift.py

操作：
    WASD 驾驶 | 鼠标瞄准 | 左键机枪 | 空格重炮
    Shift 手刹漂移（松开自动恢复抓地）
    R 重开 | ESC 暂停 / 菜单

超顺手漂移：
    惯性移动、车头平滑转向、抓地力变化、甩尾烟雾、轮胎印
    高速时松开 Shift 会快速回正，连续漂移不会失控

漂亮城市：
    雨夜霓虹城市、潮湿反光路面、暖色窗户、路灯柔光、动态雨丝
"""
import sys, os, math, random, array, pygame
# ═══════════════ 常量 ═══════════════
W, H = 960, 640
HUD_H = 52
CHUNK = 320
ROAD = 48
SIDEWALK = 10
FPS = 60
# 霓虹夜色基础色
C_BG       = (12, 16, 29)
C_HUD      = (13, 17, 27)
C_RED      = (244, 83, 91)
C_GREEN    = (66, 220, 146)
C_BLUE     = (76, 174, 255)
C_YELLOW   = (255, 207, 82)
C_WHITE    = (238, 243, 250)
C_GRAY     = (130, 144, 164)
C_DARK     = (17, 21, 33)
C_ORANGE   = (255, 145, 64)
# 坦克配色
C_P_HULL     = (69, 105, 91)
C_P_HULL2    = (51, 82, 73)
C_P_TRACK    = (43, 48, 58)
C_P_TRACK2   = (31, 35, 44)
C_P_TURRET   = (58, 91, 80)
C_P_BARREL   = (72, 83, 90)
C_P_DETAIL   = (92, 128, 112)
C_E_SCOUT    = (124, 109, 68)
C_E_SCOUT2   = (94, 82, 51)
C_E_MEDIUM   = (132, 99, 61)
C_E_MEDIUM2  = (103, 76, 45)
C_E_HEAVY    = (83, 87, 100)
C_E_HEAVY2   = (59, 62, 75)
C_E_TRACK    = (43, 44, 51)
C_E_TRACK2   = (31, 32, 38)
C_E_BARREL   = (69, 72, 82)
# ── 雨夜城市背景色 ──
C_ROAD       = (39, 44, 57)
C_ROAD_LINE  = (244, 188, 74)
C_SIDEWALK   = (82, 92, 109)
C_SIDEWALK2  = (67, 77, 94)
C_GRASS      = (31, 54, 57)
C_GRASS2     = (25, 45, 50)
C_LANE_DASH  = (245, 205, 96)
C_CROSSWALK  = (201, 211, 224)
C_MANHOLE    = (31, 35, 44)
C_TREE_TRUNK = (87, 62, 42)
C_TREE_LEAF  = (37, 106, 82)
C_TREE_LEAF2 = (49, 128, 96)
C_CAR_COLORS = [
    (202, 58, 70), (54, 105, 211), (224, 229, 235),
    (42, 46, 59), (229, 174, 55), (47, 172, 112),
    (216, 108, 49), (126, 68, 180), (45, 185, 196),
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
# ═══════════════ 武器与道具 ═══════════════
WEAPONS = {
    'single': {'name': '机枪', 'cd': 12, 'dmg': 12, 'spd': 8,   'count': 1, 'spread': 0.0,  'laser': False},
    'spread': {'name': '散弹', 'cd': 22, 'dmg': 10, 'spd': 7.5, 'count': 3, 'spread': 0.14, 'laser': False},
    'laser':  {'name': '激光', 'cd': 9,  'dmg': 10, 'spd': 14,  'count': 1, 'spread': 0.0,  'laser': True},
}
WEAPON_UPGRADE_TIME = 600   # 武器升级持续时间（帧），约 10 秒
# ═══════════════ 坦克升级系统 ═══════════════
LEVEL_MAX = 5   # 最高等级
# 各等级坦克配色（绿 → 蓝 → 紫 → 金 → 青金）
LEVEL_COLORS = [
    {'hull': C_P_HULL,     'hull2': C_P_HULL2,     'turret': C_P_TURRET,     'barrel': C_P_BARREL},
    {'hull': (52, 100, 150), 'hull2': (42, 82, 128), 'turret': (48, 92, 140), 'barrel': (50, 80, 120)},
    {'hull': (110, 60, 130), 'hull2': (90, 48, 108), 'turret': (100, 55, 120), 'barrel': (80, 60, 100)},
    {'hull': (150, 100, 40), 'hull2': (128, 84, 30), 'turret': (140, 92, 36), 'barrel': (120, 90, 40)},
    {'hull': (60, 130, 120), 'hull2': (48, 108, 100), 'turret': (54, 118, 110), 'barrel': (50, 100, 95)},
]
# 等级加成：level → (最大血量增加, 速度增加, 火力倍率, 重炮伤害加成)
LEVEL_BONUS = {
    1: (0,   0.00, 1.0, 0),
    2: (40,  0.15, 1.2, 15),
    3: (80,  0.30, 1.4, 30),
    4: (120, 0.45, 1.6, 45),
    5: (160, 0.60, 1.8, 60),
}
DROP_RATE = 0.25            # 普通敌人掉宝概率
DROP_TYPES = {
    'coin':   {'name': '金币',    'color': C_YELLOW, 'score': 50},
    'medkit': {'name': '回血包',  'color': C_GREEN,  'heal': 30},
    'shield': {'name': '护盾',    'color': C_BLUE,   'shield': 60},
    'weapon': {'name': '武器升级','color': C_ORANGE,'weapon': True},
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
# ═══════════════ 声音系统（合成电子音效 + 可选音频文件） ═══════════════
class SoundManager:
    """音效与背景音乐管理。
    优先加载 sounds/ 目录下的同名音频文件；没有文件时自动合成电子音效，
    保证开箱即用（无音频设备时静默降级，不影响游戏运行）。
    """
    RATE = 22050
    def __init__(self, base_dir='sounds'):
        self.ok = False
        self.sounds = {}
        self.music_sound = None
        self.music_path = None
        self.base_dir = base_dir
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(self.RATE, -16, 1, 512)
            self.ok = True
        except Exception:
            self.ok = False
            return
        try:
            self._build()
        except Exception:
            self.ok = False
    # ── 纯 Python 波形合成（无需 numpy，兼容任意 Python 3） ──
    def _synth(self, freq, dur, vol=0.5, wave='square', decay=2.0, sweep=0.0, noise=False):
        rate = self.RATE
        n = max(1, int(rate * dur))
        buf = array.array('h', [0]) * n
        for i in range(n):
            t = i / rate
            if noise:
                v = random.uniform(-1.0, 1.0)
            else:
                f = max(20.0, freq + sweep * t)
                ph = (t * f) % 1.0
                if wave == 'square':
                    v = 1.0 if ph < 0.5 else -1.0
                elif wave == 'saw':
                    v = 2.0 * ph - 1.0
                elif wave == 'tri':
                    v = 4.0 * abs(ph - 0.5) - 1.0
                else:
                    v = math.sin(ph * math.tau)
            env = math.exp(-decay * t / dur) if decay > 0 else (1.0 - t / dur)
            buf[i] = int(max(-1.0, min(1.0, v * env)) * vol * 32000)
        return pygame.mixer.Sound(buffer=buf.tobytes())
    def _compose(self, notes, gap=0.015, vol=0.4, wave='square'):
        """把多个音符合成一条 Sound：notes = [(freq, dur), ...]"""
        rate = self.RATE
        total = sum(int(rate * (d + gap)) for f, d in notes)
        buf = array.array('h', [0]) * total
        pos = 0
        for f, d in notes:
            n = int(rate * d)
            for i in range(n):
                t = i / rate
                ph = (t * f) % 1.0
                if wave == 'square':
                    v = 1.0 if ph < 0.5 else -1.0
                elif wave == 'saw':
                    v = 2.0 * ph - 1.0
                else:
                    v = math.sin(ph * math.tau)
                env = 1.0 - t / d
                buf[pos + i] = int(max(-1.0, min(1.0, v * env)) * vol * 32000)
            pos += n + int(rate * gap)
        return pygame.mixer.Sound(buffer=buf.tobytes())
    def _load_or_synth(self, key, synth_fn):
        path = os.path.join(self.base_dir, key + '.wav')
        try:
            if os.path.isfile(path):
                self.sounds[key] = pygame.mixer.Sound(path)
                return
        except Exception:
            pass
        self.sounds[key] = synth_fn()
    def _build(self):
        # 音效：有文件用文件，没有文件就合成
        self._load_or_synth('shoot',    lambda: self._synth(720, 0.08, 0.30, 'square', 1.5, sweep=-2600))
        self._load_or_synth('heavy',    lambda: self._synth(160, 0.35, 0.55, 'saw', 1.8, sweep=-100))
        self._load_or_synth('explode',  lambda: self._synth(80, 0.55, 0.60, 'square', 2.2, noise=True))
        self._load_or_synth('hit',      lambda: self._synth(300, 0.12, 0.35, 'square', 2.0, sweep=-150))
        self._load_or_synth('coin',     lambda: self._synth(1568, 0.12, 0.35, 'sine', 1.0))
        self._load_or_synth('pickup',   lambda: self._synth(660, 0.22, 0.40, 'tri', 1.2, sweep=900))
        self._load_or_synth('shield',   lambda: self._synth(1180, 0.18, 0.35, 'square', 1.5, sweep=500))
        self._load_or_synth('hurt',     lambda: self._synth(320, 0.22, 0.45, 'saw', 2.0, sweep=-180))
        self._load_or_synth('boss',     lambda: self._compose([(880, 0.12), (660, 0.12), (880, 0.12), (660, 0.18)], wave='square', vol=0.5))
        self._load_or_synth('gameover', lambda: self._compose([(523, 0.15), (392, 0.15), (330, 0.2), (262, 0.35)], wave='tri', vol=0.5))
        self._load_or_synth('win',      lambda: self._compose([(523, 0.1), (659, 0.1), (784, 0.1), (1047, 0.3)], wave='square', vol=0.4))
        self._load_or_synth('levelup',  lambda: self._compose([(523, 0.08), (659, 0.08), (784, 0.08), (1047, 0.25)], wave='square', vol=0.45))
        # 背景音乐：优先 sounds/bgm.wav|bgm.ogg（Sound 播放）或 bgm.mp3（music 播放），
        # 否则合成一段 8 小节电子低音循环
        for ext in ('.wav', '.ogg'):
            mp = os.path.join(self.base_dir, 'bgm' + ext)
            if os.path.isfile(mp):
                try:
                    self.music_sound = pygame.mixer.Sound(mp)
                except Exception:
                    self.music_sound = None
                break
        mp3p = os.path.join(self.base_dir, 'bgm.mp3')
        if os.path.isfile(mp3p):
            self.music_path = mp3p
        if self.music_sound is None and self.music_path is None:
            bpm = 120; note = 60.0 / bpm; gap = 0.02
            seq = []
            base = [220.0, 174.6, 130.8, 196.0]   # A2 F2 C3 G2
            for bar in range(8):
                root = base[bar % 4]
                for k in range(4):
                    f = root * (1.0 if k % 2 == 0 else 1.5)
                    seq.append((f, note * 0.9))
            self.music_sound = self._compose(seq, gap=gap, vol=0.16, wave='saw')
    def play(self, key):
        if not self.ok:
            return
        s = self.sounds.get(key)
        if s:
            try: s.play()
            except Exception: pass
    def start_music(self):
        if not self.ok:
            return
        try:
            if self.music_sound:
                self.music_sound.play(loops=-1)
            elif self.music_path:
                pygame.mixer.music.load(self.music_path)
                pygame.mixer.music.set_volume(0.6)
                pygame.mixer.music.play(-1)
        except Exception:
            pass
    def stop_music(self):
        if not self.ok:
            return
        try:
            if self.music_sound:
                self.music_sound.stop()
            pygame.mixer.music.stop()
        except Exception:
            pass
# ═══════════════ 建筑物 ═══════════════
class Building:
    """城市中的建筑物：俯视图，有碰撞体和视觉表现"""
    # 建筑配色方案
    STYLES = [
        {'wall': (82, 88, 104), 'wall2': (63, 69, 84), 'roof': (58, 64, 79),
         'accent': (38, 43, 56), 'neon': (78, 220, 255), 'name': 'glass_blue'},
        {'wall': (112, 78, 78), 'wall2': (88, 59, 61), 'roof': (76, 49, 52),
         'accent': (48, 35, 43), 'neon': (255, 91, 151), 'name': 'brick_rose'},
        {'wall': (68, 103, 111), 'wall2': (51, 81, 91), 'roof': (43, 69, 79),
         'accent': (31, 49, 60), 'neon': (83, 255, 194), 'name': 'teal'},
        {'wall': (101, 97, 113), 'wall2': (77, 73, 89), 'roof': (63, 60, 75),
         'accent': (40, 38, 51), 'neon': (255, 191, 75), 'name': 'violet_grey'},
        {'wall': (128, 72, 93), 'wall2': (101, 51, 72), 'roof': (81, 40, 59),
         'accent': (54, 29, 44), 'neon': (255, 102, 222), 'name': 'magenta'},
        {'wall': (75, 94, 75), 'wall2': (56, 73, 58), 'roof': (44, 59, 47),
         'accent': (31, 43, 35), 'neon': (164, 255, 96), 'name': 'green_tint'},
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
        pygame.draw.line(s, (188, 211, 231, 70),
                         (ox + 3, oy + 3), (ox + self.w - 4, oy + 3), 1)
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
                lit = r.random() < 0.58
                if lit:
                    wc = r.choice([(255, 215, 123), (129, 213, 255), (255, 181, 104), (183, 255, 222)])
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
        # 霓虹招牌：让雨夜街区更有层次
        if self.w >= 30 and self.h >= 30 and r.random() < 0.72:
            nc = st['neon']
            side = r.choice(('left', 'right', 'top', 'bottom'))
            if side == 'left':
                nx, ny, nw, nh = ox + 2, oy + max(5, self.h // 3), 4, min(25, self.h // 3)
            elif side == 'right':
                nx, ny, nw, nh = ox + self.w - 6, oy + max(5, self.h // 3), 4, min(25, self.h // 3)
            elif side == 'top':
                nx, ny, nw, nh = ox + max(5, self.w // 3), oy + 2, min(25, self.w // 3), 4
            else:
                nx, ny, nw, nh = ox + max(5, self.w // 3), oy + self.h - 6, min(25, self.w // 3), 4
            pygame.draw.rect(s, (*nc, 68), (nx - 2, ny - 2, nw + 4, nh + 4), border_radius=2)
            pygame.draw.rect(s, (*nc, 235), (nx, ny, nw, nh), border_radius=2)
            pygame.draw.line(s, (255, 255, 255, 220),
                             (nx + nw // 2, ny + 1), (nx + nw // 2, ny + nh - 1), 1)
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
    def draw(self, surf, cam_x=0, cam_y=0):
        if self.dmg_flash > 0:
            self.dmg_flash -= 1
        # 绘制预渲染
        surf.blit(self._surf, (self.x - self._ox - cam_x, self.y - self._oy - cam_y))
        # 受伤闪烁
        if self.dmg_flash > 0:
            flash_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            flash_surf.fill((255, 100, 50, 80))
            surf.blit(flash_surf, (self.x - cam_x, self.y - cam_y))
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
            surf.blit(crack_surf, (self.x - cam_x, self.y - cam_y))
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
# ═══════════════ 城市背景（无尽世界 · 分块生成 + 相机跟随） ═══════════════
class CityBackground:
    """无限雨夜霓虹城市：分块生成、湿路反光、路灯与动态雨丝。"""
    def __init__(self):
        self.chunks = {}
        self._order = []
        self.tick_count = 0
        self.particles = []
        for _ in range(10):
            self.particles.append({
                'x': random.uniform(0, W), 'y': random.uniform(HUD_H, H),
                'vx': random.uniform(-0.18, 0.18), 'vy': random.uniform(0.16, 0.38),
                'rot': random.uniform(0, 360), 'vr': random.uniform(-1.2, 1.2),
                'sz': random.uniform(1.5, 3.0),
                'color': random.choice([(105, 148, 79), (171, 139, 51), (155, 81, 48)]),
            })
        self.rain = []
        for _ in range(105):
            self.rain.append({
                'x': random.uniform(-30, W + 30), 'y': random.uniform(HUD_H, H + 80),
                'sp': random.uniform(7.0, 13.0), 'wind': random.uniform(-0.8, -0.25),
                'ln': random.uniform(7.0, 16.0), 'a': random.randint(45, 120),
            })
    @staticmethod
    def _chunk_seed(cx, cy):
        return ((cx * 0x9E3779B1) ^ (cy * 0x85EBCA77)) & 0xFFFFFFFF
    def _touch(self, key):
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)
        if len(self._order) > 220:
            old = self._order.pop(0)
            if old in self.chunks:
                self.chunks[old]['surf'] = None
    def get_chunk(self, cx, cy):
        key = (cx, cy)
        ch = self.chunks.get(key)
        if ch is None:
            ch = self._generate_chunk(cx, cy)
            self.chunks[key] = ch
        self._touch(key)
        if ch['surf'] is None:
            self._render_chunk_base(ch, cx, cy)
        return ch
    def _generate_chunk(self, cx, cy):
        ox, oy = cx * CHUNK, cy * CHUNK
        rng = random.Random(self._chunk_seed(cx, cy) ^ 0x5F3759DF)
        half = ROAD // 2
        block0 = half + SIDEWALK + 8
        block1 = CHUNK - half - SIDEWALK - 8
        buildings, lamps, placed = [], [], []
        n_buildings = rng.randint(3, 6)
        for _ in range(n_buildings * 4):
            if len(placed) >= n_buildings:
                break
            bw = rng.randint(30, min(72, block1 - block0))
            bh = rng.randint(30, min(72, block1 - block0))
            bx = block0 + rng.randint(0, max(0, block1 - block0 - bw))
            by = block0 + rng.randint(0, max(0, block1 - block0 - bh))
            overlap = False
            for px, py, pw, ph in placed:
                if (bx < px + pw + 9 and bx + bw + 9 > px and
                        by < py + ph + 9 and by + bh + 9 > py):
                    overlap = True
                    break
            if overlap:
                continue
            floors = rng.randint(2, 14)
            style_idx = rng.randint(0, len(Building.STYLES) - 1)
            has_helipad = floors >= 11 and bw > 42 and bh > 42 and rng.random() < 0.45
            buildings.append(Building(ox + bx, oy + by, bw, bh, style_idx, floors, has_helipad))
            placed.append((bx, by, bw, bh))
        step = 170
        for lx in range(24, CHUNK, step):
            lamps.append((ox + lx, oy + half + 4))
            lamps.append((ox + lx, oy + CHUNK - half - 4))
        for ly in range(24, CHUNK, step):
            lamps.append((ox + half + 4, oy + ly))
            lamps.append((ox + CHUNK - half - 4, oy + ly))
        return {'buildings': buildings, 'lamps': lamps, 'surf': None}
    def _render_chunk_base(self, chunk, cx, cy):
        ox, oy = cx * CHUNK, cy * CHUNK
        rng = random.Random(self._chunk_seed(cx, cy))
        half, sw = ROAD // 2, SIDEWALK
        surf = pygame.Surface((CHUNK, CHUNK), pygame.SRCALPHA)
        surf.fill(C_GRASS)
        for _ in range(1050):
            gx = rng.randrange(CHUNK); gy = rng.randrange(CHUNK)
            surf.set_at((gx, gy), rng.choice([C_GRASS, C_GRASS2, (36, 63, 63), (27, 52, 49)]))
        pygame.draw.rect(surf, C_ROAD, (0, 0, CHUNK, half))
        pygame.draw.rect(surf, C_ROAD, (0, CHUNK - half, CHUNK, half))
        pygame.draw.rect(surf, C_ROAD, (0, 0, half, CHUNK))
        pygame.draw.rect(surf, C_ROAD, (CHUNK - half, 0, half, CHUNK))
        for _ in range(320):
            rx = rng.randrange(CHUNK); ry = rng.randrange(CHUNK)
            if rx < half or rx >= CHUNK - half or ry < half or ry >= CHUNK - half:
                surf.set_at((rx, ry), rng.choice([C_ROAD, (43, 49, 63), (34, 39, 51), (48, 52, 64)]))
        for k in range(4):
            off = 6 + k * 5
            pygame.draw.line(surf, (32, 37, 49), (off, 0), (off, CHUNK), 1)
            pygame.draw.line(surf, (32, 37, 49), (CHUNK - off, 0), (CHUNK - off, CHUNK), 1)
            pygame.draw.line(surf, (32, 37, 49), (0, off), (CHUNK, off), 1)
            pygame.draw.line(surf, (32, 37, 49), (0, CHUNK - off), (CHUNK, CHUNK - off), 1)
        def scolor(lx, ly):
            wx, wy = ox + lx, oy + ly
            return C_SIDEWALK if ((wx // 8 + wy // 8) % 2 == 0) else C_SIDEWALK2
        for i in range(half, half + sw):
            for y in range(CHUNK):
                surf.set_at((i, y), scolor(i, y))
            for x in range(CHUNK):
                surf.set_at((x, i), scolor(x, i))
        for i in range(CHUNK - half - sw, CHUNK - half):
            for y in range(CHUNK):
                surf.set_at((i, y), scolor(i, y))
            for x in range(CHUNK):
                surf.set_at((x, i), scolor(x, i))
        curb = (151, 165, 181)
        edge = (79, 91, 108)
        for k in (half, CHUNK - half):
            pygame.draw.line(surf, curb, (k, 0), (k, CHUNK), 1)
            pygame.draw.line(surf, edge, (k + sw, 0), (k + sw, CHUNK), 1)
            pygame.draw.line(surf, curb, (0, k), (CHUNK, k), 1)
            pygame.draw.line(surf, edge, (0, k + sw), (CHUNK, k + sw), 1)
        for _ in range(26):
            side = rng.randrange(4)
            if side < 2:
                px = rng.randrange(3, CHUNK - 8); py = rng.randrange(3, half - 3)
                if side == 1: py = CHUNK - half + rng.randrange(3, half - 3)
            else:
                px = rng.randrange(3, half - 3); py = rng.randrange(3, CHUNK - 8)
                if side == 3: px = CHUNK - half + rng.randrange(3, half - 3)
            pw = rng.randint(8, 26); ph = rng.randint(3, 9)
            pygame.draw.ellipse(surf, (21, 35, 57, 100), (px, py, pw, ph))
            pygame.draw.ellipse(surf, (86, 171, 226, 50), (px + 2, py + 1, pw - 4, max(1, ph - 3)), 1)
            if rng.random() < 0.42:
                rc = rng.choice([(78, 220, 255), (255, 91, 151), (255, 191, 75)])
                pygame.draw.line(surf, (*rc, 55), (px + 3, py + ph // 2), (px + pw - 3, py + ph // 2), 1)
        dash, gap = 15, 17
        for yy in range(0, CHUNK, dash + gap):
            pygame.draw.rect(surf, C_LANE_DASH, (CHUNK - 3, yy, 2, dash), border_radius=1)
        for xx in range(0, CHUNK, dash + gap):
            pygame.draw.rect(surf, C_LANE_DASH, (xx, CHUNK - 3, dash, 2), border_radius=1)
        for cxx, cyy in ((0, 0), (CHUNK, 0), (0, CHUNK), (CHUNK, CHUNK)):
            for i in range(0, half, 7):
                for x0, y0, w0, h0 in ((cxx + i - half, cyy - 13, 4, 11),
                                        (cxx + i - half, cyy + half + 2, 4, 11),
                                        (cxx - 13, cyy + i - half, 11, 4),
                                        (cxx + half + 2, cyy + i - half, 11, 4)):
                    pygame.draw.rect(surf, C_CROSSWALK, (x0, y0, w0, h0))
                    if rng.random() < 0.22:
                        pygame.draw.line(surf, (99, 111, 128), (x0, y0 + h0 // 2), (x0 + w0, y0 + h0 // 2), 1)
        block0, block1 = half + sw + 8, CHUNK - half - sw - 8
        for _ in range(rng.randint(2, 5)):
            tx = rng.randint(block0, block1); ty = rng.randint(block0, block1)
            if any(b.collide_point(ox + tx, oy + ty, 13) for b in chunk['buildings']):
                continue
            tr = rng.randint(8, 15)
            tcol = rng.choice([C_TREE_LEAF, C_TREE_LEAF2, (45, 135, 99), (61, 151, 110)])
            pygame.draw.circle(surf, (8, 13, 22, 90), (tx + 3, ty + 4), tr + 1)
            pygame.draw.circle(surf, C_TREE_TRUNK, (tx, ty), 3)
            pygame.draw.circle(surf, tcol, (tx, ty), tr)
            pygame.draw.circle(surf, brighten(tcol, 1.22), (tx - 3, ty - 3), max(2, tr - 4))
        for _ in range(rng.randint(0, 2)):
            edge = rng.randrange(4)
            if edge == 0:
                cpx, cpy = rng.randint(40, CHUNK - 40), half - 15; horizontal = True
            elif edge == 1:
                cpx, cpy = rng.randint(40, CHUNK - 40), CHUNK - half + 5; horizontal = True
            elif edge == 2:
                cpx, cpy = half - 15, rng.randint(40, CHUNK - 40); horizontal = False
            else:
                cpx, cpy = CHUNK - half + 5, rng.randint(40, CHUNK - 40); horizontal = False
            if not any(b.collide_point(ox + cpx + 8, oy + cpy + 5, 10) for b in chunk['buildings']):
                car = {'x': cpx, 'y': cpy, 'w': 22 if horizontal else 12,
                       'h': 10 if horizontal else 22,
                       'color': rng.choice(C_CAR_COLORS), 'horizontal': horizontal}
                self._draw_car_static(surf, car)
                glow = pygame.Surface((46, 26), pygame.SRCALPHA)
                pygame.draw.ellipse(glow, (255, 226, 154, 25), (0, 4, 46, 18))
                surf.blit(glow, (cpx - 12, cpy - 8))
        for _ in range(rng.randint(1, 2)):
            mx = rng.randint(block0, block1); my = rng.randint(block0, block1)
            pygame.draw.circle(surf, C_MANHOLE, (mx, my), 4)
            pygame.draw.circle(surf, (68, 74, 88), (mx, my), 4, 1)
        chunk['surf'] = surf
    def _draw_car_static(self, s, car):
        cx, cy, cw, ch = car['x'], car['y'], car['w'], car['h']
        col = car['color']
        pygame.draw.rect(s, (8, 12, 20, 90), (cx + 2, cy + 2, cw, ch), border_radius=3)
        pygame.draw.rect(s, col, (cx, cy, cw, ch), border_radius=3)
        pygame.draw.rect(s, darken(col, 0.55), (cx, cy, cw, ch), 1, border_radius=3)
        if car['horizontal']:
            pygame.draw.rect(s, (107, 170, 205), (cx + 4, cy + 2, cw - 8, ch - 4), border_radius=2)
            pygame.draw.rect(s, (255, 239, 176), (cx + 1, cy + 1, 3, 3))
            pygame.draw.rect(s, (255, 239, 176), (cx + 1, cy + ch - 4, 3, 3))
            pygame.draw.rect(s, (238, 60, 68), (cx + cw - 3, cy + 1, 2, 3))
            pygame.draw.rect(s, (238, 60, 68), (cx + cw - 3, cy + ch - 4, 2, 3))
        else:
            pygame.draw.rect(s, (107, 170, 205), (cx + 2, cy + 4, cw - 4, ch - 8), border_radius=2)
            pygame.draw.rect(s, (255, 239, 176), (cx + 1, cy + 1, 3, 2))
            pygame.draw.rect(s, (255, 239, 176), (cx + cw - 4, cy + 1, 3, 2))
            pygame.draw.rect(s, (238, 60, 68), (cx + 1, cy + ch - 3, 3, 2))
            pygame.draw.rect(s, (238, 60, 68), (cx + cw - 4, cy + ch - 3, 3, 2))
    def get_buildings_near(self, x, y, radius):
        res = []
        cx0, cy0 = int(x - radius) // CHUNK, int(y - radius) // CHUNK
        cx1, cy1 = int(x + radius) // CHUNK, int(y + radius) // CHUNK
        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                res.extend(self.get_chunk(cx, cy)['buildings'])
        return res
    def point_in_building(self, x, y, r=0):
        return any(b.collide_point(x, y, r) for b in self.get_buildings_near(x, y, r))
    def check_building_collision(self, x, y, r):
        for b in self.get_buildings_near(x, y, r):
            if b.collide_point(x, y, r):
                new_x, new_y = b.push_out(x, y, r)
                return True, new_x, new_y, b
        return False, x, y, None
    def draw(self, surf, cam_x=0, cam_y=0):
        self.tick_count += 1
        ix, iy = int(cam_x), int(cam_y)
        x0 = ix // CHUNK - 1; x1 = (ix + W) // CHUNK + 1
        y0 = iy // CHUNK - 1; y1 = (iy + H) // CHUNK + 1
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                ch = self.get_chunk(cx, cy)
                surf.blit(ch['surf'], (cx * CHUNK - ix, cy * CHUNK - iy))
                for (lx, ly) in ch['lamps']:
                    self._draw_lamp(surf, lx - ix, ly - iy)
                for b in ch['buildings']:
                    b.draw(surf, cam_x, cam_y)
        for p in self.particles:
            p['x'] += p['x'] * 0.0008 + p['vx']; p['y'] += p['vy']; p['rot'] += p['vr']
            if p['y'] > H:
                p['y'] = HUD_H; p['x'] = random.uniform(0, W)
            leaf_surf = pygame.Surface((int(p['sz'] * 2) + 2, int(p['sz']) + 2), pygame.SRCALPHA)
            pygame.draw.ellipse(leaf_surf, (*p['color'][:3], 155), (0, 0, int(p['sz'] * 2), int(p['sz'])))
            surf.blit(pygame.transform.rotate(leaf_surf, p['rot']), (int(p['x']), int(p['y'])))
        rain_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        for d in self.rain:
            d['x'] += d['wind']; d['y'] += d['sp']
            if d['y'] > H + 60 or d['x'] < -40:
                d['x'] = random.uniform(W * 0.35, W + 40)
                d['y'] = random.uniform(HUD_H - 90, HUD_H - 5)
            pygame.draw.line(rain_surf, (150, 204, 241, d['a']),
                             (int(d['x']), int(d['y'])),
                             (int(d['x'] - d['wind'] * d['ln']), int(d['y'] - d['ln'])), 1)
        surf.blit(rain_surf, (0, 0))
    def _draw_lamp(self, surf, sx, sy):
        flicker = 0.91 + 0.09 * math.sin(self.tick_count * 0.055 + sx * 0.08)
        glow_r = int(31 * flicker)
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 205, 106, int(24 * flicker)), (glow_r, glow_r), glow_r)
        pygame.draw.circle(glow, (255, 224, 159, int(100 * flicker)), (glow_r, glow_r), max(2, glow_r // 3))
        pygame.draw.circle(glow, (255, 247, 214, 185), (glow_r, glow_r), 2)
        surf.blit(glow, (int(sx) - glow_r, int(sy) - glow_r))
# ═══════════════ 坦克绘制系统 ═══════════════
def draw_drop_shadow(surf, x, y, r, alpha=70):
    """坦克脚下的椭圆投影阴影"""
    w = int(r * 2)
    h = max(3, int(r * 0.55))
    sh = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, alpha), (0, 0, w, h))
    surf.blit(sh, (int(x) - w // 2, int(y) - h // 2 + 2))
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
    def draw(self, surf, cam_x=0, cam_y=0):
        a = self.life / self.ml; s = max(1, int(self.sz * a))
        c = tuple(int(v*a) for v in self.color)
        pygame.draw.circle(surf, c, (int(self.x)-cam_x, int(self.y)-cam_y), s)
class FloatText:
    def __init__(self, x, y, text, color, sz=18):
        self.x, self.y, self.text, self.color = x, y, text, color
        self.life, self.ml = 45, 45; self.ft = font(sz)
    def tick(self):
        self.y -= 0.8; self.life -= 1; return self.life > 0
    def draw(self, surf, cam_x=0, cam_y=0):
        a = self.life / self.ml
        s = self.ft.render(self.text, True, self.color); s.set_alpha(int(255*a))
        surf.blit(s, (int(self.x)-cam_x-s.get_width()//2, int(self.y)-cam_y))
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
    def smoke(self, x, y, n=8):
        """烟尘：缓慢上升、逐渐膨胀扩散的灰色粒子"""
        for _ in range(n):
            a = random.uniform(0, math.tau); s = random.uniform(0.3, 1.6)
            self.parts.append(Particle(x, y, math.cos(a)*s, math.sin(a)*s - 0.6,
                                       random.choice([(90,90,90),(120,120,120),
                                                      (150,150,150),(70,70,70)]),
                                       random.randint(30, 70), random.uniform(3, 8), -0.02, 0.97))
    def debris(self, x, y, color, n=10):
        """碎片：受重力下坠、带弹跳感的残骸碎块"""
        for _ in range(n):
            a = random.uniform(0, math.tau); s = random.uniform(2, 6)
            self.parts.append(Particle(x, y, math.cos(a)*s, math.sin(a)*s, color,
                                       random.randint(20, 45), random.uniform(2, 4), 0.12, 0.94))
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
    def draw(self, surf, cam_x=0, cam_y=0):
        for p in self.parts: p.draw(surf, cam_x, cam_y)
        for t in self.texts: t.draw(surf, cam_x, cam_y)
# ═══════════════ 炮弹 ═══════════════
class Shell:
    def __init__(self, x, y, angle, dmg=12, spd=7, friendly=True, heavy=False, laser=False):
        self.x, self.y = x, y
        self.prev_x, self.prev_y = x, y
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd
        self.dmg, self.spd = dmg, spd
        self.r = 6 if heavy else 4
        self.friendly = friendly
        self.heavy = heavy
        self.laser = laser
        self.life = 120 if heavy else 80
        self.trail = []
        self.angle = angle
        self.hit_building = False  # 标记是否命中建筑
    def tick(self):
        self.prev_x, self.prev_y = self.x, self.y
        self.trail.append((self.x, self.y))
        if len(self.trail) > (10 if self.heavy else 5): self.trail.pop(0)
        self.x += self.vx; self.y += self.vy
        self.life -= 1
        return self.life > 0
    def draw(self, surf, cam_x=0, cam_y=0):
        # 激光弹：细长光束轨迹
        if self.laser:
            pygame.draw.line(surf, (255, 120, 70),
                             (int(self.prev_x)-cam_x, int(self.prev_y)-cam_y),
                             (int(self.x)-cam_x, int(self.y)-cam_y), 4)
            pygame.draw.line(surf, (255, 230, 160),
                             (int(self.prev_x)-cam_x, int(self.prev_y)-cam_y),
                             (int(self.x)-cam_x, int(self.y)-cam_y), 1)
            pygame.draw.circle(surf, (255, 255, 220), (int(self.x)-cam_x, int(self.y)-cam_y), 4)
            return
        tc = (200, 180, 80) if self.friendly else (200, 80, 60)
        for i, (tx, ty) in enumerate(self.trail):
            a = (i+1) / max(1, len(self.trail)) * 0.5
            s = max(1, int(self.r * a * 0.7))
            c = tuple(int(v*a) for v in tc)
            pygame.draw.circle(surf, c, (int(tx)-cam_x, int(ty)-cam_y), s)
        sc = int(self.r * 1.5)
        shell_s = pygame.Surface((sc*2+4, sc*2+4), pygame.SRCALPHA)
        scx, scy = sc+2, sc+2
        pts = [(scx+sc, scy), (scx-sc//2, scy-sc//2), (scx-sc, scy-sc//3),
               (scx-sc, scy+sc//3), (scx-sc//2, scy+sc//2)]
        bc = C_YELLOW if self.friendly else C_RED
        pygame.draw.polygon(shell_s, bc, pts)
        pygame.draw.polygon(shell_s, darken(bc, 0.7), pts, 1)
        rot_s = pygame.transform.rotate(shell_s, -math.degrees(self.angle))
        surf.blit(rot_s, (int(self.x)-cam_x-rot_s.get_width()//2, int(self.y)-cam_y-rot_s.get_height()//2))
        glow = pygame.Surface((self.r*6, self.r*6), pygame.SRCALPHA)
        gc = (*C_YELLOW[:3], 30) if self.friendly else (*C_RED[:3], 30)
        pygame.draw.circle(glow, gc, (self.r*3, self.r*3), self.r*3)
        surf.blit(glow, (int(self.x)-cam_x-self.r*3, int(self.y)-cam_y-self.r*3))
# ═══════════════ 玩家 ═══════════════
class Player:
    def __init__(self):
        self.x, self.y = W // 2, H // 2
        self.r = 18
        self.max_speed = 5.15
        self.spd = self.max_speed
        self.accel = 0.39
        self.vx = self.vy = 0.0
        self.hp, self.maxhp = 120, 120
        self.body_angle = -math.pi / 2
        self.turret_angle = 0
        self.shoot_cd = 0
        self.shell_cd = 0
        self.muzzle_flash = 0
        self.invincible = 0
        self.alive = True
        self.bob = 0
        self.bldg_dmg_cd = 0
        self.moving = False
        self.handbrake = False
        self.drifting = False
        self.drift_factor = 0.0
        self.skid_marks = []
        self.last_skid = None
        self.skid_tick = 0
        self.smoke_tick = 0
        self.recoil = 0.0
        self.weapon_key = 'single'
        self.weapon_timer = 0
        self.shield = 0
        self.shield_max = 60
        self.shield_dur = 0
        self.sound = None
        self.coins = 0
        self.level = 1
        self.exp = 0
        self.dmg_mul = 1.0
        self.heavy_bonus = 0
        self.scale = 1.0

    def tick(self, keys, mouse_pos, shells, enemies, fx, shake, bg):
        if not self.alive:
            return
        if self.bldg_dmg_cd > 0: self.bldg_dmg_cd -= 1
        if self.shoot_cd > 0: self.shoot_cd -= 1
        if self.shell_cd > 0: self.shell_cd -= 1
        if self.muzzle_flash > 0: self.muzzle_flash -= 1
        if self.invincible > 0: self.invincible -= 1
        if self.weapon_timer > 0:
            self.weapon_timer -= 1
            if self.weapon_timer <= 0:
                self.weapon_key = 'single'
        if self.shield_dur > 0:
            self.shield_dur -= 1
            if self.shield_dur <= 0:
                self.shield = 0

        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        self.moving = dx != 0 or dy != 0
        self.handbrake = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        sharp_turn = 0.0
        if self.moving:
            dx, dy = norm((dx, dy))
            target_angle = math.atan2(dy, dx)
            diff = target_angle - self.body_angle
            while diff > math.pi: diff -= math.tau
            while diff < -math.pi: diff += math.tau
            sharp_turn = abs(diff)
            turn_rate = clamp(0.24 + sharp_turn * 0.075, 0.24, 0.52)
            if self.handbrake:
                turn_rate += 0.09
            self.body_angle += diff * turn_rate
            self.body_angle %= math.tau
            boost = 1.2 if self.handbrake and self.get_speed() > 1.0 else 1.0
            self.vx += dx * self.accel * boost
            self.vy += dy * self.accel * boost

        speed = self.get_speed()
        lateral = 0.0
        if speed > 0.01:
            fx_dir = math.cos(self.body_angle)
            fy_dir = math.sin(self.body_angle)
            rx_dir, ry_dir = -fy_dir, fx_dir
            fwd_speed = self.vx * fx_dir + self.vy * fy_dir
            lat_speed = self.vx * rx_dir + self.vy * ry_dir
            if self.handbrake:
                grip = 0.032
            else:
                grip = 0.23 - min(0.11, sharp_turn * 0.08)
                if speed > 3.6 and sharp_turn > 0.55:
                    grip *= 0.72
            lat_speed *= max(0.0, 1.0 - grip)
            fwd_speed *= 0.973 if not self.moving else 0.993
            self.vx = fx_dir * fwd_speed + rx_dir * lat_speed
            self.vy = fy_dir * fwd_speed + ry_dir * lat_speed
            lateral = abs(lat_speed)
        if not self.moving and not self.handbrake:
            self.vx *= 0.975
            self.vy *= 0.975
        max_now = self.max_speed * (1.15 if self.handbrake else 1.0)
        speed = self.get_speed()
        if speed > max_now:
            k = max_now / speed
            self.vx *= k; self.vy *= k
            speed = max_now
        self.drift_factor = min(1.0, lateral / max(1.0, speed * 0.72))
        self.drifting = speed > 2.05 and (self.handbrake or self.drift_factor > 0.30)

        test_x = self.x + self.vx
        hit, nx, ny, bldg = bg.check_building_collision(test_x, self.y, self.r)
        if hit:
            self.x = nx
            impact = abs(self.vx)
            self.vx *= -0.16
            self.vy *= 0.78
            if self.bldg_dmg_cd <= 0:
                self.hp -= 3
                self.bldg_dmg_cd = 28
                bldg.take_damage(2, fx)
                fx.spark(self.x + math.copysign(self.r, -self.vx if self.vx else 1), self.y, C_ORANGE, 5)
                fx.damage(self.x, self.y - 20, 3)
                shake.add(min(6, 2 + impact))
        else:
            self.x = test_x
        test_y = self.y + self.vy
        hit, nx, ny, bldg = bg.check_building_collision(self.x, test_y, self.r)
        if hit:
            self.y = ny
            impact = abs(self.vy)
            self.vy *= -0.16
            self.vx *= 0.78
            if self.bldg_dmg_cd <= 0:
                self.hp -= 3
                self.bldg_dmg_cd = 28
                bldg.take_damage(2, fx)
                fx.spark(self.x, self.y + math.copysign(self.r, -self.vy if self.vy else 1), C_ORANGE, 5)
                fx.damage(self.x, self.y - 20, 3)
                shake.add(min(6, 2 + impact))
        else:
            self.y = test_y

        speed = self.get_speed()
        self.bob += speed * 0.045
        self.turret_angle = angle_to((self.x, self.y), mouse_pos)
        self.recoil *= 0.82
        self._update_drift_marks(speed, fx)
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            fx.explosion(self.x, self.y, 35)

    def get_speed(self):
        return math.hypot(self.vx, self.vy)

    def _update_drift_marks(self, speed, fx):
        kept = []
        for x1, y1, x2, y2, life in self.skid_marks:
            if life > 1:
                kept.append((x1, y1, x2, y2, life - 1))
        self.skid_marks = kept
        if not (self.drifting and speed > 1.45):
            self.last_skid = None
            return
        self.skid_tick += 1
        fx_dir, fy_dir = math.cos(self.body_angle), math.sin(self.body_angle)
        px, py = -fy_dir * self.r * 0.55, fx_dir * self.r * 0.55
        back = self.r * 0.78
        left = (self.x - fx_dir * back + px, self.y - fy_dir * back + py)
        right = (self.x - fx_dir * back - px, self.y - fy_dir * back - py)
        if self.last_skid is not None and self.skid_tick % 2 == 0:
            self.skid_marks.append((self.last_skid[0][0], self.last_skid[0][1], left[0], left[1], 135))
            self.skid_marks.append((self.last_skid[1][0], self.last_skid[1][1], right[0], right[1], 135))
        self.last_skid = (left, right)
        self.smoke_tick += 1
        if self.smoke_tick % 3 == 0:
            fx.smoke(self.x - fx_dir * self.r + random.uniform(-6, 6),
                     self.y - fy_dir * self.r + random.uniform(-6, 6), 1)

    def draw_marks(self, surf, cam_x=0, cam_y=0):
        for x1, y1, x2, y2, life in self.skid_marks:
            shade = int(24 + 18 * (life / 135.0))
            pygame.draw.line(surf, (shade, shade + 2, shade + 5),
                             (int(x1 - cam_x), int(y1 - cam_y)),
                             (int(x2 - cam_x), int(y2 - cam_y)), 2)

    def shoot(self, shells):
        if self.shoot_cd > 0 or not self.alive:
            return
        wp = WEAPONS[self.weapon_key]
        for i in range(wp['count']):
            off = (i - (wp['count'] - 1) / 2) * wp['spread']
            ang = self.turret_angle + off
            bx = self.x + math.cos(ang) * (self.r + 7)
            by = self.y + math.sin(ang) * (self.r + 7)
            shells.append(Shell(bx, by, ang, dmg=int(wp['dmg'] * self.dmg_mul),
                                spd=wp['spd'], laser=wp['laser']))
        self.shoot_cd = wp['cd']
        self.muzzle_flash = 6
        self.recoil = 0.18
        self.vx -= math.cos(self.turret_angle) * 0.09
        self.vy -= math.sin(self.turret_angle) * 0.09

    def heavy_shell(self, shells, fx, shake):
        if self.shell_cd > 0 or not self.alive:
            return
        bx = self.x + math.cos(self.turret_angle) * (self.r + 9)
        by = self.y + math.sin(self.turret_angle) * (self.r + 9)
        shells.append(Shell(bx, by, self.turret_angle,
                            dmg=40 + self.heavy_bonus, spd=6, heavy=True))
        self.shell_cd = 60
        self.muzzle_flash = 8
        self.recoil = 0.6
        self.vx -= math.cos(self.turret_angle) * 0.34
        self.vy -= math.sin(self.turret_angle) * 0.34
        shake.add(5)

    def hurt(self, dmg, fx, shake):
        if self.invincible > 0 or not self.alive:
            return
        if self.shield > 0:
            absorb = min(self.shield, dmg)
            self.shield -= absorb
            dmg -= absorb
            fx.spark(self.x, self.y, C_BLUE, 10)
            if self.sound: self.sound.play('shield')
            if dmg <= 0:
                self.invincible = 15
                return
        self.hp -= dmg
        self.invincible = 30
        self.vx *= 0.84; self.vy *= 0.84
        fx.spark(self.x, self.y, C_ORANGE, 8)
        shake.add(5)
        if self.sound: self.sound.play('hurt')
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            fx.explosion(self.x, self.y, 35)
            shake.add(12)

    def apply_drop(self, d):
        t = d.ptype
        if t == 'coin':
            return 'coin'
        if t == 'medkit':
            self.hp = min(self.maxhp, self.hp + DROP_TYPES[t]['heal'])
            return 'medkit'
        if t == 'shield':
            self.shield = min(self.shield_max, self.shield + DROP_TYPES[t]['shield'])
            self.shield_dur = 480
            return 'shield'
        if t == 'weapon':
            opts = ['spread', 'laser']
            if self.weapon_key in opts:
                opts.remove(self.weapon_key)
            self.weapon_key = random.choice(opts)
            self.weapon_timer = WEAPON_UPGRADE_TIME
            return 'weapon'
        return t

    def exp_needed(self, level=None):
        lv = self.level if level is None else level
        if lv >= LEVEL_MAX:
            return 0
        return 3 + lv * 2

    def add_exp(self, amount, fx):
        if self.level >= LEVEL_MAX:
            return
        self.exp += amount
        while self.level < LEVEL_MAX and self.exp >= self.exp_needed(self.level):
            self.exp -= self.exp_needed(self.level)
            self.level += 1
            self._apply_level()
            self.hp = self.maxhp
            self.invincible = max(self.invincible, 60)
            fx.burst(self.x, self.y, C_YELLOW, 30, spd=6, life=40)
            fx.texts.append(FloatText(self.x, self.y - 42,
                                      '坦克升级! Lv.{}'.format(self.level), C_ORANGE, 26))
            if self.sound: self.sound.play('levelup')

    def _apply_level(self):
        bonus = LEVEL_BONUS[self.level]
        self.maxhp = 120 + bonus[0]
        self.max_speed = 5.15 + bonus[1] * 1.35
        self.spd = self.max_speed
        self.accel = 0.39 + (self.level - 1) * 0.018
        self.dmg_mul = bonus[2]
        self.heavy_bonus = bonus[3]
        self.scale = 1.0 + (self.level - 1) * 0.06

    def draw(self, surf, cam_x=0, cam_y=0):
        if not self.alive:
            return
        if self.invincible > 0 and self.invincible % 6 < 3:
            return
        sx, sy = self.x - cam_x, self.y - cam_y
        speed = self.get_speed()
        if speed > 3.0:
            fx_dir, fy_dir = math.cos(self.body_angle), math.sin(self.body_angle)
            for k in (-10, 0, 10):
                px, py = -fy_dir * k, fx_dir * k
                a = min(55, int((speed - 3.0) * 24))
                pygame.draw.line(surf, (90 + a, 170 + a, 215 + min(30, a)),
                                 (int(sx - fx_dir * 24 + px), int(sy - fy_dir * 24 + py)),
                                 (int(sx - fx_dir * (38 + speed * 3) + px),
                                  int(sy - fy_dir * (38 + speed * 3) + py)), 1)
        draw_drop_shadow(surf, sx + self.vx * 0.8, sy + 4 + self.vy * 0.8,
                         int(self.r * self.scale) + 3, alpha=95)
        lc = LEVEL_COLORS[self.level - 1]
        draw_tank(surf, sx, sy, self.body_angle, self.turret_angle,
                  lc['hull'], lc['hull2'], lc['turret'], C_P_TRACK, C_P_TRACK2,
                  lc['barrel'], scale=self.scale, hit_flash=False,
                  muzzle_flash=self.muzzle_flash)
        if self.shield > 0:
            rr = int(self.r * (1.65 + 0.06 * math.sin(pygame.time.get_ticks() * 0.01)))
            s2 = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(s2, (90, 170, 255, 42), (rr, rr), rr - 2)
            pygame.draw.circle(s2, (140, 220, 255, 150), (rr, rr), rr - 2, 2)
            surf.blit(s2, (int(sx) - rr, int(sy) - rr))
        bw = 38; bx = int(sx) - bw // 2; by = int(sy) - 34
        pygame.draw.rect(surf, C_DARK, (bx - 1, by - 1, bw + 2, 6), border_radius=2)
        fill = int(bw * self.hp / self.maxhp)
        hc = C_GREEN if self.hp > self.maxhp * 0.5 else C_YELLOW if self.hp > self.maxhp * 0.25 else C_RED
        if fill > 0:
            pygame.draw.rect(surf, hc, (bx, by, fill, 4), border_radius=2)
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
        # ── 升级新增：避障 / 导弹雨 ──
        self.avoid_timer = 0
        self.avoid_dir = 1
        self.barrage = 0
        self.barrage_ang = 0
        self.barrage_step = 0
    def tick(self, player, shells, fx, shake, bg):
        if not self.alive: return
        self.tick_count += 1
        self.barrage_step += 1
        if self.hit_flash > 0: self.hit_flash -= 1
        if self.atk_cd > 0: self.atk_cd -= 1
        if self.muzzle_flash > 0: self.muzzle_flash -= 1
        if self.bldg_dmg_cd > 0: self.bldg_dmg_cd -= 1
        self.shoot_timer -= 1
        a = angle_to((self.x, self.y), (player.x, player.y))
        diff = a - self.turret_angle
        while diff > math.pi: diff -= math.tau
        while diff < -math.pi: diff += math.tau
        # 炮管平滑瞄准：大角度差快速甩向玩家，小角度差精细对齐
        k = clamp(abs(diff) * 0.30, 0.12, 0.35)
        self.turret_angle += diff * k
        # ── 移动方向决策 ──
        if self.ai == 'chase':
            target_angle = a
            if self.etype != 'boss' and self.hp < self.maxhp * 0.35:
                # AI 升级：血量低时寻找掩体躲避
                cover = self._find_cover(bg, player)
                if cover is not None:
                    cpx, cpy = self._cover_point(cover, player)
                    target_angle = angle_to((self.x, self.y), (cpx, cpy))
                    if dist((self.x, self.y), (cpx, cpy)) < 26:
                        target_angle = a + 0.3   # 到达掩体后小幅游走，保持压制
            mvx, mvy = self._steer(target_angle, bg)
        elif self.ai == 'zigzag':
            pdist = dist((self.x, self.y), (player.x, player.y))
            if pdist < 150:
                # AI 升级：侦察兵近距离直接冲锋
                target_angle = a
                mvx = math.cos(target_angle) * self.spd * 2.0
                mvy = math.sin(target_angle) * self.spd * 2.0
            else:
                self.phase += 0.08
                side = math.sin(self.phase) * 2.5
                perp = a + math.pi/2
                mvx = math.cos(a)*self.spd + math.cos(perp)*side*0.4
                mvy = math.sin(a)*self.spd + math.sin(perp)*side*0.4
                target_angle = math.atan2(mvy, mvx)
        else:
            target_angle = a
            mvx = math.cos(a)*self.spd
            mvy = math.sin(a)*self.spd
        # 车体平滑转向
        diff2 = target_angle - self.body_angle
        while diff2 > math.pi: diff2 -= math.tau
        while diff2 < -math.pi: diff2 += math.tau
        # 车体平滑转向：大角度差快速转向，接近目标平滑微调
        k2 = clamp(abs(diff2) * 0.30, 0.15, 0.4)
        self.body_angle += diff2 * k2
        # ── 移动 + 建筑碰撞 ──
        new_x = self.x + mvx
        new_y = self.y + mvy
        hit, nx, ny, bldg = bg.check_building_collision(new_x, self.y, self.r)
        if hit:
            self.x = nx
            if self.bldg_dmg_cd <= 0:
                self.hp -= 2; self.bldg_dmg_cd = 40
                bldg.take_damage(1, fx)
                fx.spark(nx, self.y, C_ORANGE, 4)
        else:
            self.x = new_x
        hit, nx, ny, bldg = bg.check_building_collision(self.x, new_y, self.r)
        if hit:
            self.y = ny
            if self.bldg_dmg_cd <= 0:
                self.hp -= 2; self.bldg_dmg_cd = 40
                bldg.take_damage(1, fx)
                fx.spark(self.x, ny, C_ORANGE, 4)
        else:
            self.y = new_y
        # 检查撞楼死亡
        if self.hp <= 0:
            self.alive = False
            fx.explosion(self.x, self.y, 20)
        # ── Boss 特殊攻击 ──
        if self.etype == 'boss':
            phase2 = self.hp < self.maxhp * 0.5
            interval = 60 if phase2 else 80   # 狂暴阶段射击更频繁
            if self.tick_count > 0 and self.tick_count % interval == 0:
                n = 5 if phase2 else 3
                for i in range(n):
                    ba = a + (i - (n-1)/2) * 0.15
                    bx = self.x + math.cos(ba) * (self.r + 15)
                    by = self.y + math.sin(ba) * (self.r + 15)
                    shells.append(Shell(bx, by, ba, dmg=self.shell_dmg,
                                        spd=self.shell_spd, friendly=False, heavy=True))
                    self.muzzle_flash = 6
            # 导弹雨：周期触发 8 连发弧形扫射
            if self.tick_count % 420 == 200 and self.barrage <= 0:
                self.barrage = 8
                self.barrage_ang = a - 0.45
            if self.barrage > 0 and self.barrage_step % 4 == 0:
                bx = self.x + math.cos(self.barrage_ang) * (self.r + 15)
                by = self.y + math.sin(self.barrage_ang) * (self.r + 15)
                shells.append(Shell(bx, by, self.barrage_ang, dmg=self.shell_dmg,
                                    spd=self.shell_spd, friendly=False, heavy=True))
                self.barrage_ang += 0.13
                self.barrage -= 1
                self.muzzle_flash = 6
        else:
            # 普通开火
            if self.shoot_timer <= 0:
                self.shoot_timer = self.shoot_interval + random.randint(-10, 10)
                bx = self.x + math.cos(self.turret_angle) * (self.r + 12)
                by = self.y + math.sin(self.turret_angle) * (self.r + 12)
                shells.append(Shell(bx, by, self.turret_angle, dmg=self.shell_dmg,
                                    spd=self.shell_spd, friendly=False))
                self.muzzle_flash = 5
        # 碰撞玩家：普通敌方坦克被撞毁消失，我方掉血；Boss 保留原碰撞伤害（保证 Boss 战玩法）
        if dist((self.x,self.y),(player.x,player.y)) < self.r + player.r:
            if self.etype == 'boss':
                if self.atk_cd <= 0:
                    player.hurt(self.dmg, fx, shake)
                    self.atk_cd = 60
            else:
                # 敌方直接被撞毁：由统一死亡流程处理爆炸/得分/掉落
                self.alive = False
                player.hurt(self.dmg, fx, shake)
    def _steer(self, target_angle, bg):
        """AI 升级：带避障的移动向量。前方被建筑挡住时沿垂直方向绕行"""
        pred_x = self.x + math.cos(target_angle) * (self.r + 12)
        pred_y = self.y + math.sin(target_angle) * (self.r + 12)
        blocked = False
        for b in bg.get_buildings_near(pred_x, pred_y, self.r + 12):
            if not b.destroyed and b.collide_point(pred_x, pred_y, self.r):
                blocked = True
                break
        if blocked and self.avoid_timer <= 0:
            self.avoid_timer = 28
            self.avoid_dir = 1 if random.random() < 0.5 else -1
        if self.avoid_timer > 0:
            self.avoid_timer -= 1
            perp = target_angle + math.pi/2 * self.avoid_dir
            mvx = math.cos(target_angle)*self.spd*0.5 + math.cos(perp)*self.spd
            mvy = math.sin(target_angle)*self.spd*0.5 + math.sin(perp)*self.spd
        else:
            mvx = math.cos(target_angle)*self.spd
            mvy = math.sin(target_angle)*self.spd
        return mvx, mvy
    def _find_cover(self, bg, player):
        """AI 升级：寻找最近的未摧毁建筑作为掩体"""
        best = None; bd = 1e9
        for b in bg.get_buildings_near(self.x, self.y, 280):
            if b.destroyed:
                continue
            d = dist((self.x, self.y), (b.cx, b.cy))
            if d < 280 and d < bd:
                bd = d; best = b
        return best
    def _cover_point(self, b, player):
        """AI 升级：掩体远离玩家的那一侧藏身点"""
        dx = b.cx - player.x
        dy = b.cy - player.y
        dl = math.hypot(dx, dy)
        if dl < 1: dl = 1
        half = max(b.w, b.h) * 0.6 + self.r + 10
        return (b.cx + dx/dl*half, b.cy + dy/dl*half)
    def hurt(self, dmg, fx):
        self.hp -= dmg; self.hit_flash = 6
        fx.damage(self.x, self.y, dmg)
        if self.hp <= 0: self.alive = False
    def draw(self, surf, cam_x=0, cam_y=0):
        if not self.alive: return
        sx, sy = self.x - cam_x, self.y - cam_y
        draw_drop_shadow(surf, sx, sy + 4, self.r + 2, alpha=60)
        draw_tank(surf, sx, sy, self.body_angle, self.turret_angle,
                  self.hull_c, self.hull2_c, self.turret_c,
                  C_E_TRACK, C_E_TRACK2, C_E_BARREL,
                  scale=self.scale, hit_flash=self.hit_flash > 0,
                  muzzle_flash=self.muzzle_flash)
        if self.hp < self.maxhp:
            bw = int(self.r * 2.5); bx = int(sx) - bw//2
            by = int(sy) - self.r - 16
            pygame.draw.rect(surf, C_DARK, (bx-1,by-1,bw+2,5), border_radius=2)
            fill = int(bw * self.hp / self.maxhp)
            hc = C_RED if self.etype == 'boss' else C_GREEN
            if fill > 0: pygame.draw.rect(surf, hc, (bx,by,fill,3), border_radius=2)
        if self.etype == 'boss':
            ft = font(14)
            t = ft.render('重型坦克', True, C_RED)
            surf.blit(t, (int(sx)-t.get_width()//2, int(sy)-self.r-28))
# ═══════════════ 道具掉落 ═══════════════
class Drop:
    """随机掉落道具：金币 / 回血包 / 护盾 / 武器升级"""
    def __init__(self, x, y, ptype):
        self.x, self.y = x, y
        self.ptype = ptype
        self.r = 10
        self.life = 600       # 10 秒后消失
        self.phase = random.uniform(0, math.tau)
        self.taken = False
    def tick(self, player):
        self.life -= 1
        self.phase += 0.08
        if self.life <= 0:
            return False
        d = dist((self.x, self.y), (player.x, player.y))
        # 靠近玩家时自动吸附
        if d < 70 and d > 0.01:
            spd = 4 + (70 - d) * 0.05
            a = angle_to((self.x, self.y), (player.x, player.y))
            self.x += math.cos(a) * spd
            self.y += math.sin(a) * spd
        if d < player.r + 14:
            self.taken = True
            return False
        return True
    def draw(self, surf, cam_x=0, cam_y=0):
        bob = math.sin(self.phase) * 3
        blink = self.life < 120 and (self.life // 8) % 2 == 0
        if blink:
            return
        x, y = int(self.x) - cam_x, int(self.y + bob) - cam_y
        cfg = DROP_TYPES[self.ptype]
        col = cfg['color']
        # 发光底
        g = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(g, (*col[:3], 70), (16, 16), 13)
        surf.blit(g, (x - 16, y - 16))
        if self.ptype == 'coin':
            pygame.draw.circle(surf, C_YELLOW, (x, y), 8)
            pygame.draw.circle(surf, (200, 160, 30), (x, y), 8, 2)
            pygame.draw.line(surf, (150, 120, 20), (x, y - 5), (x, y + 5), 2)
            ft = font(10)
            s = ft.render('$', True, (120, 90, 0))
            surf.blit(s, (x - 3, y - 6))
        elif self.ptype == 'medkit':
            pygame.draw.rect(surf, C_WHITE, (x - 8, y - 6, 16, 12), border_radius=2)
            pygame.draw.rect(surf, (180, 180, 180), (x - 8, y - 6, 16, 12), 1, border_radius=2)
            pygame.draw.rect(surf, C_RED, (x - 2, y - 4, 4, 8))
            pygame.draw.rect(surf, C_RED, (x - 6, y, 12, 4))
        elif self.ptype == 'shield':
            pygame.draw.circle(surf, C_BLUE, (x, y), 9, 3)
            pygame.draw.circle(surf, (120, 200, 255), (x, y), 9, 1)
            ft = font(10)
            s = ft.render('盾', True, C_BLUE)
            surf.blit(s, (x - 5, y - 8))
        elif self.ptype == 'weapon':
            star = [(x, y-9), (x+7, y-3), (x+4, y), (x+9, y+5), (x+2, y+3),
                    (x, y+9), (x-2, y+3), (x-9, y+5), (x-4, y), (x-7, y-3)]
            pygame.draw.polygon(surf, C_ORANGE, star)
            ft = font(10)
            s = ft.render('W', True, (255, 255, 255))
            surf.blit(s, (x - 4, y - 7))
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
def draw_hud(surf, player, wave, score, enemy_count, enemies=()):
    for i in range(HUD_H):
        col = (12 + i // 3, 17 + i // 3, 29 + i // 2)
        pygame.draw.line(surf, col, (0, i), (W, i))
    pygame.draw.line(surf, (71, 91, 120), (0, HUD_H - 1), (W, HUD_H - 1), 2)
    f = font(16); fb = font(20)
    surf.blit(f.render('装甲', True, C_WHITE), (10, 15))
    bw, bx = 142, 50
    pygame.draw.rect(surf, C_DARK, (bx - 1, 14, bw + 2, 20), border_radius=5)
    fill = int(bw * player.hp / player.maxhp)
    hc = C_GREEN if player.hp > player.maxhp * 0.5 else C_YELLOW if player.hp > player.maxhp * 0.25 else C_RED
    if fill > 0: pygame.draw.rect(surf, hc, (bx, 15, fill, 18), border_radius=4)
    surf.blit(f.render('{}/{}'.format(player.hp, player.maxhp), True, C_WHITE), (bx + bw + 7, 15))
    if player.shield > 0:
        pygame.draw.rect(surf, C_DARK, (bx, 37, bw, 7), border_radius=3)
        sfill = int(bw * player.shield / player.shield_max)
        if sfill > 0: pygame.draw.rect(surf, C_BLUE, (bx, 37, sfill, 7), border_radius=3)
    lvcol = C_YELLOW if player.level >= LEVEL_MAX else C_WHITE
    surf.blit(f.render('Lv.{}'.format(player.level), True, lvcol), (270, 8))
    need = player.exp_needed()
    if need > 0:
        exx, exw = 270, 80
        pygame.draw.rect(surf, C_DARK, (exx, 31, exw, 7), border_radius=3)
        efill = int(exw * min(1.0, player.exp / need))
        if efill > 0: pygame.draw.rect(surf, C_ORANGE, (exx, 31, efill, 7), border_radius=3)
    speed = player.get_speed()
    sc = C_BLUE if not player.drifting else C_ORANGE
    surf.blit(f.render('速度 {:.1f}'.format(speed), True, sc), (360, 8))
    if player.drifting:
        surf.blit(f.render('DRIFT', True, C_ORANGE), (360, 31))
    else:
        surf.blit(f.render('Shift 漂移', True, C_GRAY), (360, 31))
    wp = WEAPONS[player.weapon_key]
    wcol = C_ORANGE if player.weapon_key != 'single' else C_GRAY
    surf.blit(f.render('武器 {}'.format(wp['name']), True, wcol), (620, 8))
    if player.weapon_timer > 0:
        surf.blit(f.render('{}s'.format(player.weapon_timer // 60 + 1), True, wcol), (750, 8))
    shell_ready = player.shell_cd <= 0
    st = '重炮就绪' if shell_ready else '重炮 {}s'.format(player.shell_cd // 60 + 1)
    surf.blit(f.render(st, True, C_GREEN if shell_ready else C_GRAY), (620, 32))
    surf.blit(fb.render('第 {} 波'.format(wave), True, C_BLUE), (W // 2 - 38, 14))
    surf.blit(f.render('击毁 {}'.format(score), True, C_YELLOW), (832, 8))
    surf.blit(f.render('剩余 {}'.format(enemy_count), True, C_RED), (832, 31))
    if player.bldg_dmg_cd > 0:
        warn_ft = font(14)
        warn = warn_ft.render('⚠ 撞击建筑', True, C_ORANGE)
        surf.blit(warn, (W // 2 - warn.get_width() // 2, HUD_H + 4))
    for e in enemies:
        if e.etype == 'boss' and e.alive:
            bbw = 420; bbx = W // 2 - bbw // 2; bby = 64
            pygame.draw.rect(surf, C_DARK, (bbx - 2, bby - 2, bbw + 4, 16), border_radius=5)
            bfill = int(bbw * e.hp / e.maxhp)
            pygame.draw.rect(surf, C_RED, (bbx, bby, bfill, 12), border_radius=4)
            pygame.draw.rect(surf, (255, 190, 190), (bbx, bby, bfill, 12), 1, border_radius=4)
            bf = font(14)
            surf.blit(bf.render('BOSS 重型坦克  {}/{}'.format(e.hp, e.maxhp), True, C_WHITE), (bbx, bby - 16))
            break

def draw_menu(surf, bg):
    bg.draw(surf)
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((3, 7, 18, 152))
    surf.blit(overlay, (0, 0))
    panel = pygame.Surface((690, 220), pygame.SRCALPHA)
    pygame.draw.rect(panel, (7, 13, 27, 190), (0, 0, 690, 220), border_radius=18)
    pygame.draw.rect(panel, (77, 211, 255, 105), (0, 0, 690, 220), 2, border_radius=18)
    pygame.draw.line(panel, (255, 91, 151, 150), (34, 12), (656, 12), 2)
    surf.blit(panel, (W // 2 - 345, H // 2 - 128))
    ft = font(48); ft2 = font(20); fs = font(18)
    title_sh = ft.render('坦克大战', True, (0, 0, 0))
    surf.blit(title_sh, (W // 2 - title_sh.get_width() // 2 + 3, H // 2 - 113))
    title = ft.render('坦克大战', True, C_YELLOW)
    surf.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 116))
    mark = ft2.render('N E O N   D R I F T', True, (86, 220, 255))
    surf.blit(mark, (W // 2 - mark.get_width() // 2, H // 2 - 55))
    sub = fs.render('WASD 驾驶  |  鼠标瞄准  |  左键机枪  |  空格重炮', True, C_GRAY)
    surf.blit(sub, (W // 2 - sub.get_width() // 2, H // 2 - 20))
    tip = fs.render('按住 Shift 手刹漂移，松开自动抓地回正', True, C_ORANGE)
    surf.blit(tip, (W // 2 - tip.get_width() // 2, H // 2 + 10))
    tip2 = fs.render('雨夜霓虹城市 · 无限地图 · 道具升级 · Boss 战', True, C_GREEN)
    surf.blit(tip2, (W // 2 - tip2.get_width() // 2, H // 2 + 37))
    blink = abs(math.sin(pygame.time.get_ticks() * 0.003))
    start = fs.render('— 点击任意处开始 —', True, lerp_color(C_GRAY, C_WHITE, blink))
    surf.blit(start, (W // 2 - start.get_width() // 2, H // 2 + 72))
    draw_vignette(surf)
    pygame.display.flip()

def draw_gameover(surf, score, wave):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0,0,0,170)); surf.blit(overlay, (0,0))
    ft = font(48); fs = font(24)
    t1 = ft.render('坦克被击毁', True, C_RED)
    t2 = fs.render('击毁积分: {}'.format(score), True, C_YELLOW)
    t3 = fs.render('存活到第 {} 波'.format(wave), True, C_WHITE)
    t4 = fs.render('按 R 重新出击 | ESC 退出', True, C_GRAY)
    surf.blit(t1, (W//2-t1.get_width()//2, H//2-80))
    surf.blit(t2, (W//2-t2.get_width()//2, H//2-20))
    surf.blit(t3, (W//2-t3.get_width()//2, H//2+15))
    surf.blit(t4, (W//2-t4.get_width()//2, H//2+60))
def draw_pause(surf):
    """暂停菜单"""
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0,0,0,150))
    surf.blit(overlay, (0,0))
    ft = font(48); fs = font(22)
    t = ft.render('已暂停', True, C_WHITE)
    surf.blit(t, (W//2-t.get_width()//2, H//2-90))
    for i, (k, txt) in enumerate([('ESC', '继续游戏'), ('R', '重新开始'), ('Q', '退出游戏')]):
        c = C_WHITE if i == 0 else C_GRAY
        s = fs.render('[{}] {}'.format(k, txt), True, c)
        surf.blit(s, (W//2-s.get_width()//2, H//2-20+i*36))
# ═══════════════ 波次管理 ═══════════════
def spawn_wave(wave, bg, px, py):
    """在玩家视野边缘外随机生成敌人（无尽世界坐标）"""
    enemies = []
    n_scout = 2 + wave
    n_medium = max(0, wave - 2) * 2
    n_heavy = max(0, wave - 4)
    has_boss = wave % 5 == 0 and wave > 0
    cfgs = [('scout', n_scout), ('medium', n_medium), ('heavy', n_heavy)]
    if has_boss: cfgs += [('boss', 1)]
    for etype, count in cfgs:
        for _ in range(count):
            # 尝试多次找到不撞建筑且不贴脸的出生点
            for attempt in range(40):
                side = random.randint(0, 3)
                if side == 0:
                    ex = px + random.randint(-W//2 - 60, W//2 + 60)
                    ey = py - H//2 - random.randint(40, 160)
                elif side == 1:
                    ex = px + random.randint(-W//2 - 60, W//2 + 60)
                    ey = py + H//2 + random.randint(40, 160)
                elif side == 2:
                    ex = px - W//2 - random.randint(40, 160)
                    ey = py + random.randint(-H//2 - 60, H//2 + 60)
                else:
                    ex = px + W//2 + random.randint(40, 160)
                    ey = py + random.randint(-H//2 - 60, H//2 + 60)
                if dist((ex, ey), (px, py)) < 200:
                    continue
                if bg.point_in_building(ex, ey, 25):
                    continue
                enemies.append(EnemyTank(etype, ex, ey))
                break
    return enemies
# ═══════════════ 主游戏 ═══════════════
class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption('坦克大战 · 霓虹漂移版')
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'menu'
        self.bg = CityBackground()
        self.sound = SoundManager()
        self.light_overlay = self._make_lighting()
        self.reset()
        self.sound.start_music()
    def _make_lighting(self):
        """预渲染霓虹夜色：冷色天光 + 左上柔光，避免每帧计算。"""
        light = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(H):
            t = y / H
            pygame.draw.line(light, (30, 62, 112, int(8 + 13 * t)), (0, y), (W, y))
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(210, 0, -5):
            a = int(9 * (i / 210))
            if a > 0:
                pygame.draw.circle(glow, (92, 194, 255, a), (60, 35), i)
        for i in range(150, 0, -4):
            a = int(7 * (i / 150))
            if a > 0:
                pygame.draw.circle(glow, (255, 104, 180, a), (W - 40, H - 30), i)
        light.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        return light
    def reset(self):
        self.player = Player()
        self.player.sound = self.sound
        # 确保玩家不在建筑内
        hit, nx, ny, b = self.bg.check_building_collision(
            self.player.x, self.player.y, self.player.r)
        if hit:
            self.player.x, self.player.y = nx, ny
        self.cam_x = self.player.x - W / 2
        self.cam_y = self.player.y - H / 2
        self.enemies = []
        self.shells = []
        self.drops = []
        self.fx = Particles()
        self.shake = ScreenShake()
        self.wave = 0; self.score = 0; self.wave_timer = 0
        self.next_wave()
    def next_wave(self):
        self.wave += 1
        self.enemies = spawn_wave(self.wave, self.bg, self.player.x, self.player.y)
        self.wave_timer = 120
        # Boss 波：警报音 + 震动
        if any(e.etype == 'boss' for e in self.enemies):
            self.sound.play('boss')
            self.shake.add(8)
    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False; return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == 'play': self.state = 'pause'
                    elif self.state == 'pause': self.state = 'play'
                    else: self.running = False
                    continue
                if event.key == pygame.K_r and self.state in ('over', 'pause'):
                    self.reset(); self.state = 'play'
                if event.key == pygame.K_q and self.state == 'pause':
                    self.running = False
                if event.key == pygame.K_SPACE and self.state == 'play':
                    self.player.heavy_shell(self.shells, self.fx, self.shake)
                    self.sound.play('heavy')
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == 'menu':
                    self.state = 'play'
                    self.sound.play('pickup')
        if self.state == 'play':
            keys = pygame.key.get_pressed()
            self.player.tick(keys, mouse_pos, self.shells, self.enemies,
                             self.fx, self.shake, self.bg)
            if mouse_down:
                self.player.shoot(self.shells)
                if self.player.muzzle_flash > 0:
                    self.sound.play('shoot')
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
            for b in self.bg.get_buildings_near(s.x, s.y, s.r):
                if not b.destroyed and b.collide_point(s.x, s.y, s.r):
                    b.take_damage(s.dmg, self.fx)
                    self.fx.spark(s.x, s.y, C_GRAY, 8)
                    self.fx.smoke(s.x, s.y, 4)
                    self.shake.add(2)
                    if s.heavy:
                        self.fx.explosion(s.x, s.y, 12)
                        self.fx.debris(s.x, s.y, b.style['wall'], 8)
                        self.shake.add(4)
                        self.sound.play('explode')
                    else:
                        self.sound.play('hit')
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
                        self.fx.smoke(s.x, s.y, 3)
                        self.shake.add(3)
                        self.sound.play('hit')
                        if s.heavy:
                            self.fx.explosion(s.x, s.y, 15)
                            self.fx.debris(s.x, s.y, e.hull_c, 10)
                            self.shake.add(5)
                        if s in self.shells: self.shells.remove(s)
                        break
            else:
                if self.player.alive and dist((s.x,s.y),(self.player.x,self.player.y)) < s.r + self.player.r:
                    self.player.hurt(s.dmg, self.fx, self.shake)
                    if s.heavy:
                        self.fx.explosion(s.x, s.y, 12)
                        self.sound.play('explode')
                    else:
                        self.sound.play('hit')
                    if s in self.shells: self.shells.remove(s)
        # 敌人死亡：计分 + 爆炸特效 + 道具掉落
        for e in list(self.enemies):
            if not e.alive:
                self.score += e.score_val
                # 击杀经验：经验满自动升级坦克
                self.player.add_exp(e.score_val // 100, self.fx)
                self.fx.explosion(e.x, e.y, 30)
                self.fx.smoke(e.x, e.y, 12)
                self.fx.debris(e.x, e.y, e.hull_c, 14)
                self.shake.add(6)
                self.sound.play('explode')
                if e.etype == 'boss':
                    self.sound.play('win')
                    self.drops.append(Drop(e.x, e.y, 'weapon'))
                    self.drops.append(Drop(e.x + 24, e.y + 10, 'medkit'))
                elif random.random() < DROP_RATE:
                    k = random.choices(list(DROP_TYPES.keys()), weights=[40, 22, 18, 20])[0]
                    self.drops.append(Drop(e.x, e.y, k))
                if random.random() < 0.2:
                    heal = 15
                    self.player.hp = min(self.player.maxhp, self.player.hp + heal)
                    self.fx.heal(self.player.x, self.player.y, heal)
        self.enemies = [e for e in self.enemies if e.alive]
        # 道具拾取
        for d in list(self.drops):
            if not d.tick(self.player):
                if d.taken:
                    r = self.player.apply_drop(d)
                    if r == 'coin':
                        self.sound.play('coin')
                        self.score += DROP_TYPES['coin']['score']
                    elif r == 'shield':
                        self.sound.play('shield')
                    else:
                        self.sound.play('pickup')
                    self.fx.burst(d.x, d.y, DROP_TYPES[d.ptype]['color'], 14)
                self.drops.remove(d)
        self.fx.tick()
        if len(self.enemies) == 0 and self.wave_timer <= 0: self.next_wave()
        if not self.player.alive:
            self.state = 'over'
            self.sound.play('gameover')
    def draw(self):
        if self.state == 'menu':
            draw_menu(self.screen, self.bg)
            return
        ox, oy = self.shake.get()
        look = min(32.0, self.player.get_speed() * 5.2)
        target_x = self.player.x + self.player.vx * look / max(1.0, self.player.get_speed()) - W / 2
        target_y = self.player.y + self.player.vy * look / max(1.0, self.player.get_speed()) - H / 2
        self.cam_x += (target_x - self.cam_x) * 0.115
        self.cam_y += (target_y - self.cam_y) * 0.115
        cam_x, cam_y = int(self.cam_x), int(self.cam_y)
        render = pygame.Surface((W, H))
        self.bg.draw(render, cam_x, cam_y)
        self.player.draw_marks(render, cam_x, cam_y)
        for d in self.drops: d.draw(render, cam_x, cam_y)
        for e in self.enemies: e.draw(render, cam_x, cam_y)
        self.player.draw(render, cam_x, cam_y)
        for s in self.shells: s.draw(render, cam_x, cam_y)
        self.fx.draw(render, cam_x, cam_y)
        draw_vignette(render)
        render.blit(self.light_overlay, (0, 0))
        draw_hud(render, self.player, self.wave, self.score, len(self.enemies), self.enemies)
        if self.wave_timer > 60:
            ft = font(36)
            t = ft.render('— 第 {} 波 —'.format(self.wave), True, C_YELLOW)
            t.set_alpha(int(255*(self.wave_timer-60)/60))
            render.blit(t, (W//2-t.get_width()//2, H//2-50))
        if self.state == 'over':
            draw_gameover(render, self.score, self.wave)
        if self.state == 'pause':
            draw_pause(render)
        self.screen.blit(render, (ox, oy))
        pygame.display.flip()
    def run(self):
        while self.running:
            self.handle_events(); self.update(); self.draw()
            self.clock.tick(FPS)
        pygame.quit(); sys.exit()
if __name__ == '__main__':
    Game().run()

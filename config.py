
WIDTH = 900
HEIGHT = 1000
FPS = 60

ROWS = 6
COLS = 6
CELL = 110

# 动态视口：main 依据窗口尺寸调用 set_view() 重算布局，
# 游戏内容自适应铺满窗口（不留黑边）；窗口小于最小尺寸时整体等比缩小
VIEW_W = WIDTH
VIEW_H = HEIGHT
MIN_VIEW_W = 720
MIN_VIEW_H = 900
GRID_OFFSET_X = 0
GRID_OFFSET_Y = 0


def set_view(width, height):
    """按窗口尺寸重算布局：棋盘水平居中，垂直避开顶部 HUD 与底部提示。"""
    global VIEW_W, VIEW_H, GRID_OFFSET_X, GRID_OFFSET_Y
    VIEW_W = max(MIN_VIEW_W, width)
    VIEW_H = max(MIN_VIEW_H, height)
    GRID_OFFSET_X = (VIEW_W - COLS * CELL) // 2
    top_space, bottom_space = 160, 70
    free = VIEW_H - top_space - bottom_space - ROWS * CELL
    GRID_OFFSET_Y = top_space + max(0, free // 2)


set_view(WIDTH, HEIGHT)

# 剑意值：被剑阵反噬（误点 / 飞剑受阻）的容错次数
MAX_MISTAKE = 3

# ---------------- 东方仙侠配色（青蓝白雾 · 玉绿金边 · 粉瓣灵光）----------------

# 夜空云海渐变
NIGHT_TOP = (38, 58, 98)
NIGHT_BOTTOM = (10, 20, 42)
CLOUD = (214, 228, 244)
MOON = (246, 240, 214)

# 剑气青蓝
CYAN = (120, 214, 255)
CYAN_LIGHT = (206, 244, 255)
CYAN_DARK = (46, 110, 150)
CYAN_GLOW = (140, 232, 255)

# 灵玉
JADE = (92, 200, 172)
JADE_LIGHT = (160, 230, 208)
JADE_DARK = (34, 96, 84)

# 金边符文
GOLD = (240, 208, 120)
GOLD_LIGHT = (255, 240, 190)
GOLD_DARK = (158, 120, 52)
GOLD_GLOW = (255, 222, 140)

# 花瓣灵光
PETAL = (255, 168, 198)
PETAL_LIGHT = (255, 206, 224)

# 玉石阵台
STONE = (30, 52, 72)
STONE_EDGE = (96, 150, 164)
STONE_HIGHLIGHT = (58, 90, 110)
BOARD_FRAME = (20, 38, 56)

WARNING = (232, 86, 86)
SUCCESS = JADE

# ---------------- 九重仙境关卡 ----------------
# swords: 飞剑 (行, 列, 朝向) —— 全程直线飞行
# eyes:   阵眼 (行, 列) —— 飞剑经行即解除
LEVELS = [
    {
        "name": "第一重天 · 云海入口",
        "swords": [
            (2, 2, "up"),
            (3, 3, "left"),
            (1, 4, "down"),
            (4, 1, "right"),
        ],
        "eyes": [(0, 2), (3, 0), (5, 4), (4, 5)],
        "rotators": [],
    },
    {
        "name": "第二重天 · 青竹剑林",
        "swords": [
            (0, 0, "right"), (0, 5, "down"),
            (1, 2, "up"),    (1, 3, "down"),
            (4, 2, "left"),  (4, 3, "right"),
        ],
        "eyes": [(0, 1), (0, 2), (5, 5), (4, 0), (5, 3)],
        "rotators": [],
    },
    {
        "name": "第三重天 · 古仙遗阵",
        "swords": [
            (0, 0, "right"), (4, 0, "down"), (0, 4, "up"), (3, 0, "down"),
            (3, 1, "up"),    (2, 3, "right"), (4, 3, "down"), (3, 2, "down"),
        ],
        "eyes": [(0, 1), (2, 5), (5, 0), (5, 2), (5, 3), (0, 3)],
        "rotators": [],
    },
    {
        "name": "第四重天 · 天池剑台",
        "swords": [
            (3, 1, "right"),
            (1, 4, "down"),
            (2, 1, "up"),
            (5, 5, "left"),
        ],
        "eyes": [(5, 3), (4, 4), (0, 1), (5, 0)],
    },
    {
        "name": "第五重天 · 忘川剑域",
        "swords": [
            (2, 0, "right"),
            (0, 4, "down"),
            (5, 5, "up"),
            (1, 1, "down"),
            (3, 5, "left"),
            (0, 2, "down"),
        ],
        "eyes": [(5, 2), (3, 3), (0, 5), (5, 1), (3, 0), (2, 1)],
    },
    {
        "name": "第六重天 · 万剑峡谷",
        "swords": [
            (5, 3, "left"), (4, 3, "right"), (2, 2, "right"), (1, 5, "down"),
            (1, 1, "down"), (2, 3, "right"), (4, 0, "down"),  (1, 2, "right"),
            (0, 5, "left"), (2, 4, "down"),  (5, 0, "left"),  (3, 5, "right"),
            (0, 4, "down"), (0, 0, "up"),
        ],
        "eyes": [(5, 1), (4, 5), (2, 5), (0, 3), (5, 4),
                 (0, 1), (4, 1), (1, 4), (0, 2), (3, 4)],
    },
    {
        "name": "第七重天 · 仙门秘境",
        "swords": [
            (0, 0, "down"), (5, 5, "down"), (1, 5, "up"),  (1, 0, "right"),
            (5, 1, "down"), (0, 3, "right"), (1, 1, "down"), (2, 5, "down"),
            (5, 2, "up"),   (0, 1, "up"),   (3, 2, "up"),  (4, 4, "right"),
            (0, 2, "right"), (5, 4, "up"),  (2, 3, "up"),  (4, 5, "down"),
        ],
        "eyes": [(3, 0), (1, 2), (0, 4), (4, 0), (3, 1),
                 (1, 3), (4, 2), (3, 5), (2, 0), (2, 2)],
    },
    {
        "name": "第八重天 · 天穹剑塔",
        "swords": [
            (1, 5, "left"), (1, 1, "down"), (2, 4, "down"), (2, 3, "down"),
            (3, 4, "right"), (5, 1, "down"), (4, 2, "down"), (4, 5, "up"),
            (1, 0, "left"), (5, 5, "right"), (3, 3, "right"), (4, 0, "up"),
            (5, 3, "right"), (4, 3, "right"), (2, 0, "left"), (3, 1, "down"),
            (3, 2, "right"), (0, 5, "up"),
        ],
        "eyes": [(1, 2), (5, 4), (0, 0), (3, 5), (2, 1),
                 (4, 1), (1, 3), (3, 0), (5, 2), (4, 4), (1, 4)],
    },
    {
        "name": "第九重天 · 失落剑谱",
        "swords": [
            (1, 5, "left"), (1, 1, "down"), (2, 4, "down"), (2, 3, "down"),
            (3, 4, "right"), (5, 1, "down"), (4, 2, "down"), (4, 5, "up"),
            (1, 0, "left"), (5, 5, "right"), (3, 3, "right"), (5, 0, "up"),
            (5, 3, "right"), (4, 3, "right"), (2, 0, "left"), (3, 1, "down"),
            (3, 2, "right"), (0, 5, "up"), (0, 3, "down"),
        ],
        "eyes": [(4, 0), (1, 2), (5, 4), (3, 5), (2, 1),
                 (0, 0), (3, 0), (5, 2), (4, 4), (1, 3)],
    },
]

TOTAL_LEVELS = len(LEVELS)

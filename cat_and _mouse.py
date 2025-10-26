import pygame
import random
import time
import math
import os

# 初始化游戏
pygame.init()

# Background music: try to initialize mixer and play a bundled music file if present.
music_playing = False
try:
    # initialize mixer (may raise if audio device unavailable)
    pygame.mixer.init()
    # look for common background music filenames in the game folder
    music_file = None
    # If you have a specific file elsewhere, add its full path here.
    candidates = [
        "bgm.ogg",
        "bgm.mp3",
        "background.ogg",
        "background.mp3",
        # user-specified absolute path (Windows) — included because you provided it
        "C:\\Users\\74111\\Downloads\\Scott_Bradley_-_Tom_Jerry_-_Busy_Buddies_(mp3.pm).mp3",
    ]
    for _name in candidates:
        if os.path.exists(_name):
            music_file = _name
            break
    if music_file:
        try:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)  # loop indefinitely
            music_playing = True
        except Exception as e:
            print("Failed to load/play background music:", e)
            music_playing = False
    else:
        # no music file found; skip silently
        music_playing = False
except Exception as e:
    # mixer not available
    print("Pygame mixer init failed:", e)
    music_playing = False

# 游戏设置
WIDTH, HEIGHT = 600, 600
GRID_SIZE = 3  # 3x3 网格
CELL_SIZE = WIDTH // GRID_SIZE
FPS = 30

# 颜色（像素风格配色）
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)  # 正常地面颜色
DARK_BROWN = (80, 40, 10)  # 未击中的暗格子颜色
BEIGE = (245, 245, 220)  # 地鼠颜色
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)  # 烟花颜色
PINK = (255, 192, 203)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# 创建窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("像素打地鼠")
clock = pygame.time.Clock()

# 地鼠类
class Mole:
    def __init__(self):
        self.grid = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # 地鼠是否出现
        self.disabled = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # 格子是否禁用（未击中）
        self.score = 0
        self.time_left = 30  # 30秒游戏时间
        self.last_spawn = time.time()
        # 初始地鼠出现间隔（秒）
        self.spawn_delay = 1.0  # 改为1秒初始间隔
        # 地鼠显示持续时间（秒）
        self.appearance_duration = 1.0  # 初始显示1秒
        # per-cell spawn timestamps (None when no mole present)
        self.spawn_times = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.fireworks = []  # 存储烟花效果：(x, y, 时间)
        # 连续命中计数与加速配置
        self.consecutive_hits = 0
        self.hits_to_accelerate = 5
        self.acceleration_step = 0.1  # 每次加速减少的秒数
        self.min_appearance_duration = 0.3  # 最小显示时间
        self.combo_fireworks = []  # 专门存储连击烟花的列表

    def spawn_mole(self):
        # 只在未禁用的格子随机生成地鼠
        if time.time() - self.last_spawn > self.spawn_delay:
            available = []
            for x in range(GRID_SIZE):
                for y in range(GRID_SIZE):
                    if not self.disabled[x][y] and not self.grid[x][y]:
                        available.append((x, y))
            if available:
                x, y = random.choice(available)
                self.grid[x][y] = True
                self.last_spawn = time.time()
                self.spawn_times[x][y] = self.last_spawn

    def hit(self, x, y):
        # 击打地鼠逻辑
        if self.disabled[x][y]:
            return False  # 禁用格子无法操作
        
        if self.grid[x][y]:
            # 击中：加分+烟花效果
            self.score += 10
            self.grid[x][y] = False
            # 添加普通击中烟花（位置+当前时间）
            self.fireworks.append((x, y, time.time()))
            # 更新连续命中计数并可能触发加速
            self.consecutive_hits += 1
            
            # 检查是否达到5次连击
            if self.consecutive_hits >= self.hits_to_accelerate:
                # 减少地鼠显示时间（加速），但不低于最小值
                self.appearance_duration = max(self.min_appearance_duration, self.appearance_duration - self.acceleration_step)
                # 添加连击烟花效果（在屏幕中央）
                self.combo_fireworks.append((WIDTH // 2, HEIGHT // 2, time.time(), "WELL DONE!"))
                # 重置连续计数
                self.consecutive_hits = 0
                print(f"加速！地鼠显示时间减少到: {self.appearance_duration:.1f}秒")  # 调试信息
            return True
        else:
            # 未击中：格子变暗并禁用
            self.disabled[x][y] = True
            # 失误/未击中会打断连击
            self.consecutive_hits = 0
            return False

    def update(self):
        """Update mole game state: spawn new moles and clean up expired fireworks."""
        # 尝试生成新地鼠
        self.spawn_mole()

        # 根据 appearance_duration 移除过期的地鼠（视为逃跑，打断连击）
        current_time = time.time()
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                if self.grid[x][y] and self.spawn_times[x][y] is not None:
                    if current_time - self.spawn_times[x][y] > self.appearance_duration:
                        # 地鼠时间到，消失并禁用格子
                        self.grid[x][y] = False
                        self.disabled[x][y] = True
                        self.spawn_times[x][y] = None
                        # 逃跑中断连击
                        self.consecutive_hits = 0

        # 移除过期烟花（1秒后消失）
        current_time = time.time()
        self.fireworks = [f for f in self.fireworks if current_time - f[2] < 1.0]
        # 移除过期连击烟花（2秒后消失，让文字显示更久）
        self.combo_fireworks = [f for f in self.combo_fireworks if current_time - f[2] < 2.0]

# 绘制连击计数器和速度显示
def draw_ui(mole_game):
    font = pygame.font.SysFont("Arial", 20)
    
    # 连击计数器
    combo_text = font.render(f"Combo: {mole_game.consecutive_hits}/{mole_game.hits_to_accelerate}", True, WHITE)
    screen.blit(combo_text, (10, 10))
    
    # 连击进度条
    progress_width = 100
    progress_height = 10
    progress = min(1.0, mole_game.consecutive_hits / mole_game.hits_to_accelerate)
    pygame.draw.rect(screen, (50, 50, 50), (10, 35, progress_width, progress_height))
    pygame.draw.rect(screen, GREEN, (10, 35, int(progress_width * progress), progress_height))
    
    # 当前地鼠显示时间
    speed_text = font.render(f"Speed: {mole_game.appearance_duration:.1f}s", True, WHITE)
    screen.blit(speed_text, (10, 55))
    
    # 加速指示器（当连击接近满时显示提示）
    if mole_game.consecutive_hits >= mole_game.hits_to_accelerate - 1:
        alert_font = pygame.font.SysFont("Arial", 16, bold=True)
        alert_text = alert_font.render("COMBO READY!", True, YELLOW)
        screen.blit(alert_text, (10, 80))

# 绘制像素风格地鼠
def draw_pixel_mole(x, y):
    # 鼠身体（圆形）
    mole_size = CELL_SIZE // 2
    mole_x = x * CELL_SIZE + CELL_SIZE // 4
    mole_y = y * CELL_SIZE + CELL_SIZE // 4
    pygame.draw.ellipse(screen, BEIGE, (mole_x, mole_y, mole_size, mole_size))
    # 鼠耳朵（两个小圆）
    ear_radius = mole_size // 5
    pygame.draw.circle(screen, BEIGE, (mole_x + ear_radius, mole_y + ear_radius), ear_radius)
    pygame.draw.circle(screen, BEIGE, (mole_x + mole_size - ear_radius, mole_y + ear_radius), ear_radius)
    # 鼠眼睛
    pygame.draw.rect(screen, BLACK, (mole_x + mole_size//4, mole_y + mole_size//3, 3, 3))
    pygame.draw.rect(screen, BLACK, (mole_x + mole_size*3//4 - 3, mole_y + mole_size//3, 3, 3))
    # 鼻子（小粉色圆）
    nose_x = mole_x + mole_size//2
    nose_y = mole_y + mole_size*3//4
    pygame.draw.circle(screen, (255, 150, 150), (nose_x, nose_y), 3)
    # 胡须（左右三根线）
    for i in range(-1, 2):
        pygame.draw.line(screen, BLACK, (nose_x-5, nose_y+i*2), (nose_x-15, nose_y+i*2), 1)
        pygame.draw.line(screen, BLACK, (nose_x+5, nose_y+i*2), (nose_x+15, nose_y+i*2), 1)

# 绘制锤子（带细节和旋转动画）
def draw_hammer(pos, hit_animation):
    SCALE = 2.5
    def IS(v):
        return int(v)
    hx, hy = pos
    angle = 0  # 默认角度
    rad = math.radians(angle)
    # 计算旋转后的猫头中心
    head_center_x = hx
    head_center_y = IS(hy - 8 * SCALE)
    dx = head_center_x - hx
    dy = head_center_y - hy
    rotated_cx = hx + dx * math.cos(rad) - dy * math.sin(rad)
    rotated_cy = hy + dx * math.sin(rad) + dy * math.cos(rad)
    head_x = int(rotated_cx)
    head_y = int(rotated_cy)
    head_radius = IS(24 * SCALE)  # 更大的猫头
    ear_w = IS(18 * SCALE)        # 更大的耳朵以适应比例
    ear_h = IS(26 * SCALE)
    # 主体（圆形猫头）
    DARK_GREY = (30, 30, 30)
    pygame.draw.ellipse(screen, DARK_GREY, (head_x - head_radius, head_y - head_radius, head_radius * 2, head_radius * 2))

    # 耳朵内侧（修正变量定义和点）
    # 左耳朵内侧
    pygame.draw.polygon(screen, PINK, [
        (head_x - IS(8 * SCALE), head_y - head_radius),
        (head_x - IS(8 * SCALE) - ear_w // 4, head_y - head_radius - ear_h // 2),
        (head_x - IS(8 * SCALE) + ear_w // 4, head_y - head_radius - ear_h // 2)
    ])
    # 右耳朵内侧
    pygame.draw.polygon(screen, PINK, [
        (head_x + IS(8 * SCALE), head_y - head_radius),
        (head_x + IS(8 * SCALE) - ear_w // 4, head_y - head_radius - ear_h // 2),
        (head_x + IS(8 * SCALE) + ear_w // 4, head_y - head_radius - ear_h // 2)
    ])
    # 左耳朵（外侧和内侧，三角形：顶点窄，底部宽）
    left_ear_top = (head_x - IS(8 * SCALE), head_y - head_radius - ear_h)
    left_ear_left = (head_x - IS(8 * SCALE) - ear_w // 2, head_y - head_radius)
    left_ear_right = (head_x - IS(8 * SCALE) + ear_w // 2, head_y - head_radius)
    pygame.draw.polygon(screen, DARK_GREY, [left_ear_top, left_ear_left, left_ear_right])
    # 左耳朵内侧
    pygame.draw.polygon(screen, PINK, [
        left_ear_top,
        (head_x - IS(8 * SCALE) - ear_w // 4, head_y - head_radius - ear_h // 2),
        (head_x - IS(8 * SCALE) + ear_w // 4, head_y - head_radius - ear_h // 2)
    ])
    # 右耳朵（外侧和内侧，三角形：顶点窄，底部宽）
    right_ear_top = (head_x + IS(8 * SCALE), head_y - head_radius - ear_h)
    right_ear_left = (head_x + IS(8 * SCALE) - ear_w // 2, head_y - head_radius)
    right_ear_right = (head_x + IS(8 * SCALE) + ear_w // 2, head_y - head_radius)
    pygame.draw.polygon(screen, DARK_GREY, [right_ear_top, right_ear_left, right_ear_right])
    # 右耳朵内侧
    pygame.draw.polygon(screen, PINK, [
        right_ear_top,
        (head_x + IS(8 * SCALE) - ear_w // 4, head_y - head_radius - ear_h // 2),
        (head_x + IS(8 * SCALE) + ear_w // 4, head_y - head_radius - ear_h // 2)
    ])
    # 眼睛
    eye_w = IS(4 * SCALE)
    eye_h = IS(6 * SCALE)
    if hit_animation:
        # 开心的笑眼（弧线，向上）
        left_eye_rect = pygame.Rect(head_x - IS(7 * SCALE), head_y - IS(2 * SCALE), eye_w, eye_h)
        right_eye_rect = pygame.Rect(head_x + IS(3 * SCALE), head_y - IS(2 * SCALE), eye_w, eye_h)
        pygame.draw.arc(screen, WHITE, left_eye_rect, math.pi * 1.9, math.pi * 1.1, 2)
        pygame.draw.arc(screen, WHITE, right_eye_rect, math.pi * 1.9, math.pi * 1.1, 2)
    else:
        pygame.draw.ellipse(screen, WHITE, (head_x - IS(7 * SCALE), head_y - IS(2 * SCALE), eye_w, eye_h))
        pygame.draw.ellipse(screen, WHITE, (head_x + IS(3 * SCALE), head_y - IS(2 * SCALE), eye_w, eye_h))
    # 鼻子
    nose_x = head_x
    nose_y = head_y + IS(8 * SCALE)
    pygame.draw.ellipse(screen, WHITE, (nose_x - IS(2 * SCALE), nose_y, IS(4 * SCALE), IS(3 * SCALE)))
    # 嘴巴
    if hit_animation:
        # 大笑嘴巴（更大的弧线，张开嘴）
        mouth_rect = pygame.Rect(nose_x - IS(12 * SCALE), nose_y + IS(7 * SCALE), IS(24 * SCALE), IS(18 * SCALE))
        pygame.draw.arc(screen, WHITE, mouth_rect, math.pi * 1.15, math.pi * 1.85, 4)
    else:
        # 普通嘴巴（三条线）
        pygame.draw.line(screen, WHITE, (nose_x, nose_y + IS(3 * SCALE)), (nose_x, nose_y + IS(9 * SCALE)), 2)
        pygame.draw.line(screen, WHITE, (nose_x, nose_y + IS(9 * SCALE)), (nose_x - IS(5 * SCALE), nose_y + IS(13 * SCALE)), 2)
        pygame.draw.line(screen, WHITE, (nose_x, nose_y + IS(9 * SCALE)), (nose_x + IS(5 * SCALE), nose_y + IS(13 * SCALE)), 2)
    # 更长的胡须
    whisker_len = IS(22 * SCALE)
    for i in [-1, 0, 1]:
        pygame.draw.line(screen, WHITE, (nose_x - IS(2 * SCALE), nose_y + IS(4 * SCALE) + i * IS(3 * SCALE)), (nose_x - whisker_len, nose_y + IS(4 * SCALE) + i * IS(3 * SCALE)), 2)
        pygame.draw.line(screen, WHITE, (nose_x + IS(2 * SCALE), nose_y + IS(4 * SCALE) + i * IS(3 * SCALE)), (nose_x + whisker_len, nose_y + IS(4 * SCALE) + i * IS(3 * SCALE)), 2)

# 绘制网格（区分正常/禁用格子）
def draw_grid(mole_game):
    # 柔和多彩的格子颜色
    grid_colors = [
        [(120, 180, 160), (180, 160, 120), (160, 120, 180)],
        [(140, 120, 180), (120, 160, 180), (180, 120, 140)],
        [(160, 180, 120), (120, 140, 180), (180, 160, 140)]
    ]
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            color = grid_colors[x][y]
            if mole_game.disabled[x][y]:
                # 禁用格子更暗
                color = tuple(max(0, int(c * 0.5)) for c in color)
            rect = (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, color, rect)

# 绘制烟花效果（像素粒子）
def draw_fireworks(mole_game):
    current_time = time.time()
    
    # 绘制普通烟花
    for (x, y, start_time) in mole_game.fireworks:
        center_x = x * CELL_SIZE + CELL_SIZE // 2
        center_y = y * CELL_SIZE + CELL_SIZE // 2
        # 烟花存在时间（0-1秒）
        life = current_time - start_time
        # 粒子数量和扩散范围随时间变化
        particles = int(120 * (1 - life))
        radius = int(180 * life)
        # 颜色
        colors = [YELLOW, PINK, BLUE, WHITE]
        for i in range(particles):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, radius)
            px = center_x + math.cos(angle) * dist
            py = center_y + math.sin(angle) * dist
            color = random.choice(colors)
            size = random.randint(2, 4)
            pygame.draw.rect(screen, color, (px, py, size, size))
    
    # 绘制连击烟花（更大更华丽）
    for (center_x, center_y, start_time, text) in mole_game.combo_fireworks:
        # 烟花存在时间（0-2秒）
        life = current_time - start_time
        # 粒子数量和扩散范围更大
        particles = int(300 * (1 - life/2))
        radius = int(400 * life/2)
        # 更丰富的颜色
        colors = [YELLOW, PINK, BLUE, WHITE, GREEN, (255,128,0), (128,0,255)]
        for i in range(particles):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(0, radius)
            px = center_x + math.cos(angle) * dist
            py = center_y + math.sin(angle) * dist
            color = random.choice(colors)
            size = random.randint(3, 6)
            pygame.draw.rect(screen, color, (px, py, size, size))
        
        # 绘制"WELL DONE!"文字，随烟花一起出现和消失
        welldone_font = pygame.font.SysFont("Comic Sans MS", 48, bold=True)
        alpha = max(0, 255 - int(life * 127.5))  # 2秒内淡出
        welldone_surface = welldone_font.render(text, True, YELLOW)
        welldone_surface.set_alpha(alpha)
        text_rect = welldone_surface.get_rect(center=(center_x, center_y - 60))
        screen.blit(welldone_surface, text_rect)

def main():
    mole_game = Mole()
    start_time = time.time()
    running = True
    hit_animation = None
    game_started = False
    # Start menu buttons (used before game starts)
    start_button = pygame.Rect(WIDTH // 2 - 110, HEIGHT // 2 - 20, 220, 56)
    quit_button = pygame.Rect(WIDTH // 2 - 110, HEIGHT // 2 + 50, 220, 56)
    # Restart button shown on game over
    restart_button = pygame.Rect(WIDTH // 2 - 110, HEIGHT // 2 + 120, 220, 56)
    # button font used in menus and game over
    btn_font = pygame.font.Font(None, 28)
    # persistent flag for game over state
    game_over_mode = False

    while running:
        screen.fill(BLACK)
        if not game_started:
            # 显示开始界面（带按钮和键盘快捷键）
            screen.fill(BLACK)
            title_font = pygame.font.SysFont("Comic Sans MS", 48, bold=True)
            # Use pygame's default font for buttons to avoid system font issues
            btn_font = pygame.font.Font(None, 28)

            title_surf = title_font.render("Cat and Mouse", True, WHITE)
            title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
            screen.blit(title_surf, title_rect)

            # Start 按钮
            pygame.draw.rect(screen, BLUE, start_button)
            pygame.draw.rect(screen, WHITE, start_button, 2)
            start_surf = btn_font.render("START", True, WHITE)
            start_rect = start_surf.get_rect(center=start_button.center)
            screen.blit(start_surf, start_rect)

            # Quit 按钮
            pygame.draw.rect(screen, (221, 10, 40), quit_button)
            pygame.draw.rect(screen, WHITE, quit_button, 2)
            quit_surf = btn_font.render("END", True, WHITE)
            quit_rect = quit_surf.get_rect(center=quit_button.center)
            screen.blit(quit_surf, quit_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if start_button.collidepoint(event.pos):
                        game_started = True
                        start_time = time.time()
                    elif quit_button.collidepoint(event.pos):
                        running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        game_started = True
                        start_time = time.time()
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            pygame.display.flip()
            continue

        current_time = time.time()
        mole_game.time_left = max(0, 30 - (current_time - start_time))

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # If we're in game-over mode, only respond to restart/quit
            elif game_over_mode:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if restart_button.collidepoint(event.pos):
                        # Reinitialize game state and start a new game
                        mole_game = Mole()
                        start_time = time.time()
                        hit_animation = None
                        game_over_mode = False
                        continue
                    elif quit_button.collidepoint(event.pos):
                        running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_r, pygame.K_RETURN):
                        mole_game = Mole()
                        start_time = time.time()
                        hit_animation = None
                        game_over_mode = False
                        continue
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            else:
                # Normal in-game input: hit moles by clicking
                if event.type == pygame.MOUSEBUTTONDOWN and mole_game.time_left > 0:
                    mx, my = pygame.mouse.get_pos()
                    grid_x = mx // CELL_SIZE
                    grid_y = my // CELL_SIZE
                    if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                        mole_game.hit(grid_x, grid_y)
                        # Start hammer animation at hit position
                        hit_animation = (grid_x, grid_y, current_time)

        # Hammer animation: clear after 0.3s
        if hit_animation:
            if current_time - hit_animation[2] > 0.3:
                hit_animation = None

        # 游戏逻辑
        remaining_grids = sum(1 for x in range(GRID_SIZE) for y in range(GRID_SIZE) if not mole_game.disabled[x][y])
        # reflect persistent game-over state for rendering/interaction
        game_over_triggered = game_over_mode
        if not game_over_mode and mole_game.time_left > 0 and remaining_grids > 1:
            mole_game.update()

        # 绘制游戏元素
        draw_grid(mole_game)
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                if mole_game.grid[x][y]:
                    draw_pixel_mole(x, y)

        # 绘制UI元素（连击计数器和速度显示）
        draw_ui(mole_game)

        # 绘制所有烟花效果（包括连击烟花）
        draw_fireworks(mole_game)

        # 游戏结束条件：只剩一个格子
        if remaining_grids <= 1 or mole_game.time_left <= 0:
            # 触发一次新的烟花效果
            if not hasattr(mole_game, 'game_over_firework') or not mole_game.game_over_firework:
                mole_game.fireworks.append((1, 1, time.time()))
                mole_game.game_over_firework = True
                mole_game.game_over_time = time.time()
                # enter persistent game-over mode
                game_over_mode = True
            # 渐隐Game Over文字
            fade_time = min(2.0, time.time() - getattr(mole_game, 'game_over_time', time.time()))
            alpha = max(0, 255 - int(fade_time * 120))
            font = pygame.font.SysFont("Comic Sans MS", 48, bold=True)
            game_over_text = font.render("Game Over", True, (255,255,0))
            game_over_surface = game_over_text.copy()
            game_over_surface.set_alpha(alpha)
            text_rect = game_over_surface.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(game_over_surface, text_rect)
            # 屏幕渐暗
            dark_surface = pygame.Surface((WIDTH, HEIGHT))
            dark_surface.set_alpha(int(fade_time * 100))
            dark_surface.fill((20, 20, 20))
            screen.blit(dark_surface, (0, 0))
            # 显示最终分数
            score_font = pygame.font.SysFont("Arial", 28)
            final_surf = score_font.render(f"Final Score: {mole_game.score}", True, WHITE)
            final_surf.set_alpha(alpha)
            final_rect = final_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
            screen.blit(final_surf, final_rect)

            # Restart 按钮
            pygame.draw.rect(screen, BLUE, restart_button)
            pygame.draw.rect(screen, WHITE, restart_button, 2)
            restart_surf = btn_font.render("RESTART", True, WHITE)
            restart_rect = restart_surf.get_rect(center=restart_button.center)
            screen.blit(restart_surf, restart_rect)

        # 绘制锤子（跟随鼠标/动画）
        if not game_over_triggered:
            draw_hammer(pygame.mouse.get_pos(), hit_animation)

        # 绘制分数和时间
        font = pygame.font.SysFont("Arial", 24)
        score_text = font.render(f"分数: {mole_game.score}", True, WHITE)
        time_text = font.render(f"时间: {int(mole_game.time_left)}s", True, WHITE)
        screen.blit(score_text, (10, HEIGHT - 30))
        screen.blit(time_text, (WIDTH - 120, HEIGHT - 30))

        # 游戏结束后按Q退出
        if game_over_triggered:
            if pygame.key.get_pressed()[pygame.K_q]:
                running = False

        pygame.display.flip()
        clock.tick(FPS)

    # Stop and quit the mixer if it was started
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()
    except Exception:
        pass

    pygame.quit()

if __name__ == "__main__":
    main()
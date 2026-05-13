"""
game_managers.py – Quản lý toàn bộ vòng lặp game.

Game đi LÊN: player.y giảm dần (Y nhỏ hơn = cao hơn / xa hơn).
Quái spawn ở Y = player.y - offset (phía trên player trên màn hình).
"""
import math, random, pygame
from constants import *
from entities   import Player, Enemy, Boss, Projectile
from entities.enemy      import generate_enemy_cluster
from entities.projectile import DelayedCircleAttack
from managers.camera          import Camera
from managers.player_tracker  import PlayerTracker
from managers.buff_manager import BuffManager


# ============================================================
#  MenuManager – màn hình chủ và game over
# ============================================================

def push_out_of_wall(entity, obs):
    """Đẩy một thực thể ra khỏi cạnh gần nhất của chướng ngại vật."""
    # Tìm điểm gần nhất trên hình chữ nhật tới tâm thực thể
    closest_x = max(obs['x'], min(entity.x, obs['x'] + obs['w']))
    closest_y = max(obs['y'], min(entity.y, obs['y'] + obs['h']))
    
    dist_x = entity.x - closest_x
    dist_y = entity.y - closest_y
    distance = math.hypot(dist_x, dist_y)

    if distance < entity.radius:
        # Nếu đang lún vào (distance < bán kính), tính toán vector đẩy
        if distance == 0: # Trường hợp tâm nằm đúng điểm gần nhất
            entity.y -= entity.radius
            return

        overlap = entity.radius - distance
        entity.x += (dist_x / distance) * overlap
        entity.y += (dist_y / distance) * overlap

class MenuManager:
    """Vẽ và xử lý màn hình menu (main menu + game over)."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self._font_title = pygame.font.SysFont("monospace", 42, bold=True)
        self._font_sub   = pygame.font.SysFont("monospace", 20, bold=True)
        self._font_small = pygame.font.SysFont("monospace", 14)
        self._font_hint  = pygame.font.SysFont("monospace", 12)
        self._t = 0.0   # thời gian để animation

    def update(self, dt: float):
        self._t += dt

    # ------------------------------------------------------------------ #
    def draw_main_menu(self):
        """Vẽ màn hình chủ (Main Menu)."""
        self.screen.fill(COL_BG)
        self._draw_star_bg()

        cx = SCREEN_WIDTH // 2

        # Tiêu đề
        pulse = int(abs(math.sin(self._t * 1.5)) * 20)
        title_col = (80 + pulse, 200, 255)
        title = self._font_title.render("LOL x BẮN GÀ", True, title_col)
        self.screen.blit(title, (cx - title.get_width() // 2, 160))

        sub = self._font_sub.render("Chinh phục vô tận!", True, COL_SCORE)
        self.screen.blit(sub, (cx - sub.get_width() // 2, 215))

        # Nút Play
        self._draw_button(cx, 320, "▶  BẮT ĐẦU CHƠI  ▶", (50, 200, 80), (100, 255, 130))

        # Hướng dẫn
        controls = [
            "── ĐIỀU KHIỂN ──",
            "Click Phải (RMB)  :  Di chuyển",
            "Click Trái  (LMB)  :  Bắn đạn",
            "SPACE               :  Blink (nhảy nhanh)",
        ]
        y0 = 420
        for i, line in enumerate(controls):
            col = COL_SCORE if i == 0 else COL_TEXT
            font = self._font_sub if i == 0 else self._font_small
            t = font.render(line, True, col)
            self.screen.blit(t, (cx - t.get_width() // 2, y0 + i * 26))

        # Footer
        foot = self._font_hint.render("Lê Xuân Phước  –  2025", True, (80, 90, 120))
        self.screen.blit(foot, (cx - foot.get_width() // 2, SCREEN_HEIGHT - 30))

    def draw_game_over(self, score: int, kills_normal: int, kills_boss: int):
        """Vẽ màn hình Game Over."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150)) # Số 150 là độ mờ (0-255)
        self.screen.blit(overlay, (0, 0))
        
        cx = SCREEN_WIDTH // 2

        # Game Over
        go = self._font_title.render("GAME OVER", True, (220, 60, 60))
        self.screen.blit(go, (cx - go.get_width() // 2, 170))

        # Stats
        stats = [
            f"ĐIỂM SỐ : {score}",
            f"Tiêu diệt quái thường : {kills_normal}",
            f"Tiêu diệt BOSS        : {kills_boss}",
        ]
        y0 = 270
        for i, line in enumerate(stats):
            col = COL_SCORE if i == 0 else COL_TEXT
            font = self._font_sub if i == 0 else self._font_small
            t = font.render(line, True, col)
            self.screen.blit(t, (cx - t.get_width() // 2, y0 + i * 34))

        # Buttons
        self._draw_button(cx, 430, "▶  CHƠI LẠI  ▶", (50, 200, 80), (100, 255, 130))
        self._draw_button(cx, 500, "  MENU CHÍNH  ", (60, 80, 160), (100, 130, 220))

    # ------------------------------------------------------------------ #
    def _draw_button(self, cx, cy, text, col_bg, col_text):
        font = self._font_sub
        t = font.render(text, True, col_text)
        w = t.get_width() + 40
        h = t.get_height() + 16
        rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
        pygame.draw.rect(self.screen, col_bg, rect, border_radius=8)
        pygame.draw.rect(self.screen, col_text, rect, 2, border_radius=8)
        self.screen.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))
        return rect

    def get_button_rect(self, cx, cy, text):
        font = self._font_sub
        t = font.render(text, True, (0, 0, 0))
        w = t.get_width() + 40
        h = t.get_height() + 16
        return pygame.Rect(cx - w // 2, cy - h // 2, w, h)

    def _draw_star_bg(self):
        rng = random.Random(42)
        for _ in range(60):
            x = rng.randint(0, SCREEN_WIDTH)
            y = rng.randint(0, SCREEN_HEIGHT)
            r = rng.randint(1, 2)
            alpha = rng.randint(80, 200)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (200, 220, 255, alpha), (r, r), r)
            self.screen.blit(s, (x - r, y - r))

    # ------------------------------------------------------------------ #
    def handle_main_menu_click(self, pos) -> str:
        """Trả về 'play' nếu click nút bắt đầu."""
        cx = SCREEN_WIDTH // 2
        rect = self.get_button_rect(cx, 320, "▶  BẮT ĐẦU CHƠI  ▶")
        if rect.collidepoint(pos):
            return "play"
        return ""

    def handle_game_over_click(self, pos) -> str:
        """Trả về 'restart' hoặc 'menu'."""
        cx = SCREEN_WIDTH // 2
        if self.get_button_rect(cx, 430, "▶  CHƠI LẠI  ▶").collidepoint(pos):
            return "restart"
        if self.get_button_rect(cx, 500, "  MENU CHÍNH  ").collidepoint(pos):
            return "menu"
        return ""


# ============================================================
#  GameManager – vòng lặp gameplay
# ============================================================
class GameManager:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.camera = Camera()

        # ---- Player ----
        start_x = MAP_WIDTH // 2
        # Player bắt đầu ở Y lớn (bottom), đi lên = Y giảm
        start_y = 3000
        self.player = Player(start_x, start_y)
        self._player_start_y = start_y

        # ---- World objects ----
        self.enemies:         list[Enemy]               = []
        self.bosses:          list[Boss]                = []
        self.projectiles:     list[Projectile]          = []
        self.delayed_attacks: list[DelayedCircleAttack] = []
        self.obstacles:       list[dict]                = []

        # ---- Scoring ----
        self.score          = 0
        self.kills_normal   = 0
        self.kills_boss     = 0
        self._last_boss_thresh = 0

        # ---- World generation ----
        # Spawn phía TRÊN player (Y nhỏ hơn)
        self._next_enemy_y    = start_y - ENEMY_SPAWN_INTERVAL
        self._next_obstacle_y = start_y - OBSTACLE_SPAWN_INTERVAL
        
        # ---- Buff ----
        self.buff_manager = BuffManager()

        # ---- State ----
        self.state = "playing"
        self._death_timer = 0.0
        self._boss_kill_notice = None   # dict {"buff": ..., "timer": ...} hoặc None
        self._regen_acc = 0.0   # bộ đếm hồi máu cơ bản

        # ---- Fonts ----
        self._font_hud   = pygame.font.SysFont("monospace", 14, bold=True)
        self._font_big   = pygame.font.SysFont("monospace", 32, bold=True)
        self._font_small = pygame.font.SysFont("monospace", 12)

        # ---- Background ----
        self._grid_step = 80

        # Load asset ảnh nền cho từng map, scale vừa màn hình
        def _load_map_bg(path: str) -> pygame.Surface | None:
            try:
                img = pygame.image.load(path).convert()
                return pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except Exception:
                return None   # nếu thiếu file thì fallback về màu nền

        self._map_assets = {
            "fire":  _load_map_bg(PATH_MAP_FIRE),
            "water": _load_map_bg(PATH_MAP_WATER),
        }

        # ---- Map hiện tại (random 1 trong 2 lúc khởi tạo) ----
        self._map_pool   = random.sample(MAP_POOL, len(MAP_POOL))  # shuffle
        self._map_index  = 0
        self.current_map = self._map_pool[0]

        # Đếm ngược chuyển map sau khi boss chết
        self._pending_map_switch    = False
        self._map_transition_timer  = 0.0

        # --- Behavior Modeling ---
        self.tracker = PlayerTracker(SCREEN_WIDTH, SCREEN_HEIGHT)

    # ================================================================== #
    def handle_event(self, event: pygame.event.Event):
        """Xử lý input trong lúc chơi. KHÔNG bắt QUIT ở đây."""
        if self.state != "playing":
            return

        player = self.player

        # Trong game_managers.py -> hàm handle_event
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            wx, wy = self.camera.screen_to_world(float(mx), float(my))

            if event.button == 3:   # Chuột phải — Di chuyển
                player.set_move_target(wx, wy)

            elif event.button == 1:  # Chuột trái — Bắn
                dx = wx - player.x
                dy = wy - player.y
                # Giao toàn quyền cho Player tự xử lý bắn 1 hay 3 tia
                player.try_attack(dx, dy, self.projectiles)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                mx, my = pygame.mouse.get_pos()
                wx, wy = self.camera.screen_to_world(float(mx), float(my))
                did_blink = player.try_blink(wx, wy, self.obstacles)
                if did_blink:
                    self.tracker.record_blink(player.hp / player.max_hp)

    def update(self, dt: float):
        if self.state == "dead":
            self._death_timer += dt
            return
        if self.state != "playing":
            return

        player = self.player

        player.update(dt, self.obstacles)
        
        if player.alive:
            self._regen_acc += dt
            if self._regen_acc >= PASSIVE_REGEN_INTERVAL:
                self._regen_acc -= PASSIVE_REGEN_INTERVAL
                if player.hp < player.max_hp:
                    player.hp = min(player.max_hp, player.hp + PASSIVE_REGEN_AMOUNT)
        
        self.camera.update(player.x, player.y)

        # Cập nhật tracker hành vi player
        self.tracker.update(player)

        # Score: khoảng cách đi lên (start_y - current_y)
        dist_score = max(0, self._player_start_y - player.min_y_reached)
        self.score = int(dist_score
                         + SCORE_KILL_NORMAL * self.kills_normal
                         + SCORE_KILL_BOSS   * self.kills_boss)

        self._maybe_spawn(player.y)

        for e in self.enemies:
            e.update(dt, player, self.projectiles, self.delayed_attacks, self.tracker)
        for b in self.bosses:
            b.update(dt, player, self.projectiles, self.delayed_attacks, self.tracker)

        for p in self.projectiles:
            p.update(dt)
        for da in self.delayed_attacks:
            da.update(dt)

        # Collision: player ← enemy projectiles
        DODGE_WARN_R = 120  # bán kính cảnh báo để ghi nhận né
        for p in self.projectiles:
            if not p.alive:
                continue
            if p.owner in ("enemy", "boss"):
                # Ghi nhận hành vi né khi đạn đến gần
                if math.hypot(p.x - player.x, p.y - player.y) < DODGE_WARN_R:
                    self.tracker.record_dodge(p.vx, p.vy)
                if p.hits(player.x, player.y, player.radius):
                    player.take_damage(p.dmg)
                    p.alive = False

        # Collision: player ← delayed AoE
        for da in self.delayed_attacks:
            if da.triggered and da.alive:
                if da.hits(player.x, player.y, player.radius):
                    player.take_damage(da.dmg)
                    da.alive = False

        # Collision: enemies ← player projectiles
        for p in self.projectiles:
            if not p.alive or p.owner != "player":
                continue
            hit = False
            for e in self.enemies:
                if e.alive and p.hits(e.x, e.y, e.radius):
                    e.take_damage(p.dmg)
                    p.alive = False
                    if not e.alive:
                        self.kills_normal += 1
                    hit = True
                    break
            if hit:
                continue
            
            for b in self.bosses:
                if b.alive and p.hits(b.x, b.y, b.radius):
                    b.take_damage(p.dmg)
                    p.alive = False
                    if not b.alive:
                        self.kills_boss += 1
                        # Trao buff theo map hiện tại
                        buff_id = BUFF_WATER if self.current_map == "water" else BUFF_FIRE
                        self.buff_manager.add(buff_id)
                        # Lưu thông báo để hiển thị lên màn hình
                        self._boss_kill_notice = {
                            "buff": buff_id,
                            "timer": 4.0   # hiện trong 4 giây
                        }
                        self._pending_map_switch   = True
                        self._map_transition_timer = MAP_TRANSITION_DELAY
                        self._pending_map_switch   = True      # ← thêm
                        self._map_transition_timer = MAP_TRANSITION_DELAY  # ← thêm
                    break

        self._resolve_entity_collisions()

        self.enemies[:]         = [e for e in self.enemies         if e.alive]
        self.bosses[:]          = [b for b in self.bosses          if b.alive]
        self.projectiles[:]     = [p for p in self.projectiles     if p.alive]
        self.delayed_attacks[:] = [d for d in self.delayed_attacks if d.alive]
        
        if self._pending_map_switch:
            self._map_transition_timer -= dt
            if self._map_transition_timer <= 0:
                self._pending_map_switch = False
                self._map_index  = (self._map_index + 1) % len(self._map_pool)
                self.current_map = self._map_pool[self._map_index]
        # Cập nhật buff (hồi máu water, đếm ngược thời gian)
        self.buff_manager.update(dt, player)
        
        player.apply_buff_stats(
            fire=self.buff_manager.has(BUFF_FIRE),
            wind=self.buff_manager.has(BUFF_WIND)
        )

        # Đếm ngược thông báo boss kill
        if self._boss_kill_notice:
            self._boss_kill_notice["timer"] -= dt
            if self._boss_kill_notice["timer"] <= 0:
                self._boss_kill_notice = None

        self._maybe_spawn_boss()

        if not player.alive:
            self.state = "dead"

    def draw(self):
        bg = self._map_assets.get(self.current_map)
        if bg:
            img_h = bg.get_height()   # = SCREEN_HEIGHT vì đã scale
            # Tính offset để tile cuộn theo camera
            scroll_y = int(self.camera.offset_y) % img_h
            # Vẽ tối đa 2 lần để lấp đầy màn hình liên tục
            self.screen.blit(bg, (0, -scroll_y))
            if -scroll_y + img_h < SCREEN_HEIGHT:
                self.screen.blit(bg, (0, -scroll_y + img_h))
        else:
            self.screen.fill(COL_BG)
            
        self._draw_background()

        # Obstacles
        for obs in self.obstacles:
            sx, sy = self.camera.world_to_screen(obs['x'], obs['y'])
            pygame.draw.rect(self.screen, COL_OBSTACLE,
                             (sx, sy, obs['w'], obs['h']), border_radius=4)
            pygame.draw.rect(self.screen, (70, 85, 120),
                             (sx, sy, obs['w'], obs['h']), 1, border_radius=4)

        for da in self.delayed_attacks:
            da.draw(self.screen, self.camera)
        for p in self.projectiles:
            p.draw(self.screen, self.camera)
        for e in self.enemies:
            e.draw(self.screen, self.camera)
        for b in self.bosses:
            b.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)

        self._draw_hud()

        if self.state == "dead":
            self._draw_death_screen()


    # ================================================================== #
    def _maybe_spawn(self, player_y: float):
        """
        Spawn quái / obstacle phía TRÊN player.
        Vì game đi lên, _next_enemy_y giảm dần.
        Spawn khi player_y đủ gần _next_enemy_y (tức là đi lên đủ).
        """
        # Ngưỡng: spawn khi player cách mục tiêu < 0.8 * screen height
        threshold = SCREEN_HEIGHT * 0.8

        while player_y - self._next_enemy_y < threshold:
            cluster = generate_enemy_cluster(self._next_enemy_y, self.score, self.current_map)
            self.enemies.extend(cluster)
            self._next_enemy_y -= ENEMY_SPAWN_INTERVAL

        while player_y - self._next_obstacle_y < threshold:
            self._spawn_obstacle(self._next_obstacle_y)
            self._next_obstacle_y -= OBSTACLE_SPAWN_INTERVAL

        # Cull các entity quá xa phía dưới (đã qua player)
        cull_y = player_y + SCREEN_HEIGHT * 2
        self.enemies  = [e for e in self.enemies  if e.y < cull_y]
        self.obstacles = [o for o in self.obstacles if o['y'] < cull_y]

    def _spawn_obstacle(self, world_y: float):
        slots = random.randint(1, 2)
        for _ in range(slots):
            w = random.randint(OBSTACLE_W, OBSTACLE_W * 2)
            h = OBSTACLE_H
            # Thử tìm vị trí trống tối đa 5 lần
            for _attempt in range(5):
                x = random.uniform(PLAYER_RADIUS * 2, MAP_WIDTH - w - PLAYER_RADIUS * 2)
                new_rect = {'x': x, 'y': world_y, 'w': w, 'h': h}
                
                # Kiểm tra xem có đè lên tường cũ không
                overlap = False
                for obs in self.obstacles:
                    # Kiểm tra va chạm giữa 2 hình chữ nhật
                    if (new_rect['x'] < obs['x'] + obs['w'] and
                        new_rect['x'] + new_rect['w'] > obs['x'] and
                        new_rect['y'] < obs['y'] + obs['h'] and
                        new_rect['y'] + new_rect['h'] > obs['y']):
                        overlap = True
                        break
                
                if not overlap:
                    self.obstacles.append(new_rect)
                    break

    def _maybe_spawn_boss(self):
        thresh = (self.score // BOSS_SCORE_INTERVAL) * BOSS_SCORE_INTERVAL
        if thresh > 0 and thresh > self._last_boss_thresh:
            self._last_boss_thresh = thresh
            bx = MAP_WIDTH // 2 + random.randint(-60, 60)
            by = self.player.y - int(SCREEN_HEIGHT * 0.55)
            self.bosses.append(Boss(bx, by, map_type=self.current_map))

    def _resolve_entity_collisions(self):
        p = self.player
        all_entities = [p] + self.enemies + self.bosses # Bao gồm cả player
        
        # 1. Các thực thể đẩy nhau (Logic cũ của bạn)
        for i, e1 in enumerate(all_entities):
            for e2 in all_entities[i + 1:]:
                dx = e2.x - e1.x
                dy = e2.y - e1.y
                dist = math.hypot(dx, dy)
                min_dist = e1.radius + e2.radius + 2
                if dist < min_dist and dist > 0:
                    overlap = (min_dist - dist) / 2
                    e1.x -= dx / dist * overlap
                    e1.y -= dy / dist * overlap
                    e2.x += dx / dist * overlap
                    e2.y += dy / dist * overlap

        # 2. MỚI: Tường đẩy tất cả thực thể
        for e in all_entities:
            for obs in self.obstacles:
                push_out_of_wall(e, obs)

    # ------------------------------------------------------------------ #
    def _draw_background(self):
        # Chỉ vẽ vạch xuất phát, không vẽ lưới ô vuông
        sx_start, sy_start = self.camera.world_to_screen(0, self._player_start_y)
        if -10 <= sy_start <= SCREEN_HEIGHT + 10:
            pygame.draw.line(self.screen, (50, 200, 100),
                             (0, sy_start), (SCREEN_WIDTH, sy_start), 2)
            lbl = self._font_small.render("START", True, (50, 200, 100))
            self.screen.blit(lbl, (4, sy_start + 2))
    def _draw_hud(self):
        player = self.player

        score_txt = self._font_hud.render(f"SCORE  {self.score}", True, COL_SCORE)
        self.screen.blit(score_txt, (8, 8))

        kills_txt = self._font_small.render(
            f"Kills: {self.kills_normal} thường  |  {self.kills_boss} boss", True, COL_TEXT)
        self.screen.blit(kills_txt, (8, 28))

        next_boss = ((self.score // BOSS_SCORE_INTERVAL) + 1) * BOSS_SCORE_INTERVAL
        nb_txt = self._font_small.render(f"Boss tiếp @ {next_boss} điểm", True, (180, 100, 220))
        self.screen.blit(nb_txt, (8, 44))

        # HP bar
        bar_w = 160
        bar_h = 12
        bx, by = 8, SCREEN_HEIGHT - 30
        pygame.draw.rect(self.screen, COL_HP_BAR_BG, (bx, by, bar_w, bar_h))
        fill = int(bar_w * player.hp / player.max_hp)
        pygame.draw.rect(self.screen, COL_PLAYER_HP, (bx, by, fill, bar_h))
        pygame.draw.rect(self.screen, COL_TEXT, (bx, by, bar_w, bar_h), 1)
        hp_txt = self._font_small.render(f"HP {player.hp}/{player.max_hp}", True, COL_TEXT)
        self.screen.blit(hp_txt, (bx + bar_w + 6, by))

        # Blink CD
        blink_cd = player._blink_timer
        blink_str = ("BLINK [SPACE]  SẴN SÀNG" if blink_cd <= 0
                     else f"BLINK [SPACE]  {blink_cd:.1f}s")
        col = (80, 200, 255) if blink_cd <= 0 else (100, 100, 150)
        blink_txt = self._font_small.render(blink_str, True, col)
        self.screen.blit(blink_txt, (8, SCREEN_HEIGHT - 52))

        hints = ["RMB: Di chuyển", "LMB: Bắn", "SPACE: Blink"]
        for i, h in enumerate(hints):
            t = self._font_small.render(h, True, (100, 110, 140))
            self.screen.blit(t, (SCREEN_WIDTH - 120, 8 + i * 16))

        if self._pending_map_switch:
            t = self._map_transition_timer
            next_map = self._map_pool[(self._map_index + 1) % len(self._map_pool)]
            label = {"fire": "LỬA 🔥", "water": "NƯỚC 💧"}.get(next_map, next_map.upper())
            msg = f"CHUYỂN MAP → {label}  ({t:.1f}s)"
            pulse = abs(math.sin(t * 5))
            col = (255, int(200 * pulse), 30)
            surf = self._font_hud.render(msg, True, col)
            cx = SCREEN_WIDTH // 2
            self.screen.blit(surf, (cx - surf.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            
# Thông báo hạ boss + buff nhận được
        if self._boss_kill_notice:
            notice = self._boss_kill_notice
            t = notice["timer"]
            buff_id = notice["buff"]

            if buff_id == BUFF_WATER:
                boss_name = "BOSS NƯỚC"
                buff_desc = "Hồi 1 HP mỗi 3 giây (60s)"
                col_notice = (80, 180, 255)
            else:
                boss_name = "BOSS LỬA"
                buff_desc = "Bắn 3 đạn hình nón (45s)"
                col_notice = (255, 120, 30)

            # Nhấp nháy khi gần hết
            alpha_scale = min(1.0, t / 1.0)
            pulse = abs(math.sin(t * 4)) if t < 1.5 else 1.0

            font_big   = pygame.font.SysFont("monospace", 22, bold=True)
            font_small = pygame.font.SysFont("monospace", 14)

            cx = SCREEN_WIDTH // 2
            line1 = font_big.render(f"✦ ĐÃ HẠ {boss_name}! ✦", True,
                                    tuple(int(c * pulse) for c in col_notice))
            line2 = font_small.render(f"BUFF: {buff_desc}", True, COL_TEXT)

            self.screen.blit(line1, (cx - line1.get_width() // 2, 80))
            self.screen.blit(line2, (cx - line2.get_width() // 2, 110))

    def _draw_death_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        alpha = min(180, int(self._death_timer * 300))
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

        # Chỉ vẽ chữ "GAME OVER" và Score tạm thời nếu chưa chuyển hẳn sang Menu
        # Nếu bộ đếm quá 1.5s (lúc main.py chuyển state) thì không vẽ nữa để nhường sân cho Menu
        if self._death_timer <= 1.5:
            cx = SCREEN_WIDTH // 2
            lines = [
                ("GAME OVER",     self._font_big,   (220, 60, 60)),
                (f"SCORE: {self.score}", self._font_hud, COL_SCORE),
                (f"Kills: {self.kills_normal} thường  |  {self.kills_boss} boss",
                self._font_small, COL_TEXT),
            ]
            cy = SCREEN_HEIGHT // 2 - 60
            for text, font, color in lines:
                surf = font.render(text, True, color)
                self.screen.blit(surf, (cx - surf.get_width() // 2, cy))
                cy += surf.get_height() + 8
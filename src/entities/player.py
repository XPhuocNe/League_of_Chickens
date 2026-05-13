"""
player.py – Quản lý nhân vật người chơi: trạng thái, di chuyển, tấn công, blink và buff.

Xử lý toàn bộ vòng đời của Player: nhận input di chuyển/tấn công từ GameManager,
thực thi cơ chế blink hai giai đoạn (pre-stun → teleport → post-stun),
windup trước khi bắn, giới hạn vùng di chuyển theo vạch start và biên bản đồ,
đồng bộ chỉ số từ BuffManager, và vẽ toàn bộ hiệu ứng lên màn hình.

Last modified: 10:47 PM 12/5/2026
"""
import math, pygame
from constants import *

BLINK_PRE_STUN_DURATION  = 0.15
BLINK_POST_STUN_DURATION = 0.25


class Player:
    """Quản lý toàn bộ trạng thái và hành vi của nhân vật chính."""

    BASE_SPEED          = 200.0
    BASE_BLINK_COOLDOWN = 5.0

    def __init__(self, x: float, y: float):
        """
        Khởi tạo player tại vị trí (x, y).

        Input:
            x (float): Tọa độ X ban đầu trong world space.
            y (float): Tọa độ Y ban đầu trong world space — đây cũng là start_y, giới hạn dưới.
        """
        self.x  = float(x)
        self.y  = float(y)
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.radius = PLAYER_RADIUS

        self.start_y = float(y)

        self.target_x: float | None = None
        self.target_y: float | None = None
        self.speed = self.BASE_SPEED

        self.attack_range    = PLAYER_ATTACK_RANGE
        self.attack_dmg      = PLAYER_ATTACK_DMG
        self.attack_cooldown = PLAYER_ATTACK_COOLDOWN
        self._attack_timer   = 0.0

        self.attack_windup  = PLAYER_ATTACK_WINDUP
        self._attack_timer  = 0.0

        self._windup_timer  = 0.0
        self._pending_dx    = 0.0
        self._pending_dy    = 0.0
        self._pending_projs = None

        self.blink_range    = BLINK_RANGE
        self.blink_cooldown = self.BASE_BLINK_COOLDOWN
        self._blink_timer   = 0.0

        # Blink hai giai đoạn: pre-stun (đứng yên, chuẩn bị) → teleport → post-stun (khựng sau)
        self._blink_pre_stun  = 0.0   # đếm ngược trước khi teleport
        self._blink_post_stun = 0.0   # đếm ngược sau khi teleport
        self._blink_dest_x: float | None = None
        self._blink_dest_y: float | None = None
        self._blink_obstacles: list = []

        self.hit_flash = 0.0
        self.blink_fx  = []
        self.alive     = True

        self.min_y_reached = y

        self.buff_fire_active = False
        self.buff_wind_active = False

    def apply_buff_stats(self, fire: bool, wind: bool):
        """
        Đồng bộ chỉ số speed và blink_cooldown theo trạng thái buff hiện tại.
        Được GameManager gọi mỗi frame sau khi BuffManager.update() xong.

        Input:
            fire (bool): True nếu BUFF_FIRE đang active.
            wind (bool): True nếu BUFF_WIND đang active.
        """
        self.buff_fire_active = fire
        self.buff_wind_active = wind
        self.speed          = self.BASE_SPEED          * (2.0 if wind else 1.0)
        self.blink_cooldown = self.BASE_BLINK_COOLDOWN * (0.5 if wind else 1.0)

    @property
    def blink_ready(self):
        """
        Kiểm tra kỹ năng Blink có sẵn sàng không.

        Output:
            bool: True nếu hết cooldown, không đang trong pre-stun và không đang post-stun.
        """
        return self._blink_timer <= 0 and self._blink_pre_stun <= 0

    @property
    def attack_ready(self):
        """
        Kiểm tra player có thể khai hỏa không.

        Output:
            bool: True nếu cả attack_timer lẫn windup_timer đều về 0.
        """
        return self._attack_timer <= 0 and self._windup_timer <= 0

    def _is_frozen(self) -> bool:
        """
        Trả về True nếu player đang bị khựng (windup tấn công, pre-stun hoặc post-stun blink).

        Output:
            bool: True khi player không thể di chuyển.
        """
        return self._windup_timer > 0 or self._blink_pre_stun > 0 or self._blink_post_stun > 0

    def set_move_target(self, world_x: float, world_y: float):
        """
        Đặt điểm đến để player tự di chuyển tới. Bỏ qua nếu đang bị khựng.
        Điểm đến bị kẹp để không vượt xuống dưới vạch start.

        Input:
            world_x (float): Tọa độ X đích trong world space.
            world_y (float): Tọa độ Y đích trong world space.
        """
        if self._is_frozen():
            return
        self.target_x = float(world_x)
        self.target_y = min(float(world_y), self.start_y - self.radius)

    def try_blink(self, world_x: float, world_y: float, obstacles: list) -> bool:
        """
        Khởi động cơ chế blink hai giai đoạn:
        Giai đoạn 1 — pre-stun BLINK_PRE_STUN_DURATION giây (player đứng yên, nhấp nháy).
        Giai đoạn 2 — teleport rồi áp dụng post-stun BLINK_POST_STUN_DURATION giây.
        Không blink xuống dưới vạch start.

        Input:
            world_x   (float): Tọa độ X đích trong world space.
            world_y   (float): Tọa độ Y đích trong world space.
            obstacles (list) : Danh sách dict chướng ngại vật {'x','y','w','h'}.
        Output:
            bool: True nếu đã kích hoạt pre-stun thành công, False nếu không đủ điều kiện.
        """
        if not self.blink_ready or self._windup_timer > 0:
            return False

        dx = world_x - self.x
        dy = world_y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return False

        t_max = min(1.0, self.blink_range / dist)
        dest_x = self.x + dx * t_max
        dest_y = min(self.y + dy * t_max, self.start_y - self.radius)

        if _any_circle_rect(dest_x, dest_y, self.radius, obstacles):
            low, high = 0.0, t_max
            for _ in range(10):
                mid = (low + high) / 2.0
                tx  = self.x + dx * mid
                ty  = self.y + dy * mid
                if _any_circle_rect(tx, ty, self.radius, obstacles):
                    high = mid
                else:
                    low = mid
            dest_x = self.x + dx * low
            dest_y = min(self.y + dy * low, self.start_y - self.radius)

        # Lưu đích và bắt đầu pre-stun — teleport sẽ xảy ra trong update()
        self._blink_dest_x    = dest_x
        self._blink_dest_y    = dest_y
        self._blink_obstacles = obstacles
        self._blink_pre_stun  = BLINK_PRE_STUN_DURATION
        self._blink_timer     = self.blink_cooldown
        self.target_x = None
        self.target_y = None
        return True

    def _execute_blink(self):
        """
        Thực hiện teleport ngay sau khi pre-stun kết thúc, rồi bật post-stun.
        Chỉ được gọi nội bộ từ update() khi _blink_pre_stun về 0.
        """
        if self._blink_dest_x is None:
            return
        self.blink_fx.append([self.x, self.y, 1.0])
        self.x = self._blink_dest_x
        self.y = self._blink_dest_y
        self._blink_post_stun = BLINK_POST_STUN_DURATION
        self._blink_dest_x    = None
        self._blink_dest_y    = None
        self._blink_obstacles = []

    def try_attack(self, direction_x: float, direction_y: float, projectiles: list):
        """
        Giai đoạn 1 của tấn công: bắt đầu windup, hủy di chuyển.

        Input:
            direction_x (float): Thành phần X của hướng bắn.
            direction_y (float): Thành phần Y của hướng bắn.
            projectiles (list) : Danh sách đạn để thêm vào sau khi windup xong.
        """
        if not self.attack_ready:
            return
        dist = math.hypot(direction_x, direction_y)
        if dist == 0:
            return

        self.target_x = None
        self.target_y = None

        self._pending_dx    = direction_x
        self._pending_dy    = direction_y
        self._pending_projs = projectiles
        self._windup_timer  = self.attack_windup

    def _execute_attack(self):
        """Giai đoạn 2 của tấn công: tạo đạn sau khi windup hoàn tất."""
        from entities.projectile import Projectile

        base_angle = math.atan2(self._pending_dy, self._pending_dx)
        spreads = [-0.22, 0.0, 0.22] if self.buff_fire_active else [0.0]

        for spread in spreads:
            angle = base_angle + spread
            proj = Projectile(
                owner="player",
                x=self.x, y=self.y,
                vx=math.cos(angle) * PROJECTILE_SPEED,
                vy=math.sin(angle) * PROJECTILE_SPEED,
                dmg=self.attack_dmg,
                max_range=self.attack_range,
                radius=6,
                color=COL_PROJ_PLAYER,
            )
            self._pending_projs.append(proj)

        self._attack_timer  = self.attack_cooldown
        self._pending_projs = None

    def take_damage(self, dmg: int):
        """
        Trừ máu và bật hiệu ứng chớp trắng. Đặt alive = False khi máu về 0.

        Input:
            dmg (int): Lượng sát thương cần trừ.
        """
        if not self.alive:
            return
        self.hp -= dmg
        self.hit_flash = 0.15
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def update(self, dt: float, obstacles: list):
        """
        Cập nhật toàn bộ trạng thái player mỗi frame: đếm ngược cooldown,
        xử lý blink hai giai đoạn, windup tấn công, di chuyển có va chạm,
        giới hạn biên bản đồ và vạch start, ghi lại Y nhỏ nhất để tính điểm.

        Input:
            dt        (float): Thời gian trôi qua giữa 2 frame (giây).
            obstacles (list) : Danh sách dict chướng ngại vật {'x','y','w','h'}.
        """
        if self._attack_timer > 0:
            self._attack_timer -= dt
        if self._blink_timer > 0:
            self._blink_timer -= dt
        if self.hit_flash > 0:
            self.hit_flash -= dt

        self.blink_fx = [[x, y, a - dt * 3] for x, y, a in self.blink_fx if (a - dt * 3) > 0]

        # --- Blink pre-stun: đếm ngược, khi hết thì teleport ---
        if self._blink_pre_stun > 0:
            self._blink_pre_stun -= dt
            if self._blink_pre_stun <= 0:
                self._blink_pre_stun = 0.0
                self._execute_blink()

        # --- Blink post-stun: đếm ngược sau teleport ---
        if self._blink_post_stun > 0:
            self._blink_post_stun -= dt

        # --- Windup tấn công ---
        if self._windup_timer > 0:
            self._windup_timer -= dt
            if self._windup_timer <= 0:
                self._execute_attack()

        # --- Di chuyển: chỉ khi không bị khựng ---
        if not self._is_frozen():
            if self.target_x is not None and self.target_y is not None:
                dx   = self.target_x - self.x
                dy   = self.target_y - self.y
                dist = math.hypot(dx, dy)
                step = self.speed * dt
                if dist <= step:
                    nx_pos = self.target_x
                    ny_pos = self.target_y
                    self.target_x = None
                    self.target_y = None
                else:
                    nx_pos = self.x + dx / dist * step
                    ny_pos = self.y + dy / dist * step

                ny_pos = min(ny_pos, self.start_y - self.radius)

                if not _any_circle_rect(nx_pos, self.y, self.radius, obstacles):
                    self.x = nx_pos
                if not _any_circle_rect(self.x, ny_pos, self.radius, obstacles):
                    self.y = ny_pos

        # --- Giới hạn biên bản đồ và vạch start ---
        self.x = max(self.radius, min(MAP_WIDTH - self.radius, self.x))
        self.y = min(self.y, self.start_y - self.radius)

        if self.y < self.min_y_reached:
            self.min_y_reached = self.y

    def draw(self, surface: pygame.Surface, camera):
        """
        Vẽ player và toàn bộ hiệu ứng lên surface: bóng ma blink, vòng pre-stun nhấp nháy,
        vòng post-stun vàng, thân, thanh máu, vòng cung cooldown blink, chấm đích di chuyển.

        Input:
            surface (pygame.Surface): Bề mặt màn hình để vẽ lên.
            camera  (Camera)        : Dùng để chuyển tọa độ world sang screen.
        """
        sx, sy = camera.world_to_screen(self.x, self.y)

        # Bóng ma blink
        for gx, gy, alpha in self.blink_fx:
            gsx, gsy = camera.world_to_screen(gx, gy)
            alpha_val = max(0, min(255, int(alpha * 180)))
            ghost_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(ghost_surf, (*COL_BLINK_FX, alpha_val),
                               (self.radius, self.radius), self.radius)
            surface.blit(ghost_surf, (gsx - self.radius, gsy - self.radius))

        # Pre-stun: vòng tròn xanh lam nhấp nháy báo hiệu chuẩn bị blink
        if self._blink_pre_stun > 0:
            ratio      = self._blink_pre_stun / BLINK_PRE_STUN_DURATION
            pre_alpha  = int(200 * ratio)
            pre_surf   = pygame.Surface((self.radius * 2 + 16, self.radius * 2 + 16), pygame.SRCALPHA)
            pygame.draw.circle(pre_surf, (80, 200, 255, pre_alpha),
                               (self.radius + 8, self.radius + 8), self.radius + 6, 3)
            surface.blit(pre_surf, (int(sx) - self.radius - 8, int(sy) - self.radius - 8))

        # Post-stun: vòng tròn vàng mờ dần sau teleport
        if self._blink_post_stun > 0:
            stun_ratio = self._blink_post_stun / BLINK_POST_STUN_DURATION
            stun_alpha = int(160 * stun_ratio)
            stun_surf  = pygame.Surface((self.radius * 2 + 12, self.radius * 2 + 12), pygame.SRCALPHA)
            pygame.draw.circle(stun_surf, (255, 255, 100, stun_alpha),
                               (self.radius + 6, self.radius + 6), self.radius + 4, 3)
            surface.blit(stun_surf, (int(sx) - self.radius - 6, int(sy) - self.radius - 6))

        color = COL_HIT_FLASH if self.hit_flash > 0 else COL_PLAYER
        pygame.draw.circle(surface, color, (int(sx), int(sy)), self.radius)
        pygame.draw.circle(surface, (200, 240, 255), (int(sx), int(sy)), self.radius // 2)

        bar_w = self.radius * 2 + 4
        bar_h = 5
        bx    = int(sx) - bar_w // 2
        by    = int(sy) - self.radius - 10
        pygame.draw.rect(surface, COL_HP_BAR_BG, (bx, by, bar_w, bar_h))
        fill = int(bar_w * self.hp / self.max_hp)
        pygame.draw.rect(surface, COL_PLAYER_HP, (bx, by, fill, bar_h))

        if not self.blink_ready:
            ratio = 1 - self._blink_timer / self.blink_cooldown
            pygame.draw.arc(surface, (80, 180, 255),
                            (int(sx) - self.radius - 4, int(sy) - self.radius - 4,
                             (self.radius + 4) * 2, (self.radius + 4) * 2),
                            math.pi / 2, math.pi / 2 + ratio * 2 * math.pi, 2)

        if self.target_x is not None and self.target_y is not None:
            tsx, tsy = camera.world_to_screen(self.target_x, self.target_y)
            pygame.draw.circle(surface, (80, 255, 120), (int(tsx), int(tsy)), 4, 1)


def _any_circle_rect(cx, cy, r, obstacles):
    """
    Kiểm tra hình tròn có chạm bất kỳ chướng ngại vật nào trong danh sách không.

    Input:
        cx        (float): Tọa độ X tâm hình tròn.
        cy        (float): Tọa độ Y tâm hình tròn.
        r         (float): Bán kính hình tròn.
        obstacles (list) : Danh sách dict {'x','y','w','h'}.
    Output:
        bool: True nếu có ít nhất một va chạm.
    """
    for obs in obstacles:
        if _circle_rect(cx, cy, r, obs):
            return True
    return False


def _circle_rect(cx, cy, r, rect_dict):
    """
    Kiểm tra va chạm giữa hình tròn và một hình chữ nhật bằng điểm gần nhất.

    Input:
        cx        (float): Tọa độ X tâm hình tròn.
        cy        (float): Tọa độ Y tâm hình tròn.
        r         (float): Bán kính hình tròn.
        rect_dict (dict) : Hình chữ nhật với các key 'x', 'y', 'w', 'h'.
    Output:
        bool: True nếu hình tròn và hình chữ nhật giao nhau.
    """
    rx, ry, rw, rh = rect_dict['x'], rect_dict['y'], rect_dict['w'], rect_dict['h']
    closest_x = max(rx, min(cx, rx + rw))
    closest_y = max(ry, min(cy, ry + rh))
    return math.hypot(cx - closest_x, cy - closest_y) < r
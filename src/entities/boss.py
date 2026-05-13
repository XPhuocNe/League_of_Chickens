"""
boss.py – Quản lý kẻ địch đặc biệt Boss với hai pha tấn công mặc định và behavior modeling.

Boss lắc ngang liên tục, chờ player vào tầm rồi thực hiện windup
trước khi khai hỏa. Khi PlayerTracker tích lũy đủ 120 frame dữ liệu,
Boss phân tích BehaviorProfile để chọn pattern tấn công phù hợp:
    - Player aggressive  → AoE phạt việc áp sát.
    - Player hay né trái/phải → wide spread bịt đường né.
    - Player phòng thủ   → snipe chính xác vào vị trí yêu thích.
Khi chưa đủ data thì dùng hai pha mặc định (spread / aoe).

Last modified: 10:22 PM 12/5/2026
"""
import math, random, pygame
from constants import *

BOSS_WINDUP_DURATION = 0.6
_BOSS_SPRITE_CACHE: dict = {}


def _load_strip(path: str, n_frames: int, target_h: int) -> list:
    """
    Cắt spritesheet ngang thành danh sách Surface và scale về target_h.

    Input:
        path     (str): Đường dẫn spritesheet.
        n_frames (int): Số frame.
        target_h (int): Chiều cao đích.
    Output:
        list[pygame.Surface]: Danh sách frame, rỗng nếu lỗi.
    """
    try:
        import numpy as np
        sheet = pygame.image.load(path).convert_alpha()
        bg = sheet.get_at((0, 0))
        arr = pygame.surfarray.pixels3d(sheet)
        alp = pygame.surfarray.pixels_alpha(sheet)
        mask = (
            (np.abs(arr[:, :, 0].astype(int) - bg.r) <= 15) &
            (np.abs(arr[:, :, 1].astype(int) - bg.g) <= 15) &
            (np.abs(arr[:, :, 2].astype(int) - bg.b) <= 15)
        )
        alp[mask] = 0
        del arr, alp
        sw, sh = sheet.get_size()
        fw = sw // n_frames
        frames = []
        for i in range(n_frames):
            frame = sheet.subsurface((i * fw, 0, fw, sh)).copy()
            scale = target_h / sh
            nw    = max(1, int(fw * scale))
            frames.append(pygame.transform.scale(frame, (nw, target_h)))
        return frames
    except Exception:
        return []


def _get_boss_sprites() -> dict:
    """
    Trả về dict sprite boss đã load (lazy-load lần đầu).

    Output:
        dict: key 'fire' và 'water', mỗi key là list frame dragon animation.
    """
    global _BOSS_SPRITE_CACHE
    if _BOSS_SPRITE_CACHE:
        return _BOSS_SPRITE_CACHE
    BASE = "src/assets/"
    _BOSS_SPRITE_CACHE = {
        "fire":  _load_strip(BASE + "fire_dragon.png",  16, 635),
        "water": _load_strip(BASE + "water_dragon.png", 16, 558),
    }
    return _BOSS_SPRITE_CACHE


class Boss:
    """Quản lý trạng thái, chuyển động, windup, tấn công và sprite animation của Boss."""

    def __init__(self, x: float, y: float, map_type: str = "fire"):
        """
        Khởi tạo Boss tại vị trí (x, y).

        Input:
            x        (float): Tọa độ X ban đầu.
            y        (float): Tọa độ Y ban đầu.
            map_type (str)  : 'fire' hoặc 'water' xác định sprite dragon.
        """
        self.x        = float(x)
        self.y        = float(y)
        self.hp       = BOSS_HP
        self.max_hp   = BOSS_HP
        self.radius   = 120
        self.alive    = True
        self.map_type = map_type

        self.attack_range = R
        self.attack_dmg   = BOSS_DMG

        self._phase        = 0
        self._cooldown_max = BOSS_ATTACK_COOLDOWN
        self._timer        = 0.5
        self._burst_count  = 0

        self._windup_timer    = 0.0
        self._windup_player   = None
        self._windup_projs    = None
        self._windup_delayed  = None
        self._windup_tracker  = None

        self._sway_dir   = random.choice([-1, 1])
        self._sway_speed = 30.0
        self._sway_limit = 80.0
        self._origin_x   = float(x)

        self.hit_flash = 0.0
        self.color     = COL_BOSS
        self._pulse    = 0.0

        self._facing     = 1        # 1=phải, -1=trái
        self._anim_timer = 0.0
        self._anim_fps   = 12.0
        self._frame_idx  = 0

    def take_damage(self, dmg: int):
        """
        Trừ máu, bật flash và đánh dấu chết khi máu về 0.

        Input:
            dmg (int): Lượng sát thương.
        """
        self.hp -= dmg
        self.hit_flash = 0.15
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False

    def in_range(self, px: float, py: float) -> bool:
        """
        Kiểm tra player có trong tầm tấn công không.

        Input:
            px (float): Tọa độ X player.
            py (float): Tọa độ Y player.
        Output:
            bool: True nếu khoảng cách ≤ attack_range.
        """
        return math.hypot(self.x - px, self.y - py) <= self.attack_range

    def update(self, dt: float, player, projectiles: list,
               delayed_attacks: list, tracker=None):
        """
        Cập nhật Boss mỗi frame: animation, lắc ngang, cooldown, windup, tấn công.

        Input:
            dt              (float): Thời gian trôi qua (giây).
            player          (Player): Đối tượng player.
            projectiles     (list) : Danh sách đạn.
            delayed_attacks (list) : Danh sách AoE trễ.
            tracker                : PlayerTracker tùy chọn.
        """
        if not self.alive:
            return

        self._pulse = (self._pulse + dt * 3) % (2 * math.pi)
        if self.hit_flash > 0:
            self.hit_flash -= dt

        # Tiến frame animation dragon
        self._anim_timer += dt
        if self._anim_timer >= 1.0 / self._anim_fps:
            self._anim_timer -= 1.0 / self._anim_fps
            strip = _get_boss_sprites().get(self.map_type, [])
            if strip:
                self._frame_idx = (self._frame_idx + 1) % len(strip)

        # Lắc ngang — quay đầu theo chiều di chuyển
        prev_x  = self.x
        self.x += self._sway_dir * self._sway_speed * dt
        if abs(self.x - self._origin_x) > self._sway_limit:
            self._sway_dir *= -1
        self.x = max(self.radius + 10, min(MAP_WIDTH - self.radius - 10, self.x))
        if self.x != prev_x:
            self._facing = 1 if self.x > prev_x else -1

        # Windup: đếm ngược → khai hỏa
        if self._windup_timer > 0:
            self._windup_timer -= dt
            if self._windup_timer <= 0:
                self._windup_timer = 0.0
                self._fire(self._windup_player, self._windup_projs,
                           self._windup_delayed, self._windup_tracker)
                self._windup_player = self._windup_projs = None
                self._windup_delayed = self._windup_tracker = None

                self._burst_count += 1
                if self._phase == 0 and self._burst_count >= 2:
                    self._phase = 1; self._burst_count = 0
                    self._timer = self._cooldown_max * 0.7
                elif self._phase == 1:
                    self._phase = 0; self._burst_count = 0
                    self._timer = self._cooldown_max * 1.2
                else:
                    self._timer = self._cooldown_max * 0.5
            return

        if not self.in_range(player.x, player.y):
            self._timer = min(self._timer + dt * 0.5, self._cooldown_max)
            return

        self._timer -= dt
        if self._timer > 0:
            return

        # Quay về phía player trước windup
        self._facing         = 1 if player.x >= self.x else -1
        self._windup_timer   = BOSS_WINDUP_DURATION
        self._windup_player  = player
        self._windup_projs   = projectiles
        self._windup_delayed = delayed_attacks
        self._windup_tracker = tracker

    def _choose_pattern(self, profile) -> str:
        """
        Chọn pattern tấn công dựa trên BehaviorProfile.

        Input:
            profile (BehaviorProfile): Snapshot hành vi player từ PlayerTracker.
        Output:
            str: Một trong 'aoe', 'wide_spread', 'snipe', 'spread'.
        """
        if profile.is_aggressive:
            return "aoe"
        if profile.dodge_bias in ("left", "right"):
            return "wide_spread"
        if not profile.is_aggressive and profile.dodge_bias == "none":
            return "snipe"
        return "spread"

    def _fire(self, player, projectiles: list, delayed_attacks: list, tracker=None):
        """
        Thực hiện pattern tấn công đã được chọn sau windup.

        Input:
            player          (Player): Dùng để tính hướng/vị trí bắn.
            projectiles     (list) : Danh sách đạn.
            delayed_attacks (list) : Danh sách AoE trễ.
            tracker                : PlayerTracker tùy chọn.
        """
        from entities.projectile import Projectile, DelayedCircleAttack

        pattern = None
        if tracker is not None:
            profile = tracker.get_profile()
            if profile.reliable:
                pattern = self._choose_pattern(profile)
        if pattern is None:
            pattern = "spread" if self._phase == 0 else "aoe"

        self._facing = 1 if player.x >= self.x else -1

        if pattern == "spread":
            self._do_spread(player, projectiles, [-0.18, 0.0, 0.18], 1.2)

        elif pattern == "wide_spread":
            self._do_spread(player, projectiles, [-0.35, -0.18, 0.0, 0.18, 0.35], 1.1)

        elif pattern == "snipe":
            profile  = tracker.get_profile()
            tx, ty   = profile.avg_x, player.y - 40
            dx, dy   = tx - self.x, ty - self.y
            dist     = math.hypot(dx, dy)
            if dist == 0:
                return
            self._facing = 1 if dx >= 0 else -1
            speed = ENEMY_PROJ_SPEED * 1.8
            projectiles.append(Projectile(
                owner="boss", x=self.x, y=self.y,
                vx=dx / dist * speed, vy=dy / dist * speed,
                dmg=self.attack_dmg, max_range=self.attack_range + 200,
                radius=10, color=(255, 80, 255), use_fireball_sprite=True,
            ))

        elif pattern == "aoe":
            delayed_attacks.append(DelayedCircleAttack(
                owner="boss", x=player.x, y=player.y,
                aoe_r=BOSS_TYPE2_AOE_R, dmg=self.attack_dmg, delay=TYPE2_DELAY * 1.3,
            ))
            ox = random.uniform(-BOSS_TYPE2_AOE_R, BOSS_TYPE2_AOE_R)
            oy = random.uniform(-BOSS_TYPE2_AOE_R, BOSS_TYPE2_AOE_R)
            delayed_attacks.append(DelayedCircleAttack(
                owner="boss", x=player.x + ox, y=player.y + oy,
                aoe_r=BOSS_TYPE2_AOE_R * 0.8, dmg=self.attack_dmg, delay=TYPE2_DELAY * 1.5,
            ))

    def _do_spread(self, player, projectiles: list, spreads: list, speed_mult: float):
        """
        Bắn nhiều đạn tỏa góc theo danh sách spreads.

        Input:
            player      (Player): Dùng để tính hướng.
            projectiles (list)  : Danh sách đạn.
            spreads     (list)  : Độ lệch góc (radian) mỗi đạn.
            speed_mult  (float) : Hệ số nhân tốc độ đạn.
        """
        from entities.projectile import Projectile
        dx, dy = player.x - self.x, player.y - self.y
        dist   = math.hypot(dx, dy)
        if dist == 0:
            return
        self._facing   = 1 if dx >= 0 else -1
        base_angle     = math.atan2(dy, dx)
        speed          = ENEMY_PROJ_SPEED * speed_mult
        for spread in spreads:
            angle = base_angle + spread
            projectiles.append(Projectile(
                owner="boss", x=self.x, y=self.y,
                vx=math.cos(angle) * speed, vy=math.sin(angle) * speed,
                dmg=self.attack_dmg, max_range=self.attack_range + 100,
                radius=12, color=(220, 60, 255), use_fireball_sprite=True,
            ))

    def draw(self, surface: pygame.Surface, camera):
        """
        Vẽ Boss: dragon sprite quay hướng, vòng pulse, vòng windup, thanh máu, nhãn BOSS.

        Input:
            surface (pygame.Surface): Bề mặt màn hình.
            camera  (Camera)        : Chuyển tọa độ world sang screen.
        """
        sx, sy = camera.world_to_screen(self.x, self.y)

        # Màu aura theo map: water=xanh dương, fire=cam đỏ
        aura_color = (60, 160, 255) if self.map_type == "water" else COL_BOSS
        pulse_r   = self.radius + 6 + int(4 * math.sin(self._pulse))
        aura_surf = pygame.Surface((pulse_r * 2 + 4, pulse_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(aura_surf, (*aura_color, 60), (pulse_r + 2, pulse_r + 2), pulse_r)
        surface.blit(aura_surf, (int(sx) - pulse_r - 2, int(sy) - pulse_r - 2))

        # Vòng cảnh báo windup
        if self._windup_timer > 0:
            ratio     = self._windup_timer / BOSS_WINDUP_DURATION
            warn_r    = int(self.radius + 20 + 30 * ratio)
            w_alpha   = int(180 * (1 - ratio))
            w_surf    = pygame.Surface((warn_r * 2 + 4, warn_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(w_surf, (255, 60, 60, w_alpha),
                               (warn_r + 2, warn_r + 2), warn_r, 3)
            surface.blit(w_surf, (int(sx) - warn_r - 2, int(sy) - warn_r - 2))

        # Dragon sprite
        strip = _get_boss_sprites().get(self.map_type, [])
        if strip:
            frame = strip[self._frame_idx % len(strip)]
            if self._facing < 0:
                frame = pygame.transform.flip(frame, True, False)
            fw, fh = frame.get_size()
            surface.blit(frame, (int(sx) - fw // 2, int(sy) - fh // 2))
        else:
            color = COL_HIT_FLASH if self.hit_flash > 0 else self.color
            pygame.draw.circle(surface, color, (int(sx), int(sy)), self.radius)
            pygame.draw.circle(surface, (220, 100, 255), (int(sx), int(sy)), self.radius // 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), self.radius // 4)

        # Hit flash: vòng tròn trắng bán trong suốt đúng với hitbox, không đè lên sprite
        if self.hit_flash > 0:
            alpha   = int(180 * (self.hit_flash / 0.15))   # mờ dần theo thời gian
            flash_r = self.radius                           # = 120, khớp hitbox
            f_surf  = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(f_surf, (255, 255, 255, alpha),
                               (flash_r, flash_r), flash_r)
            surface.blit(f_surf, (int(sx) - flash_r, int(sy) - flash_r))

        # Thanh máu + nhãn
        bar_w     = self.radius * 2 + 20
        bar_h     = 7
        bx        = int(sx) - bar_w // 2
        by        = int(sy) - self.radius - 14
        bar_color = (60, 200, 255) if self.map_type == "water" else (220, 100, 255)
        lbl_color = (180, 230, 255) if self.map_type == "water" else (255, 200, 255)
        pygame.draw.rect(surface, COL_HP_BAR_BG,  (bx, by, bar_w, bar_h))
        fill = int(bar_w * self.hp / self.max_hp)
        pygame.draw.rect(surface, COL_BOSS_HP_FG, (bx, by, fill, bar_h))
        pygame.draw.rect(surface, bar_color, (bx, by, bar_w, bar_h), 1)

        font = pygame.font.SysFont("monospace", 11, bold=True)
        lbl  = font.render("BOSS", True, lbl_color)
        surface.blit(lbl, (int(sx) - lbl.get_width() // 2, by - 14))

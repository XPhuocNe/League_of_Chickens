"""
Quái thường với hai kiểu hành vi tấn công khác nhau.

Type 1 bắn đạn thẳng có tính toán dự đoán vị trí người chơi.
Khi PlayerTracker cung cấp đủ dữ liệu, Type 1 nâng cấp lên
bắn đón hướng né quen thuộc của player (behavior modeling).
Type 2 đặt vùng nổ AoE trễ gần vị trí người chơi.
Cả hai loại không di chuyển — đứng yên và tấn công theo cooldown.
"""
import math, random, pygame
from constants import *


def _crop_alpha(surface: pygame.Surface) -> pygame.Surface:
    """
    Cắt bỏ vùng trong suốt xung quanh, trả về bounding box thực của sprite.

    Input:
        surface (pygame.Surface): Surface cần crop.
    Output:
        pygame.Surface: Surface đã crop, hoặc surface gốc nếu lỗi.
    """
    try:
        import numpy as np
        alp = pygame.surfarray.pixels_alpha(surface)   # shape (w, h)
        cols = np.any(alp > 10, axis=1)  # cột (x) có pixel không trong suốt
        rows = np.any(alp > 10, axis=0)  # hàng (y) có pixel không trong suốt
        del alp
        if not cols.any() or not rows.any():
            return surface
        x0, x1 = int(cols.argmax()), int(len(cols) - cols[::-1].argmax() - 1)
        y0, y1 = int(rows.argmax()), int(len(rows) - rows[::-1].argmax() - 1)
        w = max(1, x1 - x0 + 1)
        h = max(1, y1 - y0 + 1)
        return surface.subsurface((x0, y0, w, h)).copy()
    except Exception:
        return surface


def _load_strip(path: str, n_frames: int, target_h: int) -> list:
    """
    Cắt spritesheet nằm ngang thành danh sách Surface, crop alpha rồi scale về target_h.

    Input:
        path     (str): Đường dẫn file spritesheet.
        n_frames (int): Số frame đều nhau theo chiều ngang.
        target_h (int): Chiều cao đích sau khi scale.
    Output:
        list[pygame.Surface]: Danh sách frame đã scale, rỗng nếu lỗi.
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
            frame = _crop_alpha(frame)          # crop bounding box thực
            cw, ch = frame.get_size()
            scale = target_h / ch
            nw = max(1, int(cw * scale))
            frames.append(pygame.transform.scale(frame, (nw, target_h)))
        return frames
    except Exception:
        return []


def _load_single(path: str, target_h: int):
    """
    Tải ảnh đơn, crop alpha bounding box, rồi scale về target_h.

    Input:
        path     (str): Đường dẫn file ảnh.
        target_h (int): Chiều cao đích.
    Output:
        pygame.Surface | None: Surface đã scale, None nếu lỗi.
    """
    try:
        import numpy as np
        img = pygame.image.load(path).convert_alpha()
        bg = img.get_at((0, 0))
        arr = pygame.surfarray.pixels3d(img)
        alp = pygame.surfarray.pixels_alpha(img)
        mask = (
            (np.abs(arr[:, :, 0].astype(int) - bg.r) <= 15) &
            (np.abs(arr[:, :, 1].astype(int) - bg.g) <= 15) &
            (np.abs(arr[:, :, 2].astype(int) - bg.b) <= 15)
        )
        alp[mask] = 0
        del arr, alp
        img = _crop_alpha(img)                  # crop bounding box thực
        w, h = img.get_size()
        nw = max(1, int(w * target_h / h))
        return pygame.transform.scale(img, (nw, target_h))
    except Exception:
        return None


_SPRITE_CACHE: dict = {}


def _get_sprites() -> dict:
    """
    Trả về dict sprite đã load (lazy-load lần đầu).

    Output:
        dict: Chứa các key 'blue_idle', 'blue_atk', 'red_idle', 'red_atk', ...
    """
    global _SPRITE_CACHE
    if _SPRITE_CACHE:
        return _SPRITE_CACHE
    BASE = "src/assets/"
    # Idle và attack dùng cùng target_h sau khi đã crop → kích cỡ đồng nhất
    _H_RANGED  = 52
    _H_SIEGE   = 56
    _SPRITE_CACHE = {
        "blue_idle":       _load_single(BASE + "idle_blue_ranged_minion.png",   _H_RANGED),
        "blue_atk":        _load_strip (BASE + "attack_blue_ranged_minion.png", 12, _H_RANGED),
        "red_idle":        _load_single(BASE + "idle_red_ranged_minion.png",    _H_RANGED),
        "red_atk":         _load_strip (BASE + "attack_red_ranged_minion.png",  12, _H_RANGED),
        "siege_blue_idle": _load_single(BASE + "idle_blue_siege_minion.png",    _H_SIEGE),
        "siege_blue_atk":  _load_strip (BASE + "attack_blue_siege_minion.png",  11, _H_SIEGE),
        "siege_red_idle":  _load_single(BASE + "idle_red_siege.png",            _H_SIEGE),
        "siege_red_atk":   _load_strip (BASE + "red_siege_minion_attack.png",   11, _H_SIEGE),
    }
    return _SPRITE_CACHE


class Enemy:
    """Quái đứng yên, tự động tấn công khi player vào tầm, hiển thị sprite animation."""

    def __init__(self, x: float, y: float, etype: int = 1, map_type: str = "fire"):
        """
        Khởi tạo quái tại (x, y).

        Input:
            x        (float): Tọa độ X world space.
            y        (float): Tọa độ Y world space.
            etype    (int)  : 1 = ranged (bắn đạn), 2 = siege (AoE trễ).
            map_type (str)  : 'fire' hoặc 'water' — xác định phe màu sắc sprite.
        """
        self.x      = float(x)
        self.y      = float(y)
        self.hp     = ENEMY_HP
        self.max_hp = ENEMY_HP
        self.radius = ENEMY_RADIUS
        self.etype  = etype
        self.alive  = True

        self.attack_range  = R
        self.attack_dmg    = 1
        self._cooldown_max = ENEMY_ATTACK_COOLDOWN
        self._timer        = random.uniform(0.3, ENEMY_ATTACK_COOLDOWN)

        self.hit_flash = 0.0
        self.color     = COL_ENEMY1 if etype == 1 else COL_ENEMY2

        self._facing          = 1
        self._anim_timer      = 0.0
        self._anim_fps        = 10.0
        self._frame_idx       = 0
        self._is_attacking    = False
        self._atk_frames_done = 0
        self._side            = "blue" if map_type == "water" else "red"

    def take_damage(self, dmg: int):
        """
        Trừ máu, bật flash trắng, đánh dấu chết khi máu về 0.

        Input:
            dmg (int): Lượng sát thương.
        """
        self.hp -= dmg
        self.hit_flash = 0.12
        if self.hp <= 0:
            self.hp = 0
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

    def _get_idle_key(self) -> str:
        return f"{self._side}_idle" if self.etype == 1 else f"siege_{self._side}_idle"

    def _get_atk_key(self) -> str:
        return f"{self._side}_atk" if self.etype == 1 else f"siege_{self._side}_atk"

    def update(self, dt: float, player, projectiles: list,
               delayed_attacks: list, tracker=None):
        """
        Cập nhật trạng thái mỗi frame: hướng quay, animation, cooldown, tấn công.

        Input:
            dt              (float): Thời gian trôi qua (giây).
            player          (Player): Đối tượng player.
            projectiles     (list) : Danh sách đạn.
            delayed_attacks (list) : Danh sách AoE trễ.
            tracker                : PlayerTracker tùy chọn.
        """
        if not self.alive:
            return
        if self.hit_flash > 0:
            self.hit_flash -= dt

        self._facing = -1 if player.x < self.x else 1

        self._anim_timer += dt
        if self._anim_timer >= 1.0 / self._anim_fps:
            self._anim_timer -= 1.0 / self._anim_fps
            self._frame_idx += 1
            if self._is_attacking:
                self._atk_frames_done += 1
                strip = _get_sprites().get(self._get_atk_key()) or []
                if self._atk_frames_done >= max(len(strip), 1):
                    self._is_attacking    = False
                    self._atk_frames_done = 0
                    self._frame_idx       = 0

        if not self.in_range(player.x, player.y):
            self._timer = min(self._timer + dt * 0.5, self._cooldown_max)
            return

        self._timer -= dt
        if self._timer > 0:
            return

        self._timer           = self._cooldown_max
        self._is_attacking    = True
        self._atk_frames_done = 0
        self._frame_idx       = 0
        self._fire(player, projectiles, delayed_attacks, tracker)

    def _fire(self, player, projectiles: list, delayed_attacks: list, tracker=None):
        """
        Thực hiện đòn tấn công theo etype.
        """
        from entities.projectile import Projectile, DelayedCircleAttack

        if self.etype == 1:
            dx   = player.x - self.x
            dy   = player.y - self.y
            dist = math.hypot(dx, dy)
            if dist == 0:
                return

            target_x, target_y = player.x, player.y

            if tracker is not None:
                profile = tracker.get_profile()
                if profile.reliable:
                    if profile.dodge_bias == "left":
                        target_x = player.x - 75
                    elif profile.dodge_bias == "right":
                        target_x = player.x + 75
                    if profile.is_aggressive:
                        target_y = player.y - 50
                else:
                    lead_t   = dist / ENEMY_PROJ_SPEED
                    target_x = player.x + ((player.target_x - player.x)
                                if player.target_x is not None else 0) * lead_t * 0.3
                    target_y = player.y + ((player.target_y - player.y)
                                if player.target_y is not None else 0) * lead_t * 0.3
            else:
                lead_t   = dist / ENEMY_PROJ_SPEED
                target_x = player.x + ((player.target_x - player.x)
                            if player.target_x is not None else 0) * lead_t * 0.3
                target_y = player.y + ((player.target_y - player.y)
                            if player.target_y is not None else 0) * lead_t * 0.3

            dx2 = target_x - self.x
            dy2 = target_y - self.y
            d2  = math.hypot(dx2, dy2) or dist
            self._facing = 1 if dx2 >= 0 else -1

            proj = Projectile(
                owner="enemy",
                x=self.x, y=self.y,
                vx=dx2 / d2 * ENEMY_PROJ_SPEED,
                vy=dy2 / d2 * ENEMY_PROJ_SPEED,
                dmg=self.attack_dmg,
                max_range=self.attack_range + 50,
                radius=7,
                color=COL_PROJ_ENEMY,
                use_fireball_sprite=True,
            )
            projectiles.append(proj)

        else:
            offset_r = 40
            tx = player.x + random.uniform(-offset_r, offset_r)
            ty = player.y + random.uniform(-offset_r, offset_r)
            self._facing = 1 if tx >= self.x else -1
            delayed_attacks.append(DelayedCircleAttack(
                owner="enemy", x=tx, y=ty,
                aoe_r=TYPE2_AOE_R, dmg=self.attack_dmg, delay=TYPE2_DELAY,
            ))

    def draw(self, surface: pygame.Surface, camera):
        """
        Vẽ quái: sprite animation quay theo hướng + thanh máu.

        Input:
            surface (pygame.Surface): Bề mặt màn hình.
            camera  (Camera)        : Chuyển tọa độ world sang screen.
        """
        sx, sy = camera.world_to_screen(self.x, self.y)
        sp = _get_sprites()

        if self._is_attacking:
            strip = sp.get(self._get_atk_key()) or []
            frame = strip[min(self._frame_idx, len(strip) - 1)] if strip else sp.get(self._get_idle_key())
        else:
            frame = sp.get(self._get_idle_key())

        if frame:
            if self._facing < 0:
                frame = pygame.transform.flip(frame, True, False)
            if self.hit_flash > 0:
                frame = frame.copy()
                white = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
                white.fill((255, 255, 255, 180))
                frame.blit(white, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            fw, fh = frame.get_size()
            surface.blit(frame, (int(sx) - fw // 2, int(sy) - fh // 2))
        else:
            color = COL_HIT_FLASH if self.hit_flash > 0 else self.color
            pygame.draw.circle(surface, color, (int(sx), int(sy)), self.radius)
            if self.etype == 2:
                pygame.draw.circle(surface, COL_WARN_CIRCLE,
                                   (int(sx), int(sy)), self.radius + 4, 2)

        bar_w = self.radius * 2
        bx    = int(sx) - self.radius
        by    = int(sy) - self.radius - 8
        pygame.draw.rect(surface, COL_HP_BAR_BG, (bx, by, bar_w, 4))
        fill = int(bar_w * self.hp / self.max_hp)
        pygame.draw.rect(surface, COL_HP_BAR_FG, (bx, by, fill, 4))

        font = pygame.font.SysFont("monospace", 10)
        lbl  = font.render(f"T{self.etype}", True, (200, 200, 200))
        surface.blit(lbl, (int(sx) - 8, int(sy) - 6))


def generate_enemy_cluster(world_y: float, score: int, map_type: str = "fire") -> list:
    """
    Tạo một đợt quái tại hàng world_y, số lượng và cooldown tăng theo điểm số.

    Input:
        world_y  (float): Tọa độ Y spawn.
        score    (int)  : Điểm số hiện tại.
        map_type (str)  : 'fire' hoặc 'water' — truyền xuống Enemy để chọn sprite đúng phe.
    Output:
        list[Enemy]: Danh sách quái vừa tạo.
    """
    enemies    = []
    difficulty = min(score / 700, 5.0)
    n_type1    = random.randint(1, 2 + int(difficulty))
    n_type2    = random.randint(0, 1 + int(difficulty * 0.6))
    positions  = _spread_positions(n_type1 + n_type2, MAP_WIDTH, ENEMY_RADIUS * 2)

    idx = 0
    for _ in range(n_type1):
        if idx >= len(positions):
            break
        e = Enemy(positions[idx], world_y + random.uniform(-60, 60), etype=1, map_type=map_type)
        e._cooldown_max = max(0.8, ENEMY_ATTACK_COOLDOWN - difficulty * 0.2)
        enemies.append(e)
        idx += 1

    for _ in range(n_type2):
        if idx >= len(positions):
            break
        e = Enemy(positions[idx], world_y + random.uniform(-60, 60), etype=2, map_type=map_type)
        e._cooldown_max = max(1.0, ENEMY_ATTACK_COOLDOWN - difficulty * 0.15)
        enemies.append(e)
        idx += 1

    return enemies


def _spread_positions(n: int, width: int, margin: int) -> list:
    """
    Chia đều n vị trí X trong chiều rộng bản đồ với nhiễu nhỏ.

    Input:
        n      (int): Số vị trí.
        width  (int): Chiều rộng bản đồ.
        margin (int): Khoảng cách tối thiểu từ biên.
    Output:
        list[float]: Danh sách tọa độ X đã xáo trộn.
    """
    if n == 0:
        return []
    margin = max(margin, ENEMY_RADIUS * 2)
    usable = width - margin * 2
    step   = usable / max(n, 1)
    result = [
        max(margin, min(width - margin,
            margin + step * i + step * 0.5 + random.uniform(-step * 0.25, step * 0.25)))
        for i in range(n)
    ]
    random.shuffle(result)
    return result
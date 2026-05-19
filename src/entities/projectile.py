<<<<<<< HEAD
"""
Định nghĩa các lớp đạn và đòn tấn công trễ trong game.

Projectile là đạn bay thẳng theo vận tốc cố định, tự hủy khi đi quá tầm
hoặc ra khỏi biên bản đồ. DelayedCircleAttack là vùng nổ AoE được kích hoạt
sau một khoảng trễ — trong thời gian chờ có hiệu ứng cảnh báo vòng tròn co dần,
khi nổ có hiệu ứng flash cam đỏ tắt nhanh.

Cập nhật lần cuối: 23:17 ngày 28/04/2026
"""
import math, pygame
from constants import *

_PROJ_SPRITE_CACHE: dict = {}


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
        fw     = sw // n_frames
        frames = []
        for i in range(n_frames):
            frame = sheet.subsurface((i * fw, 0, fw, sh)).copy()
            scale = target_h / sh
            nw    = max(1, int(fw * scale))
            frames.append(pygame.transform.scale(frame, (nw, target_h)))
        return frames
    except Exception:
        return []


def _load_strip_greenscreen(path: str, n_frames: int, target_h: int) -> list:
    try:
        import numpy as np
        sheet = pygame.image.load(path).convert_alpha()
        arr = pygame.surfarray.pixels3d(sheet)
        alp = pygame.surfarray.pixels_alpha(sheet)
        arr_f = arr.astype(float)
        ratio = arr_f[:, :, 1] / (arr_f[:, :, 0] + arr_f[:, :, 2] + 1)
        alp[ratio > 1.5] = 0
        del arr, alp, arr_f, ratio
        sw, sh = sheet.get_size()
        fw = sw // n_frames
        frames = []
        for i in range(n_frames):
            frame = sheet.subsurface((i * fw, 0, fw, sh)).copy()
            scale = target_h / sh
            nw = max(1, int(fw * scale))
            frames.append(pygame.transform.scale(frame, (nw, target_h)))
        return frames
    except Exception:
        return []


def _get_proj_sprites() -> dict:
    global _PROJ_SPRITE_CACHE
    if _PROJ_SPRITE_CACHE:
        return _PROJ_SPRITE_CACHE
    BASE = "src/assets/"
    fire_arr   = [pygame.transform.flip(f, True, False)
                  for f in _load_strip(BASE + "Fire_Arrow.png",  8, 42)]
    water_arr  = [pygame.transform.flip(f, True, False)
                  for f in _load_strip(BASE + "Water_Arrow.png", 8, 40)]
    _PROJ_SPRITE_CACHE = {
        "fireball":        _load_strip(BASE + "fire_ball.png",            9,  22),
        "explosion":       _load_strip(BASE + "explosion.png",            8,  48),
        "fire_arrow":      fire_arr,
        "water_arrow":     water_arr,
        "fire_explosion":  _load_strip(BASE + "fire_explosion.png",       8,  87),
        "water_explosion": _load_strip_greenscreen(BASE + "water_explosion.png", 5, 112),
    }
    return _PROJ_SPRITE_CACHE


class Projectile:
    """
    Quản lý trạng thái và hiển thị của viên đạn bay thẳng.
    """

    def __init__(self, owner: str, x: float, y: float,
                 vx: float, vy: float, dmg: int,
                 max_range: float, radius: int = 6,
                 color: tuple = COL_PROJ_ENEMY,
                 sprite_name: str = "fireball",
                 use_fireball_sprite: bool = True): # <-- THÊM THAM SỐ NÀY Ở ĐÂY
        self.owner          = owner
        self.x              = float(x)
        self.y              = float(y)
        self.vx             = vx
        self.vy             = vy
        self.dmg            = dmg
        self.radius         = radius
        self.color          = color
        self.max_range      = max_range
        self.sprite_name    = sprite_name
        self._origin_x      = x
        self._origin_y      = y
        self.alive          = True
        self._trail: list   = []
        self._anim_timer    = 0.0
        self._frame_idx     = 0
        self._anim_fps      = 12.0
        self._angle_deg     = math.degrees(math.atan2(vy, vx))
    def update(self, dt: float):
        """
        Di chuyển đạn, tiến frame animation và kiểm tra điều kiện tự hủy.

        Input:
            dt (float): Thời gian trôi qua (giây).
        """
        self._trail.append((self.x, self.y))
        if len(self._trail) > 5:
            self._trail.pop(0)

        self.x += self.vx * dt
        self.y += self.vy * dt

        # Tiến frame animation sprite
        self._anim_timer += dt
        if self._anim_timer >= 1.0 / self._anim_fps:
            self._anim_timer -= 1.0 / self._anim_fps
            sp = _get_proj_sprites()
            strip = sp.get(self.sprite_name, [])
            if strip:
                self._frame_idx = (self._frame_idx + 1) % len(strip)

        dist = math.hypot(self.x - self._origin_x, self.y - self._origin_y)
        if dist >= self.max_range:
            self.alive = False
        if self.x < -200 or self.x > MAP_WIDTH + 200:
            self.alive = False

    def hits(self, entity_x: float, entity_y: float, entity_r: float) -> bool:
        """
        Kiểm tra đạn có chạm vào hình tròn của thực thể mục tiêu không.

        Input:
            entity_x (float): Tọa độ X tâm mục tiêu.
            entity_y (float): Tọa độ Y tâm mục tiêu.
            entity_r (float): Bán kính mục tiêu.
        Output:
            bool: True nếu giao nhau.
        """
        return math.hypot(self.x - entity_x, self.y - entity_y) < (self.radius + entity_r)

    def draw(self, surface: pygame.Surface, camera):
        """
        Vẽ đạn: sprite xoay theo hướng bay, hoặc fallback vệt đuôi + hình tròn.

        Input:
            surface (pygame.Surface): Bề mặt màn hình.
            camera  (Camera)        : Chuyển tọa độ world sang screen.
        """
        sx, sy = camera.world_to_screen(self.x, self.y)

        sp    = _get_proj_sprites()
        strip = sp.get(self.sprite_name, [])
        if strip:
            frame = strip[self._frame_idx % len(strip)]
            # Xoay theo hướng bay
            rotated = pygame.transform.rotate(frame, -self._angle_deg)
            rw, rh  = rotated.get_size()
            surface.blit(rotated, (int(sx) - rw // 2, int(sy) - rh // 2))
            return

        # Fallback: vệt đuôi + hình tròn
        for i, (tx, ty) in enumerate(self._trail):
            alpha = int(60 * (i + 1) / len(self._trail))
            tsx, tsy = camera.world_to_screen(tx, ty)
            trail_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color, alpha),
                               (self.radius, self.radius), max(1, self.radius - 2))
            surface.blit(trail_surf, (int(tsx) - self.radius, int(tsy) - self.radius))

        pygame.draw.circle(surface, self.color, (int(sx), int(sy)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), max(1, self.radius - 3))


class DelayedCircleAttack:
    """
    Quản lý vùng nổ AoE được kích hoạt sau khoảng trễ, hiển thị sprite explosion phù hợp.

    Trong giai đoạn chờ: vòng cảnh báo vàng mở rộng dần.
    Khi nổ: sprite explosion chạy full animation rồi tự hủy.
    """

    def __init__(self, owner: str, x: float, y: float,
                 aoe_r: float, dmg: int, delay: float = TYPE2_DELAY,
                 explosion_type: str = "explosion"):
        """
        Khởi tạo vùng nổ trễ.

        Input:
            owner           (str)  : 'enemy' hoặc 'boss'.
            x, y            (float): Tọa độ tâm nổ trong world space.
            aoe_r           (float): Bán kính vùng sát thương.
            dmg             (int)  : Sát thương gây ra khi nổ.
            delay           (float): Thời gian chờ (giây) trước khi nổ.
            explosion_type  (str)  : Loại explosion sprite ('explosion' hoặc 'water_explosion').
        """
        self.owner          = owner
        self.x              = float(x)
        self.y              = float(y)
        self.aoe_r          = aoe_r
        self.dmg            = dmg
        self.delay          = delay
        self._timer         = delay
        self.triggered      = False
        self.alive          = True
        self._expand        = 0.0
        self.explosion_type = explosion_type

        # Animation explosion sau khi nổ
        self._exp_frame_idx   = 0
        self._exp_anim_timer  = 0.0
        self._exp_anim_fps    = 14.0
        self._exp_done        = False

    def update(self, dt: float):
        """
        Đếm ngược thời gian trễ, chuyển sang triggered và chạy animation explosion.

        Input:
            dt (float): Thời gian trôi qua (giây).
        """
        if self.triggered:
            # Chạy animation explosion
            self._exp_anim_timer += dt
            if self._exp_anim_timer >= 1.0 / self._exp_anim_fps:
                self._exp_anim_timer -= 1.0 / self._exp_anim_fps
                self._exp_frame_idx += 1
                sp    = _get_proj_sprites()
                strip = sp.get(self.explosion_type, [])
                if self._exp_frame_idx >= max(len(strip), 1):
                    self._exp_done = True
                    self.alive     = False
            return

        self._timer  -= dt
        self._expand  = 1 - (self._timer / self.delay)
        if self._timer <= 0:
            self.triggered      = True
            self._timer         = 0
            self._exp_frame_idx = 0

    def hits(self, entity_x: float, entity_y: float, entity_r: float) -> bool:
        """
        Kiểm tra vùng nổ có chạm vào thực thể sau khi đã triggered không.

        Input:
            entity_x (float): Tọa độ X tâm mục tiêu.
            entity_y (float): Tọa độ Y tâm mục tiêu.
            entity_r (float): Bán kính mục tiêu.
        Output:
            bool: True khi triggered và mục tiêu nằm trong aoe_r.
        """
        if not self.triggered:
            return False
        return math.hypot(self.x - entity_x, self.y - entity_y) < (self.aoe_r + entity_r)

    def draw(self, surface: pygame.Surface, camera):
        """
        Vẽ AoE: vòng cảnh báo vàng khi chờ, sprite explosion khi nổ.

        Input:
            surface (pygame.Surface): Bề mặt màn hình.
            camera  (Camera)        : Chuyển tọa độ world sang screen.
        """
        sx, sy = camera.world_to_screen(self.x, self.y)
        r      = int(self.aoe_r)

        if not self.triggered:
            progress   = self._expand
            ring_alpha = int(80 + 140 * progress)
            inner_r    = max(1, int(r * progress))

            warn_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(warn_surf, (*COL_WARN_CIRCLE, 40), (r + 2, r + 2), r)
            pygame.draw.circle(warn_surf, (*COL_WARN_CIRCLE, ring_alpha), (r + 2, r + 2), inner_r, 3)
            surface.blit(warn_surf, (int(sx) - r - 2, int(sy) - r - 2))

        else:
            sp    = _get_proj_sprites()
            strip = sp.get(self.explosion_type, [])
            if strip and self._exp_frame_idx < len(strip):
                frame  = strip[self._exp_frame_idx]
                # Scale explosion lên bằng aoe_r
                target = max(1, r * 2)
                scaled = pygame.transform.scale(frame, (target, target))
                surface.blit(scaled, (int(sx) - target // 2, int(sy) - target // 2))
            else:
                # Fallback flash
                flash_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (255, 120, 30, 160), (r + 2, r + 2), r)
                surface.blit(flash_surf, (int(sx) - r - 2, int(sy) - r - 2))


class LaserBeam:
    """
    Tia laser bay thẳng — dùng cho pattern lux_beam của Boss.

    Giai đoạn charge (delay): vẽ đường cảnh báo mảnh dọc theo hướng bay.
    Giai đoạn active: vẽ beam đậm phát sáng, gây sát thương liên tục cho player
    nếu player nằm trong vùng quét.
    Tự hủy sau khi active_duration kết thúc.
    """

    def __init__(self, owner: str, x: float, y: float,
                 angle_rad: float, length: float, width: int,
                 dmg: int, delay: float, active_duration: float,
                 color: tuple = (200, 80, 255)):
        """
        Khởi tạo tia laser.

        Input:
            owner           (str)  : 'boss' hoặc 'enemy'.
            x, y            (float): Gốc phát laser (world space).
            angle_rad       (float): Góc bay (radian, 0 = sang phải).
            length          (float): Chiều dài tia.
            width           (int)  : Bề rộng tia khi active.
            dmg             (int)  : Sát thương gây ra khi active.
            delay           (float): Thời gian charge trước khi active.
            active_duration (float): Thời gian tia tồn tại sau khi active.
            color           (tuple): Màu tia.
        """
        self.owner           = owner
        self.x               = float(x)
        self.y               = float(y)
        self.angle_rad       = angle_rad
        self.length          = length
        self.width           = width
        self.dmg             = dmg
        self.delay           = delay
        self.active_duration = active_duration
        self.color           = color

        self._timer    = delay
        self.active    = False
        self.alive     = True
        self._hit_done = False   # chỉ gây dmg 1 lần mỗi lần active

        self.end_x = x + math.cos(angle_rad) * length
        self.end_y = y + math.sin(angle_rad) * length

    def update(self, dt: float):
        """
        Đếm ngược charge → active → hủy.

        Input:
            dt (float): Thời gian trôi qua (giây).
        """
        if not self.active:
            self._timer -= dt
            if self._timer <= 0:
                self.active    = True
                self._timer    = self.active_duration
                self._hit_done = False
        else:
            self._timer -= dt
            if self._timer <= 0:
                self.alive = False

    def hits(self, entity_x: float, entity_y: float, entity_r: float) -> bool:
        """
        Kiểm tra điểm (entity_x, entity_y) có nằm trong vùng quét beam không.
        Dùng khoảng cách từ điểm tới đoạn thẳng.

        Input:
            entity_x (float): Tọa độ X tâm mục tiêu.
            entity_y (float): Tọa độ Y tâm mục tiêu.
            entity_r (float): Bán kính mục tiêu.
        Output:
            bool: True khi active và mục tiêu cắt qua beam.
        """
        if not self.active or self._hit_done:
            return False
        # Chiếu điểm lên đoạn thẳng, tính khoảng cách vuông góc
        lx, ly = self.end_x - self.x, self.end_y - self.y
        seg_len = math.hypot(lx, ly)
        if seg_len == 0:
            return False
        t = max(0.0, min(1.0, ((entity_x - self.x) * lx + (entity_y - self.y) * ly) / (seg_len ** 2)))
        nearest_x = self.x + t * lx
        nearest_y = self.y + t * ly
        dist = math.hypot(entity_x - nearest_x, entity_y - nearest_y)
        if dist < self.width // 2 + entity_r:
            self._hit_done = True
            return True
        return False

    def draw(self, surface: pygame.Surface, camera):
        """
        Vẽ laser: đường cảnh báo mảnh khi charge, beam sáng khi active.

        Input:
            surface (pygame.Surface): Bề mặt màn hình.
            camera  (Camera)        : Chuyển tọa độ world sang screen.
        """
        sx0, sy0 = camera.world_to_screen(self.x, self.y)
        sx1, sy1 = camera.world_to_screen(self.end_x, self.end_y)

        if not self.active:
            # Cảnh báo: đường mảnh nhấp nháy
            progress = 1.0 - (self._timer / self.delay)
            alpha    = int(60 + 150 * progress)
            warn_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            pygame.draw.line(warn_surf, (*self.color, alpha), (sx0, sy0), (sx1, sy1), 2)
            surface.blit(warn_surf, (0, 0))
        else:
            # Active: beam lõi trắng + viền màu + glow ngoài
            ratio  = self._timer / self.active_duration
            w_core = max(2, self.width // 3)
            w_glow = self.width + int(8 * ratio)

            glow_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            glow_alpha = int(80 * ratio)
            pygame.draw.line(glow_surf, (*self.color, glow_alpha),
                             (sx0, sy0), (sx1, sy1), w_glow)
            surface.blit(glow_surf, (0, 0))

            pygame.draw.line(surface, self.color, (sx0, sy0), (sx1, sy1), self.width)
            pygame.draw.line(surface, (255, 255, 255), (sx0, sy0), (sx1, sy1), w_core)
=======
"""
Định nghĩa các lớp đạn và đòn tấn công trễ trong game.

Projectile là đạn bay thẳng theo vận tốc cố định, tự hủy khi đi quá tầm
hoặc ra khỏi biên bản đồ. DelayedCircleAttack là vùng nổ AoE được kích hoạt
sau một khoảng trễ — trong thời gian chờ có hiệu ứng cảnh báo vòng tròn co dần,
khi nổ có hiệu ứng flash cam đỏ tắt nhanh.

Cập nhật lần cuối: 23:17 ngày 28/04/2026
"""
import math, pygame
from constants import *

_PROJ_SPRITE_CACHE: dict = {}


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
        fw     = sw // n_frames
        frames = []
        for i in range(n_frames):
            frame = sheet.subsurface((i * fw, 0, fw, sh)).copy()
            scale = target_h / sh
            nw    = max(1, int(fw * scale))
            frames.append(pygame.transform.scale(frame, (nw, target_h)))
        return frames
    except Exception:
        return []


def _get_proj_sprites() -> dict:
    """
    Trả về dict sprite đạn/nổ đã load (lazy-load lần đầu).

    Output:
        dict: key 'fireball' (list frame), 'explosion' (list frame).
    """
    global _PROJ_SPRITE_CACHE
    if _PROJ_SPRITE_CACHE:
        return _PROJ_SPRITE_CACHE
    BASE = "src/assets/"
    _PROJ_SPRITE_CACHE = {
        "fireball":  _load_strip(BASE + "fire_ball.png",  9, 22),
        "explosion": _load_strip(BASE + "explosion.png",  8, 48),
    }
    return _PROJ_SPRITE_CACHE


class Projectile:
    """
    Quản lý trạng thái và hiển thị của viên đạn bay thẳng.

    Dùng sprite fire_ball quay theo góc bay khi use_fireball_sprite=True,
    fallback về hình tròn + vệt đuôi nếu sprite không load được.
    """

    def __init__(self, owner: str, x: float, y: float,
                 vx: float, vy: float, dmg: int,
                 max_range: float, radius: int = 6,
                 color: tuple = COL_PROJ_ENEMY,
                 use_fireball_sprite: bool = False):
        """
        Khởi tạo đạn.

        Input:
            owner               (str)  : 'player', 'enemy' hoặc 'boss'.
            x, y                (float): Vị trí xuất phát.
            vx, vy              (float): Vận tốc.
            dmg                 (int)  : Sát thương.
            max_range           (float): Khoảng cách tối đa trước khi tự hủy.
            radius              (int)  : Bán kính va chạm và vẽ fallback.
            color               (tuple): Màu fallback.
            use_fireball_sprite (bool) : True = dùng sprite fire_ball.
        """
        self.owner              = owner
        self.x                  = float(x)
        self.y                  = float(y)
        self.vx                 = vx
        self.vy                 = vy
        self.dmg                = dmg
        self.radius             = radius
        self.color              = color
        self.max_range          = max_range
        self.use_fireball_sprite = use_fireball_sprite
        self._origin_x          = x
        self._origin_y          = y
        self.alive              = True
        self._trail: list       = []
        self._anim_timer        = 0.0
        self._frame_idx         = 0
        self._anim_fps          = 12.0
        # Góc bay (radian) để xoay sprite
        self._angle_deg         = math.degrees(math.atan2(vy, vx))

    def update(self, dt: float):
        """
        Di chuyển đạn, tiến frame animation và kiểm tra điều kiện tự hủy.

        Input:
            dt (float): Thời gian trôi qua (giây).
        """
        self._trail.append((self.x, self.y))
        if len(self._trail) > 5:
            self._trail.pop(0)

        self.x += self.vx * dt
        self.y += self.vy * dt

        # Tiến frame animation fireball
        self._anim_timer += dt
        if self._anim_timer >= 1.0 / self._anim_fps:
            self._anim_timer -= 1.0 / self._anim_fps
            sp = _get_proj_sprites()
            strip = sp.get("fireball", [])
            if strip:
                self._frame_idx = (self._frame_idx + 1) % len(strip)

        dist = math.hypot(self.x - self._origin_x, self.y - self._origin_y)
        if dist >= self.max_range:
            self.alive = False
        if self.x < -200 or self.x > MAP_WIDTH + 200:
            self.alive = False

    def hits(self, entity_x: float, entity_y: float, entity_r: float) -> bool:
        """
        Kiểm tra đạn có chạm vào hình tròn của thực thể mục tiêu không.

        Input:
            entity_x (float): Tọa độ X tâm mục tiêu.
            entity_y (float): Tọa độ Y tâm mục tiêu.
            entity_r (float): Bán kính mục tiêu.
        Output:
            bool: True nếu giao nhau.
        """
        return math.hypot(self.x - entity_x, self.y - entity_y) < (self.radius + entity_r)

    def draw(self, surface: pygame.Surface, camera):
        """
        Vẽ đạn: sprite fire_ball xoay theo hướng bay, hoặc fallback vệt đuôi + hình tròn.

        Input:
            surface (pygame.Surface): Bề mặt màn hình.
            camera  (Camera)        : Chuyển tọa độ world sang screen.
        """
        sx, sy = camera.world_to_screen(self.x, self.y)

        if self.use_fireball_sprite:
            sp    = _get_proj_sprites()
            strip = sp.get("fireball", [])
            if strip:
                frame = strip[self._frame_idx % len(strip)]
                # Xoay theo hướng bay
                rotated = pygame.transform.rotate(frame, -self._angle_deg)
                rw, rh  = rotated.get_size()
                surface.blit(rotated, (int(sx) - rw // 2, int(sy) - rh // 2))
                return

        # Fallback: vệt đuôi + hình tròn
        for i, (tx, ty) in enumerate(self._trail):
            alpha = int(60 * (i + 1) / len(self._trail))
            tsx, tsy = camera.world_to_screen(tx, ty)
            trail_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (*self.color, alpha),
                               (self.radius, self.radius), max(1, self.radius - 2))
            surface.blit(trail_surf, (int(tsx) - self.radius, int(tsy) - self.radius))

        pygame.draw.circle(surface, self.color, (int(sx), int(sy)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), max(1, self.radius - 3))


class DelayedCircleAttack:
    """
    Quản lý vùng nổ AoE được kích hoạt sau khoảng trễ, hiển thị sprite explosion khi nổ.

    Trong giai đoạn chờ: vòng cảnh báo vàng mở rộng dần.
    Khi nổ: sprite explosion chạy full animation rồi tự hủy.
    """

    def __init__(self, owner: str, x: float, y: float,
                 aoe_r: float, dmg: int, delay: float = TYPE2_DELAY):
        """
        Khởi tạo vùng nổ trễ.

        Input:
            owner  (str)  : 'enemy' hoặc 'boss'.
            x, y   (float): Tọa độ tâm nổ trong world space.
            aoe_r  (float): Bán kính vùng sát thương.
            dmg    (int)  : Sát thương gây ra khi nổ.
            delay  (float): Thời gian chờ (giây) trước khi nổ.
        """
        self.owner     = owner
        self.x         = float(x)
        self.y         = float(y)
        self.aoe_r     = aoe_r
        self.dmg       = dmg
        self.delay     = delay
        self._timer    = delay
        self.triggered = False
        self.alive     = True
        self._expand   = 0.0

        # Animation explosion sau khi nổ
        self._exp_frame_idx   = 0
        self._exp_anim_timer  = 0.0
        self._exp_anim_fps    = 14.0
        self._exp_done        = False

    def update(self, dt: float):
        """
        Đếm ngược thời gian trễ, chuyển sang triggered và chạy animation explosion.

        Input:
            dt (float): Thời gian trôi qua (giây).
        """
        if self.triggered:
            # Chạy animation explosion
            self._exp_anim_timer += dt
            if self._exp_anim_timer >= 1.0 / self._exp_anim_fps:
                self._exp_anim_timer -= 1.0 / self._exp_anim_fps
                self._exp_frame_idx += 1
                sp    = _get_proj_sprites()
                strip = sp.get("explosion", [])
                if self._exp_frame_idx >= max(len(strip), 1):
                    self._exp_done = True
                    self.alive     = False
            return

        self._timer  -= dt
        self._expand  = 1 - (self._timer / self.delay)
        if self._timer <= 0:
            self.triggered      = True
            self._timer         = 0
            self._exp_frame_idx = 0

    def hits(self, entity_x: float, entity_y: float, entity_r: float) -> bool:
        """
        Kiểm tra vùng nổ có chạm vào thực thể sau khi đã triggered không.

        Input:
            entity_x (float): Tọa độ X tâm mục tiêu.
            entity_y (float): Tọa độ Y tâm mục tiêu.
            entity_r (float): Bán kính mục tiêu.
        Output:
            bool: True khi triggered và mục tiêu nằm trong aoe_r.
        """
        if not self.triggered:
            return False
        return math.hypot(self.x - entity_x, self.y - entity_y) < (self.aoe_r + entity_r)

    def draw(self, surface: pygame.Surface, camera):
        """
        Vẽ AoE: vòng cảnh báo vàng khi chờ, sprite explosion khi nổ.

        Input:
            surface (pygame.Surface): Bề mặt màn hình.
            camera  (Camera)        : Chuyển tọa độ world sang screen.
        """
        sx, sy = camera.world_to_screen(self.x, self.y)
        r      = int(self.aoe_r)

        if not self.triggered:
            progress   = self._expand
            ring_alpha = int(80 + 140 * progress)
            inner_r    = max(1, int(r * progress))

            warn_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(warn_surf, (*COL_WARN_CIRCLE, 40), (r + 2, r + 2), r)
            pygame.draw.circle(warn_surf, (*COL_WARN_CIRCLE, ring_alpha), (r + 2, r + 2), inner_r, 3)
            surface.blit(warn_surf, (int(sx) - r - 2, int(sy) - r - 2))

        else:
            sp    = _get_proj_sprites()
            strip = sp.get("explosion", [])
            if strip and self._exp_frame_idx < len(strip):
                frame  = strip[self._exp_frame_idx]
                # Scale explosion lên bằng aoe_r
                target = max(1, r * 2)
                scaled = pygame.transform.scale(frame, (target, target))
                surface.blit(scaled, (int(sx) - target // 2, int(sy) - target // 2))
            else:
                # Fallback flash
                flash_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(flash_surf, (255, 120, 30, 160), (r + 2, r + 2), r)
                surface.blit(flash_surf, (int(sx) - r - 2, int(sy) - r - 2))
>>>>>>> 7e7533b68f27d227fe69f1e1e6ff7aa2c15fffb9

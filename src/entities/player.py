"""
player.py – Quản lý nhân vật người chơi: trạng thái, di chuyển, tấn công, blink và buff.

Xử lý toàn bộ vòng đời của Player: nhận input di chuyển/tấn công từ GameManager,
thực thi cơ chế blink hai giai đoạn (pre-stun → teleport → post-stun),
windup trước khi bắn, giới hạn vùng di chuyển theo vạch start và biên bản đồ,
đồng bộ chỉ số từ BuffManager, và vẽ toàn bộ hiệu ứng lên màn hình.

Hệ thống sprite animation:
  - idle   : đứng yên (ilde_player_opt.png, 20 frames)
  - run    : đang di chuyển (run_player_opt.png, 16 frames)
  - attack : windup tấn công (attack_player_opt.png, 20 frames)
  - dead   : đang chết (dead_player_opt.png, 20 frames, chạy 1 lần)
  Sprite gốc hướng LÊN TRÊN — xoay theo hướng di chuyển/bắn thực tế.

Hiệu ứng chết:
  - dead_player animation chạy trong 3 giây
  - Màn hình xám dần đồng thời (0 → 200 alpha)

Last modified: 19/05/2026
"""
import math
import pygame
from constants import *

BLINK_PRE_STUN_DURATION  = 0.15
BLINK_POST_STUN_DURATION = 0.25

# ──────────────────────────────────────────────────────────────
#  Sprite loader
# ──────────────────────────────────────────────────────────────

_PLAYER_SPRITE_CACHE: dict = {}

# (path, n_frames, frame_w, frame_h, target_h)
# Sprite gốc hướng LÊN TRÊN (↑), đã remove blue screen.
_PLAYER_SPRITE_META = {
    # key: (path, n_frames, target_h)
    # n_frames=0 → tự detect bằng gap analysis (dùng cho run)
    # Dùng thẳng file gốc — runtime xử lý blue screen + căn chân
    "idle"  : ("src/assets/ilde_player.png",   20,  96),
    "run"   : ("src/assets/run_player.png",     0,  96),  # auto-detect frames
    "attack": ("src/assets/attack_player.png",  0,  96),  # auto-detect frames
    "dead"  : ("src/assets/dead_player.png",   20, 140),  # cao hơn vì nằm ngang
}

# FPS mỗi animation
_ANIM_FPS = {
    "idle"  : 12.0,
    "run"   : 12.0,
    "attack": 18.0,
    "dead"  : 8.0,
}


def _remove_bluescreen(arr: "np.ndarray") -> "np.ndarray":
    """
    Remove nền xanh dương (blue screen) bằng chroma key.
    B > 100 AND (B-R) > 80 AND (B-G) > 80 → alpha = 0.
    """
    import numpy as np
    r = arr[:, :, 0].astype(int)
    g = arr[:, :, 1].astype(int)
    b = arr[:, :, 2].astype(int)
    is_bg = (b > 100) & ((b - r) > 80) & ((b - g) > 80)
    arr[:, :, 3] = np.where(is_bg, 0, 255)
    return arr


def _detect_segments(arr: "np.ndarray") -> list:
    """
    Tìm các đoạn content liên tục theo chiều ngang (dùng cho sprite bị đặt thưa).
    Trả về list[(x_start, x_end)] của từng sprite.
    """
    import numpy as np
    col_has = (arr[:, :, 3] > 10).any(axis=0)
    segs, in_seg = [], False
    for x in range(len(col_has)):
        if col_has[x]:
            if not in_seg:
                in_seg, seg_start = True, x
        else:
            if in_seg:
                in_seg = False
                segs.append((seg_start, x - 1))
    if in_seg:
        segs.append((seg_start, len(col_has) - 1))
    return segs


def _make_frame_surface(content: "np.ndarray", canvas_w: int, canvas_h: int,
                         target_w: int, target_h: int) -> pygame.Surface:
    """
    Đặt content vào canvas cố định (căn giữa X, chân cố định đáy Y) rồi scale.
    """
    import numpy as np
    from PIL import Image as _PIL
    ch, cw = content.shape[:2]
    canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
    px = max(0, (canvas_w - cw) // 2)
    py = max(0, canvas_h - 4 - ch)
    px2 = min(px + cw, canvas_w)
    py2 = min(py + ch, canvas_h)
    canvas[py:py2, px:px2, :] = content[:py2 - py, :px2 - px, :]
    pil = _PIL.fromarray(canvas, 'RGBA')
    if target_w != canvas_w or target_h != canvas_h:
        pil = pil.resize((target_w, target_h), _PIL.LANCZOS)
    return pygame.image.fromstring(pil.tobytes(), pil.size, pil.mode).convert_alpha()


def _load_player_strip(path: str, n_frames: int, target_h: int) -> list:
    """
    Load spritesheet gốc, xử lý blue screen, căn chân, scale.

    n_frames=0 → tự detect số frame bằng gap analysis (cho sprite thưa như run).
    n_frames>0 → chia đều theo chiều rộng (cho sprite đặt đều như idle/dead).

    Input:
        path     (str): Đường dẫn ảnh gốc.
        n_frames (int): Số frame (0 = auto-detect).
        target_h (int): Chiều cao đích trên màn hình.
    Output:
        list[pygame.Surface]
    """
    import numpy as np
    try:
        from PIL import Image as _PIL
        img = _PIL.open(path).convert('RGBA')
        sw, sh = img.size
        arr = np.array(img)
        arr = _remove_bluescreen(arr)

        # ── Lấy danh sách content array từng frame ──────────────────────
        frame_arrays = []

        if n_frames == 0:
            # Auto-detect: tìm segment content thật sự
            segs = _detect_segments(arr)
            for x0, x1 in segs:
                ys, _ = np.where(arr[:, x0:x1+1, 3] > 10)
                if len(ys) == 0:
                    continue
                y0, y1 = int(ys.min()), int(ys.max())
                frame_arrays.append(arr[y0:y1+1, x0:x1+1, :].copy())
        else:
            # Chia đều theo n_frames
            fw = sw // n_frames
            for i in range(n_frames):
                fa = arr[:, i*fw:(i+1)*fw, :].copy()
                ys, xs = np.where(fa[:, :, 3] > 10)
                if len(xs) == 0:
                    frame_arrays.append(np.zeros((1, 1, 4), dtype=np.uint8))
                    continue
                x0, x1 = int(xs.min()), int(xs.max())
                y0, y1 = int(ys.min()), int(ys.max())
                frame_arrays.append(fa[y0:y1+1, x0:x1+1, :].copy())

        # Lọc bỏ frame trống (chỉ có 1x1 pixel) — tránh thừa frame rỗng
        frame_arrays = [f for f in frame_arrays if f.shape[0] > 1 or f.shape[1] > 1]

        if not frame_arrays:
            return []

        # ── Canvas chuẩn: max content size + padding ────────────────────
        max_cw = max(f.shape[1] for f in frame_arrays)
        max_ch = max(f.shape[0] for f in frame_arrays)
        pad_x  = 20
        pad_top = 10
        canvas_w = max_cw + pad_x * 2
        canvas_h = max_ch + pad_top + 4

        scale    = target_h / canvas_h
        target_w = max(1, int(canvas_w * scale))

        # ── Build surface list ───────────────────────────────────────────
        frames = []
        for fa in frame_arrays:
            surf = _make_frame_surface(fa, canvas_w, canvas_h, target_w, target_h)
            frames.append(surf)
        return frames

    except Exception as e:
        print(f"[Player sprite] load error {path}: {e}")
        return []


def _get_player_sprites() -> dict:
    """
    Lazy-load + cache sprite player. Gọi lần đầu sẽ load + xử lý tất cả.
    Các lần sau trả về cache ngay, không load lại.

    Output:
        dict[str, list[pygame.Surface]]
    """
    global _PLAYER_SPRITE_CACHE
    if _PLAYER_SPRITE_CACHE:
        return _PLAYER_SPRITE_CACHE
    for key, (path, n, th) in _PLAYER_SPRITE_META.items():
        _PLAYER_SPRITE_CACHE[key] = _load_player_strip(path, n, th)
    return _PLAYER_SPRITE_CACHE


# ──────────────────────────────────────────────────────────────
#  Player
# ──────────────────────────────────────────────────────────────

class Player:
    """Quản lý toàn bộ trạng thái và hành vi của nhân vật chính."""

    BASE_SPEED          = 200.0
    BASE_BLINK_COOLDOWN = 5.0

    # Thời gian màn hình xám dần khi chết (giây)
    DEATH_FADE_DURATION = 3.0

    def __init__(self, x: float, y: float):
        """
        Khởi tạo player tại vị trí (x, y).

        Input:
            x (float): Tọa độ X ban đầu trong world space.
            y (float): Tọa độ Y ban đầu trong world space — đây cũng là start_y, giới hạn dưới.
        """
        self.x   = float(x)
        self.y   = float(y)
        self.hp  = PLAYER_MAX_HP
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
        self._windup_timer  = 0.0
        self._pending_dx    = 0.0
        self._pending_dy    = 0.0
        self._pending_projs = None

        self.blink_range    = BLINK_RANGE
        self.blink_cooldown = self.BASE_BLINK_COOLDOWN
        self._blink_timer   = 0.0

        self._blink_pre_stun  = 0.0
        self._blink_post_stun = 0.0
        self._blink_dest_x: float | None = None
        self._blink_dest_y: float | None = None
        self._blink_obstacles: list = []

        self.hit_flash = 0.0
        self.blink_fx  = []
        self.alive     = True

        self.min_y_reached = y

        self.buff_fire_active = False
        self.buff_wind_active = False

        # ── Animation ───────────────────────────────────────────────────
        # Trạng thái animation hiện tại: "idle" | "run" | "attack" | "dead"
        self._anim_state  = "idle"
        self._anim_timer  = 0.0
        self._frame_idx   = 0
        self._dead_done   = False   # True sau khi dead animation chạy xong 1 lần

        # Hướng nhìn (radian): sprite gốc hướng lên (↑) = -π/2
        # Cập nhật khi di chuyển hoặc bắn. Mặc định hướng lên.
        self._facing_angle = -math.pi / 2

        # Đệm Surface cho gray overlay khi chết (tạo 1 lần)
        self._gray_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Timer màn hình xám khi chết
        self._death_fade_timer = 0.0

        # Warm-up sprite cache
        _get_player_sprites()

    # ────────────────────────────────────────────────────────────
    #  Buff
    # ────────────────────────────────────────────────────────────

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
        self.speed            = self.BASE_SPEED * (2.0 if wind else 1.0)
        self.blink_cooldown   = self.BASE_BLINK_COOLDOWN * (0.5 if wind else 1.0)

    # ────────────────────────────────────────────────────────────
    #  Properties
    # ────────────────────────────────────────────────────────────

    @property
    def blink_ready(self) -> bool:
        return self._blink_timer <= 0 and self._blink_pre_stun <= 0

    @property
    def attack_ready(self) -> bool:
        return self._attack_timer <= 0 and self._windup_timer <= 0

    def _is_frozen(self) -> bool:
        return self._windup_timer > 0 or self._blink_pre_stun > 0 or self._blink_post_stun > 0

    # ────────────────────────────────────────────────────────────
    #  Di chuyển & blink
    # ────────────────────────────────────────────────────────────

    def set_move_target(self, world_x: float, world_y: float):
        """
        Đặt điểm đến để player tự di chuyển tới. Bỏ qua nếu đang bị khựng.

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
        Khởi động cơ chế blink hai giai đoạn.

        Input:
            world_x   (float): Tọa độ X đích.
            world_y   (float): Tọa độ Y đích.
            obstacles (list) : Danh sách dict chướng ngại vật.
        Output:
            bool: True nếu kích hoạt thành công.
        """
        if not self.blink_ready or self._windup_timer > 0:
            return False

        dx   = world_x - self.x
        dy   = world_y - self.y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return False

        t_max  = min(1.0, self.blink_range / dist)
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

        self._blink_dest_x    = dest_x
        self._blink_dest_y    = dest_y
        self._blink_obstacles = obstacles
        self._blink_pre_stun  = BLINK_PRE_STUN_DURATION
        self._blink_timer     = self.blink_cooldown
        self.target_x         = None
        self.target_y         = None
        return True

    def _execute_blink(self):
        """Teleport ngay sau khi pre-stun kết thúc."""
        if self._blink_dest_x is None:
            return
        self.blink_fx.append([self.x, self.y, 1.0])
        self.x                = self._blink_dest_x
        self.y                = self._blink_dest_y
        self._blink_post_stun = BLINK_POST_STUN_DURATION
        self._blink_dest_x    = None
        self._blink_dest_y    = None
        self._blink_obstacles = []

    # ────────────────────────────────────────────────────────────
    #  Tấn công
    # ────────────────────────────────────────────────────────────

    def try_attack(self, direction_x: float, direction_y: float, projectiles: list):
        """
        Bắt đầu windup tấn công, cập nhật hướng nhìn.

        Input:
            direction_x (float): Hướng X bắn.
            direction_y (float): Hướng Y bắn.
            projectiles (list) : Danh sách đạn để thêm vào sau windup.
        """
        if not self.attack_ready:
            return
        dist = math.hypot(direction_x, direction_y)
        if dist == 0:
            return

        # Cập nhật hướng nhìn theo hướng bắn
        self._facing_angle = math.atan2(direction_y, direction_x)

        self.target_x       = None
        self.target_y       = None
        self._pending_dx    = direction_x
        self._pending_dy    = direction_y
        self._pending_projs = projectiles
        self._windup_timer  = self.attack_windup

        # Chuyển sang animation attack, reset frame
        self._set_anim("attack")

    def _execute_attack(self):
        """Tạo đạn sau khi windup hoàn tất."""
        from entities.projectile import Projectile

        base_angle = math.atan2(self._pending_dy, self._pending_dx)
        spreads    = [-0.22, 0.0, 0.22] if self.buff_fire_active else [0.0]

        for spread in spreads:
            angle = base_angle + spread
            proj  = Projectile(
                owner="player",
                x=self.x, y=self.y,
                vx=math.cos(angle) * PROJECTILE_SPEED,
                vy=math.sin(angle) * PROJECTILE_SPEED,
                dmg=self.attack_dmg,
                max_range=self.attack_range,
                radius=6,
                color=COL_PROJ_PLAYER,
                sprite_name="fire_arrow",   # đạn player luôn dùng fire_arrow
            )
            self._pending_projs.append(proj)

        self._attack_timer  = self.attack_cooldown
        self._pending_projs = None

    # ────────────────────────────────────────────────────────────
    #  Nhận damage
    # ────────────────────────────────────────────────────────────

    def take_damage(self, dmg: int):
        """
        Trừ máu, bật hit flash. Kích hoạt animation dead khi hp về 0.

        Input:
            dmg (int): Lượng sát thương.
        """
        if not self.alive:
            return
        self.hp       -= dmg
        self.hit_flash = 0.15
        if self.hp <= 0:
            self.hp   = 0
            self.alive = False
            self._set_anim("dead")
            self._death_fade_timer = 0.0

    # ────────────────────────────────────────────────────────────
    #  Animation helpers
    # ────────────────────────────────────────────────────────────

    def _set_anim(self, state: str):
        """
        Chuyển animation state, reset frame về 0 nếu state thay đổi.

        Input:
            state (str): 'idle' | 'run' | 'attack' | 'dead'
        """
        if self._anim_state != state:
            self._anim_state = state
            self._frame_idx  = 0
            self._anim_timer = 0.0

    def _advance_anim(self, dt: float):
        """
        Tiến frame animation theo thời gian.
        Animation dead chạy 1 lần rồi dừng ở frame cuối.

        Input:
            dt (float): Thời gian trôi qua (giây).
        """
        fps      = _ANIM_FPS.get(self._anim_state, 12.0)
        sprites  = _get_player_sprites().get(self._anim_state, [])
        n_frames = len(sprites)
        if n_frames == 0:
            return

        self._anim_timer += dt
        interval = 1.0 / fps
        while self._anim_timer >= interval:
            self._anim_timer -= interval
            if self._anim_state == "dead":
                if self._frame_idx < n_frames - 1:
                    self._frame_idx += 1
                else:
                    self._dead_done = True  # giữ ở frame cuối
            else:
                self._frame_idx = (self._frame_idx + 1) % n_frames

    # ────────────────────────────────────────────────────────────
    #  Update
    # ────────────────────────────────────────────────────────────

    def update(self, dt: float, obstacles: list):
        """
        Cập nhật toàn bộ trạng thái player mỗi frame.

        Input:
            dt        (float): Thời gian trôi qua giữa 2 frame (giây).
            obstacles (list) : Danh sách dict chướng ngại vật {'x','y','w','h'}.
        """
        # Nếu đã chết, chỉ cập nhật timer xám màn hình + animation dead
        if not self.alive:
            self._death_fade_timer += dt
            self._advance_anim(dt)
            return

        # Cooldown
        if self._attack_timer > 0:
            self._attack_timer -= dt
        if self._blink_timer > 0:
            self._blink_timer -= dt
        if self.hit_flash > 0:
            self.hit_flash -= dt

        self.blink_fx = [
            [x, y, a - dt * 3]
            for x, y, a in self.blink_fx
            if (a - dt * 3) > 0
        ]

        # Blink pre-stun
        if self._blink_pre_stun > 0:
            self._blink_pre_stun -= dt
            if self._blink_pre_stun <= 0:
                self._blink_pre_stun = 0.0
                self._execute_blink()

        # Blink post-stun
        if self._blink_post_stun > 0:
            self._blink_post_stun -= dt

        # Windup tấn công
        if self._windup_timer > 0:
            self._windup_timer -= dt
            if self._windup_timer <= 0:
                self._execute_attack()

        # Di chuyển
        is_moving = False
        if not self._is_frozen():
            if self.target_x is not None and self.target_y is not None:
                dx   = self.target_x - self.x
                dy   = self.target_y - self.y
                dist = math.hypot(dx, dy)
                step = self.speed * dt
                if dist <= step:
                    nx_pos    = self.target_x
                    ny_pos    = self.target_y
                    self.target_x = None
                    self.target_y = None
                else:
                    nx_pos = self.x + dx / dist * step
                    ny_pos = self.y + dy / dist * step
                    # Cập nhật hướng nhìn theo hướng di chuyển
                    self._facing_angle = math.atan2(dy, dx)
                    is_moving = True

                ny_pos = min(ny_pos, self.start_y - self.radius)

                if not _any_circle_rect(nx_pos, self.y, self.radius, obstacles):
                    self.x = nx_pos
                if not _any_circle_rect(self.x, ny_pos, self.radius, obstacles):
                    self.y = ny_pos

        # Giới hạn biên bản đồ
        self.x = max(self.radius, min(MAP_WIDTH - self.radius, self.x))
        self.y = min(self.y, self.start_y - self.radius)

        if self.y < self.min_y_reached:
            self.min_y_reached = self.y

        # Chọn animation state phù hợp
        if self._windup_timer > 0:
            self._set_anim("attack")
        elif is_moving:
            self._set_anim("run")
        else:
            # Trở về idle sau khi attack xong hoặc đứng yên
            if self._anim_state == "attack" and self._windup_timer <= 0:
                self._set_anim("idle")
            elif self._anim_state != "attack":
                self._set_anim("idle")

        self._advance_anim(dt)

    # ────────────────────────────────────────────────────────────
    #  Draw
    # ────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera):
        """
        Vẽ player và toàn bộ hiệu ứng:
          - Sprite animation xoay đúng hướng
          - Bóng ma blink, vòng pre/post-stun
          - Thanh HP
          - Vòng cung cooldown blink
          - Chấm đích di chuyển
          - Overlay xám khi chết

        Sprite gốc hướng lên (↑) = góc -90° (atan2 = -π/2).
        pygame.transform.rotate() xoay ngược chiều kim đồng hồ.
        Rotation = -(facing_deg + 90) để căn sprite đúng hướng.

        Input:
            surface (pygame.Surface): Bề mặt màn hình.
            camera  (Camera)        : Chuyển world → screen.
        """
        sx, sy = camera.world_to_screen(self.x, self.y)

        # ── Bóng ma blink ───────────────────────────────────────────────
        for gx, gy, alpha in self.blink_fx:
            gsx, gsy  = camera.world_to_screen(gx, gy)
            alpha_val = max(0, min(255, int(alpha * 180)))
            ghost     = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(ghost, (*COL_BLINK_FX, alpha_val),
                               (self.radius, self.radius), self.radius)
            surface.blit(ghost, (gsx - self.radius, gsy - self.radius))

        # ── Pre-stun: vòng xanh nhấp nháy ───────────────────────────────
        if self._blink_pre_stun > 0:
            ratio     = self._blink_pre_stun / BLINK_PRE_STUN_DURATION
            pre_surf  = pygame.Surface((self.radius * 2 + 16, self.radius * 2 + 16), pygame.SRCALPHA)
            pygame.draw.circle(pre_surf, (80, 200, 255, int(200 * ratio)),
                               (self.radius + 8, self.radius + 8), self.radius + 6, 3)
            surface.blit(pre_surf, (int(sx) - self.radius - 8, int(sy) - self.radius - 8))

        # ── Post-stun: vòng vàng mờ dần ─────────────────────────────────
        if self._blink_post_stun > 0:
            ratio      = self._blink_post_stun / BLINK_POST_STUN_DURATION
            stun_surf  = pygame.Surface((self.radius * 2 + 12, self.radius * 2 + 12), pygame.SRCALPHA)
            pygame.draw.circle(stun_surf, (255, 255, 100, int(160 * ratio)),
                               (self.radius + 6, self.radius + 6), self.radius + 4, 3)
            surface.blit(stun_surf, (int(sx) - self.radius - 6, int(sy) - self.radius - 6))

        # ── Sprite player ────────────────────────────────────────────────
        sprites = _get_player_sprites().get(self._anim_state, [])
        if sprites:
            frame = sprites[self._frame_idx % len(sprites)]

            # Sprite gốc hướng ↑ (= -90°).
            # facing_angle (radian) = atan2(dy, dx): sang phải = 0, lên = -π/2.
            # Đổi sang độ rồi tính góc xoay:
            #   facing_deg = degrees(facing_angle)  e.g. lên = -90°
            #   sprite_offset = +90 (vì sprite hướng ↑ tương ứng facing = -90°)
            #   rotate_angle  = -(facing_deg + 90)
            # pygame.transform.rotate xoay ngược chiều kim đồng hồ → dùng dấu âm.
            facing_deg   = math.degrees(self._facing_angle)
            rotate_angle = -(facing_deg + 90)

            if self.hit_flash > 0:
                # Tint trắng khi bị hit — mask theo alpha sprite, không tô vùng trong suốt
                tinted = frame.copy()
                white_layer = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
                white_layer.fill((255, 255, 255, 160))
                white_layer.blit(tinted, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                tinted.blit(white_layer, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                rotated = pygame.transform.rotate(tinted, rotate_angle)
            else:
                rotated = pygame.transform.rotate(frame, rotate_angle)

            rw, rh = rotated.get_size()
            surface.blit(rotated, (int(sx) - rw // 2, int(sy) - rh // 2))

        else:
            # Fallback vòng tròn nếu sprite không load được
            color = COL_HIT_FLASH if self.hit_flash > 0 else COL_PLAYER
            pygame.draw.circle(surface, color, (int(sx), int(sy)), self.radius)
            pygame.draw.circle(surface, (200, 240, 255), (int(sx), int(sy)), self.radius // 2)

        # ── Thanh HP (chỉ khi còn sống) ────────────────────────────────
        if self.alive:
            bar_w = self.radius * 2 + 4
            bar_h = 5
            bx    = int(sx) - bar_w // 2
            by    = int(sy) - self.radius - 14
            pygame.draw.rect(surface, COL_HP_BAR_BG, (bx, by, bar_w, bar_h))
            fill  = int(bar_w * self.hp / self.max_hp)
            pygame.draw.rect(surface, COL_PLAYER_HP, (bx, by, fill, bar_h))

        # ── Vòng cung cooldown blink ────────────────────────────────────
        if not self.blink_ready and self.alive:
            ratio = 1 - self._blink_timer / self.blink_cooldown
            pygame.draw.arc(
                surface, (80, 180, 255),
                (int(sx) - self.radius - 4, int(sy) - self.radius - 4,
                 (self.radius + 4) * 2, (self.radius + 4) * 2),
                math.pi / 2, math.pi / 2 + ratio * 2 * math.pi, 2
            )

        # ── Chấm đích di chuyển ─────────────────────────────────────────
        if self.target_x is not None and self.target_y is not None and self.alive:
            tsx, tsy = camera.world_to_screen(self.target_x, self.target_y)
            pygame.draw.circle(surface, (80, 255, 120), (int(tsx), int(tsy)), 4, 1)

        # ── Overlay xám khi chết ────────────────────────────────────────
        if not self.alive:
            t      = min(self._death_fade_timer / self.DEATH_FADE_DURATION, 1.0)
            # Easing: bắt đầu chậm, cuối mạnh → t^2
            alpha  = int(200 * (t ** 2))
            self._gray_surf.fill((30, 30, 30, alpha))
            surface.blit(self._gray_surf, (0, 0))


# ──────────────────────────────────────────────────────────────
#  Collision helpers
# ──────────────────────────────────────────────────────────────

def _any_circle_rect(cx, cy, r, obstacles):
    """
    Kiểm tra hình tròn có chạm bất kỳ chướng ngại vật nào không.

    Input:
        cx        (float): Tọa độ X tâm hình tròn.
        cy        (float): Tọa độ Y tâm hình tròn.
        r         (float): Bán kính hình tròn.
        obstacles (list) : Danh sách dict {'x','y','w','h'}.
    Output:
        bool
    """
    for obs in obstacles:
        if _circle_rect(cx, cy, r, obs):
            return True
    return False


def _circle_rect(cx, cy, r, rect_dict):
    """
    Va chạm hình tròn – hình chữ nhật bằng điểm gần nhất.

    Input:
        cx        (float): Tọa độ X tâm hình tròn.
        cy        (float): Tọa độ Y tâm hình tròn.
        r         (float): Bán kính hình tròn.
        rect_dict (dict) : {'x','y','w','h'}.
    Output:
        bool
    """
    rx, ry, rw, rh = rect_dict['x'], rect_dict['y'], rect_dict['w'], rect_dict['h']
    closest_x      = max(rx, min(cx, rx + rw))
    closest_y      = max(ry, min(cy, ry + rh))
    return math.hypot(cx - closest_x, cy - closest_y) < r
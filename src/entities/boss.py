<<<<<<< HEAD
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

BOSS_WINDUP_DURATION = 0.5
BOSS_ATTACK_COOLDOWN_OVERRIDE = 2.5
_BOSS_SPRITE_CACHE: dict = {}


def _load_strip(path: str, n_frames: int, target_h: int, bg_color_hex: str = None) -> list:
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
        if bg_color_hex is not None:
            bg = pygame.Color(bg_color_hex)
        else:
            bg = sheet.get_at((0, 0))
        arr = pygame.surfarray.pixels3d(sheet)
        alp = pygame.surfarray.pixels_alpha(sheet)
        mask = (
            (np.abs(arr[:, :, 0].astype(int) - bg.r) <= 80) &
            (np.abs(arr[:, :, 1].astype(int) - bg.g) <= 80) &
            (np.abs(arr[:, :, 2].astype(int) - bg.b) <= 80)
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
        "fire":  _load_strip(BASE + "fire_dragon.png",  16, 350, bg_color_hex="#00b551"),
        "water": _load_strip(BASE + "water_dragon.png", 16, 350, bg_color_hex="#00b551"),
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
        self.radius   = 80
        self.alive    = True
        self.map_type = map_type

        self.attack_range = R
        self.attack_dmg   = BOSS_DMG

        self._phase        = 0
        self._cooldown_max = BOSS_ATTACK_COOLDOWN_OVERRIDE
        self._timer        = 0.5
        self._burst_count  = 0

        self._windup_timer    = 0.0
        self._windup_player   = None
        self._windup_projs    = None
        self._windup_delayed  = None
        self._windup_tracker  = None

        # Boss đứng cố định, không lắc ngang
        self._origin_x   = float(x)

        self.hit_flash = 0.0
        self.color     = COL_BOSS
        self._pulse    = 0.0

        self._facing        = 1
        self._attack_angle  = 90.0   # góc target tới player
        self._display_angle = 90.0   # góc hiển thị — lerp chậm khi idle, snap khi tấn công
        self._anim_timer    = 0.0
        self._anim_fps      = 12.0
        self._frame_idx     = 0

        self.lasers: list   = []     # LaserBeam đang active
        self._spiral_angle  = 0.0   # góc tích lũy cho pattern spiral

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

        # Góc target tới player — luôn lerp chậm khi idle, snap khi khai hỏa
        target_angle = math.degrees(
            math.atan2(player.y - self.y, player.x - self.x)
        )
        self._attack_angle = target_angle
        self._facing = 1 if player.x >= self.x else -1

        # Luôn lerp chậm 60°/giây — kể cả lúc windup
        TURN_SPEED = 60.0
        diff = (target_angle - self._display_angle + 180) % 360 - 180
        max_turn = TURN_SPEED * dt
        if abs(diff) <= max_turn:
            self._display_angle = target_angle
        else:
            self._display_angle += math.copysign(max_turn, diff)

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
            # Cập nhật lasers ngay cả khi đang trong windup
            for laser in self.lasers:
                laser.update(dt)
            self.lasers = [l for l in self.lasers if l.alive]
            return

        # Cập nhật lasers
        for laser in self.lasers:
            laser.update(dt)
        self.lasers = [l for l in self.lasers if l.alive]

        if not self.in_range(player.x, player.y):
            self._timer = min(self._timer + dt * 0.5, self._cooldown_max)
            return

        self._timer -= dt
        if self._timer > 0:
            return

        # Bắt đầu windup
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
            str: Một trong 'aoe', 'wide_spread', 'snipe', 'spread',
                 'lux_beam', 'spiral', 'ring_burst',
                 'ez_volley', 'zed_shadow', 'jinx_rocket'.
        """
        if profile.is_aggressive:
            return random.choice(["aoe", "ring_burst", "ez_volley"])
        if profile.dodge_bias in ("left", "right"):
            return random.choice(["wide_spread", "lux_beam", "zed_shadow"])
        if not profile.is_aggressive and profile.dodge_bias == "none":
            return random.choice(["snipe", "spiral", "jinx_rocket"])
        return random.choice(["spread", "ez_volley", "jinx_rocket"])

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
            self._do_spread(player, projectiles,
                            [-0.18, 0.0, 0.18], 1.6)

        elif pattern == "wide_spread":
            self._do_spread(player, projectiles,
                            [-0.40, 0.0, 0.40], 1.5)

        elif pattern == "snipe":
            profile  = tracker.get_profile()
            tx, ty   = profile.avg_x, player.y - 40
            dx, dy   = tx - self.x, ty - self.y
            dist     = math.hypot(dx, dy)
            if dist == 0:
                return
            self._facing = 1 if dx >= 0 else -1
            speed      = ENEMY_PROJ_SPEED * 2.4
            base_angle = math.atan2(dy, dx)
            for offset in (-0.05, 0.0, 0.05):   # 3 viên
                a = base_angle + offset
                projectiles.append(Projectile(
                    owner="boss", x=self.x, y=self.y,
                    vx=math.cos(a) * speed, vy=math.sin(a) * speed,
                    dmg=self.attack_dmg, max_range=self.attack_range + 200,
                    radius=10, color=(255, 80, 255),
                    sprite_name="water_arrow" if self.map_type == "water" else "fire_arrow",
                ))

        elif pattern == "aoe":
            # 3 vùng nổ: 1 trúng đúng player + 2 xung quanh
            delayed_attacks.append(DelayedCircleAttack(
                owner="boss", x=player.x, y=player.y,
                aoe_r=BOSS_TYPE2_AOE_R, dmg=self.attack_dmg, delay=TYPE2_DELAY * 1.3,
                explosion_type="water_explosion" if self.map_type == "water" else "fire_explosion",
            ))
            for _ in range(2):
                ox = random.uniform(-BOSS_TYPE2_AOE_R * 1.2, BOSS_TYPE2_AOE_R * 1.2)
                oy = random.uniform(-BOSS_TYPE2_AOE_R * 1.2, BOSS_TYPE2_AOE_R * 1.2)
                delayed_attacks.append(DelayedCircleAttack(
                    owner="boss", x=player.x + ox, y=player.y + oy,
                    aoe_r=BOSS_TYPE2_AOE_R * 0.8, dmg=self.attack_dmg, delay=TYPE2_DELAY * 1.5,
                    explosion_type="water_explosion" if self.map_type == "water" else "fire_explosion",
                ))

        elif pattern == "lux_beam":
            self._do_lux_beam(player)

        elif pattern == "spiral":
            self._do_spiral(player, projectiles)

        elif pattern == "ring_burst":
            self._do_ring_burst(player, projectiles, delayed_attacks)

        elif pattern == "ez_volley":
            self._do_ez_volley(player, projectiles)

        elif pattern == "zed_shadow":
            self._do_zed_shadow(player, projectiles, delayed_attacks)

        elif pattern == "jinx_rocket":
            self._do_jinx_rocket(player, projectiles)

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
        # Snap ngay khi khai hỏa thực sự
        self._display_angle = math.degrees(base_angle)
        speed          = ENEMY_PROJ_SPEED * speed_mult
        for spread in spreads:
            angle = base_angle + spread
            projectiles.append(Projectile(
                owner="boss", x=self.x, y=self.y,
                vx=math.cos(angle) * speed, vy=math.sin(angle) * speed,
                dmg=self.attack_dmg, max_range=self.attack_range + 100,
                radius=12, color=(220, 60, 255),
                sprite_name="water_arrow" if self.map_type == "water" else "fire_arrow",
            ))

    def _do_lux_beam(self, player):
        """
        Pattern lux_beam: 5 tia laser song song theo hướng player, mỗi tia lệch
        ngang nhau, delay stagger để có hiệu ứng quét như Final Spark của Lux.

        Input:
            player (Player): Dùng để tính hướng gốc.
        """
        from entities.projectile import LaserBeam
        dx, dy = player.x - self.x, player.y - self.y
        dist   = math.hypot(dx, dy)
        if dist == 0:
            return
        base_angle = math.atan2(dy, dx)
        self._display_angle = math.degrees(base_angle)
        self._facing        = 1 if dx >= 0 else -1

        # 5 tia, lệch ngang ±10° mỗi tia, stagger delay 0.18s
        beam_color  = (80, 180, 255) if self.map_type == "water" else (255, 120, 30)
        n_beams     = 5
        half        = n_beams // 2
        for i in range(n_beams):
            offset    = (i - half) * 0.314  # radian, ~18° mỗi bước
            angle     = base_angle + offset
            stagger   = i * 0.18            # tia giữa bắn trước, toả dần ra ngoài
            self.lasers.append(LaserBeam(
                owner="boss",
                x=self.x, y=self.y,
                angle_rad=angle,
                length=self.attack_range + 100,
                width=14 if i == half else 8,
                dmg=self.attack_dmg,
                delay=0.65 + stagger,
                active_duration=0.45,
                color=beam_color,
            ))

    def _do_spiral(self, player, projectiles: list):
        """
        Pattern spiral: bắn 3 loạt, mỗi loạt 8 đạn tỏa đều 360°, góc xoay
        lệch 15° giữa các loạt tạo hiệu ứng xoáy ốc khó né.

        Input:
            player      (Player): Dùng để snap display angle.
            projectiles (list)  : Danh sách đạn.
        """
        from entities.projectile import Projectile
        dx, dy = player.x - self.x, player.y - self.y
        self._facing = 1 if dx >= 0 else -1

        n_arms   = 5
        n_rounds = 2
        speed    = ENEMY_PROJ_SPEED * 1.9
        col      = (100, 220, 255) if self.map_type == "water" else (255, 160, 40)

        for rnd in range(n_rounds):
            rot_offset = math.radians(self._spiral_angle + rnd * 15)
            for arm in range(n_arms):
                angle = rot_offset + arm * (2 * math.pi / n_arms)
                projectiles.append(Projectile(
                    owner="boss", x=self.x, y=self.y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed,
                    dmg=self.attack_dmg,
                    max_range=self.attack_range,
                    radius=9, color=col,
                    sprite_name="water_arrow" if self.map_type == "water" else "fire_arrow",
                ))
        self._spiral_angle = (self._spiral_angle + 22.5) % 360

    def _do_ring_burst(self, player, projectiles: list, delayed_attacks: list):
        """
        Pattern ring_burst: vòng tròn 12 AoE delay bao quanh player
        rồi 8 đạn bắn thẳng vào tâm player — buộc player phải chạy ra
        nhưng vòng ngoài lại nổ.

        Input:
            player          (Player): Mục tiêu.
            projectiles     (list)  : Danh sách đạn.
            delayed_attacks (list)  : Danh sách AoE trễ.
        """
        from entities.projectile import Projectile, DelayedCircleAttack

        # Vòng AoE bao quanh player
        ring_r   = BOSS_TYPE2_AOE_R * 1.6
        n_mines  = 6
        col_mine = (80, 200, 255) if self.map_type == "water" else (255, 100, 30)
        for i in range(n_mines):
            angle = i * (2 * math.pi / n_mines)
            mx    = player.x + math.cos(angle) * ring_r
            my    = player.y + math.sin(angle) * ring_r
            delayed_attacks.append(DelayedCircleAttack(
                owner="boss", x=mx, y=my,
                aoe_r=BOSS_TYPE2_AOE_R * 0.7,
                dmg=self.attack_dmg,
                delay=TYPE2_DELAY * 1.6,
                explosion_type="water_explosion" if self.map_type == "water" else "fire_explosion",
            ))

        # Sau khi vòng nổ, bắn 8 đạn vào tâm player
        dx, dy  = player.x - self.x, player.y - self.y
        dist    = math.hypot(dx, dy)
        if dist == 0:
            return
        self._facing    = 1 if dx >= 0 else -1
        base_angle      = math.atan2(dy, dx)
        self._display_angle = math.degrees(base_angle)
        speed           = ENEMY_PROJ_SPEED * 1.8
        n_shots         = 3
        spread_total    = math.radians(20)
        for i in range(n_shots):
            offset = -spread_total / 2 + i * (spread_total / (n_shots - 1))
            angle  = base_angle + offset
            projectiles.append(Projectile(
                owner="boss", x=self.x, y=self.y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                dmg=self.attack_dmg,
                max_range=self.attack_range + 150,
                radius=11, color=col_mine,
            sprite_name="water_arrow" if self.map_type == "water" else "fire_arrow",
            ))

    def _do_ez_volley(self, player, projectiles: list):
        """
        Pattern ez_volley — Ezreal Mystic Shot: 3 đạn bắn liên tiếp thẳng
        vào player, mỗi viên lệch nhau 0.1s, bay nhanh và xuyên thẳng.
        Dễ né nếu player di chuyển liên tục.

        Input:
            player      (Player): Mục tiêu.
            projectiles (list)  : Danh sách đạn.
        """
        from entities.projectile import Projectile
        dx, dy = player.x - self.x, player.y - self.y
        dist   = math.hypot(dx, dy)
        if dist == 0:
            return
        self._facing = 1 if dx >= 0 else -1
        base_angle   = math.atan2(dy, dx)
        self._display_angle = math.degrees(base_angle)
        speed        = ENEMY_PROJ_SPEED * 2.7
        col          = (100, 200, 255) if self.map_type == "water" else (255, 180, 40)
        # 3 đạn cùng hướng, offset góc nhỏ để không stack hoàn toàn
        for i, offset in enumerate((-0.04, 0.0, 0.04)):
            angle = base_angle + offset
            projectiles.append(Projectile(
                owner="boss", x=self.x, y=self.y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                dmg=self.attack_dmg,
                max_range=self.attack_range + 200,
                radius=10, color=col,
            sprite_name="water_arrow" if self.map_type == "water" else "fire_arrow",
            ))

    def _do_zed_shadow(self, player, projectiles: list, delayed_attacks: list):
        """
        Pattern zed_shadow — Zed Death Mark: boss thả 2 bóng phân thân
        hai bên player, sau đó cả 3 điểm (boss + 2 bóng) cùng bắn 1 đạn
        về hướng player tạo thành hình chữ V siết chặt. Dễ thấy để né
        nhờ cảnh báo AoE nhỏ tại vị trí bóng.

        Input:
            player          (Player): Mục tiêu.
            projectiles     (list)  : Danh sách đạn.
            delayed_attacks (list)  : Danh sách AoE trễ.
        """
        from entities.projectile import Projectile, DelayedCircleAttack
        dx, dy = player.x - self.x, player.y - self.y
        dist   = math.hypot(dx, dy)
        if dist == 0:
            return
        self._facing = 1 if dx >= 0 else -1
        base_angle   = math.atan2(dy, dx)
        self._display_angle = math.degrees(base_angle)
        speed        = ENEMY_PROJ_SPEED * 1.9
        col          = (180, 60, 255) if self.map_type == "water" else (255, 80, 60)

        # 2 vị trí bóng: lệch ngang 120px so với boss
        perp_x = -math.sin(base_angle) * 120
        perp_y =  math.cos(base_angle) * 120
        shadow_origins = [
            (self.x + perp_x, self.y + perp_y),
            (self.x - perp_x, self.y - perp_y),
        ]

        # Cảnh báo nhỏ tại vị trí bóng
        for sx, sy in shadow_origins:
            delayed_attacks.append(DelayedCircleAttack(
                owner="boss", x=sx, y=sy,
                aoe_r=0, dmg=0, delay=0.3,   # dmg=0: chỉ visual cảnh báo
            ))

        # Boss bắn thẳng
        projectiles.append(Projectile(
            owner="boss", x=self.x, y=self.y,
            vx=math.cos(base_angle) * speed,
            vy=math.sin(base_angle) * speed,
            dmg=self.attack_dmg, max_range=self.attack_range + 100,
            radius=11, color=col,
            sprite_name="water_arrow" if self.map_type == "water" else "fire_arrow",
        ))
        # Mỗi bóng bắn về phía player (hội tụ)
        for sx, sy in shadow_origins:
            a = math.atan2(player.y - sy, player.x - sx)
            projectiles.append(Projectile(
                owner="boss", x=sx, y=sy,
                vx=math.cos(a) * speed,
                vy=math.sin(a) * speed,
                dmg=self.attack_dmg, max_range=self.attack_range + 100,
                radius=9, color=col,
                sprite_name="water_arrow" if self.map_type == "water" else "fire_arrow",
            ))

    def _do_jinx_rocket(self, player, projectiles: list):
        """
        Pattern jinx_rocket — Jinx Super Mega Death Rocket: 1 đạn to
        bay thẳng vào player với vệt sáng dài, bán kính lớn và sát thương
        cao hơn thường. Dễ né nhờ chỉ có 1 đạn, nhưng bán kính hitbox lớn.

        Input:
            player      (Player): Mục tiêu.
            projectiles (list)  : Danh sách đạn.
        """
        from entities.projectile import Projectile
        dx, dy = player.x - self.x, player.y - self.y
        dist   = math.hypot(dx, dy)
        if dist == 0:
            return
        self._facing = 1 if dx >= 0 else -1
        base_angle   = math.atan2(dy, dx)
        self._display_angle = math.degrees(base_angle)
        speed = ENEMY_PROJ_SPEED * 2.1
        col   = (255, 60, 120) if self.map_type == "water" else (255, 220, 30)
        # 3 đạn nhỏ kèm theo để không quá đơn giản
        for offset in (-0.08, 0.0, 0.08):
            angle = base_angle + offset
            r     = 16 if offset == 0.0 else 8
            projectiles.append(Projectile(
                owner="boss", x=self.x, y=self.y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                dmg=self.attack_dmg * (2 if offset == 0.0 else 1),
                max_range=self.attack_range + 300,
                radius=r, color=col,
            sprite_name="water_arrow" if self.map_type == "water" else "fire_arrow",
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

        # Dragon sprite — rotate theo _display_angle (lerp idle / snap khi tấn công)
        strip = _get_boss_sprites().get(self.map_type, [])
        if strip:
            import numpy as _np
            frame = strip[self._frame_idx % len(strip)]
            angle = 90.0 - self._display_angle
            frame = pygame.transform.rotate(frame, angle)
            if self.hit_flash > 0:
                frame = frame.copy()
                alpha_val = int(160 * (self.hit_flash / 0.15))
                white_layer = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
                white_layer.fill((255, 255, 255, alpha_val))
                wl_alpha = pygame.surfarray.pixels_alpha(white_layer)
                fr_alpha = pygame.surfarray.pixels_alpha(frame)
                wl_alpha[:] = _np.minimum(wl_alpha, fr_alpha)
                del wl_alpha, fr_alpha
                frame.blit(white_layer, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            fw, fh = frame.get_size()
            surface.blit(frame, (int(sx) - fw // 2, int(sy) - fh // 2))
        else:
            color = COL_HIT_FLASH if self.hit_flash > 0 else self.color
            pygame.draw.circle(surface, color, (int(sx), int(sy)), self.radius)
            pygame.draw.circle(surface, (220, 100, 255), (int(sx), int(sy)), self.radius // 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(sx), int(sy)), self.radius // 4)

        # Vẽ các LaserBeam đang active
        for laser in self.lasers:
            laser.draw(surface, camera)

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

        if not hasattr(self, "_font_lbl"):
            self._font_lbl = pygame.font.SysFont("monospace", 11, bold=True)
        lbl  = self._font_lbl.render("BOSS", True, lbl_color)
        surface.blit(lbl, (int(sx) - lbl.get_width() // 2, by - 14))
=======
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
>>>>>>> 7e7533b68f27d227fe69f1e1e6ff7aa2c15fffb9

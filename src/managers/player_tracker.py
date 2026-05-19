<<<<<<< HEAD
"""
Theo dõi hành vi người chơi theo thời gian thực.

Thu thập dữ liệu về hướng né, vùng đứng yêu thích, thời điểm blink
và mức độ tấn công. Tổng hợp thành BehaviorProfile cung cấp cho
quái và boss để ra quyết định tấn công thông minh hơn.

Cần ít nhất 120 frame (2 giây) trước khi profile đủ tin cậy.
"""
import math
from collections import deque, Counter


class BehaviorProfile:
    """
    Snapshot hành vi người chơi tại một thời điểm.

    Được tạo bởi PlayerTracker.get_profile() và truyền vào
    _fire() của quái/boss để chọn chiến thuật tấn công.
    """

    def __init__(self, dodge_bias: str, avg_x: float,
                 is_aggressive: bool, blink_hp_thresh: float,
                 favorite_x_ratio: float, reliable: bool):
        self.dodge_bias       = dodge_bias        # "left" | "right" | "none"
        self.avg_x            = avg_x             # vị trí X trung bình của player
        self.is_aggressive    = is_aggressive     # hay lao lên gần quái không
        self.blink_hp_thresh  = blink_hp_thresh   # HP% trung bình lúc blink
        self.favorite_x_ratio = favorite_x_ratio  # 0.0=trái 1.0=phải
        self.reliable         = reliable          # đủ data chưa (>= 120 frame)


class PlayerTracker:
    """
    Quan sát và phân tích hành vi người chơi mỗi frame.

    Lưu lịch sử vị trí, hướng di chuyển và các sự kiện đặc biệt
    (blink, né đạn). Cung cấp BehaviorProfile để quái/boss dùng
    khi quyết định tấn công.
    """

    HISTORY_SIZE = 360   # 6 giây tại 60fps

    def __init__(self, screen_w: float, screen_h: float):
        self._screen_w = screen_w
        self._screen_h = screen_h

        self._pos_history:  deque = deque(maxlen=self.HISTORY_SIZE)
        self._dx_history:   deque = deque(maxlen=60)
        self._dy_history:   deque = deque(maxlen=60)
        self._dodge_counter: Counter = Counter()
        self._blink_hp_log:  list   = []

        self._prev_x: float | None = None
        self._prev_y: float | None = None
        self._frame  = 0

    def update(self, player):
        """
        Ghi lại vị trí và hướng di chuyển của player mỗi frame.

        Gọi từ GameManager.update() trước khi cập nhật quái.
        """
        self._frame += 1
        x, y = player.x, player.y
        self._pos_history.append((x, y))

        if self._prev_x is not None:
            self._dx_history.append(x - self._prev_x)
            self._dy_history.append(y - self._prev_y)

        self._prev_x = x
        self._prev_y = y

    def record_blink(self, hp_ratio: float):
        """
        Ghi nhận sự kiện blink cùng HP% tại thời điểm đó.

        Gọi từ GameManager khi player.try_blink() trả về True.
        """
        self._blink_hp_log.append(max(0.0, min(1.0, hp_ratio)))

    def record_dodge(self, proj_vx: float, proj_vy: float):
        """
        Ghi nhận hướng né khi đạn địch bay đến gần player.

        Gọi từ GameManager khi phát hiện đạn địch trong vùng cảnh báo.
        Phân tích hướng di chuyển gần đây của player so với hướng bay đạn.
        """
        if not self._dx_history:
            return

        # Lấy vector di chuyển trung bình 10 frame gần nhất
        recent_n = min(10, len(self._dx_history))
        mdx = sum(list(self._dx_history)[-recent_n:]) / recent_n
        mdy = sum(list(self._dy_history)[-recent_n:]) / recent_n

        # Tính vector vuông góc với hướng đạn (pháp tuyến)
        perp_x = -proj_vy
        perp_y =  proj_vx
        plen   = math.hypot(perp_x, perp_y)
        if plen == 0:
            return
        perp_x /= plen
        perp_y /= plen

        dot = mdx * perp_x + mdy * perp_y
        if dot > 0.3:
            self._dodge_counter["right"] += 1
        elif dot < -0.3:
            self._dodge_counter["left"]  += 1

    def get_profile(self) -> BehaviorProfile:
        """
        Tổng hợp toàn bộ dữ liệu thành BehaviorProfile.

        Trả về profile với reliable=False nếu chưa đủ 120 frame dữ liệu.
        Quái nên kiểm tra profile.reliable trước khi thay đổi hành vi.
        """
        reliable = len(self._pos_history) >= 120

        # Vị trí X trung bình
        avg_x = (sum(p[0] for p in self._pos_history) / len(self._pos_history)
                 if self._pos_history else self._screen_w / 2)

        # Xu hướng né
        dodge_bias = "none"
        total_dodge = sum(self._dodge_counter.values())
        if total_dodge >= 5:
            top, count = self._dodge_counter.most_common(1)[0]
            if count / total_dodge > 0.45:
                dodge_bias = top

        # Mức độ tích cực — player hay đứng phần trên màn hình
        avg_y = (sum(p[1] for p in self._pos_history) / len(self._pos_history)
                 if self._pos_history else self._screen_h / 2)
        is_aggressive = avg_y < self._screen_h * 0.4

        # HP% trung bình lúc blink
        blink_hp = (sum(self._blink_hp_log) / len(self._blink_hp_log)
                    if self._blink_hp_log else 0.5)

        # Tỷ lệ vị trí X (0=trái, 1=phải)
        fav_x_ratio = avg_x / self._screen_w

        return BehaviorProfile(
            dodge_bias       = dodge_bias,
            avg_x            = avg_x,
            is_aggressive    = is_aggressive,
            blink_hp_thresh  = blink_hp,
            favorite_x_ratio = fav_x_ratio,
            reliable         = reliable,
=======
"""
Theo dõi hành vi người chơi theo thời gian thực.

Thu thập dữ liệu về hướng né, vùng đứng yêu thích, thời điểm blink
và mức độ tấn công. Tổng hợp thành BehaviorProfile cung cấp cho
quái và boss để ra quyết định tấn công thông minh hơn.

Cần ít nhất 120 frame (2 giây) trước khi profile đủ tin cậy.
"""
import math
from collections import deque, Counter


class BehaviorProfile:
    """
    Snapshot hành vi người chơi tại một thời điểm.

    Được tạo bởi PlayerTracker.get_profile() và truyền vào
    _fire() của quái/boss để chọn chiến thuật tấn công.
    """

    def __init__(self, dodge_bias: str, avg_x: float,
                 is_aggressive: bool, blink_hp_thresh: float,
                 favorite_x_ratio: float, reliable: bool):
        self.dodge_bias       = dodge_bias        # "left" | "right" | "none"
        self.avg_x            = avg_x             # vị trí X trung bình của player
        self.is_aggressive    = is_aggressive     # hay lao lên gần quái không
        self.blink_hp_thresh  = blink_hp_thresh   # HP% trung bình lúc blink
        self.favorite_x_ratio = favorite_x_ratio  # 0.0=trái 1.0=phải
        self.reliable         = reliable          # đủ data chưa (>= 120 frame)


class PlayerTracker:
    """
    Quan sát và phân tích hành vi người chơi mỗi frame.

    Lưu lịch sử vị trí, hướng di chuyển và các sự kiện đặc biệt
    (blink, né đạn). Cung cấp BehaviorProfile để quái/boss dùng
    khi quyết định tấn công.
    """

    HISTORY_SIZE = 360   # 6 giây tại 60fps

    def __init__(self, screen_w: float, screen_h: float):
        self._screen_w = screen_w
        self._screen_h = screen_h

        self._pos_history:  deque = deque(maxlen=self.HISTORY_SIZE)
        self._dx_history:   deque = deque(maxlen=60)
        self._dy_history:   deque = deque(maxlen=60)
        self._dodge_counter: Counter = Counter()
        self._blink_hp_log:  list   = []

        self._prev_x: float | None = None
        self._prev_y: float | None = None
        self._frame  = 0

    def update(self, player):
        """
        Ghi lại vị trí và hướng di chuyển của player mỗi frame.

        Gọi từ GameManager.update() trước khi cập nhật quái.
        """
        self._frame += 1
        x, y = player.x, player.y
        self._pos_history.append((x, y))

        if self._prev_x is not None:
            self._dx_history.append(x - self._prev_x)
            self._dy_history.append(y - self._prev_y)

        self._prev_x = x
        self._prev_y = y

    def record_blink(self, hp_ratio: float):
        """
        Ghi nhận sự kiện blink cùng HP% tại thời điểm đó.

        Gọi từ GameManager khi player.try_blink() trả về True.
        """
        self._blink_hp_log.append(max(0.0, min(1.0, hp_ratio)))

    def record_dodge(self, proj_vx: float, proj_vy: float):
        """
        Ghi nhận hướng né khi đạn địch bay đến gần player.

        Gọi từ GameManager khi phát hiện đạn địch trong vùng cảnh báo.
        Phân tích hướng di chuyển gần đây của player so với hướng bay đạn.
        """
        if not self._dx_history:
            return

        # Lấy vector di chuyển trung bình 10 frame gần nhất
        recent_n = min(10, len(self._dx_history))
        mdx = sum(list(self._dx_history)[-recent_n:]) / recent_n
        mdy = sum(list(self._dy_history)[-recent_n:]) / recent_n

        # Tính vector vuông góc với hướng đạn (pháp tuyến)
        perp_x = -proj_vy
        perp_y =  proj_vx
        plen   = math.hypot(perp_x, perp_y)
        if plen == 0:
            return
        perp_x /= plen
        perp_y /= plen

        dot = mdx * perp_x + mdy * perp_y
        if dot > 0.3:
            self._dodge_counter["right"] += 1
        elif dot < -0.3:
            self._dodge_counter["left"]  += 1

    def get_profile(self) -> BehaviorProfile:
        """
        Tổng hợp toàn bộ dữ liệu thành BehaviorProfile.

        Trả về profile với reliable=False nếu chưa đủ 120 frame dữ liệu.
        Quái nên kiểm tra profile.reliable trước khi thay đổi hành vi.
        """
        reliable = len(self._pos_history) >= 120

        # Vị trí X trung bình
        avg_x = (sum(p[0] for p in self._pos_history) / len(self._pos_history)
                 if self._pos_history else self._screen_w / 2)

        # Xu hướng né
        dodge_bias = "none"
        total_dodge = sum(self._dodge_counter.values())
        if total_dodge >= 5:
            top, count = self._dodge_counter.most_common(1)[0]
            if count / total_dodge > 0.45:
                dodge_bias = top

        # Mức độ tích cực — player hay đứng phần trên màn hình
        avg_y = (sum(p[1] for p in self._pos_history) / len(self._pos_history)
                 if self._pos_history else self._screen_h / 2)
        is_aggressive = avg_y < self._screen_h * 0.4

        # HP% trung bình lúc blink
        blink_hp = (sum(self._blink_hp_log) / len(self._blink_hp_log)
                    if self._blink_hp_log else 0.5)

        # Tỷ lệ vị trí X (0=trái, 1=phải)
        fav_x_ratio = avg_x / self._screen_w

        return BehaviorProfile(
            dodge_bias       = dodge_bias,
            avg_x            = avg_x,
            is_aggressive    = is_aggressive,
            blink_hp_thresh  = blink_hp,
            favorite_x_ratio = fav_x_ratio,
            reliable         = reliable,
>>>>>>> 7e7533b68f27d227fe69f1e1e6ff7aa2c15fffb9
        )
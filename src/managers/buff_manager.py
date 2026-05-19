"""
Quản lý hệ thống hiệu ứng tăng cường (buff) đang hoạt động trên nhân vật.

Cập nhật lần cuối: 23:17 ngày 28/04/2026
"""
import heapq
from constants import *

_BUFF_DURATION = {
    BUFF_WATER: BUFF_WATER_DURATION,
    BUFF_FIRE:  BUFF_FIRE_DURATION,
    BUFF_WIND:  BUFF_WIND_DURATION,
}

class BuffManager:
    """
    Quản lý danh sách các buff đang hoạt động và điều phối thời gian hiệu lực của chúng.
    """

    def __init__(self):
        """
        Khởi tạo hệ thống quản lý buff, bộ đếm thời gian và các cấu trúc dữ liệu tối ưu.
        """
        self._heap: list[tuple[float, str]] = []
        self._invalid: set[tuple[float, str]] = set()
        self.active: set[str] = set()
        self._current_expires: dict[str, float] = {}

        self._elapsed = 0.0
        self._water_regen_acc = 0.0

    def add(self, buff_id: str):
        """
        Kích hoạt một hiệu ứng mới hoặc làm mới thời gian nếu hiệu ứng đó đang tồn tại.
        Input: 
            buff_id (str): Mã định danh của loại buff cần thêm.
        """
        duration = _BUFF_DURATION.get(buff_id, 30.0)
        expire_at = self._elapsed + duration

        if buff_id in self.active:
            old_expire_at = self._current_expires.get(buff_id)
            if old_expire_at is not None:
                self._invalid.add((old_expire_at, buff_id))

        entry = (expire_at, buff_id)
        heapq.heappush(self._heap, entry)
        self.active.add(buff_id)
        self._current_expires[buff_id] = expire_at

        if buff_id == BUFF_WATER:
            self._water_regen_acc = 0.0

    def has(self, buff_id: str) -> bool:
        """
        Kiểm tra một loại hiệu ứng cụ thể có đang hoạt động hay không.
        Input: 
            buff_id (str): Mã định danh buff cần kiểm tra.
        Output: 
            (bool): True nếu buff còn hiệu lực, ngược lại False.
        """
        return buff_id in self.active

    def update(self, dt: float, player) -> list[str]:
        """
        Cập nhật đồng hồ hệ thống, xử lý các buff hết hạn và áp dụng hiệu ứng hồi phục cho người chơi.
        Input: 
            dt (float): Thời gian trôi qua giữa 2 frame (giây).
            player (Player): Đối tượng nhân vật để áp dụng hiệu ứng hồi máu.
        Output: 
            (list[str]): Danh sách các buff_id vừa hết hạn trong frame này.
        """
        self._elapsed += dt
        expired = []

        while self._heap:
            expire_at, buff_id = self._heap[0]

            if (expire_at, buff_id) in self._invalid:
                heapq.heappop(self._heap)
                self._invalid.discard((expire_at, buff_id))
                continue

            if expire_at <= self._elapsed:
                heapq.heappop(self._heap)
                if self._current_expires.get(buff_id) == expire_at:
                    self.active.discard(buff_id)
                    self._current_expires.pop(buff_id, None)
                    expired.append(buff_id)
                    if buff_id == BUFF_WATER:
                        self._water_regen_acc = 0.0
            else:
                break

        if self.has(BUFF_WATER) and player.alive:
            self._water_regen_acc += dt
            if self._water_regen_acc >= BUFF_WATER_REGEN_INTERVAL:
                self._water_regen_acc -= BUFF_WATER_REGEN_INTERVAL
                if player.hp < player.max_hp:
                    player.hp = min(player.max_hp, player.hp + BUFF_WATER_REGEN_AMOUNT)

        return expired

    def remaining(self, buff_id: str) -> float:
        """
        Tính toán thời gian hiệu lực còn lại của một loại buff cụ thể.
        Input: 
            buff_id (str): Mã định danh của buff cần kiểm tra.
        Output: 
            (float): Số giây còn lại trước khi hết hạn.
        """
        expire_at = self._current_expires.get(buff_id, 0.0)
        return max(0.0, expire_at - self._elapsed)

    def clear(self):
        """
        Xóa bỏ toàn bộ buff và đặt lại các bộ đếm thời gian về trạng thái ban đầu.
        """
        self._heap.clear()
        self._invalid.clear()
        self.active.clear()
        self._current_expires.clear()
        self._elapsed = 0.0
        self._water_regen_acc = 0.0
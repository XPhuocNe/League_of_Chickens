"""
Quản lý hệ thống camera — điều chỉnh góc nhìn theo vị trí nhân vật.

Cung cấp các phép chuyển đổi tọa độ giữa không gian thế giới (world space)
và không gian màn hình (screen space). Camera chỉ cuộn theo trục Y,
trục X luôn cố định với offset bằng 0.

Cập nhật lần cuối: 23:17 ngày 28/04/2026
"""
from constants import *


class Camera:
    """
    Quản lý offset cuộn của màn hình theo vị trí nhân vật người chơi.

    Lưu offset_x và offset_y để các hàm chuyển đổi tọa độ biết cần
    dịch chuyển bao nhiêu pixel khi vẽ thực thể từ world space lên screen.
    """

    def __init__(self):
        self.offset_x = 0.0
        self.offset_y = 0.0

    def update(self, player_world_x: float, player_world_y: float):
        """
        Tính lại offset camera để nhân vật luôn hiển thị tại vị trí cố định trên màn hình.

        Input:
            player_world_x (float): Tọa độ X của player trong thế giới (không dùng, giữ offset_x = 0).
            player_world_y (float): Tọa độ Y của player trong thế giới — dùng tính offset_y.
        """
        self.offset_x = 0.0
        self.offset_y = player_world_y - PLAYER_SCREEN_Y

    def world_to_screen(self, wx: float, wy: float) -> tuple:
        """
        Chuyển tọa độ world space sang pixel screen space để vẽ lên màn hình.

        Input:
            wx (float): Tọa độ X trong thế giới.
            wy (float): Tọa độ Y trong thế giới.
        Output:
            tuple[int, int]: Cặp (sx, sy) là tọa độ pixel trên màn hình.
        """
        sx = wx - self.offset_x
        sy = wy - self.offset_y
        return int(sx), int(sy)

    def screen_to_world(self, sx: float, sy: float) -> tuple:
        """
        Chuyển tọa độ pixel màn hình (thường từ sự kiện chuột) sang world space.

        Input:
            sx (float): Tọa độ X trên màn hình (pixel).
            sy (float): Tọa độ Y trên màn hình (pixel).
        Output:
            tuple[float, float]: Cặp (world_x, world_y) trong không gian thế giới.
        """
        wx = sx + self.offset_x
        wy = sy + self.offset_y
        return wx, wy
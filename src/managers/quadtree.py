<<<<<<< HEAD
"""
Cấu trúc dữ liệu Quadtree dùng để tăng tốc phát hiện va chạm giữa các thực thể.

Thay vì kiểm tra mọi cặp thực thể O(n²), Quadtree chia không gian thành
4 vùng con đệ quy. Mỗi thực thể chỉ được kiểm tra với những thực thể
trong cùng vùng hoặc vùng lân cận — giảm độ phức tạp xuống O(n log n).
Cây được tạo lại hoàn toàn mỗi frame vì các thực thể di chuyển liên tục.

Cập nhật lần cuối: 12:15 ngày 29/04/2026
"""
import math


class _Rect:
    """Hình chữ nhật axis-aligned dùng nội bộ trong Quadtree để đại diện cho vùng không gian."""

    def __init__(self, x: float, y: float, w: float, h: float):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, ex: float, ey: float) -> bool:
        """
        Kiểm tra một điểm có nằm trong (hoặc trên biên) hình chữ nhật không.

        Input:
            ex (float): Tọa độ X của điểm cần kiểm tra.
            ey (float): Tọa độ Y của điểm cần kiểm tra.
        Output:
            bool: True nếu điểm nằm trong hoặc trên biên.
        """
        return self.x <= ex <= self.x + self.w and self.y <= ey <= self.y + self.h

    def intersects(self, other: "_Rect") -> bool:
        """
        Kiểm tra hai hình chữ nhật có giao nhau không (kể cả chạm cạnh).

        Input:
            other (_Rect): Hình chữ nhật cần so sánh.
        Output:
            bool: True nếu hai hình chữ nhật giao nhau hoặc chạm cạnh.
        """
        return not (other.x > self.x + self.w or
                    other.x + other.w < self.x or
                    other.y > self.y + self.h or
                    other.y + other.h < self.y)


class QuadTree:
    """
    Cây Quadtree phân vùng không gian 2D để tăng tốc collision detection.

    Mỗi node quản lý một vùng hình chữ nhật và tối đa CAPACITY thực thể.
    Khi đầy, node tự chia thành 4 vùng con (NW, NE, SW, SE) và phân phối
    lại toàn bộ thực thể xuống các con. Độ sâu tối đa là 8 để tránh đệ quy
    vô hạn khi nhiều thực thể nằm đúng cùng một điểm.
    """

    CAPACITY = 4

    def __init__(self, boundary: _Rect, depth: int = 0):
        """
        Khởi tạo một node Quadtree với vùng quản lý là boundary.

        Input:
            boundary (_Rect): Hình chữ nhật xác định vùng không gian node này quản lý.
            depth    (int)  : Độ sâu hiện tại trong cây, dùng để giới hạn đệ quy tối đa 8 cấp.
        """
        self.boundary = boundary
        self.depth    = depth
        self._items: list = []
        self._divided = False
        self._nw: "QuadTree | None" = None
        self._ne: "QuadTree | None" = None
        self._sw: "QuadTree | None" = None
        self._se: "QuadTree | None" = None

    def insert(self, entity) -> bool:
        """
        Thêm một thực thể vào cây.

        Input:
            entity: Thực thể có thuộc tính .x và .y — là Player, Enemy hoặc Boss.
        Output:
            bool: True nếu insert thành công, False nếu thực thể nằm ngoài vùng quản lý.
        """
        if not self.boundary.contains(entity.x, entity.y):
            return False

        if len(self._items) < self.CAPACITY and not self._divided:
            self._items.append(entity)
            return True

        if not self._divided:
            self._subdivide()

        return (self._nw.insert(entity) or
                self._ne.insert(entity) or
                self._sw.insert(entity) or
                self._se.insert(entity))

    def query_radius(self, cx: float, cy: float, radius: float) -> list:
        """
        Trả về tất cả thực thể nằm trong vùng tìm kiếm hình vuông bao quanh tâm (cx, cy).

        Dùng hình vuông thay hình tròn để tránh tính sqrt — bộ lọc chính xác
        được thực hiện bên ngoài bằng math.hypot khi cần.

        Input:
            cx     (float): Tọa độ X tâm vùng tìm kiếm.
            cy     (float): Tọa độ Y tâm vùng tìm kiếm.
            radius (float): Bán kính (dùng tạo hình vuông 2*radius x 2*radius).
        Output:
            list: Danh sách các thực thể nằm trong vùng tìm kiếm.
        """
        result = []
        search_rect = _Rect(cx - radius, cy - radius, radius * 2, radius * 2)
        self._query(search_rect, result)
        return result

    def _query(self, rect: _Rect, result: list):
        """
        Đệ quy thu thập tất cả thực thể trong các node giao với rect.

        Input:
            rect   (_Rect): Hình chữ nhật tìm kiếm.
            result (list) : Danh sách tích lũy kết quả, được sửa trực tiếp (in-place).
        """
        if not self.boundary.intersects(rect):
            return

        for item in self._items:
            if rect.contains(item.x, item.y):
                result.append(item)

        if self._divided:
            self._nw._query(rect, result)
            self._ne._query(rect, result)
            self._sw._query(rect, result)
            self._se._query(rect, result)

    def _subdivide(self):
        """
        Chia node hiện tại thành 4 node con bằng nhau và phân phối lại các thực thể.

        Giới hạn độ sâu tối đa là 8 để tránh đệ quy vô hạn khi nhiều thực thể
        nằm đúng cùng một điểm. Nếu đã đạt độ sâu tối đa, không tạo thêm con.
        """
        x, y, w, h = self.boundary.x, self.boundary.y, self.boundary.w, self.boundary.h
        hw, hh = w / 2, h / 2
        max_depth = 8

        next_depth = self.depth + 1
        self._nw = QuadTree(_Rect(x,      y,      hw, hh), next_depth)
        self._ne = QuadTree(_Rect(x + hw, y,      hw, hh), next_depth)
        self._sw = QuadTree(_Rect(x,      y + hh, hw, hh), next_depth)
        self._se = QuadTree(_Rect(x + hw, y + hh, hw, hh), next_depth)
        self._divided = True

        if self.depth < max_depth:
            old_items = self._items
            self._items = []
            for item in old_items:
                self._nw.insert(item) or \
                self._ne.insert(item) or \
                self._sw.insert(item) or \
                self._se.insert(item)


def build_quadtree(entities: list, x: float, y: float,
                   w: float, h: float) -> QuadTree:
    """
    Tạo một Quadtree mới bao phủ vùng (x, y, w, h) và insert toàn bộ entities vào.

    Hàm tiện ích này được GameManager gọi mỗi frame trước khi kiểm tra va chạm.
    Thực thể nằm ngoài vùng bao phủ bị bỏ qua một cách im lặng.

    Input:
        entities (list) : Danh sách các thực thể cần đưa vào cây (Player, Enemy, Boss).
        x        (float): Tọa độ X góc trên-trái của vùng Quadtree.
        y        (float): Tọa độ Y góc trên-trái của vùng Quadtree.
        w        (float): Chiều rộng vùng Quadtree.
        h        (float): Chiều cao vùng Quadtree.
    Output:
        QuadTree: Cây Quadtree đã được insert toàn bộ entities.
    """
    qt = QuadTree(_Rect(x, y, w, h))
    for e in entities:
        qt.insert(e)
=======
"""
Cấu trúc dữ liệu Quadtree dùng để tăng tốc phát hiện va chạm giữa các thực thể.

Thay vì kiểm tra mọi cặp thực thể O(n²), Quadtree chia không gian thành
4 vùng con đệ quy. Mỗi thực thể chỉ được kiểm tra với những thực thể
trong cùng vùng hoặc vùng lân cận — giảm độ phức tạp xuống O(n log n).
Cây được tạo lại hoàn toàn mỗi frame vì các thực thể di chuyển liên tục.

Cập nhật lần cuối: 12:15 ngày 29/04/2026
"""
import math


class _Rect:
    """Hình chữ nhật axis-aligned dùng nội bộ trong Quadtree để đại diện cho vùng không gian."""

    def __init__(self, x: float, y: float, w: float, h: float):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, ex: float, ey: float) -> bool:
        """
        Kiểm tra một điểm có nằm trong (hoặc trên biên) hình chữ nhật không.

        Input:
            ex (float): Tọa độ X của điểm cần kiểm tra.
            ey (float): Tọa độ Y của điểm cần kiểm tra.
        Output:
            bool: True nếu điểm nằm trong hoặc trên biên.
        """
        return self.x <= ex <= self.x + self.w and self.y <= ey <= self.y + self.h

    def intersects(self, other: "_Rect") -> bool:
        """
        Kiểm tra hai hình chữ nhật có giao nhau không (kể cả chạm cạnh).

        Input:
            other (_Rect): Hình chữ nhật cần so sánh.
        Output:
            bool: True nếu hai hình chữ nhật giao nhau hoặc chạm cạnh.
        """
        return not (other.x > self.x + self.w or
                    other.x + other.w < self.x or
                    other.y > self.y + self.h or
                    other.y + other.h < self.y)


class QuadTree:
    """
    Cây Quadtree phân vùng không gian 2D để tăng tốc collision detection.

    Mỗi node quản lý một vùng hình chữ nhật và tối đa CAPACITY thực thể.
    Khi đầy, node tự chia thành 4 vùng con (NW, NE, SW, SE) và phân phối
    lại toàn bộ thực thể xuống các con. Độ sâu tối đa là 8 để tránh đệ quy
    vô hạn khi nhiều thực thể nằm đúng cùng một điểm.
    """

    CAPACITY = 4

    def __init__(self, boundary: _Rect, depth: int = 0):
        """
        Khởi tạo một node Quadtree với vùng quản lý là boundary.

        Input:
            boundary (_Rect): Hình chữ nhật xác định vùng không gian node này quản lý.
            depth    (int)  : Độ sâu hiện tại trong cây, dùng để giới hạn đệ quy tối đa 8 cấp.
        """
        self.boundary = boundary
        self.depth    = depth
        self._items: list = []
        self._divided = False
        self._nw: "QuadTree | None" = None
        self._ne: "QuadTree | None" = None
        self._sw: "QuadTree | None" = None
        self._se: "QuadTree | None" = None

    def insert(self, entity) -> bool:
        """
        Thêm một thực thể vào cây.

        Input:
            entity: Thực thể có thuộc tính .x và .y — là Player, Enemy hoặc Boss.
        Output:
            bool: True nếu insert thành công, False nếu thực thể nằm ngoài vùng quản lý.
        """
        if not self.boundary.contains(entity.x, entity.y):
            return False

        if len(self._items) < self.CAPACITY and not self._divided:
            self._items.append(entity)
            return True

        if not self._divided:
            self._subdivide()

        return (self._nw.insert(entity) or
                self._ne.insert(entity) or
                self._sw.insert(entity) or
                self._se.insert(entity))

    def query_radius(self, cx: float, cy: float, radius: float) -> list:
        """
        Trả về tất cả thực thể nằm trong vùng tìm kiếm hình vuông bao quanh tâm (cx, cy).

        Dùng hình vuông thay hình tròn để tránh tính sqrt — bộ lọc chính xác
        được thực hiện bên ngoài bằng math.hypot khi cần.

        Input:
            cx     (float): Tọa độ X tâm vùng tìm kiếm.
            cy     (float): Tọa độ Y tâm vùng tìm kiếm.
            radius (float): Bán kính (dùng tạo hình vuông 2*radius x 2*radius).
        Output:
            list: Danh sách các thực thể nằm trong vùng tìm kiếm.
        """
        result = []
        search_rect = _Rect(cx - radius, cy - radius, radius * 2, radius * 2)
        self._query(search_rect, result)
        return result

    def _query(self, rect: _Rect, result: list):
        """
        Đệ quy thu thập tất cả thực thể trong các node giao với rect.

        Input:
            rect   (_Rect): Hình chữ nhật tìm kiếm.
            result (list) : Danh sách tích lũy kết quả, được sửa trực tiếp (in-place).
        """
        if not self.boundary.intersects(rect):
            return

        for item in self._items:
            if rect.contains(item.x, item.y):
                result.append(item)

        if self._divided:
            self._nw._query(rect, result)
            self._ne._query(rect, result)
            self._sw._query(rect, result)
            self._se._query(rect, result)

    def _subdivide(self):
        """
        Chia node hiện tại thành 4 node con bằng nhau và phân phối lại các thực thể.

        Giới hạn độ sâu tối đa là 8 để tránh đệ quy vô hạn khi nhiều thực thể
        nằm đúng cùng một điểm. Nếu đã đạt độ sâu tối đa, không tạo thêm con.
        """
        x, y, w, h = self.boundary.x, self.boundary.y, self.boundary.w, self.boundary.h
        hw, hh = w / 2, h / 2
        max_depth = 8

        next_depth = self.depth + 1
        self._nw = QuadTree(_Rect(x,      y,      hw, hh), next_depth)
        self._ne = QuadTree(_Rect(x + hw, y,      hw, hh), next_depth)
        self._sw = QuadTree(_Rect(x,      y + hh, hw, hh), next_depth)
        self._se = QuadTree(_Rect(x + hw, y + hh, hw, hh), next_depth)
        self._divided = True

        if self.depth < max_depth:
            old_items = self._items
            self._items = []
            for item in old_items:
                self._nw.insert(item) or \
                self._ne.insert(item) or \
                self._sw.insert(item) or \
                self._se.insert(item)


def build_quadtree(entities: list, x: float, y: float,
                   w: float, h: float) -> QuadTree:
    """
    Tạo một Quadtree mới bao phủ vùng (x, y, w, h) và insert toàn bộ entities vào.

    Hàm tiện ích này được GameManager gọi mỗi frame trước khi kiểm tra va chạm.
    Thực thể nằm ngoài vùng bao phủ bị bỏ qua một cách im lặng.

    Input:
        entities (list) : Danh sách các thực thể cần đưa vào cây (Player, Enemy, Boss).
        x        (float): Tọa độ X góc trên-trái của vùng Quadtree.
        y        (float): Tọa độ Y góc trên-trái của vùng Quadtree.
        w        (float): Chiều rộng vùng Quadtree.
        h        (float): Chiều cao vùng Quadtree.
    Output:
        QuadTree: Cây Quadtree đã được insert toàn bộ entities.
    """
    qt = QuadTree(_Rect(x, y, w, h))
    for e in entities:
        qt.insert(e)
>>>>>>> 7e7533b68f27d227fe69f1e1e6ff7aa2c15fffb9
    return qt
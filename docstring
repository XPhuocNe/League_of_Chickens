# LEAGUE OF CHICKENS — AUTO-GENERATED DOCSTRING REFERENCE
============================================================

============================================================
  src/constants.py
============================================================

FILE: constants.py
Tập hợp toàn bộ hằng số cấu hình của game.

Các nhóm hằng số được chia theo chức năng:
    - Màn hình & bản đồ   : kích thước cửa sổ, vị trí camera cố định.
    - Thời gian & tốc độ  : FPS, cooldown tấn công, tốc độ đạn.
    - Kích thước hitbox   : bán kính va chạm của từng loại thực thể.
    - Chiến đấu           : máu, sát thương, tầm đánh.
    - Điểm số & spawn     : ngưỡng điểm xuất hiện Boss, khoảng cách sinh quái.
    - Map phase           : ngưỡng điểm chuyển map và thông số từng map.
    - Buff                : id và thời lượng các buff nhận được khi hạ boss.
    - Màu sắc             : toàn bộ bảng màu RGB dùng khi vẽ.

Cập nhật lần cuối: 22:34 ngày 13/05/2026
────────────────────────────────────────

============================================================
  src/main.py
============================================================

FILE: main.py
Điểm khởi động game và vòng lặp chính.

Quản lý chuyển đổi giữa ba trạng thái ứng dụng:
- 'main_menu': hiển thị màn hình chính, chờ người dùng nhấn bắt đầu.
- 'playing': chạy GameManager, kiểm tra điều kiện chuyển sang game_over.
- 'game_over': vẽ game phía dưới làm nền rồi phủ màn hình kết quả lên trên.

Cập nhật lần cuối: 23:17 ngày 28/04/2026
────────────────────────────────────────
  METHOD/FUNC: main
Khởi tạo pygame, tạo cửa sổ và chạy vòng lặp game cho đến khi thoát.


============================================================
  src/managers/buff_manager.py
============================================================

FILE: buff_manager.py
Quản lý hệ thống hiệu ứng tăng cường (buff) đang hoạt động trên nhân vật.

Cập nhật lần cuối: 23:17 ngày 28/04/2026
────────────────────────────────────────
CLASS: BuffManager
Quản lý danh sách các buff đang hoạt động và điều phối thời gian hiệu lực của chúng.

  METHOD/FUNC: __init__
Khởi tạo hệ thống quản lý buff, bộ đếm thời gian và các cấu trúc dữ liệu tối ưu.

  METHOD/FUNC: add
Kích hoạt một hiệu ứng mới hoặc làm mới thời gian nếu hiệu ứng đó đang tồn tại.
Input: 
    buff_id (str): Mã định danh của loại buff cần thêm.

  METHOD/FUNC: has
Kiểm tra một loại hiệu ứng cụ thể có đang hoạt động hay không.
Input: 
    buff_id (str): Mã định danh buff cần kiểm tra.
Output: 
    (bool): True nếu buff còn hiệu lực, ngược lại False.

  METHOD/FUNC: update
Cập nhật đồng hồ hệ thống, xử lý các buff hết hạn và áp dụng hiệu ứng hồi phục cho người chơi.
Input: 
    dt (float): Thời gian trôi qua giữa 2 frame (giây).
    player (Player): Đối tượng nhân vật để áp dụng hiệu ứng hồi máu.
Output: 
    (list[str]): Danh sách các buff_id vừa hết hạn trong frame này.

  METHOD/FUNC: remaining
Tính toán thời gian hiệu lực còn lại của một loại buff cụ thể.
Input: 
    buff_id (str): Mã định danh của buff cần kiểm tra.
Output: 
    (float): Số giây còn lại trước khi hết hạn.

  METHOD/FUNC: clear
Xóa bỏ toàn bộ buff và đặt lại các bộ đếm thời gian về trạng thái ban đầu.


============================================================
  src/managers/camera.py
============================================================

FILE: camera.py
Quản lý hệ thống camera — điều chỉnh góc nhìn theo vị trí nhân vật.

Cung cấp các phép chuyển đổi tọa độ giữa không gian thế giới (world space)
và không gian màn hình (screen space). Camera chỉ cuộn theo trục Y,
trục X luôn cố định với offset bằng 0.

Cập nhật lần cuối: 23:17 ngày 28/04/2026
────────────────────────────────────────
CLASS: Camera
Quản lý offset cuộn của màn hình theo vị trí nhân vật người chơi.

Lưu offset_x và offset_y để các hàm chuyển đổi tọa độ biết cần
dịch chuyển bao nhiêu pixel khi vẽ thực thể từ world space lên screen.

  METHOD/FUNC: update
Tính lại offset camera để nhân vật luôn hiển thị tại vị trí cố định trên màn hình.

Input:
    player_world_x (float): Tọa độ X của player trong thế giới (không dùng, giữ offset_x = 0).
    player_world_y (float): Tọa độ Y của player trong thế giới — dùng tính offset_y.

  METHOD/FUNC: world_to_screen
Chuyển tọa độ world space sang pixel screen space để vẽ lên màn hình.

Input:
    wx (float): Tọa độ X trong thế giới.
    wy (float): Tọa độ Y trong thế giới.
Output:
    tuple[int, int]: Cặp (sx, sy) là tọa độ pixel trên màn hình.

  METHOD/FUNC: screen_to_world
Chuyển tọa độ pixel màn hình (thường từ sự kiện chuột) sang world space.

Input:
    sx (float): Tọa độ X trên màn hình (pixel).
    sy (float): Tọa độ Y trên màn hình (pixel).
Output:
    tuple[float, float]: Cặp (world_x, world_y) trong không gian thế giới.


============================================================
  src/managers/game_managers.py
============================================================

FILE: game_managers.py
game_managers.py – Quản lý toàn bộ vòng lặp game.

Game đi LÊN: player.y giảm dần (Y nhỏ hơn = cao hơn / xa hơn).
Quái spawn ở Y = player.y - offset (phía trên player trên màn hình).
────────────────────────────────────────
  METHOD/FUNC: push_out_of_wall
Đẩy một thực thể ra khỏi cạnh gần nhất của chướng ngại vật.

CLASS: MenuManager
Vẽ và xử lý màn hình menu (main menu + game over).

  METHOD/FUNC: draw_main_menu
Vẽ màn hình chủ (Main Menu).

  METHOD/FUNC: draw_game_over
Vẽ màn hình Game Over.

  METHOD/FUNC: handle_main_menu_click
Trả về 'play' nếu click nút bắt đầu.

  METHOD/FUNC: handle_game_over_click
Trả về 'restart' hoặc 'menu'.

  METHOD/FUNC: handle_event
Xử lý input trong lúc chơi. KHÔNG bắt QUIT ở đây.

  METHOD/FUNC: _maybe_spawn
Spawn quái / obstacle phía TRÊN player.
Vì game đi lên, _next_enemy_y giảm dần.
Spawn khi player_y đủ gần _next_enemy_y (tức là đi lên đủ).


============================================================
  src/managers/quadtree.py
============================================================

FILE: quadtree.py
Cấu trúc dữ liệu Quadtree dùng để tăng tốc phát hiện va chạm giữa các thực thể.

Thay vì kiểm tra mọi cặp thực thể O(n²), Quadtree chia không gian thành
4 vùng con đệ quy. Mỗi thực thể chỉ được kiểm tra với những thực thể
trong cùng vùng hoặc vùng lân cận — giảm độ phức tạp xuống O(n log n).
Cây được tạo lại hoàn toàn mỗi frame vì các thực thể di chuyển liên tục.

Cập nhật lần cuối: 12:15 ngày 29/04/2026
────────────────────────────────────────
CLASS: _Rect
Hình chữ nhật axis-aligned dùng nội bộ trong Quadtree để đại diện cho vùng không gian.

CLASS: QuadTree
Cây Quadtree phân vùng không gian 2D để tăng tốc collision detection.

Mỗi node quản lý một vùng hình chữ nhật và tối đa CAPACITY thực thể.
Khi đầy, node tự chia thành 4 vùng con (NW, NE, SW, SE) và phân phối
lại toàn bộ thực thể xuống các con. Độ sâu tối đa là 8 để tránh đệ quy
vô hạn khi nhiều thực thể nằm đúng cùng một điểm.

  METHOD/FUNC: build_quadtree
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

  METHOD/FUNC: contains
Kiểm tra một điểm có nằm trong (hoặc trên biên) hình chữ nhật không.

Input:
    ex (float): Tọa độ X của điểm cần kiểm tra.
    ey (float): Tọa độ Y của điểm cần kiểm tra.
Output:
    bool: True nếu điểm nằm trong hoặc trên biên.

  METHOD/FUNC: intersects
Kiểm tra hai hình chữ nhật có giao nhau không (kể cả chạm cạnh).

Input:
    other (_Rect): Hình chữ nhật cần so sánh.
Output:
    bool: True nếu hai hình chữ nhật giao nhau hoặc chạm cạnh.

  METHOD/FUNC: __init__
Khởi tạo một node Quadtree với vùng quản lý là boundary.

Input:
    boundary (_Rect): Hình chữ nhật xác định vùng không gian node này quản lý.
    depth    (int)  : Độ sâu hiện tại trong cây, dùng để giới hạn đệ quy tối đa 8 cấp.

  METHOD/FUNC: insert
Thêm một thực thể vào cây.

Input:
    entity: Thực thể có thuộc tính .x và .y — là Player, Enemy hoặc Boss.
Output:
    bool: True nếu insert thành công, False nếu thực thể nằm ngoài vùng quản lý.

  METHOD/FUNC: query_radius
Trả về tất cả thực thể nằm trong vùng tìm kiếm hình vuông bao quanh tâm (cx, cy).

Dùng hình vuông thay hình tròn để tránh tính sqrt — bộ lọc chính xác
được thực hiện bên ngoài bằng math.hypot khi cần.

Input:
    cx     (float): Tọa độ X tâm vùng tìm kiếm.
    cy     (float): Tọa độ Y tâm vùng tìm kiếm.
    radius (float): Bán kính (dùng tạo hình vuông 2*radius x 2*radius).
Output:
    list: Danh sách các thực thể nằm trong vùng tìm kiếm.

  METHOD/FUNC: _query
Đệ quy thu thập tất cả thực thể trong các node giao với rect.

Input:
    rect   (_Rect): Hình chữ nhật tìm kiếm.
    result (list) : Danh sách tích lũy kết quả, được sửa trực tiếp (in-place).

  METHOD/FUNC: _subdivide
Chia node hiện tại thành 4 node con bằng nhau và phân phối lại các thực thể.

Giới hạn độ sâu tối đa là 8 để tránh đệ quy vô hạn khi nhiều thực thể
nằm đúng cùng một điểm. Nếu đã đạt độ sâu tối đa, không tạo thêm con.


============================================================
  src/entities/__init__.py
============================================================

[Không có docstring]


============================================================
  src/entities/player.py
============================================================

FILE: player.py
player.py – Quản lý nhân vật người chơi: trạng thái, di chuyển, tấn công, blink và buff.

Xử lý toàn bộ vòng đời của Player: nhận input di chuyển/tấn công từ GameManager,
thực thi cơ chế blink hai giai đoạn (pre-stun → teleport → post-stun),
windup trước khi bắn, giới hạn vùng di chuyển theo vạch start và biên bản đồ,
đồng bộ chỉ số từ BuffManager, và vẽ toàn bộ hiệu ứng lên màn hình.

Last modified: 10:47 PM 12/5/2026
────────────────────────────────────────
CLASS: Player
Quản lý toàn bộ trạng thái và hành vi của nhân vật chính.

  METHOD/FUNC: _any_circle_rect
Kiểm tra hình tròn có chạm bất kỳ chướng ngại vật nào trong danh sách không.

Input:
    cx        (float): Tọa độ X tâm hình tròn.
    cy        (float): Tọa độ Y tâm hình tròn.
    r         (float): Bán kính hình tròn.
    obstacles (list) : Danh sách dict {'x','y','w','h'}.
Output:
    bool: True nếu có ít nhất một va chạm.

  METHOD/FUNC: _circle_rect
Kiểm tra va chạm giữa hình tròn và một hình chữ nhật bằng điểm gần nhất.

Input:
    cx        (float): Tọa độ X tâm hình tròn.
    cy        (float): Tọa độ Y tâm hình tròn.
    r         (float): Bán kính hình tròn.
    rect_dict (dict) : Hình chữ nhật với các key 'x', 'y', 'w', 'h'.
Output:
    bool: True nếu hình tròn và hình chữ nhật giao nhau.

  METHOD/FUNC: __init__
Khởi tạo player tại vị trí (x, y).

Input:
    x (float): Tọa độ X ban đầu trong world space.
    y (float): Tọa độ Y ban đầu trong world space — đây cũng là start_y, giới hạn dưới.

  METHOD/FUNC: apply_buff_stats
Đồng bộ chỉ số speed và blink_cooldown theo trạng thái buff hiện tại.
Được GameManager gọi mỗi frame sau khi BuffManager.update() xong.

Input:
    fire (bool): True nếu BUFF_FIRE đang active.
    wind (bool): True nếu BUFF_WIND đang active.

  METHOD/FUNC: blink_ready
Kiểm tra kỹ năng Blink có sẵn sàng không.

Output:
    bool: True nếu hết cooldown, không đang trong pre-stun và không đang post-stun.

  METHOD/FUNC: attack_ready
Kiểm tra player có thể khai hỏa không.

Output:
    bool: True nếu cả attack_timer lẫn windup_timer đều về 0.

  METHOD/FUNC: _is_frozen
Trả về True nếu player đang bị khựng (windup tấn công, pre-stun hoặc post-stun blink).

Output:
    bool: True khi player không thể di chuyển.

  METHOD/FUNC: set_move_target
Đặt điểm đến để player tự di chuyển tới. Bỏ qua nếu đang bị khựng.
Điểm đến bị kẹp để không vượt xuống dưới vạch start.

Input:
    world_x (float): Tọa độ X đích trong world space.
    world_y (float): Tọa độ Y đích trong world space.

  METHOD/FUNC: try_blink
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

  METHOD/FUNC: _execute_blink
Thực hiện teleport ngay sau khi pre-stun kết thúc, rồi bật post-stun.
Chỉ được gọi nội bộ từ update() khi _blink_pre_stun về 0.

  METHOD/FUNC: try_attack
Giai đoạn 1 của tấn công: bắt đầu windup, hủy di chuyển.

Input:
    direction_x (float): Thành phần X của hướng bắn.
    direction_y (float): Thành phần Y của hướng bắn.
    projectiles (list) : Danh sách đạn để thêm vào sau khi windup xong.

  METHOD/FUNC: _execute_attack
Giai đoạn 2 của tấn công: tạo đạn sau khi windup hoàn tất.

  METHOD/FUNC: take_damage
Trừ máu và bật hiệu ứng chớp trắng. Đặt alive = False khi máu về 0.

Input:
    dmg (int): Lượng sát thương cần trừ.

  METHOD/FUNC: update
Cập nhật toàn bộ trạng thái player mỗi frame: đếm ngược cooldown,
xử lý blink hai giai đoạn, windup tấn công, di chuyển có va chạm,
giới hạn biên bản đồ và vạch start, ghi lại Y nhỏ nhất để tính điểm.

Input:
    dt        (float): Thời gian trôi qua giữa 2 frame (giây).
    obstacles (list) : Danh sách dict chướng ngại vật {'x','y','w','h'}.

  METHOD/FUNC: draw
Vẽ player và toàn bộ hiệu ứng lên surface: bóng ma blink, vòng pre-stun nhấp nháy,
vòng post-stun vàng, thân, thanh máu, vòng cung cooldown blink, chấm đích di chuyển.

Input:
    surface (pygame.Surface): Bề mặt màn hình để vẽ lên.
    camera  (Camera)        : Dùng để chuyển tọa độ world sang screen.


============================================================
  src/entities/enemy.py
============================================================

FILE: enemy.py
Quái thường với hai kiểu hành vi tấn công khác nhau.

Type 1 bắn đạn thẳng có tính toán dự đoán vị trí người chơi.
Khi PlayerTracker cung cấp đủ dữ liệu, Type 1 nâng cấp lên
bắn đón hướng né quen thuộc của player (behavior modeling).
Type 2 đặt vùng nổ AoE trễ gần vị trí người chơi.
Cả hai loại không di chuyển — đứng yên và tấn công theo cooldown.
────────────────────────────────────────
  METHOD/FUNC: _crop_alpha
Cắt bỏ vùng trong suốt xung quanh, trả về bounding box thực của sprite.

Input:
    surface (pygame.Surface): Surface cần crop.
Output:
    pygame.Surface: Surface đã crop, hoặc surface gốc nếu lỗi.

  METHOD/FUNC: _load_strip
Cắt spritesheet nằm ngang thành danh sách Surface, crop alpha rồi scale về target_h.

Input:
    path     (str): Đường dẫn file spritesheet.
    n_frames (int): Số frame đều nhau theo chiều ngang.
    target_h (int): Chiều cao đích sau khi scale.
Output:
    list[pygame.Surface]: Danh sách frame đã scale, rỗng nếu lỗi.

  METHOD/FUNC: _load_single
Tải ảnh đơn, crop alpha bounding box, rồi scale về target_h.

Input:
    path     (str): Đường dẫn file ảnh.
    target_h (int): Chiều cao đích.
Output:
    pygame.Surface | None: Surface đã scale, None nếu lỗi.

  METHOD/FUNC: _get_sprites
Trả về dict sprite đã load (lazy-load lần đầu).

Output:
    dict: Chứa các key 'blue_idle', 'blue_atk', 'red_idle', 'red_atk', ...

CLASS: Enemy
Quái đứng yên, tự động tấn công khi player vào tầm, hiển thị sprite animation.

  METHOD/FUNC: generate_enemy_cluster
Tạo một đợt quái tại hàng world_y, số lượng và cooldown tăng theo điểm số.

Input:
    world_y  (float): Tọa độ Y spawn.
    score    (int)  : Điểm số hiện tại.
    map_type (str)  : 'fire' hoặc 'water' — truyền xuống Enemy để chọn sprite đúng phe.
Output:
    list[Enemy]: Danh sách quái vừa tạo.

  METHOD/FUNC: _spread_positions
Chia đều n vị trí X trong chiều rộng bản đồ với nhiễu nhỏ.

Input:
    n      (int): Số vị trí.
    width  (int): Chiều rộng bản đồ.
    margin (int): Khoảng cách tối thiểu từ biên.
Output:
    list[float]: Danh sách tọa độ X đã xáo trộn.

  METHOD/FUNC: __init__
Khởi tạo quái tại (x, y).

Input:
    x        (float): Tọa độ X world space.
    y        (float): Tọa độ Y world space.
    etype    (int)  : 1 = ranged (bắn đạn), 2 = siege (AoE trễ).
    map_type (str)  : 'fire' hoặc 'water' — xác định phe màu sắc sprite.

  METHOD/FUNC: take_damage
Trừ máu, bật flash trắng, đánh dấu chết khi máu về 0.

Input:
    dmg (int): Lượng sát thương.

  METHOD/FUNC: in_range
Kiểm tra player có trong tầm tấn công không.

Input:
    px (float): Tọa độ X player.
    py (float): Tọa độ Y player.
Output:
    bool: True nếu khoảng cách ≤ attack_range.

  METHOD/FUNC: update
Cập nhật trạng thái mỗi frame: hướng quay, animation, cooldown, tấn công.

Input:
    dt              (float): Thời gian trôi qua (giây).
    player          (Player): Đối tượng player.
    projectiles     (list) : Danh sách đạn.
    delayed_attacks (list) : Danh sách AoE trễ.
    tracker                : PlayerTracker tùy chọn.

  METHOD/FUNC: _fire
Thực hiện đòn tấn công theo etype.

  METHOD/FUNC: draw
Vẽ quái: sprite animation quay theo hướng + thanh máu.

Input:
    surface (pygame.Surface): Bề mặt màn hình.
    camera  (Camera)        : Chuyển tọa độ world sang screen.


============================================================
  src/entities/boss.py
============================================================

FILE: boss.py
boss.py – Quản lý kẻ địch đặc biệt Boss với hai pha tấn công mặc định và behavior modeling.

Boss lắc ngang liên tục, chờ player vào tầm rồi thực hiện windup
trước khi khai hỏa. Khi PlayerTracker tích lũy đủ 120 frame dữ liệu,
Boss phân tích BehaviorProfile để chọn pattern tấn công phù hợp:
    - Player aggressive  → AoE phạt việc áp sát.
    - Player hay né trái/phải → wide spread bịt đường né.
    - Player phòng thủ   → snipe chính xác vào vị trí yêu thích.
Khi chưa đủ data thì dùng hai pha mặc định (spread / aoe).

Last modified: 10:22 PM 12/5/2026
────────────────────────────────────────
  METHOD/FUNC: _load_strip
Cắt spritesheet ngang thành danh sách Surface và scale về target_h.

Input:
    path     (str): Đường dẫn spritesheet.
    n_frames (int): Số frame.
    target_h (int): Chiều cao đích.
Output:
    list[pygame.Surface]: Danh sách frame, rỗng nếu lỗi.

  METHOD/FUNC: _get_boss_sprites
Trả về dict sprite boss đã load (lazy-load lần đầu).

Output:
    dict: key 'fire' và 'water', mỗi key là list frame dragon animation.

CLASS: Boss
Quản lý trạng thái, chuyển động, windup, tấn công và sprite animation của Boss.

  METHOD/FUNC: __init__
Khởi tạo Boss tại vị trí (x, y).

Input:
    x        (float): Tọa độ X ban đầu.
    y        (float): Tọa độ Y ban đầu.
    map_type (str)  : 'fire' hoặc 'water' xác định sprite dragon.

  METHOD/FUNC: take_damage
Trừ máu, bật flash và đánh dấu chết khi máu về 0.

Input:
    dmg (int): Lượng sát thương.

  METHOD/FUNC: in_range
Kiểm tra player có trong tầm tấn công không.

Input:
    px (float): Tọa độ X player.
    py (float): Tọa độ Y player.
Output:
    bool: True nếu khoảng cách ≤ attack_range.

  METHOD/FUNC: update
Cập nhật Boss mỗi frame: animation, lắc ngang, cooldown, windup, tấn công.

Input:
    dt              (float): Thời gian trôi qua (giây).
    player          (Player): Đối tượng player.
    projectiles     (list) : Danh sách đạn.
    delayed_attacks (list) : Danh sách AoE trễ.
    tracker                : PlayerTracker tùy chọn.

  METHOD/FUNC: _choose_pattern
Chọn pattern tấn công dựa trên BehaviorProfile.

Input:
    profile (BehaviorProfile): Snapshot hành vi player từ PlayerTracker.
Output:
    str: Một trong 'aoe', 'wide_spread', 'snipe', 'spread'.

  METHOD/FUNC: _fire
Thực hiện pattern tấn công đã được chọn sau windup.

Input:
    player          (Player): Dùng để tính hướng/vị trí bắn.
    projectiles     (list) : Danh sách đạn.
    delayed_attacks (list) : Danh sách AoE trễ.
    tracker                : PlayerTracker tùy chọn.

  METHOD/FUNC: _do_spread
Bắn nhiều đạn tỏa góc theo danh sách spreads.

Input:
    player      (Player): Dùng để tính hướng.
    projectiles (list)  : Danh sách đạn.
    spreads     (list)  : Độ lệch góc (radian) mỗi đạn.
    speed_mult  (float) : Hệ số nhân tốc độ đạn.

  METHOD/FUNC: draw
Vẽ Boss: dragon sprite quay hướng, vòng pulse, vòng windup, thanh máu, nhãn BOSS.

Input:
    surface (pygame.Surface): Bề mặt màn hình.
    camera  (Camera)        : Chuyển tọa độ world sang screen.


============================================================
  src/entities/projectile.py
============================================================

FILE: projectile.py
Định nghĩa các lớp đạn và đòn tấn công trễ trong game.

Projectile là đạn bay thẳng theo vận tốc cố định, tự hủy khi đi quá tầm
hoặc ra khỏi biên bản đồ. DelayedCircleAttack là vùng nổ AoE được kích hoạt
sau một khoảng trễ — trong thời gian chờ có hiệu ứng cảnh báo vòng tròn co dần,
khi nổ có hiệu ứng flash cam đỏ tắt nhanh.

Cập nhật lần cuối: 23:17 ngày 28/04/2026
────────────────────────────────────────
  METHOD/FUNC: _load_strip
Cắt spritesheet ngang thành danh sách Surface và scale về target_h.

Input:
    path     (str): Đường dẫn spritesheet.
    n_frames (int): Số frame.
    target_h (int): Chiều cao đích.
Output:
    list[pygame.Surface]: Danh sách frame, rỗng nếu lỗi.

  METHOD/FUNC: _get_proj_sprites
Trả về dict sprite đạn/nổ đã load (lazy-load lần đầu).

Output:
    dict: key 'fireball' (list frame), 'explosion' (list frame).

CLASS: Projectile
Quản lý trạng thái và hiển thị của viên đạn bay thẳng.

Dùng sprite fire_ball quay theo góc bay khi use_fireball_sprite=True,
fallback về hình tròn + vệt đuôi nếu sprite không load được.

CLASS: DelayedCircleAttack
Quản lý vùng nổ AoE được kích hoạt sau khoảng trễ, hiển thị sprite explosion khi nổ.

Trong giai đoạn chờ: vòng cảnh báo vàng mở rộng dần.
Khi nổ: sprite explosion chạy full animation rồi tự hủy.

  METHOD/FUNC: __init__
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

  METHOD/FUNC: update
Di chuyển đạn, tiến frame animation và kiểm tra điều kiện tự hủy.

Input:
    dt (float): Thời gian trôi qua (giây).

  METHOD/FUNC: hits
Kiểm tra đạn có chạm vào hình tròn của thực thể mục tiêu không.

Input:
    entity_x (float): Tọa độ X tâm mục tiêu.
    entity_y (float): Tọa độ Y tâm mục tiêu.
    entity_r (float): Bán kính mục tiêu.
Output:
    bool: True nếu giao nhau.

  METHOD/FUNC: draw
Vẽ đạn: sprite fire_ball xoay theo hướng bay, hoặc fallback vệt đuôi + hình tròn.

Input:
    surface (pygame.Surface): Bề mặt màn hình.
    camera  (Camera)        : Chuyển tọa độ world sang screen.

  METHOD/FUNC: __init__
Khởi tạo vùng nổ trễ.

Input:
    owner  (str)  : 'enemy' hoặc 'boss'.
    x, y   (float): Tọa độ tâm nổ trong world space.
    aoe_r  (float): Bán kính vùng sát thương.
    dmg    (int)  : Sát thương gây ra khi nổ.
    delay  (float): Thời gian chờ (giây) trước khi nổ.

  METHOD/FUNC: update
Đếm ngược thời gian trễ, chuyển sang triggered và chạy animation explosion.

Input:
    dt (float): Thời gian trôi qua (giây).

  METHOD/FUNC: hits
Kiểm tra vùng nổ có chạm vào thực thể sau khi đã triggered không.

Input:
    entity_x (float): Tọa độ X tâm mục tiêu.
    entity_y (float): Tọa độ Y tâm mục tiêu.
    entity_r (float): Bán kính mục tiêu.
Output:
    bool: True khi triggered và mục tiêu nằm trong aoe_r.

  METHOD/FUNC: draw
Vẽ AoE: vòng cảnh báo vàng khi chờ, sprite explosion khi nổ.

Input:
    surface (pygame.Surface): Bề mặt màn hình.
    camera  (Camera)        : Chuyển tọa độ world sang screen.



"""
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
"""
PATH_MAP_FIRE = "src/assets/fire_map.jpg"

PATH_MAP_WATER = "src/assets/water_map.jpg"

MAP_POOL = ["fire", "water"]

MAP_TRANSITION_DELAY = 1.0   

SCREEN_WIDTH  = 600
SCREEN_HEIGHT = 800
MAP_WIDTH     = SCREEN_WIDTH
WORLD_ORIGIN_Y = 0

PLAYER_SCREEN_Y = SCREEN_HEIGHT - 300

R = 800
BLINK_RANGE = 200

FPS = 60
ENEMY_ATTACK_COOLDOWN  = 5.0
BOSS_ATTACK_COOLDOWN   = 4.0
TYPE2_DELAY            = 1.2
PROJECTILE_SPEED       = 600
ENEMY_PROJ_SPEED       = 150

PLAYER_RADIUS   = 16
ENEMY_RADIUS    = 18
BOSS_RADIUS     = 36
OBSTACLE_W      = 80
OBSTACLE_H      = 40

PLAYER_MAX_HP       = 100
PLAYER_ATTACK_DMG   = 1
PLAYER_ATTACK_RANGE = 600
PLAYER_ATTACK_COOLDOWN = 0.5
PLAYER_ATTACK_WINDUP   = 0.2
ENEMY_HP            = 1
BOSS_HP             = 20
BOSS_DMG            = 2
PASSIVE_REGEN_INTERVAL = 15.0   
PASSIVE_REGEN_AMOUNT   = 1

BOSS_SCORE_INTERVAL = 1000
SCORE_KILL_NORMAL   = 50
SCORE_KILL_BOSS     = 500

ENEMY_SPAWN_INTERVAL   = 400
OBSTACLE_SPAWN_INTERVAL = 400

# --- Map phase (ngưỡng điểm chuyển map) ---
MAP_PHASE_1_SCORE = 0        
MAP_PHASE_2_SCORE = 15000   
MAP_PHASE_3_SCORE = 30000    

# --- Buff ID ---
BUFF_WATER = "buff_water"   
BUFF_FIRE  = "buff_fire"  
BUFF_WIND  = "buff_wind"     

BUFF_WATER_DURATION = 60.0
BUFF_FIRE_DURATION  = 30.0
BUFF_WIND_DURATION  = 120.0

BUFF_WATER_REGEN_INTERVAL = 3.0   # hồi máu mỗi 3 giây
BUFF_WATER_REGEN_AMOUNT   = 1

# --- Màu sắc map ---
# Map 1 — nước (xanh dương)
MAP1_COL_BG     = (5,   15,  35)
MAP1_COL_GRID   = (15,  40,  80)
MAP1_COL_OBS    = (20,  60,  110)
MAP1_COL_OBS_BD = (30,  90,  160)

# Map 2 — lửa (đỏ cam)
MAP2_COL_BG     = (30,  8,   5)
MAP2_COL_GRID   = (70,  20,  10)
MAP2_COL_OBS    = (100, 35,  15)
MAP2_COL_OBS_BD = (160, 60,  20)

# Map 3 — gió (xanh lá nhạt / trắng xanh)
MAP3_COL_BG     = (8,   25,  20)
MAP3_COL_GRID   = (20,  60,  45)
MAP3_COL_OBS    = (30,  80,  60)
MAP3_COL_OBS_BD = (50,  130, 90)

# Màu sắc mặc định (dùng khi chưa xác định map)
COL_BG           = (10,  12,  20)
COL_GROUND       = (20,  25,  40)
COL_GRID         = (25,  32,  55)
COL_PLAYER       = (80, 200, 255)
COL_PLAYER_HP    = (0,  220,  80)
COL_ENEMY1       = (220, 80,  60)
COL_ENEMY2       = (220, 160,  40)
COL_BOSS         = (180,  30, 220)
COL_OBSTACLE     = (50,  60,  90)
COL_PROJ_PLAYER  = (120, 240, 120)
COL_PROJ_ENEMY   = (255, 100,  60)
COL_WARN_CIRCLE  = (255, 200,  40)
COL_BLINK_FX     = (80,  180, 255)
COL_HIT_FLASH    = (255, 255, 255)
COL_TEXT         = (220, 230, 255)
COL_SCORE        = (255, 220,  60)
COL_HP_BAR_BG    = (60,  10,  10)
COL_HP_BAR_FG    = (220,  50,  50)
COL_BOSS_HP_FG   = (180,  30, 220)
COL_OVERLAY      = (0,    0,   0)

TYPE2_AOE_R      = 80
BOSS_TYPE2_AOE_R = 140
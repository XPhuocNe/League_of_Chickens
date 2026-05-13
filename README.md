# League of Chickens.

> Game bắn súng theo hướng nhìn từ trên xuống (top-down shooter), kết hợp cơ chế leo lên vô tận với hệ thống Boss thông minh học cách bạn chơi để tấn công lại.

---

## Giới Thiệu

**League of Chickens** là game hành động 2D viết bằng Python + Pygame, lấy cảm hứng từ thể loại top-down shooter kết hợp yếu tố roguelite.

Người chơi điều khiển nhân vật di chuyển liên tục lên phía trên bản đồ vô tận, tiêu diệt quái vật, né đòn và đối mặt với Boss xuất hiện định kỳ. Điểm số tăng theo khoảng cách đi được và số quái tiêu diệt.

### Điểm nổi bật

- **Behavior Modeling** — Boss và quái theo dõi thói quen né tránh, hướng di chuyển và mức độ hung hăng của người chơi, sau đó điều chỉnh pattern tấn công theo thời gian thực.
- Sử dụng Quatree để kiểm tra va chạm tổng thể.
- Sử dụng chặt nhị phân để kiểm tra va chạm của người chơi lúc blank.
- **Hai phe map** — Map Lửa và Map Nước luân phiên sau mỗi lần hạ Boss, mỗi phe có sprite và màu sắc riêng.
- **Hệ thống Buff** — Hạ Boss nhận buff đặc biệt: Boss Nước cho buff hồi máu, Boss Lửa cho buff bắn 3 đạn hình nón.
- **Hai loại quái** — Quái Ranged bắn đạn dự đoán vị trí, quái Siege đặt vùng nổ AoE trễ.
- **Boss 4 pattern** — Spread, Wide Spread, Snipe, AoE — Boss chọn pattern dựa trên profile hành vi người chơi.

---

## Hướng Dẫn Chơi

### Điều Khiển

| Phím / Chuột | Hành động |
|---|---|
| **Chuột Phải (RMB)** | Di chuyển đến vị trí click |
| **Chuột Trái (LMB)** | Bắn đạn về phía click |
| **SPACE** | Blink — dịch chuyển nhanh đến vị trí con trỏ (có cooldown) |

### Mục Tiêu

- Di chuyển **lên phía trên** càng xa càng tốt để tăng điểm.
- Tiêu diệt quái và Boss để nhận điểm thưởng.
- Tránh bị đạn và vùng nổ AoE (vòng tròn cảnh báo đỏ) chạm vào người.

### Hệ Thống Điểm

```
Điểm = Khoảng cách đi được + (Quái thường × điểm/quái) + (Boss × điểm/boss)
```

### Quái Vật

| Loại | Hành vi |
|---|---|
| **Ranged (Type 1)** | Bắn đạn thẳng, có tính toán dự đoán vị trí người chơi |
| **Siege (Type 2)** | Đặt vùng nổ AoE trễ gần vị trí người chơi — chú ý vòng cảnh báo! |

### Boss

Boss xuất hiện định kỳ theo mốc điểm số. Boss lắc ngang liên tục và có windup (vòng tròn đỏ co lại) trước khi tấn công. Sau **120 frame** quan sát, Boss chuyển sang dùng pattern thông minh:

- **Bạn hay lao vào gần** → Boss dùng AoE phạt vào vị trí bạn.
- **Bạn hay né trái/phải** → Boss bắn Wide Spread bịt đường né.
- **Bạn phòng thủ, đứng yên** → Boss Snipe chính xác vào vị trí yêu thích.

### Buff Sau Khi Hạ Boss

| Boss | Buff |
|---|---|
| Boss Nước | Hồi 1 HP mỗi 3 giây trong 60 giây |
| Boss Lửa | Bắn 3 đạn hình nón trong 45 giây |

---

## ⚙️ Hướng Dẫn Cài Đặt

### Yêu Cầu Hệ Thống

- Python **3.10** trở lên
- pip

### Cài Đặt

**1. Clone repository**

```bash
git clone https://github.com/<your-username>/league-of-chickens.git
cd league-of-chickens
```

**2. Tạo môi trường ảo (khuyến nghị)**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Cài thư viện**

```bash
pip install -r requirements.txt
```

Nếu chưa có file `requirements.txt`, cài thủ công:

```bash
pip install pygame numpy
```

**4. Chạy game**

```bash
python src/main.py
```

### Cấu Trúc Thư Mục

```
league-of-chickens/
├── src/
│   ├── assets/                  # Sprite, ảnh nền, âm thanh
│   ├── entities/
│   │   ├── player.py            # Logic người chơi, blink, tấn công
│   │   ├── enemy.py             # Quái Ranged & Siege + spawn cluster
│   │   ├── boss.py              # Boss với behavior modeling
│   │   └── projectile.py        # Đạn & AoE trễ
│   ├── managers/
│   │   ├── camera.py            # Camera theo dõi player
│   │   ├── game_managers.py     # Vòng lặp gameplay chính
│   │   ├── buff_manager.py      # Quản lý buff người chơi
│   │   ├── player_tracker.py    # Behavior modeling
│   │   └── quadtree.py          # Tối ưu collision detection
│   ├── constants.py             # Hằng số toàn cục
│   └── main.py                  # Entry point
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Công Nghệ Sử Dụng

- **Python 3.10+**
- **Pygame** — vòng lặp game, render, xử lý input
- **NumPy** — xử lý pixel spritesheet (crop alpha, background removal)

---

##  Tác Giả

**Lê Xuân Phước** — 2025

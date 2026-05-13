"""
Điểm khởi động game và vòng lặp chính.

Quản lý chuyển đổi giữa ba trạng thái ứng dụng:
- 'main_menu': hiển thị màn hình chính, chờ người dùng nhấn bắt đầu.
- 'playing': chạy GameManager, kiểm tra điều kiện chuyển sang game_over.
- 'game_over': vẽ game phía dưới làm nền rồi phủ màn hình kết quả lên trên.

Cập nhật lần cuối: 23:17 ngày 28/04/2026
"""
import pygame
import sys
import os

from constants import * 
from managers.game_managers import GameManager, MenuManager 


def main():
    """Khởi tạo pygame, tạo cửa sổ và chạy vòng lặp game cho đến khi thoát."""
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Welcome to League of Chickens")

    clock   = pygame.time.Clock()
    menu    = MenuManager(screen)
    game    = None

    app_state = "main_menu"

    running = True
    dt = 0.0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                break

            if app_state == "main_menu":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = menu.handle_main_menu_click(event.pos)
                    if action == "play":
                        game = GameManager(screen)
                        app_state = "playing"

            elif app_state == "playing":
                if game:
                    game.handle_event(event)

            elif app_state == "game_over":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = menu.handle_game_over_click(event.pos)
                    if action == "restart":
                        game = GameManager(screen)
                        app_state = "playing"
                    elif action == "menu":
                        game = None
                        app_state = "main_menu"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    game = GameManager(screen)
                    app_state = "playing"

        if not running:
            break

        menu.update(dt)

        if app_state == "main_menu":
            menu.draw_main_menu()

        elif app_state == "playing" and game:
            game.update(dt)
            game.draw()

            if game.state == "dead" and game._death_timer > 1.5:
                app_state = "game_over"

        elif app_state == "game_over" and game:
            game.draw()
            menu.draw_game_over(game.score, game.kills_normal, game.kills_boss)

        pygame.display.flip()
        dt = clock.tick(FPS) / 1000.0

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

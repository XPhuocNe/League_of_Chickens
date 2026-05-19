def main():
    pygame.init()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("GAME LOL x BẮN GÀ - Lê Xuân Phước")
    
    game_manager = GameManager(screen)
    
    clock = pygame.time.Clock()
    running = True
    dt = 0.0

    print("=== GAME LOL x BẮN GÀ ĐÃ KHỞI ĐỘNG ===")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            game_manager.handle_event(event)

        game_manager.update(dt)
        game_manager.draw()

        dt = clock.tick(FPS) / 1000.0

    pygame.quit()
    sys.exit()
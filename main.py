# modules
import pygame
import os
import time
from pynput import keyboard
import random
import sys
pygame.font.init()

#center game window into center
os.environ['SDL_VIDEO_CENTERED'] = '1'

WIDTH, HEIGHT = 800, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

# load images
RED_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))

# player ship
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png"))

# lasers
RED_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png"))

# background
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))

class Laser:
    """laser class"""
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not (self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


class Ship:
    """abstract ship class parent class"""

    COOLDOWN = 30
    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

class Player(Ship):
    """Player's Ship"""
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.player_img = YELLOW_SPACE_SHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.player_img)
        self.max_health = health

    def draw(self, window):
        window.blit(self.player_img, (self.x, self.y))
        self.healthbar(window)
        super().draw(window)

    def get_width(self):
        return self.player_img.get_width()

    def get_height(self):
        return self.player_img.get_height()

    def move_lasers(self, vel, objs):
        self.cooldown()
        lasers_to_remove = []
        objs_to_remove = []
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                lasers_to_remove.append(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs_to_remove.append(obj)
                        lasers_to_remove.append(laser)
        lasers_to_remove = list(set(lasers_to_remove))
        for laser in lasers_to_remove:
            self.lasers.remove(laser)
        for obj in objs_to_remove:
            objs.remove(obj)

    def healthbar(self, window):
        pygame.draw.rect(window, (255, 0, 0), (self.x, (self.y + self.player_img.get_height()) + 10, self.player_img.get_width(), 10))
        pygame.draw.rect(window, (0, 255, 0), (self.x, (self.y + self.player_img.get_height()) + 10, self.player_img.get_width() * (1-((self.max_health-self.health)/self.max_health)), 10))


class Enemy(Ship):
    """Enemy's Ship"""
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, RED_LASER),
        "green": (GREEN_SPACE_SHIP, GREEN_LASER),
        "blue": (BLUE_SPACE_SHIP, BLUE_LASER)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health=100)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)


    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))


    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

    def move(self, enemy_vel):
        self.y += enemy_vel



def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None


#main game loop
pause = False


def main():
    #main game vars
    run = True
    FPS = 60
    level = 0
    lives = 5
    main_font = pygame.font.SysFont("comicsans", 50)
    lost_font = pygame.font.SysFont("comicsans", 60)
    enemies = []
    wave_length = 5
    player_vel = 5
    enemy_vel = 2
    laser_vel = 10
    player = Player(300, 650)
    clock = pygame.time.Clock()
    lost = False
    lost_count = 0

    def keybind(key):
        global pause
        if (str(key)[1] == 'p'):
            pause = not pause
        elif (str(key)[1] == 'q'):
            run = False



    listener = keyboard.Listener(on_press=keybind)
    listener.start()

    def redraw_window():
        global pause_text, lost_text
        WIN.blit(BG, (0, 0))
        # draw text
        lives_label = main_font.render(f"Lives: {lives}", 1, (255, 255, 255))
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))
        pause_text = main_font.render("Game Paused. Press 'p' to unpause", 1, (255, 255, 255))
        lost_text = lost_font.render(f"YOU LOST!!", 1, (255, 255, 255))

        WIN.blit(lives_label, (10, 10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))

        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)
        pygame.display.update()


    while run:
        #run game at correct FPS
        clock.tick(FPS)
        keys = pygame.key.get_pressed()


        # player movement
        if keys[pygame.K_LEFT] and player.x - player_vel + 10 > 0:  # left
            player.x -= player_vel
        if keys[pygame.K_RIGHT] and player.x + player_vel + player.get_width() - 10 < WIDTH:  # right
            player.x += player_vel
        if keys[pygame.K_UP] and player.y - player_vel > 0 - 10:  # up
            player.y -= player_vel
        if keys[pygame.K_DOWN] and player.y + player_vel + player.get_height() < HEIGHT:  # down
            player.y += player_vel

        if pause:
            WIN.blit(pause_text, (100, 300))
            pygame.display.update()
            continue

        redraw_window()

        #if player health or lives = 0
        if lives == 0 or player.health == 0:
            lost = True

        if lost == True:
            WIN.blit(lost_text, (WIDTH/2 - (lost_text.get_width()/2), HEIGHT/2 - (lost_text.get_height()/2)))
            pygame.display.update()
            time.sleep(3)
            sys.exit()

        if len(enemies) == 0:
            level += 1
            wave_length += 1
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH-100), random.randrange(-1500, -100), random.choice(["red", "blue", "green"]))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()


        #laser shooting
        if keys[pygame.K_SPACE]:
            player.shoot()

        #moves enemies and controls what happens when they reach the bottom of the screen
        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.draw(WIN)



            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)

            if enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)


        player.move_lasers(-laser_vel, enemies)


def main_menu():
    title_font = pygame.font.SysFont("comicsans", 70)
    run = True
    while run:
        WIN.blit(BG, (0, 0))
        title_label = title_font.render("Click the mouse to begin...", 1, (255, 255, 255))
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 350))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()

    pygame.quit()

#run game loop
main_menu()

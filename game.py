import pygame
from pygame import mixer 
import csv
import sys
import os

pygame.init()
mixer.init()
bgm = mixer.music.load("sounds/bg.wav")

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Platformer Game - Collect the coin')


clock = pygame.time.Clock()
FPS = 60


ROWS = 16
TILE_SIZE = SCREEN_HEIGHT // ROWS
MAX_COLS = 150


GREEN = (144, 201, 120)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (200, 25, 25)
YELLOW = (255, 255, 0)


pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()


img_list = []
for x in range(3):
    img = pygame.image.load(f'img/tile/{x}.png').convert_alpha()
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

class AudioManager:
    def __init__(self):
        self.sounds = {}
        self.music_volume = 0.8
        self.sfx_volume = 1
        self.load_audio()
        
    def load_audio(self):
        pygame.mixer.music.load('sounds/bg.wav')
            
        self.sounds['jump'] = pygame.mixer.Sound('sounds/jump.wav')
        self.sounds['coin'] = pygame.mixer.Sound('sounds/coin.wav')
            
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)
                
    def play_music(self):
        try:
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)  
        except:
            print("Could not play background music")
    
    def play_sound(self, sound_name):
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                pass
    
    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)


def load_player_animations():
    animations = {
        'idle': [pygame.transform.scale((pygame.image.load(f'img/avatar.png').convert_alpha()),(TILE_SIZE+ 20, TILE_SIZE+ 20))],
        'run': [pygame.transform.scale((pygame.image.load(f'img/avatar.png').convert_alpha()),(TILE_SIZE+ 20, TILE_SIZE+ 20)),pygame.transform.scale((pygame.image.load(f'img/avatar1.png').convert_alpha()),(TILE_SIZE+ 20, TILE_SIZE+ 20))],
        'jump': [pygame.transform.scale((pygame.image.load(f'img/avatar1.png').convert_alpha()),(TILE_SIZE+ 20, TILE_SIZE+ 20))],
        'fall': [pygame.transform.scale((pygame.image.load(f'img/avatar1.png').convert_alpha()),(TILE_SIZE+ 20, TILE_SIZE+ 20))]
    }
    
    
    return animations



coin_img = pygame.image.load('img/tile/2.png').convert_alpha()
coin_img = pygame.transform.scale(coin_img, (TILE_SIZE - 10, TILE_SIZE - 10))

class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x + 5, y + 5, TILE_SIZE - 10, TILE_SIZE - 10)
        self.collected = False
        self.animation_index = 0
        self.animation_speed = 0.2
        
    def update(self):
        self.animation_index += self.animation_speed
        if self.animation_index >= 360:
            self.animation_index = 0
            
    def draw(self, surface, scroll):
        if not self.collected:
            rotated_coin = pygame.transform.rotate(coin_img, self.animation_index)
            new_rect = rotated_coin.get_rect(center=self.rect.center)
            surface.blit(rotated_coin, (new_rect.x - scroll, new_rect.y))

class Player:
    def __init__(self, x, y, animations, audio_manager):
        self.animations = animations
        self.reset(x, y)
        self.audio = audio_manager
        
    def reset(self, x, y):
        self.rect = pygame.Rect(x + 5, y + 2, TILE_SIZE + 10, TILE_SIZE + 10)
        self.vel_x = 0
        self.vel_y = 0
        self.jumping = False
        self.on_ground = False
        self.speed = 5
        self.jump_strength = -12
        self.gravity = 0.5
        self.direction = 1
        self.flip = False
        self.air_timer = 0
        self.animation_index = 0
        self.animation_speed = 0.1
        self.current_state = 'idle'
        
    def update_animation(self):
        if not self.on_ground:
            if self.vel_y < 0:
                self.current_state = 'jump'
            else:
                self.current_state = 'fall'
        elif self.vel_x != 0:
            self.current_state = 'run'
        else:
            self.current_state = 'idle'
            
        if self.current_state in ['run', 'idle']:
            self.animation_index += self.animation_speed
            if self.animation_index >= len(self.animations[self.current_state]):
                self.animation_index = 0
        else:
            self.animation_index = 0 
            
    def update(self, world_data, coins):
        self.vel_y += self.gravity
        
        if self.vel_y > 10:
            self.vel_y = 10
            
        self.rect.x += self.vel_x
        self.collision_x(world_data)
        
        self.rect.y += self.vel_y
        self.on_ground = False
        self.collision_y(world_data)
        
        if not self.on_ground:
            self.air_timer += 1
        else:
            self.air_timer = 0
            
        if self.vel_x > 0:
            self.direction = 1
            self.flip = True
        elif self.vel_x < 0:
            self.direction = -1
            self.flip = False
            
        self.update_animation()
        
        self.collect_coins(coins)
    
    def collect_coins(self, coins):
        for coin in coins:
            if not coin.collected and self.rect.colliderect(coin.rect):
                coin.collected = True
                print("Coin collected!")
                self.audio.play_sound("coin")
    
    def collision_x(self, world_data):
        for y, row in enumerate(world_data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if self.rect.colliderect(tile_rect):
                        if self.vel_x > 0:
                            self.rect.right = tile_rect.left
                        elif self.vel_x < 0:
                            self.rect.left = tile_rect.right
    
    def collision_y(self, world_data):
        for y, row in enumerate(world_data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if self.rect.colliderect(tile_rect):
                        if self.vel_y > 0:
                            self.rect.bottom = tile_rect.top
                            self.on_ground = True
                            self.vel_y = 0
                            self.jumping = False
                        elif self.vel_y < 0:
                            self.rect.top = tile_rect.bottom
                            self.vel_y = 0
        
        if self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
            self.on_ground = True
            self.vel_y = 0
            self.jumping = False
    
    def jump(self):
        if self.on_ground and self.air_timer < 6:
            self.vel_y = self.jump_strength
            self.on_ground = False
            self.jumping = True
            self.air_timer = 6
            self.audio.play_sound('jump')
    
    def draw(self, surface, scroll):
        if self.current_state in self.animations and self.animations[self.current_state]:
            frame_index = int(self.animation_index) % len(self.animations[self.current_state])
            current_frame = self.animations[self.current_state][frame_index]
            
            if self.flip:
                current_frame = pygame.transform.flip(current_frame, True, False) 
            surface.blit(current_frame, (self.rect.x - scroll, self.rect.y))
        else:
            pygame.draw.rect(surface, BLUE, (self.rect.x - scroll, self.rect.y, self.rect.width, self.rect.height))

class Game:
    def __init__(self, level=1):
        self.level = level
        self.scroll = 0
        self.audio = AudioManager()
        self.scroll_thresh = 200
        self.player_animations = load_player_animations()
        self.load_level(level)
        
        start_x, start_y = self.find_start_position()
        self.player = Player(start_x, start_y, self.player_animations, self.audio)
        
        self.game_over = False
        self.victory = False
        self.font = pygame.font.SysFont('Futura', 30)
        
        self.audio.play_music()
        
    def find_start_position(self):
        for y in range(ROWS - 1, -1, -1):
            for x in range(5):
                if self.world_data[y][x] >= 0:
                    return x * TILE_SIZE, (y - 1) * TILE_SIZE
        return 100, SCREEN_HEIGHT - 130
        
    def load_level(self, level):
        self.world_data = []
        self.coins = []
        
        for row in range(ROWS):
            r = [-1] * MAX_COLS
            self.world_data.append(r)
        
        with open(f'level{level}_data.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for x, row in enumerate(reader):
                for y, tile in enumerate(row):
                    if y < MAX_COLS:
                        tile_value = int(tile)
                        self.world_data[x][y] = tile_value
                        
                        if tile_value == 2:  
                            self.coins.append(Coin(y * TILE_SIZE, x * TILE_SIZE))
                            self.world_data[x][y] = -1  
                                
            
    
    def get_remaining_coins(self):
        return sum(1 for coin in self.coins if not coin.collected)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.player.jump()
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r:
                    self.reset_level()
                if event.key == pygame.K_n:
                    self.next_level()
                if event.key == pygame.K_p:
                    self.prev_level()
        return True
    
    def reset_level(self):
        self.scroll = 0
        start_x, start_y = self.find_start_position()
        self.player.reset(start_x, start_y)
        self.game_over = False
        self.victory = False
        for coin in self.coins:
            coin.collected = False
    
    def next_level(self):
        if self.victory:
            self.level += 1
            self.load_level(self.level)
            self.reset_level()
        # self.level += 1
        # self.load_level(self.level)
        # self.reset_level()
    def prev_level(self):
        if self.level > 0:
            self.level -= 1
            self.load_level(self.level)
            self.reset_level()
    
    def update(self):
        keys = pygame.key.get_pressed()
        self.player.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.vel_x = -self.player.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.vel_x = self.player.speed
        
        self.player.update(self.world_data, self.coins)
        
        for coin in self.coins:
            coin.update()
        
        player_screen_x = self.player.rect.x - self.scroll
        if player_screen_x > SCREEN_WIDTH - self.scroll_thresh:
            self.scroll = self.player.rect.x - (SCREEN_WIDTH - self.scroll_thresh)
        if player_screen_x < self.scroll_thresh and self.scroll > 0:
            self.scroll = self.player.rect.x - self.scroll_thresh
        
        level_width = MAX_COLS * TILE_SIZE
        self.scroll = max(0, min(self.scroll, level_width - SCREEN_WIDTH))
        
        if self.player.rect.top > SCREEN_HEIGHT:
            self.game_over = True
            
        if self.get_remaining_coins() == 0:
            self.victory = True
    
    def draw_bg(self):
        screen.fill(GREEN)
        width = sky_img.get_width()
        bg_count = (MAX_COLS * TILE_SIZE) // width + 2
        
        for x in range(bg_count):
            screen.blit(sky_img, ((x * width) - self.scroll * 0.5, 0))
            screen.blit(mountain_img, ((x * width) - self.scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
            screen.blit(pine1_img, ((x * width) - self.scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
            screen.blit(pine2_img, ((x * width) - self.scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))
    
    def draw_world(self):
        start_col = self.scroll // TILE_SIZE
        end_col = start_col + (SCREEN_WIDTH // TILE_SIZE) + 2
        end_col = min(end_col, MAX_COLS)
        
        for y, row in enumerate(self.world_data):
            for x in range(start_col, end_col):
                tile = row[x]
                if tile >= 0:
                    screen.blit(img_list[tile], (x * TILE_SIZE - self.scroll, y * TILE_SIZE))
    
    def draw_coins(self):
        for coin in self.coins:
            coin.draw(screen, self.scroll)
    
    def draw_ui(self):
        level_text = self.font.render(f'Level: {self.level}', True, WHITE)
        screen.blit(level_text, (10, 10))
        
        remaining_coins = self.get_remaining_coins()
        coins_text = self.font.render(f'Coins: {remaining_coins}/{len(self.coins)}', True, YELLOW)
        screen.blit(coins_text, (10, 40))
                
        controls_text = self.font.render('Arrow Keys: Move, Space: Jump, R: Reset, ESC: Quit', True, WHITE)
        screen.blit(controls_text, (10, SCREEN_HEIGHT - 30))
        

        if self.game_over:
            game_over_text = self.font.render('Game Over! Press R to restart', True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))
        
        if self.victory:
            victory_text = self.font.render(f'Level Complete! Coins: {len(self.coins)}/{len(self.coins)} Press N for next level', True, WHITE)
            screen.blit(victory_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2))
    
    def draw(self):
        self.draw_bg()
        self.draw_world()
        self.draw_coins()
        self.player.draw(screen, self.scroll)
        self.draw_ui()
    
    def run(self):
        running = True
        while running:
            clock.tick(FPS)
            
            running = self.handle_events()
            
            if not self.game_over and not self.victory:
                self.update()
            
            self.draw()
            pygame.display.update()

def main():
    level = 1
    if len(sys.argv) > 1:
        try:
            level = int(sys.argv[1])
        except ValueError:
            print("Invalid level number. Starting with level 0.")
    
    game = Game(level)
    game.run()

if __name__ == "__main__":
    main()
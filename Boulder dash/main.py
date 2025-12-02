# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 19:16:50 2023

@author: Barkn
"""
import pygame
import pandas as pd
import time
import sys
import os


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

level = 0

WIDTH, HEIGHT = 1200, 672
DISPLAY_WIDTH, DISPLAY_HEIGHT = 400, 224
TILE_SIZE = 16


'''
SOUNDS
'''
pygame.mixer.init()
dig_dirt_sound = pygame.mixer.Sound("data/mine_dirt.wav")
boulder_crash_sound = pygame.mixer.Sound("data/boulder_crash.wav")
collect_gem_sound = pygame.mixer.Sound("data/collect_gem.wav")
enough_gems_sound = pygame.mixer.Sound("data/enough_gems_collected.wav")
'''
SIMPLIFIERS
'''
    
BASE_IMG_PATH = 'data/bilder/'

def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path)
    return img

def load_images(path):
    images = []
    for img_name in os.listdir(BASE_IMG_PATH + path):
        images.append(load_image(path + '/' + img_name))
    
    return images

def text(text, surf, pos, size):
    font = pygame.font.Font('Retro Gaming.ttf', size)
    text = font.render(text, True, WHITE)
    surf.blit(text, pos)

class Animation:
    def __init__(self, images, image_dur=5):
        self.images = images
        self.img_dur = image_dur
        self.index = 1
    
    def update(self):
        if self.index < len(self.images) - 1:
            self.index += 1 / self.img_dur
        else:
            self.index = 0
    
    def img(self):
        return self.images[int(self.index)]

class Game:
    def __init__(self):
        pygame.init() 
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.display = pygame.Surface((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.transparent_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        pygame.display.set_caption('Boulder Dash')
        
        self.all_sprites = []
        
        self.clock = pygame.time.Clock()
        pygame.time.set_timer(pygame.USEREVENT, 200)
        
        self.gems_needed = 0
        self.lives = 3
        self.level_clear = False
        self.score = 0
        self.hard_score = 0
        self.seconds = 500
        self.frames = 0
        
        if pygame.joystick.get_count() > 0:
            self.jstick = pygame.joystick.Joystick(0)
            self.jon = True
        else:
            self.jon = False
        self.jstick_right = False
        self.jstick_left = False
        self.jstick_up = False
        self.jstick_down = False
        self.move_right = False
        self.move_left = False
        self.move_up = False
        self.move_down = False
        
        self.game_over_anim = Animation(load_images('game_over_animation'), 4)
    
    
    def load_map(self, lv='map0'):
        
        self.map = Tilemap(lv + '.txt')
        
    def new_sprite(self, level):
         self.all_sprites = pygame.sprite.Group()
         self.dirt_sprites = pygame.sprite.Group()
         self.static_sprites = pygame.sprite.Group()
         self.player_sprites = pygame.sprite.Group()
         self.boulder_sprites = pygame.sprite.Group()
         self.roll_sprites = pygame.sprite.Group()
         self.door_sprites = pygame.sprite.Group()
         self.gem_sprites = pygame.sprite.Group()
         self.enemy_sprites = pygame.sprite.Group()
         self.empty_tiles = pygame.sprite.Group()
         self.all_with_empty_sprites = pygame.sprite.Group()
         self.load_map(lv=level)
         
         for row, tiles in enumerate(self.map.data):
             for col, tile in enumerate(tiles): 
                 if tile == 'e':
                     Edge(self, col, row)
                 if tile == '.':
                     Dirt(self, col, row)
                 if tile == 'b':
                     Brick(self, col, row)
                 if tile == 'B':
                     Boulder(self, col, row)
                 if tile == 'G':
                     Gem(self, col, row)
                     self.gems_needed += 1
                 if tile == 'D':
                     Door(self, col, row)
                 if tile == 'E':
                     Enemy(self, col, row)
                 if tile == ' ' or tile == 'x':
                     Empty(self, col, row)
                 if tile == 'P':
                     self.player = Player(self, col, row)
        
         if level == 'map4':
             self.gems_needed = 7
         elif level == 'map2':
             self.gems_needed = 14
         elif level == 'map5':
             self.gems_needed += 10
         self.camera = Camera(self.map.width, self.map.height) 
         
    def run(self):
         global level
         self.running = True
         while self.running:
             self.clock.tick(60)
             
             self.event_handler()
             
             self.death()
             if self.level_clear:
                 self.gems_needed = 0
                 break
             self.update()
             self.draw()
             
    def event_handler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
             if event.key == pygame.K_LEFT:       
                 self.move_right, self.move_up, self.move_down = False, False, False
                 self.move_left = True
             if event.key == pygame.K_RIGHT:
                 self.move_left, self.move_up, self.move_down = False, False, False
                 self.move_right = True
             if event.key == pygame.K_UP:
                 self.move_right, self.move_left, self.move_down = False, False, False
                 self.move_up = True
             if event.key == pygame.K_DOWN:
                 self.move_right, self.move_up, self.move_left = False, False, False
                 self.move_down = True
             if event.key == pygame.K_ESCAPE:
                 self.pause_menu()
                
            if event.type == pygame.KEYUP:
             if event.key == pygame.K_LEFT: 
                 self.move_left = False
                 self.player.idle_timer = 17
             if event.key == pygame.K_RIGHT:
                 self.move_right = False
                 self.player.idle_timer = 17
             if event.key == pygame.K_UP:
                 self.move_up = False
                 self.player.idle_timer = 17
             if event.key == pygame.K_DOWN:
                 self.move_down = False
                 self.player.idle_timer = 17
            
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 7:
                    self.pause_menu()
            
            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 0 and self.jstick.get_axis(0) > 0.9 and self.jstick.get_axis(0) < 1.1:
                    self.jstick_right = True
                    self.jstick_down, self.jstick_up, self.jstick_left = False, False, False
                if event.axis == 0 and self.jstick.get_axis(0) > -1.1 and self.jstick.get_axis(0) < -0.9:
                    self.jstick_left = True
                    self.jstick_down, self.jstick_up, self.jstick_right = False, False, False
                if event.axis == 1 and self.jstick.get_axis(1) > -1.1 and self.jstick.get_axis(1) < -0.9:
                    self.jstick_up = True
                    self.jstick_down, self.jstick_right, self.jstick_left = False, False, False
                if event.axis == 1 and self.jstick.get_axis(1) < 1.1 and self.jstick.get_axis(1) > 0.9:
                    self.jstick_down = True
                    self.jstick_right, self.jstick_up, self.jstick_left = False, False, False
            
            if event.type == pygame.USEREVENT:
                if self.jon:
                    self.joy_movement()
                else:
                    self.key_movement()
                
    
    def joy_movement(self):
        if self.jstick.get_axis(0) > -0.1 and self.jstick.get_axis(0) < 0.1:
            if self.player.idle_timer < 17:
                self.player.idle_timer = 17
            self.jstick_right, self.jstick_left = False, False
        if self.jstick.get_axis(1) > -0.1 and self.jstick.get_axis(1) < 0.1:
            if self.player.idle_timer < 17:
                self.player.idle_timer = 17
            self.jstick_up, self.jstick_down = False, False
        
        if self.jstick_right:
            self.player.move(dx=1)
            self.player.idle_timer = 0
        if self.jstick_left:
            self.player.move(dx=-1)
            self.player.idle_timer = 0
        if self.jstick_up:
            self.player.move(dy=-1)
            self.player.idle_timer = 0
        if self.jstick_down:
            self.player.move(dy=1)
            self.player.idle_timer = 0
    
    def key_movement(self):
        if self.move_right:
            self.player.move(dx=1)
            self.player.idle_timer = 0
        if self.move_left:
            self.player.move(dx=-1)
            self.player.idle_timer = 0
        if self.move_up:
            self.player.move(dy=-1)
            self.player.idle_timer = 0
        if self.move_down:
            self.player.move(dy=1)
            self.player.idle_timer = 0
    
    def death(self):
        global level
        if self.player.hit:
            if self.lives < 1:
                self.game_over_screen()
                level = 0
                self.lives = 3
            self.gems_needed = 0
            self.score = 0
            self.seconds = 500
            self.running = False
    
    def game_over_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                return True
                
    
    def game_over_screen(self):
        self.hard_score += self.score
        while True:
            self.screen.blit(self.game_over_anim.img(), (0, 0))
            text(str(self.hard_score), self.screen, (490, 452), 100)
            
            if self.game_over_events():
               break
            
            self.game_over_anim.update()
            
            pygame.display.flip()
        self.score_board()
        self.hard_score = 0
    def score_board(self):
        
        alfabet = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
        
        df = pd.read_csv("scores.csv", decimal = ".", comment = "#", sep= ",")
        
        nr1 = df['1'].tolist()
        nr2 = df['2'].tolist()
        nr3 = df['3'].tolist()
        
        namer = []
        name = ''
        if int(nr3[1]) > self.hard_score:
            pass
        else:
            run = True
            while run:
                self.screen.fill(BLACK)
                
                text(str(nr1[0].capitalize()) + ': ' + str(nr1[1]), self.screen, (250,50), 75)
                text(str(nr2[0].capitalize()) + ': ' + str(nr2[1]), self.screen, (250,150), 75)
                text(str(nr3[0].capitalize()) + ': ' + str(nr3[1]), self.screen, (250,250), 75)
                text('Score: ' + str(self.hard_score), self.screen, (250,400), 75)
                text('Name: ' + str(name.capitalize()), self.screen, (250,500), 75)
                text('_', self.screen, (540,525), 85)
                text('_', self.screen, (590,525), 85)
                text('_', self.screen, (640,525), 85)
                text('_', self.screen, (690,525), 85)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            run = False
                        if event.key == pygame.K_BACKSPACE:
                            namer.pop()
                    if event.type == pygame.JOYBUTTONDOWN:
                        if event.button == 0 or event.button == 1:
                            run = False
                if len(namer)<4:            
                    keys = pygame.key.get_pressed()
                    for i in range(122,96,-1):
                        if keys[i]:
                            letter = alfabet[i - 97]
                            namer.append(letter)
                            letter = ''
                            time.sleep(0.3)
                name = ''
                for i in namer:
                    name += i
                pygame.display.update()
        if name != '' and name != ' ':   
            if self.hard_score > int(nr1[1]):
                nr3 = nr2
                nr2 = nr1[:]
                
                nr1[0], nr1[1] = name, self.hard_score
            elif self.hard_score > int(nr2[1]) and self.hard_score < int(nr1[1]):
                nr3 = nr2[:]
                nr2[0], nr2[1] = name, self.hard_score
            elif self.hard_score > int(nr3[1]):
                nr3[0], nr3[1] = name, self.hard_score
            
            header = ['1', '2', '3']
            row_data = [
                [nr1[0], nr2[0], nr3[0]],
                [nr1[1], nr2[1], nr3[1]]
                ] 
            data = pd.DataFrame(row_data, columns= header)
            data.to_csv('scores.csv', index = False)
            self.hard_score = 0
        run = True
        
        while run:
            self.screen.fill(BLACK)
            
            text(str(nr1[0].capitalize()) + ': ' + str(nr1[1]), self.screen, (250,100), 100)
            text(str(nr2[0].capitalize()) + ': ' + str(nr2[1]), self.screen, (250,200), 100)
            text(str(nr3[0].capitalize()) + ': ' + str(nr3[1]), self.screen, (250,300), 100)
            text('Score: ' + str(self.hard_score), self.screen, (250,500), 100)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        run = False
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 0 or event.button == 1:
                        run = False
            pygame.display.update()
        
        
    def level_timer(self):
        if self.frames == 60:
            self.seconds -= 1
            self.frames = 0
        else: 
            self.frames += 1
    
    def start_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0 or event.button == 1:
                    return True
    
    def pause_events(self):
        action = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    action = 1
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    action = 2
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0 or event.button == 1:
                    pass
        return action
            
    def draw(self):
        self.display.fill(BLACK)

        for sprite in self.all_sprites:
            self.display.blit(sprite.image, self.camera.apply_to(sprite))
        self.display.blit((pygame.transform.flip(self.player.image, self.player.flip, False)), self.camera.apply_to(self.player))
        self.display.blit(self.transparent_surface, (0, 0))

        self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0,0))
        
        self.hud()
        pygame.display.flip()
        
    def update(self):
         self.level_timer()
         self.all_sprites.update()
         self.player_sprites.update()
         self.camera.update(self.player)
    
    def pause_menu(self):
        self.state = 0
        while True:
            (px, py) = pygame.mouse.get_pos()
            if px > 240 and px < 980 and py > 26 and py < 240:
                self.state = 1
            elif px > 215 and px < 1030 and py > 290 and py < 505:
                self.state = 2
            else:
                self.state = 0
            self.screen.blit(load_image('pause_' + str(self.state) + '.png'), (0, 0))
            
            action = self.pause_events()
            
            if action  == 1:
                if self.state == 1:
                    break
                if self.state == 2:
                    self.player.hit = True
                    self.lives -= 1
                    break
            elif action == 2:
                break
            pygame.display.flip()
         

    def start_screen(self):
         while True:
             self.screen.blit(load_image('start_screen.png'), (0, 0))
             if self.start_events():
                 break
             pygame.display.flip()
    
    def hud(self):
        self.hud_rect = pygame.Rect(0, 0, WIDTH, 16)
        pygame.draw.rect(self.transparent_surface, (0, 0, 170, 200), self.hud_rect)
        
        self.gem_image = load_image('gems_animation/sprite_02.png')
        self.screen.blit(pygame.transform.scale(self.gem_image, (30,30)), (50,10))
        text('x' + str(self.player.gems_collected) + '/' + str(self.gems_needed), self.screen, (82, 10), 25)
        
        self.player_image = load_image('player.png')
        self.screen.blit(pygame.transform.scale(self.player_image, (31,31)), (270, 10))
        text('x' + str(self.lives), self.screen, (302, 10), 25)
        
        text('score: ' + str(self.score + self.hard_score), self.screen, (500, 10), 25)
        text('time: ' + str(self.seconds), self.screen, (825, 10), 25)
        
        text(str(round(pygame.time.Clock.get_fps(self.clock), 2)), self.screen, (1100, 10), 25)

'''
PLAYER
'''

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.player_sprites, game.all_with_empty_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = load_image('player.png')
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.idle_timer = 0
        self.gems_collected = 0
        self.hit = False
        self.push_counter = 0
        
        self.action = 'idle'
        self.flip = False
        self.animation_idle = Animation(load_images('player/idle'), 8)
        self.animation_run = Animation(load_images('player/run'), 2)

    def move(self, dx=0, dy=0):
        self.action = 'run'
        if self.dig_dirt(dx, dy):
            pass
        elif self.collect_gem(dx, dy):
            pass
        else:
            self.push_boulder(dx, dy)
        if not self.static_tile(dx, dy):
            self.x += dx
            self.y += dy
        
        if dx < 0:
            self.flip = True
        if dx > 0:
            self.flip = False
        self.idle_timer = 0
    
    def set_action(self):

        if self.idle_timer > 30:
            self.action = 'idle'
        self.idle_timer += 1
    
    def static_tile(self, dx=0, dy=0):
        for static_tile in self.game.static_sprites:
            if static_tile.x == self.x + dx and static_tile.y == self.y + dy:
                return True
        for static_tile in self.game.boulder_sprites:
            if static_tile.x == self.x + dx and static_tile.y == self.y + dy:
                return True
        return False
    
    def dig_dirt(self, dx=0, dy=0):
        for dirt in self.game.dirt_sprites:
            if dirt.x == self.x + dx and dirt.y == self.y + dy:
                Empty(self.game, self.x + dx, self.y + dy)
                # pygame.mixer.Sound.play(dig_dirt_sound)
                dirt.kill()
                return True
    
    def collect_gem(self, dx=0, dy=0):
        for gem in self.game.gem_sprites:
            if gem.x == self.x + dx and gem.y == self.y + dy:
                self.gems_collected += 1
                self.game.score += 50
                gem.kill()   
                pygame.mixer.Sound.play(collect_gem_sound)
                if self.gems_collected == self.game.gems_needed:
                    pygame.mixer.Sound.play(enough_gems_sound)
                    pygame.mixer_music.stop()
                return True
    
    def level_fin(self):
        for door in self.game.door_sprites:
            if door.x == self.x and door.y == self.y:
                if self.gems_collected >= self.game.gems_needed:
                    self.game.score += self.game.seconds
                    self.game.hard_score += self.game.score
                    self.game.score = 0
                    self.game.seconds = 500
                    self.game.level_clear = True
                    
    
    def push_boulder(self, dx, dy):
        for boulder in self.game.boulder_sprites:
            if boulder.x == self.x + dx and boulder.y == self.y:
                self.push_counter += 1
                if self.push_counter > 4:
                    boulder.pushed = True
                    self.push_counter = 0
    def update(self):
        if self.action == 'run':
            self.image = self.animation_run.img()
            self.animation_run.update()
        else: 
            self.image = self.animation_idle.img()
            self.animation_idle.update()
        
        self.level_fin()
        self.set_action()
        self.rect.x = self.x * TILE_SIZE
        self.rect.y = self.y * TILE_SIZE
        
        

'''
TILES
'''
class Empty(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.empty_tiles, game.all_with_empty_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.x = x
        self.y = y
        
class Edge(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.static_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = load_image('tiles/edge/0.png')
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x, self.rect.y = self.x * TILE_SIZE, self.y * TILE_SIZE

class Brick(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.static_sprites, game.roll_sprites, game.all_with_empty_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = load_image('tiles/brick/0.png')
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x, self.rect.y = self.x * TILE_SIZE, self.y * TILE_SIZE
        
class Dirt(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.dirt_sprites, game.all_with_empty_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = load_image('tiles/dirt/0.png')
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x, self.rect.y = self.x * TILE_SIZE, self.y * TILE_SIZE

class Door(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.door_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = load_image('tiles/door/0.png')
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x, self.rect.y = self.x * TILE_SIZE, self.y * TILE_SIZE
        self.enough_gems = False
        
        self.animation = Animation(load_images('door_animation'), 25)
        
        
    def update(self):
        self.image = self.animation.img()
        self.rect.x = self.x * TILE_SIZE
        self.rect.y = self.y * TILE_SIZE
        if self.game.gems_needed <= self.game.player.gems_collected:
            self.enough_gems = True
        if self.enough_gems:    
            self.animation.update()

class Boulder(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.boulder_sprites, game.roll_sprites, game.all_with_empty_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = load_image('tiles/boulder/0.png')
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x, self.rect.y = self.x * TILE_SIZE, self.y * TILE_SIZE
        self.time = 0
        self.fall_time = 0
        self.falling = False
        self.pushed = False
        self.push_dir = None
        

    def update(self):
        self.time += 3
        if self.time >= 40:
            self.move()
            self.time = 0
        self.rect.x = self.x * TILE_SIZE
        self.rect.y = self.y * TILE_SIZE
    
    def move(self):
        if self.move_down():
            Empty(self.game, self.x, self.y)
            self.y = self.y + 1
            self.fall_time += 1
            if self.fall_time > 0:
                self.falling = True
                self.fall_time = 0
            for space in self.game.empty_tiles:
                if space.x == self.x and space.y == self.y:
                    space.kill()
        elif self.roll_right():
            Empty(self.game, self.x, self.y)
            self.x = self.x + 1
            self.falling = True
            for space in self.game.empty_tiles:
                if space.x == self.x and space.y == self.y:
                    space.kill()
        elif self.roll_left():
            Empty(self.game, self.x, self.y)
            self.x = self.x - 1
            self.falling = True
            for space in self.game.empty_tiles:
                if space.x == self.x and space.y == self.y:
                    space.kill()
        
        if self.pushed == True:
            self.player_pushed()
            Empty(self.game, self.x, self.y)
            if self.push_dir == 'left':
                self.x -= 1
            if self.push_dir == 'right':
                self.x += 1
            
            for space in self.game.empty_tiles:
                if space.x == self.x and space.y == self.y:
                    space.kill()
                    
            self.push_dir = None
            self.pushed = False
        
            
    def can_roll(self):
        for sprite in self.game.roll_sprites:
            if sprite.x == self.x and sprite.y == self.y + 1:
                return True
        return False
    
    def move_down(self):
        for sprite in self.game.all_sprites:
            if sprite.x == self.x and sprite.y == self.y + 1:
                self.falling = False
                return False
        if self.game.player.x == self.x and self.game.player.y == self.y + 1:
            if self.falling:
                self.game.lives -= 1
                self.game.player.hit = True                
            else:
                self.falling = False
                return False
        elif self.game.player.x == self.x and self.game.player.y == self.y:
            self.game.lives -= 1
            self.game.player.hit = True
        for enemy in self.game.enemy_sprites:
            if enemy.x == self.x and enemy.y == self.y + 1:
                enemy.kill()
            elif enemy.x == self.x and enemy.y == self.y:
                enemy.kill()
        pygame.mixer.Sound.play(boulder_crash_sound)
        pygame.mixer_music.stop()
        return True
    
    def roll_right(self):
        if self.can_roll():
            if not self.move_down():
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x + 1 and sprite.y == self.y:
                        return False
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x + 1 and sprite.y == self.y + 1:
                        return False
                if self.game.player.x == self.x + 1 and (self.game.player.y == self.y or self.game.player.y == self.y + 1):
                    return False
            return True
    
    def roll_left(self):
        if self.can_roll():
            if not self.move_down():
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x - 1 and sprite.y == self.y:
                        return False
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x - 1 and sprite.y == self.y + 1:
                        return False
                if self.game.player.x == self.x - 1 and (self.game.player.y == self.y or self.game.player.y == self.y + 1):
                    return False
            return True
    
    def pushed_right(self):
        for sprite in self.game.all_sprites:
            if sprite.x == self.x + 1 and sprite.y == self.y:
                return False
        return True
    
    def pushed_left(self):
        for sprite in self.game.all_sprites:
            if sprite.x == self.x - 1 and sprite.y == self.y:
                return False
        return True
    
    def player_pushed(self):
        if self.game.player.x == self.x - 1:
            if self.pushed_right():
                self.push_dir = 'right'
        if self.game.player.x == self.x + 1:
            if self.pushed_left():
                self.push_dir = 'left'
        return self.push_dir

class Gem(Boulder):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.roll_sprites, game.gem_sprites, game.all_with_empty_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = load_image('tiles/gem/0.png')
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.time = 0
        self.fall_time = 0
        self.falling = False
        
        self.rect.x, self.rect.y = self.x * TILE_SIZE, self.y * TILE_SIZE      
        self.animation = Animation(load_images('gems_animation'), 4)
        
    def move(self):
        if self.move_down():
            self.y = self.y + 1
            self.fall_time += 1
            if self.fall_time > 1:
                self.falling = True
                self.fall_time = 0
        elif self.roll_right():
            self.x = self.x + 1
            self.falling = True
        elif self.roll_left():
            self.x = self.x - 1
            self.falling = True
            
    def update(self):
        self.image = self.animation.img()
            
        self.time += 3
        if self.time >= 40:
            self.move()
            self.time = 0
        self.rect.x = self.x * TILE_SIZE
        self.rect.y = self.y * TILE_SIZE
            
        self.animation.update()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.enemy_sprites, game.all_with_empty_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.x = x
        self.y = y
        self.image = load_image('enemy_animation/1.png')
        self.rect = self.image.get_rect()
        
        self.rect.x, self.rect.y = self.x * TILE_SIZE, self.y * TILE_SIZE
        
        self.direction = 'right'
        self.hug = 'bottom'
        self.clock = 0
        
        self.animation = Animation(load_images('enemy_animation'), 6)
    
    def move(self):
        self.change_direction()
        if self.direction == 'right':
            self.x += 1
        if self.direction == 'left':
            self.x -= 1
        if self.direction == 'down':
            self.y += 1
        if self.direction == 'up':
            self.y -= 1
            
    def check_death(self):
        for boulder in self.game.boulder_sprites:
            if self.x == boulder.x and (self.y == boulder.y + 1 or self.y == boulder.y):
                self.kill_anim()
                self.kill()
    
    def kill_anim(self):
        for sprite in self.game.all_with_empty_sprites:
            if sprite.x == self.x and sprite.y == self.y:
                sprite.kill()
                Gem(self.game, sprite.x, sprite.y)
            if sprite.x == self.x + 1 and sprite.y == self.y:
                sprite.kill()
                Gem(self.game, sprite.x, sprite.y)
            if sprite.x == self.x -1 and sprite.y == self.y:
                sprite.kill()
                Gem(self.game, sprite.x, sprite.y)
            if sprite.x == self.x and sprite.y == self.y + 1:
                sprite.kill()
                Gem(self.game, sprite.x, sprite.y)
            if sprite.x == self.x and sprite.y == self.y - 1:
                sprite.kill()
                Gem(self.game, sprite.x, sprite.y)
            if sprite.x == self.x + 1 and sprite.y == self.y + 1:
                sprite.kill()
                Gem(self.game, sprite.x, sprite.y)
            if sprite.x == self.x + 1 and sprite.y == self.y - 1:
                sprite.kill()
                Gem(self.game, sprite.x, sprite.y)
            if sprite.x == self.x - 1 and sprite.y == self.y + 1:
                sprite.kill()
                Gem(self.game, sprite.x, sprite.y)
            if sprite.x == self.x - 1 and sprite.y == self.y - 1:
                sprite.kill()
                Gem(self.game, sprite.x, sprite.y)
        
    def change_direction(self):
        self.check_death()
        if self.direction == 'right':
            for space in self.game.empty_tiles:
                if self.hug == 'bottom':
                    if space.x == self.x and space.y == self.y + 1:
                        self.direction = 'down'
                        self.hug = 'left'
                elif self.hug == 'top':
                    if space.x == self.x and space.y == self.y - 1:
                        self.direction = 'up'
                        self.hug = 'left'
        
            if self.direction == 'right' and self.hug == 'bottom':
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x + 1 and sprite.y == self.y:
                        self.direction = 'up'
                        self.hug = 'right'
                if self.direction == 'up':
                    for sprite in self.game.all_sprites:
                        if sprite.x == self.x and sprite.y == self.y - 1:
                            self.direction = 'left'
                            self.hug = 'top'
                    
            elif self.direction == 'right' and self.hug == 'top':
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x + 1 and sprite.y == self.y:
                        self.direction = 'down'
                        self.hug = 'right'
                if self.direction == 'down':
                    for sprite in self.game.all_sprites:
                        if sprite.x == self.x and sprite.y == self.y + 1:
                            self.direction = 'left'
                            self.hug = 'bottom'
                        
        
        elif self.direction == 'left':
            for space in self.game.empty_tiles:
                if self.hug == 'bottom':
                    if space.x == self.x and space.y == self.y + 1:
                        self.direction = 'down'
                        self.hug = 'right'
                elif self.hug == 'top':
                    if space.x == self.x and space.y == self.y - 1:
                        self.direction = 'up'
                        self.hug = 'right'
            
            if self.direction == 'left' and self.hug == 'bottom':
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x - 1 and sprite.y == self.y:
                        self.direction = 'up'
                        self.hug = 'left'
                if self.direction == 'up':
                    for sprite in self.game.all_sprites:
                        if sprite.x == self.x and sprite.y == self.y - 1:
                            self.direction = 'right'
                            self.hug = 'top'
            elif self.direction == 'left' and self.hug == 'top':
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x - 1 and sprite.y == self.y:
                        self.direction = 'down'
                        self.hug = 'left' 
                if self.direction == 'down':
                    for sprite in self.game.all_sprites:
                        if sprite.x == self.x and sprite.y == self.y + 1:
                            self.direction = 'right'
                            self.hug = 'bottom'
                        
        elif self.direction == 'down':
            for space in self.game.empty_tiles:
                if self.hug == 'right':
                    if space.x == self.x + 1 and space.y == self.y:
                        self.direction = 'right'
                        self.hug = 'top'
                elif self.hug == 'left':
                    if space.x == self.x - 1 and space.y == self.y:
                        self.direction = 'left'
                        self.hug = 'top'
            
            if self.direction == 'down' and self.hug == 'right':
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x and sprite.y == self.y + 1:
                        self.direction = 'left'
                        self.hug = 'bottom'
                if self.direction == 'left':
                    for sprite in self.game.all_sprites:
                        if sprite.x == self.x - 1 and sprite.y == self.y:
                            self.direction = 'up'
                            self.hug = 'left'
            elif self.direction == 'down' and self.hug == 'left':
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x and sprite.y == self.y + 1:
                        self.direction = 'right'
                        self.hug = 'bottom' 
                if self.direction == 'right':
                    for sprite in self.game.all_sprites:
                        if sprite.x == self.x + 1 and sprite.y == self.y:
                            self.direction = 'up'
                            self.hug = 'right'
        
        elif self.direction == 'up':
            for space in self.game.empty_tiles:
                if self.hug == 'left':
                    if space.x == self.x - 1 and space.y == self.y:
                        self.direction = 'left'
                        self.hug = 'bottom'
                elif self.hug == 'right':
                    if space.x == self.x + 1 and space.y == self.y:
                        self.direction = 'right'
                        self.hug = 'bottom'
            
            if self.direction == 'up' and self.hug == 'right':
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x and sprite.y == self.y - 1:
                        self.direction = 'left'
                        self.hug = 'top'
                if self.direction == 'left':
                    for sprite in self.game.all_sprites:
                        if sprite.x == self.x - 1 and sprite.y == self.y:
                            self.direction = 'down'
                            self.hug = 'left'
            elif self.direction == 'up' and self.hug == 'left':
                for sprite in self.game.all_sprites:
                    if sprite.x == self.x and sprite.y == self.y - 1:
                        self.direction = 'right'
                        self.hug = 'top' 
                if self.direction == 'right':
                    for sprite in self.game.all_sprites:
                        if sprite.x == self.x + 1 and sprite.y == self.y:
                            self.direction = 'up'
                            self.hug = 'right'
        
    def player_kill(self):
        if self.game.player.x == self.x and self.game.player.y == self.y:
            self.game.lives -= 1
            self.game.player.hit = True   
        
    def update(self):
        self.image = self.animation.img()
        self.clock += 1
        if self.clock == 15:
            self.move()
            self.clock = 0
        
        self.player_kill()
        
        self.rect.x = self.x * TILE_SIZE
        self.rect.y = self.y * TILE_SIZE

        self.animation.update()
        
'''
TILEMAP
'''
class Tilemap:
    def __init__(self, filename):
        self.filename = filename
        map_folder = os.path.dirname('data/maps/')
        
        self.data = []
        with open(os.path.join(map_folder, self.filename), 'rt') as f:
            for line in f:
               self.data.append(line.strip())
        
        self.tilewidth = len(self.data[0])
        self.tileheigth = len(self.data)
        self.width = self.tilewidth * TILE_SIZE
        self.height = self.tileheigth * TILE_SIZE

class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
    
    def apply_to(self, entity):
        return entity.rect.move(self.camera.topleft)
    
    def update(self, target):
        x = -target.rect.x + int(DISPLAY_WIDTH/2)
        y = -target.rect.y + int(DISPLAY_HEIGHT/2)
        
        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - DISPLAY_WIDTH), x)
        y = max(-(self.height - DISPLAY_HEIGHT), y)
        
        self.camera = pygame.Rect(x, y, self.width, self.height)
        
start = Game()
start.start_screen()
while True:
    if start.level_clear:
        level += 1
        start.level_clear = False
    
    start.new_sprite('map'+str(level))
    start.run()


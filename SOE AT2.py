from pathlib import Path
import pygame
from pygame.math import Vector2
import random 

pygame.init()

root = Path(__file__).resolve().parents[0]
assets = root/"Assets"

screen = pygame.display.set_mode((1080, 720), pygame.RESIZABLE)
clock = pygame.time.Clock()
running = True

def GetFrame(spritesheet, grid, frameIndex):
    columns = grid[0]
    rows = grid[1]
    frameWidth = spritesheet.get_width() // columns
    frameHeight = spritesheet.get_height() // rows
    column = frameIndex % columns
    row = frameIndex // columns
    x = column * frameWidth
    y = row * frameHeight
    frame = pygame.Surface((frameWidth, frameHeight), pygame.SRCALPHA)
    frame.blit(spritesheet, (0, 0), (x, y, frameWidth, frameHeight))
    return frame

def GetDaFrames(spritesheet, grid):
    frames = []
    for i in range(grid[0]*grid[1]):
        frames.append(GetFrame(spritesheet, grid, i))
    return frames

# ---- PLAYER SETUP ----
position = Vector2(590,360)
speed = 300
player_rect = pygame.Rect(position.x, position.y, 0, 0) 
player_lives = 3
player_invulnerable = False
player_invulnerable_timer = 0
invulnerability_duration = 1500 

spritesheet = pygame.image.load(assets/"PlayerPlane.png")
playerplaneframes = GetDaFrames(spritesheet, (2, 3))
playerplanecurrentframe = 0
playerplanelasttick = pygame.time.get_ticks()

player_rect.width = playerplaneframes[0].get_width()
player_rect.height = playerplaneframes[0].get_height()

deltaTime = 0.1
leftHeld = False
rightHeld = False
upHeld = False
downHeld = False

# --- BULLET SETUP ---
bulletspritesheet = pygame.image.load(assets/"BulletShot.png")
bulletframes = GetDaFrames(bulletspritesheet, (2, 3))

# --- Enemy Assets ---
try:
    death_sheet = pygame.image.load(assets/"EnemyPlaneDeath.png")
    explosion_frames = GetDaFrames(death_sheet, (2, 3)) 
except FileNotFoundError:
    print("No explosion spritesheet found. Using bullet frames as placeholder.")
    explosion_frames = bulletframes 

enemy1 = pygame.image.load(assets/"EnemyPlane1.png")
enemy1_frames = GetDaFrames(enemy1, (2, 3))

enemy2 = pygame.image.load(assets/"EnemyPlane2.png")
enemy2_frames = GetDaFrames(enemy2, (2, 3))

class Enemy():
    enemies = []

    def __init__(self, x, y, speed, frames, explosion_frames, hp=1, shoot_delay=2000):
        super().__init__()
        self.frames = frames
        self.explosion_frames = explosion_frames
        
        self.image = self.frames[0]
        self.currentframe = 0
        self.lastframetick = pygame.time.get_ticks()
        
        self.position = Vector2(x - self.image.get_width()/2, y)
        self.speed = speed
        
        self.rect = pygame.Rect(self.position.x, self.position.y, self.image.get_width(), self.image.get_height())
        self.state = "alive" 
        
        self.hp = hp
        self.max_hp = hp
        self.shoot_delay = shoot_delay
        self.last_shot = pygame.time.get_ticks() + random.randint(0, 1000) 
        
        # Flashing & Hit Cooldown mechanics
        self.is_flashing = False
        self.flash_start_time = 0
        self.flash_duration = 100 
        
        # NEW: Stop multi-hits from simultaneous bullets
        self.last_hit_time = 0
        self.hit_cooldown = 100 # Invulnerable for 100ms after taking damage

        Enemy.enemies.append(self)

    def take_damage(self, amount=1):
        now = pygame.time.get_ticks()
        # NEW: Only take damage if the cooldown has passed
        if self.state == "alive" and now - self.last_hit_time > self.hit_cooldown:
            self.hp -= amount
            self.last_hit_time = now # Reset the cooldown timer
            
            if self.hp <= 0:
                self.die()
            else:
                self.is_flashing = True
                self.flash_start_time = now

    def die(self):
        if self.state == "alive":
            self.state = "dying"
            self.currentframe = 0
            self.frames = self.explosion_frames 
            self.image = self.frames[0]

    def update(self, deltaTime):
        if self.lastframetick + 1000/24 <= pygame.time.get_ticks():
            self.currentframe += 1
            self.lastframetick = pygame.time.get_ticks()
            
            if self.currentframe >= len(self.frames):
                if self.state == "dying":
                    Enemy.enemies.remove(self)
                    return
                else:
                    self.currentframe = 0

        self.image = self.frames[self.currentframe]

        if self.state == "alive":
            self.position.y += (self.speed * deltaTime)
            self.rect.topleft = (self.position.x, self.position.y) 

            now = pygame.time.get_ticks()
            if now - self.last_shot > self.shoot_delay:
                self.last_shot = now
                Bullet(self.rect.centerx, self.rect.bottom, 200, bulletframes, is_enemy=True)

        if self.is_flashing and self.state == "alive":
            now = pygame.time.get_ticks()
            if now - self.flash_start_time > self.flash_duration:
                self.is_flashing = False
            else:
                mask = pygame.mask.from_surface(self.image)
                white_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
                screen.blit(white_surf, self.position)
        
        if not self.is_flashing:
            screen.blit(self.image, self.position)
    
        if self.position.y > 800 and self in Enemy.enemies:
            Enemy.enemies.remove(self)


class Bullet():
    bullets = []

    def __init__(self, x, y, speed, frames, is_enemy=False):
        super().__init__()
        self.is_enemy = is_enemy
        
        if self.is_enemy:
            self.frames = [pygame.transform.rotate(f, 180) for f in frames]
        else:
            self.frames = frames

        self.image = self.frames[0]
        self.currentframe = 0
        self.lastframetick = pygame.time.get_ticks()
        self.position = Vector2(x - self.image.get_width()/2, y)
        self.speed = speed
        
        self.rect = pygame.Rect(self.position.x, self.position.y, self.image.get_width(), self.image.get_height())
        
        Bullet.bullets.append(self)

    def update(self, deltaTime):
        if self.lastframetick + 1000/24 <= pygame.time.get_ticks():
            self.currentframe += 1
            self.lastframetick = pygame.time.get_ticks()
            if self.currentframe >= len(self.frames):
                self.currentframe = 0

        self.image = self.frames[self.currentframe]
        self.position.y += (self.speed * deltaTime)
        self.rect.topleft = (self.position.x, self.position.y) 

        screen.blit(self.image, self.position)
        
        if (self.position.y <= -50 or self.position.y >= 800) and self in Bullet.bullets:
            Bullet.bullets.remove(self)

shoot_delay = 100 
last_shot = pygame.time.get_ticks()

def shoot(spawn_pos):
    global last_shot
    now = pygame.time.get_ticks()
    if now - last_shot > shoot_delay:
        last_shot = now
        Bullet(spawn_pos.x-16, spawn_pos.y, -400, bulletframes, is_enemy=False)
        Bullet(spawn_pos.x-8, spawn_pos.y, -400, bulletframes, is_enemy=False)
        Bullet(spawn_pos.x+16, spawn_pos.y, -400, bulletframes, is_enemy=False)
        Bullet(spawn_pos.x+8, spawn_pos.y, -400, bulletframes, is_enemy=False)

# Enemy Spawning Setup
enemy_spawn_timer = pygame.time.get_ticks()
enemy_spawn_delay = 1500 # ms

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a: leftHeld = True
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d: rightHeld = True
            if event.key == pygame.K_UP or event.key == pygame.K_w: upHeld = True
            if event.key == pygame.K_DOWN or event.key == pygame.K_s: downHeld = True
            
            if event.key == pygame.K_SPACE:    
                plane_size = playerplaneframes[playerplanecurrentframe].get_size()
                center_x = position.x + (plane_size[0] / 2)
                center_y = position.y
                shoot(Vector2(center_x, center_y))

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a: leftHeld = False
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d: rightHeld = False        
            if event.key == pygame.K_UP or event.key == pygame.K_w: upHeld = False
            if event.key == pygame.K_DOWN or event.key == pygame.K_s: downHeld = False

    if leftHeld: position.x -= speed*deltaTime
    if rightHeld: position.x += speed*deltaTime
    if upHeld: position.y -= speed*deltaTime
    if downHeld: position.y += speed*deltaTime

    # Keep player on screen (Optional but recommended)
    position.x = max(0, min(1080 - player_rect.width, position.x))
    position.y = max(0, min(720 - player_rect.height, position.y))
   
    player_rect.topleft = (position.x, position.y)

    if playerplanelasttick + 1000/24 <= pygame.time.get_ticks():
        playerplanelasttick = pygame.time.get_ticks()
        playerplanecurrentframe += 1
        if playerplanecurrentframe > len(playerplaneframes) -1:
            playerplanecurrentframe = 0

    # ---- NEW: Modular Spawning System ----
    now = pygame.time.get_ticks()
    if now - enemy_spawn_timer > enemy_spawn_delay:
        enemy_spawn_timer = now
        random_x = random.randint(50, 1030)
        
        # Pick a random enemy type to spawn
        enemy_type = random.choice(["E1", "E2"])
        
        if enemy_type == "E1":
            # 1 HP, Fast Movement, Shoots slow
            Enemy(random_x, -50, 100, enemy1_frames, explosion_frames, hp=1, shoot_delay=2000)
        elif enemy_type == "E2":
            # 2 HP, Slow Movement, Shoots fast
            Enemy(random_x, -50, 100, enemy2_frames, explosion_frames, hp=2, shoot_delay=1500)


    # ---- Collision Detection Loop ----
    for bullet in Bullet.bullets[:]:
        if not bullet.is_enemy:
            for enemy in Enemy.enemies[:]:
                if enemy.state == "alive" and bullet.rect.colliderect(enemy.rect):
                    # We pass 1 damage. The enemy class handles the invulnerability cooldown now.
                    enemy.take_damage(1) 
                    if bullet in Bullet.bullets:
                        Bullet.bullets.remove(bullet)
                    break 
        
        elif bullet.is_enemy:
            if not player_invulnerable and bullet.rect.colliderect(player_rect):
                player_lives -= 1
                print(f"Player Hit! Lives remaining: {player_lives}")
                
                player_invulnerable = True
                player_invulnerable_timer = pygame.time.get_ticks()
                
                if bullet in Bullet.bullets:
                    Bullet.bullets.remove(bullet)
                    
                if player_lives <= 0:
                    print("GAME OVER")
                    running = False 

    screen.fill((119, 178, 212))

    for bullet in Bullet.bullets[:]:
        bullet.update(deltaTime)

    for enemy in Enemy.enemies[:]:
        enemy.update(deltaTime)

    # ---- Player Rendering & I-Frames ----
    now = pygame.time.get_ticks()
    if player_invulnerable:
        if now - player_invulnerable_timer > invulnerability_duration:
            player_invulnerable = False
        
        if (now // 100) % 2 == 0:
            screen.blit(playerplaneframes[playerplanecurrentframe], position)
    else:
        screen.blit(playerplaneframes[playerplanecurrentframe], position)

    pygame.display.flip()

    fps = 0 
    deltaTime = clock.tick(fps) / 1000
    deltaTime = max(0.001, min(0.1, deltaTime))
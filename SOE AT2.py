from pathlib import Path
import pygame
from pygame.math import Vector2
import random 
import math

pygame.init()

root = Path(__file__).resolve().parents[0]
assets = root/"Assets"

# ---- WINDOW & VIRTUAL SCREEN SETUP ----
window = pygame.display.set_mode((1080, 720), pygame.RESIZABLE)
screen = pygame.Surface((1080, 720))

clock = pygame.time.Clock()
running = True
game_over = False  

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

def get_angle_to_target(source_pos, target_pos):
    dx = target_pos.x - source_pos.x
    dy = target_pos.y - source_pos.y
    rads = math.atan2(-dy, dx) 
    degs = math.degrees(rads)
    return degs - 90 

# ---- SCORE & GAME STATE SETUP ----
score = 0

# ---- FONT SYSTEM SETUP ----
font_filename = "ArcadeFont.ttf" 
custom_font_path = assets / font_filename

if custom_font_path.exists():
    ui_font = pygame.font.Font(str(custom_font_path), 28)
    game_over_font = pygame.font.Font(str(custom_font_path), 72)
else:
    print(f"Custom font '{font_filename}' not found in Assets. Using system default fallback.")
    ui_font = pygame.font.SysFont("Arial", 32, bold=True)
    game_over_font = pygame.font.SysFont("Arial", 80, bold=True)

# --- OCEAN SETUP ---
ocean_sheet = pygame.image.load(assets/"OceanTile2.2.png")
ocean_frames = GetDaFrames(ocean_sheet, (1, 2)) 
ocean_scroll_y = 0
ocean_scroll_speed = 50 
ocean_current_frame = 0
ocean_anim_timer = pygame.time.get_ticks()

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
bulletspritesheet = pygame.image.load(assets/"NewBulletShot.png")
bulletframes = GetDaFrames(bulletspritesheet, (3, 2))

# Guided Missile Asset Setup
try:
    missile_sheet = pygame.image.load(assets/"GuidedBullet.png")
    missile_frames = GetDaFrames(missile_sheet, (3, 2))
except FileNotFoundError:
    print("GuidedMissile.png not found! Falling back to bullet frames.")
    missile_frames = bulletframes

# --- Enemy Assets ---
try:
    death_sheet = pygame.image.load(assets/"EnemyPlaneDeath.png")
    explosion_frames = GetDaFrames(death_sheet, (2, 3)) 
except FileNotFoundError:
    print("No explosion spritesheet found. Using bullet frames as placeholder.")
    explosion_frames = bulletframes 

# Universal Explosion Asset Setup
try:
    universal_explosion_sheet = pygame.image.load(assets/"UniversalExplosion.png")
    universal_explosion_frames = GetDaFrames(universal_explosion_sheet, (2, 2)) 
except FileNotFoundError:
    print("UniversalExplosion.png not found! Falling back to standard explosion frames.")
    universal_explosion_frames = explosion_frames

enemy1 = pygame.image.load(assets/"EnemyPlane1.png")
enemy1_frames = GetDaFrames(enemy1, (2, 3))

enemy2 = pygame.image.load(assets/"EnemyPlane2.png")
enemy2_frames = GetDaFrames(enemy2, (2, 3))

enemy3 = pygame.image.load(assets/"EnemyPlane3.png")
enemy3_frames = GetDaFrames(enemy3, (2, 3))

enemy4 = pygame.image.load(assets/"EnemyPlane4.png")
enemy4_frames = GetDaFrames(enemy4, (2, 3))

bigenemy_sheet = pygame.image.load(assets/"BigEnemy.png")
bigenemy_frames = GetDaFrames(bigenemy_sheet, (2, 3))

bigenemy_death_sheet = pygame.image.load(assets/"BigEnemyDeath.png")
bigenemy_explosion_frames = GetDaFrames(bigenemy_death_sheet, (2, 2))

spinny_blade_sheet = pygame.image.load(assets/"SpinnyBlade.png")
spinny_blade_frames = GetDaFrames(spinny_blade_sheet, (2, 2))

boatenemy_sheet = pygame.image.load(assets/"EnemyBoat.png")
boatenemy_frames = GetDaFrames(boatenemy_sheet, (3, 2))

boatenemydeath_sheet = pygame.image.load(assets/"EnemyBoatDeath.png")
boatenemy_explosion_frames = GetDaFrames(boatenemydeath_sheet, (3, 2))

class Enemy():
    enemies = []

    def __init__(self, x, y, speed, frames, explosion_frames, hp=1, shoot_delay=2000, enemy_type="Basic"):
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
        
        self.is_flashing = False
        self.flash_start_time = 0
        self.flash_duration = 100 
        
        self.last_hit_time = 0
        self.hit_cooldown = 100 

        self.enemy_type = enemy_type
        self.missile_fired = False

        Enemy.enemies.append(self)

    def take_damage(self, amount=1):
        now = pygame.time.get_ticks()
        if self.state == "alive" and now - self.last_hit_time > self.hit_cooldown:
            self.hp -= amount
            self.last_hit_time = now 
            
            if self.hp <= 0:
                self.die()
            else:
                self.is_flashing = True
                self.flash_start_time = now

    def die(self):
        global score
        if self.state == "alive":
            self.state = "dying"
            self.currentframe = 0
            self.frames = self.explosion_frames 
            self.image = self.frames[0]
            score += 100  

    def update(self, deltaTime):
        global score
        if self.lastframetick + 1000/24 <= pygame.time.get_ticks():
            self.currentframe += 1
            self.lastframetick = pygame.time.get_ticks()
            
            if self.currentframe >= len(self.frames):
                if self.state == "dying":
                    if self in Enemy.enemies:
                        Enemy.enemies.remove(self)
                    return
                else:
                    self.currentframe = 0

        self.image = self.frames[self.currentframe]

        if self.state == "alive":
            self.position.y += (self.speed * deltaTime)
            self.rect.topleft = (self.position.x, self.position.y) 

            now = pygame.time.get_ticks()
            
            if self.enemy_type == "E4" and not self.missile_fired:
                dist_to_player = math.hypot(position.x - self.position.x, position.y - self.position.y)
                if dist_to_player < 450:
                    self.missile_fired = True
                    TrackingMissile(self.rect.centerx, self.rect.bottom, 220, missile_frames, lifetime=4000)

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
            if self.state == "alive":
                if not isinstance(self, SpecialEnemy):
                    score = max(0, score - 50) 
                Enemy.enemies.remove(self)

class SpecialEnemy(Enemy):
    def __init__(self, x, start_y, speed, frames, explosion_frames, track_frames, hp, hover_y, hover_time):
        super().__init__(x, start_y, speed, frames, explosion_frames, hp, shoot_delay=1000)
        
        self.track_frames = track_frames
        self.hover_y = hover_y
        self.hover_time = hover_time
        self.hover_start_time = 0
        self.phase = "entering" 
        self.last_multi_shot = pygame.time.get_ticks()

    def update(self, deltaTime):
        if self.lastframetick + 1000/24 <= pygame.time.get_ticks():
            self.currentframe += 1
            self.lastframetick = pygame.time.get_ticks()
            
            if self.currentframe >= len(self.frames):
                if self.state == "dying":
                    if self in Enemy.enemies:
                        Enemy.enemies.remove(self)
                    return
                else:
                    self.currentframe = 0

        self.image = self.frames[self.currentframe]
        now = pygame.time.get_ticks()

        if self.state == "alive":
            if self.phase == "entering":
                self.position.y -= (self.speed * deltaTime) 
                if self.position.y <= self.hover_y:
                    self.phase = "hovering"
                    self.hover_start_time = now

            elif self.phase == "hovering":
                if now - self.hover_start_time > self.hover_time:
                    self.phase = "leaving"
                    
                if now - self.last_shot > 1500: 
                    self.last_shot = now
                    TrackingMissile(self.rect.centerx, self.rect.centery, 180, self.track_frames, lifetime=3500)
                    
                if now - self.last_multi_shot > 1000:
                    self.last_multi_shot = now
                    Bullet(self.rect.left, self.rect.centery, 0, bulletframes, is_enemy=True, speed_x=-200, angle=90)
                    Bullet(self.rect.right, self.rect.centery, 0, bulletframes, is_enemy=True, speed_x=200, angle=270)
                    Bullet(self.rect.centerx, self.rect.bottom, 200, bulletframes, is_enemy=True, speed_x=0, angle=180)

            elif self.phase == "leaving":
                self.position.y -= (self.speed * deltaTime) 
                if self.position.y < -200: 
                    if self in Enemy.enemies:
                        Enemy.enemies.remove(self)

            self.rect.topleft = (self.position.x, self.position.y) 

        if self.is_flashing and self.state == "alive":
            if now - self.flash_start_time > self.flash_duration:
                self.is_flashing = False
            else:
                mask = pygame.mask.from_surface(self.image)
                white_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
                screen.blit(white_surf, self.position)
        else:
            screen.blit(self.image, self.position)

class TrailParticle:
    particles = []

    def __init__(self, x, y):
        self.position = Vector2(x, y)
        self.radius = random.uniform(3, 6)
        self.life = 255  
        self.decay_rate = random.uniform(300, 500)

        TrailParticle.particles.append(self)

    def update(self, deltaTime):
        self.life -= self.decay_rate * deltaTime
        self.radius -= 2 * deltaTime
        if self.life <= 0 or self.radius <= 0:
            if self in TrailParticle.particles:
                TrailParticle.particles.remove(self)

    def draw(self, surface):
        if self.life > 0 and self.radius > 0:
            s = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (150, 150, 150, int(self.life)), (int(self.radius), int(self.radius)), int(self.radius))
            surface.blit(s, (self.position.x - self.radius, self.position.y - self.radius))

class Bullet():
    bullets = []

    def __init__(self, x, y, speed_y, frames, is_enemy=False, speed_x=0, angle=0):
        super().__init__()
        self.is_enemy = is_enemy
        
        self.frames = []
        for f in frames:
            rot = 180 if is_enemy and angle == 0 else angle
            self.frames.append(pygame.transform.rotate(f, rot))

        self.image = self.frames[0]
        self.currentframe = 0
        self.lastframetick = pygame.time.get_ticks()
        self.position = Vector2(x - self.image.get_width()/2, y)
        self.velocity = Vector2(speed_x, speed_y)
        self.rect = pygame.Rect(self.position.x, self.position.y, self.image.get_width(), self.image.get_height())
        
        Bullet.bullets.append(self)

    def update(self, deltaTime):
        if self.lastframetick + 1000/24 <= pygame.time.get_ticks():
            self.currentframe += 1
            self.lastframetick = pygame.time.get_ticks()
            if self.currentframe >= len(self.frames):
                self.currentframe = 0

        self.image = self.frames[self.currentframe]
        self.position += self.velocity * deltaTime
        self.rect.topleft = (self.position.x, self.position.y) 

        screen.blit(self.image, self.position)
        
        if (self.position.y <= -100 or self.position.y >= 850 or 
            self.position.x <= -100 or self.position.x >= 1180):
            if self in Bullet.bullets:
                Bullet.bullets.remove(self)

class TrackingMissile(Bullet):
    def __init__(self, x, y, speed, frames, lifetime=3000):
        super().__init__(x, y, 0, frames, is_enemy=True)
        self.base_speed = speed
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = lifetime
        self.state = "alive" 
        self.hp = 2
        
        self.original_frames = [f.copy() for f in frames]
        global universal_explosion_frames 
        self.explosion_frames = [f.copy() for f in universal_explosion_frames] 

    def explode(self):
        if self.state == "alive":
            self.state = "dying"
            self.original_frames = self.explosion_frames
            self.currentframe = 0
            self.base_speed = 0 
            self.velocity = Vector2(0, 0)
            self.lastframetick = pygame.time.get_ticks()

    def update(self, deltaTime):
        now = pygame.time.get_ticks()

        # Handle Explosion State
        if self.state == "dying":
            if self.lastframetick + 1000/24 <= pygame.time.get_ticks():
                self.currentframe += 1
                self.lastframetick = pygame.time.get_ticks()
                
                if self.currentframe >= len(self.original_frames):
                    if self in Bullet.bullets:
                        Bullet.bullets.remove(self)
                    return

            self.image = self.original_frames[self.currentframe]
            self.rect = self.image.get_rect(center=(self.position.x, self.position.y))
            screen.blit(self.image, self.rect.topleft)
            return

        # Alive State Logic
        if now - self.spawn_time > self.lifetime:
            self.explode() 
            return

        target_x = position.x + (player_rect.width / 2)
        target_y = position.y + (player_rect.height / 2)
        target_center = Vector2(target_x, target_y)
        
        dir_x = target_x - self.position.x
        dir_y = target_y - self.position.y
        
        distance = math.hypot(dir_x, dir_y)
        if distance != 0:
            dir_x /= distance
            dir_y /= distance
            
        self.velocity.x = dir_x * self.base_speed
        self.velocity.y = dir_y * self.base_speed

        self.position += self.velocity * deltaTime

        if self.lastframetick + 1000/24 <= pygame.time.get_ticks():
            self.currentframe = (self.currentframe + 1) % len(self.original_frames)
            self.lastframetick = pygame.time.get_ticks()

        orig_image = self.original_frames[self.currentframe]
        target_angle = get_angle_to_target(self.position, target_center)
        self.image = pygame.transform.rotate(orig_image, target_angle)
        
        self.rect = self.image.get_rect(center=(self.position.x, self.position.y))

        tail_offset = orig_image.get_height() / 2
        tail_x = self.position.x - (dir_x * tail_offset)
        tail_y = self.position.y - (dir_y * tail_offset)
        TrailParticle(tail_x, tail_y)

        screen.blit(self.image, self.rect.topleft)

        if (self.position.y <= -100 or self.position.y >= 850 or 
            self.position.x <= -100 or self.position.x >= 1180):
            if self in Bullet.bullets:
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

# ---- MODULAR SPAWNING HELPERS ----
def spawn_enemy(e_type, x, y):
    """Helper to instantiate enemies cleanly."""
    if e_type == "E1":
        Enemy(x, y, 100, enemy1_frames, explosion_frames, hp=1, shoot_delay=4000, enemy_type="E1")
    elif e_type == "E2":
        Enemy(x, y, 100, enemy2_frames, explosion_frames, hp=2, shoot_delay=3000, enemy_type="E2")
    elif e_type == "E3":
        Enemy(x, y, 125, enemy3_frames, explosion_frames, hp=2, shoot_delay=1500, enemy_type="E3") 
    elif e_type == "E4":
        Enemy(x, y, 150, enemy4_frames, explosion_frames, hp=3, shoot_delay=1000, enemy_type="E4")

def get_formation_offsets(form_type, size):
    """Returns a list of (x_offset, y_offset) relative to a formation's base coordinate."""
    offsets = []
    spacing = 50
    
    if form_type == "horizontal":
        start_x = -((size - 1) * spacing) / 2
        for i in range(size):
            offsets.append((start_x + i * spacing, 0))
            
    elif form_type == "vertical":
        for i in range(size):
            offsets.append((0, -i * spacing))
            
    elif form_type == "v_shape":
        offsets.append((0, 0)) # Leader at front
        for i in range(1, size):
            side = -1 if i % 2 != 0 else 1
            row = (i + 1) // 2
            offsets.append((side * row * spacing, -row * spacing))
            
    elif form_type == "half_v":
        side = random.choice([-1, 1]) # Slant left or slant right
        for i in range(size):
            offsets.append((side * i * spacing, -i * spacing))
            
    return offsets

# Spawning Timers
enemy_spawn_timer = pygame.time.get_ticks()
enemy_spawn_delay = 1500 

formation_spawn_timer = pygame.time.get_ticks()
formation_spawn_delay = random.randint(8000, 15000) 

special_enemy_spawn_timer = pygame.time.get_ticks()
special_enemy_spawn_delay = random.randint(10000, 18000) 

# ---- MAIN GAME LOOP ----
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if game_over:
                if event.key == pygame.K_SPACE:
                    game_over = False
                    player_lives = 3
                    score = 0
                    position = Vector2(590, 360)
                    player_invulnerable = False
                    leftHeld = rightHeld = upHeld = False
                    downHeld = False
                    
                    Enemy.enemies.clear()
                    Bullet.bullets.clear()
                    TrailParticle.particles.clear()
                    
                    now = pygame.time.get_ticks()
                    enemy_spawn_timer = now
                    formation_spawn_timer = now
                    special_enemy_spawn_timer = now
            else:
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
            if not game_over:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a: leftHeld = False
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d: rightHeld = False        
                if event.key == pygame.K_UP or event.key == pygame.K_w: upHeld = False
                if event.key == pygame.K_DOWN or event.key == pygame.K_s: downHeld = False

    if not game_over:
        if leftHeld: position.x -= speed*deltaTime
        if rightHeld: position.x += speed*deltaTime
        if upHeld: position.y -= speed*deltaTime
        if downHeld: position.y += speed*deltaTime

        position.x = max(0, min(1080 - player_rect.width, position.x))
        position.y = max(0, min(720 - player_rect.height, position.y))
       
        player_rect.topleft = (position.x, position.y)

        if playerplanelasttick + 1000/24 <= pygame.time.get_ticks():
            playerplanelasttick = pygame.time.get_ticks()
            playerplanecurrentframe += 1
            if playerplanecurrentframe > len(playerplaneframes) -1:
                playerplanecurrentframe = 0

        # ---- Spawning Framework ----
        now = pygame.time.get_ticks()
        
        # 1. Standard Staggered Enemy Spawning
        if now - enemy_spawn_timer > enemy_spawn_delay:
            enemy_spawn_timer = now
            enemy_type = random.choice(["E1", "E2", "E3", "E4"])
            x = random.randint(50, 1030)
            y = -50
            spawn_enemy(enemy_type, x, y)
            
        # 2. Modular Formation Spawning
        if now - formation_spawn_timer > formation_spawn_delay:
            formation_spawn_timer = now
            formation_spawn_delay = random.randint(8000, 15000) 
            
            form_type = random.choice(["horizontal", "vertical", "v_shape", "half_v"])
            size = random.randint(3, 7)
            
            # Determine formation pool based on requested logic
            pool_roll = random.random()
            if pool_roll < 0.90:
                allowed_types = ["E1", "E2"] 
            elif pool_roll < 0.95:
                allowed_types = ["E3"] 
            else:
                allowed_types = ["E4"] 
                
            base_x = random.randint(250, 830) 
            base_y = -100
            
            offsets = get_formation_offsets(form_type, size)
            for ox, oy in offsets:
                spawn_x = max(50, min(1030, base_x + ox)) 
                spawn_y = base_y + oy
                e_type = random.choice(allowed_types)
                spawn_enemy(e_type, spawn_x, spawn_y)

        # 3. Special Enemy Spawning (Bosses)
        if now - special_enemy_spawn_timer > special_enemy_spawn_delay:
            special_enemy_spawn_timer = now
            special_enemy_spawn_delay = random.randint(10000, 18000) 
            special_enemy_type = random.choice(["B1", "B2"]) 
            random_boss_x = random.randint(100, 980)

            if special_enemy_type == "B1":
                SpecialEnemy(random_boss_x, 800, 80, bigenemy_frames, bigenemy_explosion_frames, spinny_blade_frames, 15, 200, 5000)
            elif special_enemy_type == "B2":
                SpecialEnemy(random_boss_x, 800, 110, boatenemy_frames, boatenemy_explosion_frames, spinny_blade_frames, 20, 200, 10000)

        # ---- Collision Processing Loops ----
        for bullet in Bullet.bullets[:]:
            if isinstance(bullet, TrackingMissile) and bullet.state != "alive":
                continue

            if not bullet.is_enemy:
                # 1. Player Bullet vs Enemy Logic
                for enemy in Enemy.enemies[:]:
                    if enemy.state == "alive" and bullet.rect.colliderect(enemy.rect):
                        enemy.take_damage(1) 
                        if bullet in Bullet.bullets:
                            Bullet.bullets.remove(bullet)
                        break 
                
                # 2. Player Bullet vs Tracking Missile Logic
                if bullet in Bullet.bullets: 
                    for enemy_bullet in Bullet.bullets[:]:
                        if isinstance(enemy_bullet, TrackingMissile) and enemy_bullet.state == "alive":
                            if bullet.rect.colliderect(enemy_bullet.rect):
                                enemy_bullet.hp -= 1
                                if enemy_bullet.hp <= 0:
                                    enemy_bullet.explode() 
                                if bullet in Bullet.bullets:
                                    Bullet.bullets.remove(bullet)
                                break
            
            elif bullet.is_enemy:
                # 3. Enemy Bullet/Missile vs Player Logic
                if not player_invulnerable and bullet.rect.colliderect(player_rect):
                    player_lives -= 1
                    print(f"Player Hit! Lives remaining: {player_lives}")
                    
                    player_invulnerable = True
                    player_invulnerable_timer = pygame.time.get_ticks()
                    
                    if isinstance(bullet, TrackingMissile):
                        bullet.explode() 
                    else:
                        if bullet in Bullet.bullets:
                            Bullet.bullets.remove(bullet)
                        
                    if player_lives <= 0:
                        player_lives = 0  
                        game_over = True

    # ---- RENDERING ENGINE ----
    screen.fill((20, 40, 80))

    now = pygame.time.get_ticks()
    if now - ocean_anim_timer > 1000:
        ocean_anim_timer = now
        ocean_current_frame = (ocean_current_frame + 1) % len(ocean_frames)

    if not game_over:
        ocean_scroll_y += ocean_scroll_speed * deltaTime
        if ocean_scroll_y >= 64:
            ocean_scroll_y -= 64 
            
    screen_w, screen_h = screen.get_size()
    for x in range(0, screen_w + 64, 64):
        for y in range(-64, screen_h + 64, 64):
            screen.blit(ocean_frames[ocean_current_frame], (x, y + int(ocean_scroll_y)))

    for particle in TrailParticle.particles[:]:
        particle.update(deltaTime if not game_over else 0)
        particle.draw(screen)

    for bullet in Bullet.bullets[:]:
        bullet.update(deltaTime if not game_over else 0)

    for enemy in Enemy.enemies[:]:
        enemy.update(deltaTime if not game_over else 0)

    # ---- Player Display ----
    if not game_over:
        if player_invulnerable:
            if now - player_invulnerable_timer > invulnerability_duration:
                player_invulnerable = False
            if (now // 100) % 2 == 0:
                screen.blit(playerplaneframes[playerplanecurrentframe], position)
        else:
            screen.blit(playerplaneframes[playerplanecurrentframe], position)

    # ---- DRAW TEXT ON SCREEN (HUD) ----
    score_surface = ui_font.render(f"SCORE: {score}", True, (255, 255, 255))
    screen.blit(score_surface, (20, 20))

    lives_surface = ui_font.render(f"LIVES: {player_lives}", True, (255, 255, 255))
    lives_rect = lives_surface.get_rect(topright=(1060, 20))
    screen.blit(lives_surface, lives_rect)

    # ---- DEAD STATE INTERACTION ----
    if game_over:
        death_surface = game_over_font.render("YOU DIED", True, (200, 30, 30))
        death_rect = death_surface.get_rect(center=(1080 // 2, 720 // 2 - 40))
        screen.blit(death_surface, death_rect)
        
        restart_surface = ui_font.render("PRESS SPACE TO RESTART", True, (255, 255, 255))
        restart_rect = restart_surface.get_rect(center=(1080 // 2, 720 // 2 + 40))
        screen.blit(restart_surface, restart_rect)

    # ---- VIRTUAL CANVAS SCALING ENGINE ----
    window_w, window_h = window.get_size()
    game_ratio = 1080 / 720
    window_ratio = window_w / window_h

    if window_ratio > game_ratio:
        new_h = window_h
        new_w = int(new_h * game_ratio)
    else:
        new_w = window_w
        new_h = int(new_w / game_ratio)

    x_offset = (window_w - new_w) // 2
    y_offset = (window_h - new_h) // 2

    window.fill((0, 0, 0))

    scaled_screen = pygame.transform.scale(screen, (new_w, new_h))
    window.blit(scaled_screen, (x_offset, y_offset))

    pygame.display.flip()

    fps = 60 
    deltaTime = clock.tick(fps) / 1000
    deltaTime = max(0.001, min(0.1, deltaTime))

pygame.quit()
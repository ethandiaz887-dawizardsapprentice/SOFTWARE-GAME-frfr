from pathlib import Path
import pygame
from pygame.math import Vector2
import random 
import math

pygame.init()

root = Path(__file__).resolve().parents[0]
assets = root / "Assets"

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
kill_count = 0
double_points_active = False
double_points_start = 0
double_points_duration = 30000

insta_kill_active = False
insta_kill_start = 0
insta_kill_duration = 30000

# ---- FONT SYSTEM SETUP ----
font_filename = "Pixel Digivolve.otf"
custom_font_path = assets / font_filename

if custom_font_path.exists():
    font_small = pygame.font.Font(str(custom_font_path), 20)
    font_medium = pygame.font.Font(str(custom_font_path), 28)
    font_large = pygame.font.Font(str(custom_font_path), 36)
    font_huge = pygame.font.Font(str(custom_font_path), 64)
    ui_font = font_medium
    game_over_font = font_huge
else:
    print(f"Custom font '{font_filename}' not found in Assets. Using system default fallback.")
    font_small = pygame.font.SysFont("Arial", 20, bold=True)
    font_medium = pygame.font.SysFont("Arial", 28, bold=True)
    font_large = pygame.font.SysFont("Arial", 36, bold=True)
    font_huge = pygame.font.SysFont("Arial", 64, bold=True)
    ui_font = font_medium
    game_over_font = font_huge

# --- OCEAN SETUP ---
ocean_sheet = pygame.image.load(assets / "OceanTile2.2.png")
ocean_frames = GetDaFrames(ocean_sheet, (1, 2)) 
ocean_scroll_y = 0
ocean_scroll_speed = 50 
ocean_current_frame = 0
ocean_anim_timer = pygame.time.get_ticks()

# ---- PLAYER SETUP ----
position = Vector2(590, 360)
speed = 300
player_rect = pygame.Rect(position.x, position.y, 0, 0) 
player_lives = 20
player_invulnerable = False
player_invulnerable_timer = 0
invulnerability_duration = 1500 

spritesheet = pygame.image.load(assets / "PlayerPlane.png")
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
bulletspritesheet = pygame.image.load(assets / "NewBulletShot.png")
bulletframes = GetDaFrames(bulletspritesheet, (3, 2))

try:
    missile_sheet = pygame.image.load(assets / "GuidedBullet.png")
    missile_frames = GetDaFrames(missile_sheet, (3, 2))
except FileNotFoundError:
    print("GuidedBullet.png not found! Falling back to bullet frames.")
    missile_frames = bulletframes

# --- POWERUP SETUP ---
doublepointssheet = pygame.image.load(assets / "DoublePointsPowerup.png")
doublepointsframes = GetDaFrames(doublepointssheet, (2, 3))

healsheet = pygame.image.load(assets / "HealPowerup.png")
healframes = GetDaFrames(healsheet, (2, 3))

instakillsheet = pygame.image.load(assets / "InstakillPowerup.png")
instakillframes = GetDaFrames(instakillsheet, (4, 2))

try:
    death_sheet = pygame.image.load(assets / "EnemyPlaneDeath.png")
    explosion_frames = GetDaFrames(death_sheet, (2, 3)) 
except FileNotFoundError:
    print("No explosion spritesheet found. Using bullet frames as placeholder.")
    explosion_frames = bulletframes 

try:
    universal_explosion_sheet = pygame.image.load(assets / "UniversalExplosion.png")
    universal_explosion_frames = GetDaFrames(universal_explosion_sheet, (2, 2)) 
except FileNotFoundError:
    print("UniversalExplosion.png not found! Falling back to standard explosion frames.")
    universal_explosion_frames = explosion_frames

enemy1 = pygame.image.load(assets / "EnemyPlane1.png")
enemy1_frames = GetDaFrames(enemy1, (2, 3))

enemy2 = pygame.image.load(assets / "EnemyPlane2.png")
enemy2_frames = GetDaFrames(enemy2, (2, 3))

enemy3 = pygame.image.load(assets / "EnemyPlane3.png")
enemy3_frames = GetDaFrames(enemy3, (2, 3))

enemy4 = pygame.image.load(assets / "EnemyPlane4.png")
enemy4_frames = GetDaFrames(enemy4, (2, 3))

bigenemy_sheet = pygame.image.load(assets / "BigEnemy.png")
bigenemy_frames = GetDaFrames(bigenemy_sheet, (2, 3))

bigenemy_death_sheet = pygame.image.load(assets / "BigEnemyDeath.png")
bigenemy_explosion_frames = GetDaFrames(bigenemy_death_sheet, (2, 2))

spinny_blade_sheet = pygame.image.load(assets / "SpinnyBlade.png")
spinny_blade_frames = GetDaFrames(spinny_blade_sheet, (2, 2))

boatenemy_sheet = pygame.image.load(assets / "EnemyBoat.png")
boatenemy_frames = GetDaFrames(boatenemy_sheet, (3, 2))

boatenemydeath_sheet = pygame.image.load(assets / "EnemyBoatDeath.png")
boatenemy_explosion_frames = GetDaFrames(boatenemydeath_sheet, (3, 2))

# ---- BOSS ASSET LOADING ----
boss_main_sprite = pygame.image.load(assets / "BossSprite.png")
boss_hitbox_sprite = pygame.image.load(assets / "BossSpriteHitBox.png")

boss_gun1_img = pygame.image.load(assets / "BossGun1.png")
boss_gun1_dead_img = pygame.image.load(assets / "BossGun1Dead.png")

boss_gun2_img = pygame.image.load(assets / "BossGun2.png")
boss_gun2_dead_img = pygame.image.load(assets / "BossGun2Dead.png")

boss_gun3_img = pygame.image.load(assets / "BossGun3.png")
boss_gun3_dead_img = pygame.image.load(assets / "BossGun3Dead.png")


# ---- ENEMY CLASSES ----
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
        global score, kill_count, double_points_active
        if self.state == "alive":
            self.state = "dying"
            self.currentframe = 0
            self.frames = self.explosion_frames 
            self.image = self.frames[0]
            
            # Award points (doubled if DoublePoints powerup is active)
            points = 200 if double_points_active else 100
            score += points
            kill_count += 1
            
            # Spawn powerup every 25 kills
            if kill_count % 25 == 0:
                powerup_type = random.choice(["DoublePoints", "Heal", "InstaKill"])
                Powerup(self.rect.centerx, self.rect.centery, powerup_type)  

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


# ---- TRANSLATIONAL PARTICLE AND BULLET CLASSES ----
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


# ---- POWERUP SYSTEM ----
class Powerup:
    powerups = []
    
    def __init__(self, x, y, powerup_type):
        self.position = Vector2(x, y)
        self.powerup_type = powerup_type
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 20000  # 20 seconds
        self.currentframe = 0
        self.lastframetick = pygame.time.get_ticks()
        self.flash_start = self.spawn_time  # Start flashing immediately
        
        # Set frames based on powerup type
        if powerup_type == "DoublePoints":
            self.frames = doublepointsframes
            self.color = (255, 200, 0)  # Yellow
        elif powerup_type == "Heal":
            self.frames = healframes
            self.color = (0, 255, 0)  # Green
        elif powerup_type == "InstaKill":
            self.frames = instakillframes
            self.color = (255, 0, 0)  # Red
        
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))
        
        Powerup.powerups.append(self)
    
    def update(self, deltaTime):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        
        # Animation frame update
        if self.lastframetick + 1000/12 <= pygame.time.get_ticks():  # 12 FPS animation
            self.currentframe += 1
            self.lastframetick = pygame.time.get_ticks()
            if self.currentframe >= len(self.frames):
                self.currentframe = 0
        
        self.image = self.frames[self.currentframe]
        self.rect = self.image.get_rect(center=self.position)
        
        # Check if powerup has expired
        if elapsed >= self.duration:
            if self in Powerup.powerups:
                Powerup.powerups.remove(self)
    
    def draw(self, surface):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        
        # Flash warning in last 5 seconds (flashing every 200ms)
        if elapsed >= 15000:  # Last 5 seconds
            if ((now // 200) % 2 == 0):
                # Draw flashing effect
                alpha = 255 if ((now // 100) % 2 == 0) else 128
                flash_surf = self.image.copy()
                flash_surf.set_alpha(alpha)
                surface.blit(flash_surf, self.rect.topleft)
            else:
                surface.blit(self.image, self.rect.topleft)
        else:
            surface.blit(self.image, self.rect.topleft)


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
        self.hp = 10  # Explicit Boss parameters assignment override
        
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


# ---- MODULAR MULTI-HITBOX BOSS SYSTEM ----
class VisualExplosionParticle:
    """Standalone particle logic to decouple rendering loops from main lists."""
    def __init__(self, center_pos, frames, scale=1.0):
        self.center = center_pos
        self.frames = []
        for f in frames:
            if scale != 1.0:
                sz = f.get_size()
                self.frames.append(pygame.transform.scale(f, (int(sz[0]*scale), int(sz[1]*scale))))
            else:
                self.frames.append(f)
        self.current_frame = 0
        self.last_tick = pygame.time.get_ticks()
        self.finished = False

    def update(self):
        if pygame.time.get_ticks() - self.last_tick > 1000 / 24:
            self.last_tick = pygame.time.get_ticks()
            self.current_frame += 1
            if self.current_frame >= len(self.frames):
                self.finished = True

    def draw(self, surface):
        if not self.finished:
            img = self.frames[self.current_frame]
            rect = img.get_rect(center=self.center)
            surface.blit(img, rect.topleft)


class BossComponent:
    def __init__(self, alive_img, dead_img, offset_x, offset_y, hp):
        # Scale every component image up by 50% (2x)
        self.alive_img = pygame.transform.scale(alive_img, (int(alive_img.get_width() * 2), int(alive_img.get_height() * 2)))
        self.dead_img = pygame.transform.scale(dead_img, (int(dead_img.get_width() * 2), int(dead_img.get_height() * 2)))
        self.image = self.alive_img
        # Scale the offsets by 2 to match the larger structural footprint
        self.offset = Vector2(offset_x * 2, offset_y * 2)
        self.hp = hp
        self.max_hp = hp
        self.is_dead = False
        self.rect = self.image.get_rect()
        
        self.is_flashing = False
        self.flash_start = 0

    def take_damage(self, amt):
        if self.is_dead: return
        self.hp -= amt
        self.is_flashing = True
        self.flash_start = pygame.time.get_ticks()
        if self.hp <= 0:
            self.is_dead = True
            self.image = self.dead_img
            global boss_explosions, universal_explosion_frames
            boss_explosions.append(VisualExplosionParticle(self.rect.center, universal_explosion_frames, scale=1.0))

    def update(self, boss_center, player_center, dt, can_fire=True):
        self.rect.center = boss_center + self.offset
        if pygame.time.get_ticks() - self.flash_start > 100:
            self.is_flashing = False

    def draw(self, surface):
        if self.is_flashing and not self.is_dead:
            mask = pygame.mask.from_surface(self.image)
            white_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
            surface.blit(white_surf, self.rect.topleft)
        else:
            surface.blit(self.image, self.rect.topleft)


class BossTrackingGun(BossComponent):
    """BossGun1 Logic: Always handles rotation/tracking. Fires 5 targeting missiles."""
    def __init__(self, alive_img, dead_img, offset_x, offset_y, hp):
        super().__init__(alive_img, dead_img, offset_x, offset_y, hp)
        self.last_shot = pygame.time.get_ticks()
        self.shot_interval = 20000 

    def update(self, boss_center, player_center, dt, can_fire=True):
        super().update(boss_center, player_center, dt, can_fire)
        if not self.is_dead:
            dx = player_center.x - self.rect.centerx
            dy = player_center.y - self.rect.centery
            angle = math.degrees(math.atan2(-dy, dx)) - 90
            self.image = pygame.transform.rotate(self.alive_img, angle)
            self.rect = self.image.get_rect(center=self.rect.center)

            now = pygame.time.get_ticks()
            if can_fire and now - self.last_shot > self.shot_interval:
                self.last_shot = now
                for i in range(5):
                    TrackingMissile(self.rect.centerx, self.rect.centery, 220, missile_frames, lifetime=5000)


class BossBurstGun(BossComponent):
    """BossGun2 Logic: Rotates and tracks the target. Fires bursts of 4 round shots."""
    def __init__(self, alive_img, dead_img, offset_x, offset_y, hp):
        super().__init__(alive_img, dead_img, offset_x, offset_y, hp)
        self.last_burst = pygame.time.get_ticks()
        self.burst_interval = 2000
        self.in_burst = False
        self.burst_count = 0
        self.last_shot = 0
        self.shot_delay = 150
        self.fire_angle = 180

    def update(self, boss_center, player_center, dt, can_fire=True):
        super().update(boss_center, player_center, dt, can_fire)
        if not self.is_dead:
            dx = player_center.x - self.rect.centerx
            dy = player_center.y - self.rect.centery
            angle = math.degrees(math.atan2(-dy, dx)) - 90
            self.fire_angle = angle
            self.image = pygame.transform.rotate(self.alive_img, angle)
            self.rect = self.image.get_rect(center=self.rect.center)

            now = pygame.time.get_ticks()
            if not self.in_burst and can_fire and now - self.last_burst > self.burst_interval:
                self.in_burst = True
                self.burst_count = 0
                self.last_shot = now

            if self.in_burst and now - self.last_shot > self.shot_delay:
                self.last_shot = now
                rads = math.radians(-self.fire_angle + 90)
                bx = math.cos(rads) * 250
                by = -math.sin(rads) * 250
                Bullet(self.rect.centerx, self.rect.centery, by, bulletframes, is_enemy=True, speed_x=-bx, angle=self.fire_angle)
                self.burst_count += 1
                if self.burst_count >= 3:
                    self.in_burst = False
                    self.last_burst = now


class BossSpreadGun(BossComponent):
    """BossGun3 Logic: Static side components firing spreads of 7 rounds."""
    def __init__(self, alive_img, dead_img, offset_x, offset_y, hp, flip_x=False):
        if flip_x:
            alive_img = pygame.transform.flip(alive_img, True, False)
            dead_img = pygame.transform.flip(dead_img, True, False)
        super().__init__(alive_img, dead_img, offset_x, offset_y, hp)
        self.last_burst = pygame.time.get_ticks()
        self.burst_interval = 3500
        self.in_burst = False
        self.burst_count = 0
        self.last_shot = 0
        self.shot_delay = 120
        self.flip_x = flip_x

    def update(self, boss_center, player_center, dt, can_fire=True):
        super().update(boss_center, player_center, dt, can_fire)
        if not self.is_dead:
            now = pygame.time.get_ticks()
            if not self.in_burst and can_fire and now - self.last_burst > self.burst_interval:
                self.in_burst = True
                self.burst_count = 0
                self.last_shot = now

            if self.in_burst and now - self.last_shot > self.shot_delay:
                self.last_shot = now
                base_angle = 135 if not self.flip_x else 225
                for offset_deg in [-30, -15, 0, 15, 30]:
                    final_angle = base_angle + offset_deg
                    rads = math.radians(-final_angle + 90)
                    bx = math.cos(rads) * 200
                    by = -math.sin(rads) * 200
                    
                    bx = -bx
                    final_angle = -final_angle
                    
                    Bullet(self.rect.centerx, self.rect.centery, by, bulletframes, is_enemy=True, speed_x=-bx, angle=final_angle)
                
                self.burst_count += 1
                if self.burst_count >= 5:
                    self.in_burst = False
                    self.last_burst = now


class MasterBossFight:
    def __init__(self):
        self.position = Vector2(540, 850) 
        self.hp = 250
        self.max_hp = 250
        self.state = "entering"  
        self.timer = 0
        self.components = []
        
        self.visual_img = pygame.transform.scale(boss_main_sprite, (int(boss_main_sprite.get_width() * 2), int(boss_main_sprite.get_height() * 2)))
        self.hitbox_img = pygame.transform.scale(boss_hitbox_sprite, (int(boss_hitbox_sprite.get_width() * 2), int(boss_hitbox_sprite.get_height() * 2)))
        self.rect = self.visual_img.get_rect()
        self.hitbox_rect = self.hitbox_img.get_rect()
        
        self.is_flashing = False
        self.flash_start = 0
        
        self.death_interval_timer = 0
        self.death_glide_speed = -100

        # ---- LAYER REORDERING ----
        # Appending the SpreadGuns (Gun3) FIRST so they render BEHIND/UNDER BossTrackingGun (Gun1)
        self.components.append(BossSpreadGun(boss_gun3_img, boss_gun3_dead_img, 20, 15, 45, flip_x=False)) # Right Side Spread
        self.components.append(BossSpreadGun(boss_gun3_img, boss_gun3_dead_img, -20, 15, 45, flip_x=True))  # Left Side Spread
        
        # Now adding the rest of the guns so they appear on higher visual layers
        self.components.append(BossTrackingGun(boss_gun1_img, boss_gun1_dead_img, 0, -20, 30)) # Central Tracking Gun
        self.components.append(BossBurstGun(boss_gun2_img, boss_gun2_dead_img, -160, -14, 30))  # Left Wing
        self.components.append(BossBurstGun(boss_gun2_img, boss_gun2_dead_img, -100, -9, 30))  # Left Wing

        self.components.append(BossBurstGun(boss_gun2_img, boss_gun2_dead_img, 160, -14, 30))   # Right Wing
        self.components.append(BossBurstGun(boss_gun2_img, boss_gun2_dead_img, 100, -9, 30))   # Right Wing

        self.components.append(BossBurstGun(boss_gun2_img, boss_gun2_dead_img, -30, 70, 30))    # Left Tail
        self.components.append(BossBurstGun(boss_gun2_img, boss_gun2_dead_img, 30, 70, 30))     # Right Tail

    def take_damage(self, amt):
        if self.state in ["dying", "dead"]: return
        self.hp -= amt
        self.is_flashing = True
        self.flash_start = pygame.time.get_ticks()
        
        if self.hp <= 0:
            self.state = "dying"
            self.death_interval_timer = pygame.time.get_ticks()
            
            # ---- INSTANT COMPONENT DEATH TRIGGERS ----
            # Forces all surviving components to immediately switch to their death states/animations
            for comp in self.components:
                if not comp.is_dead:
                    comp.take_damage(comp.hp) # Deals damage equal to remaining health to cleanly trigger internal explosion rules

    def update(self, dt):
        now = pygame.time.get_ticks()
        player_center = Vector2(position.x + player_rect.width/2, position.y + player_rect.height/2)
        
        if pygame.time.get_ticks() - self.flash_start > 100:
            self.is_flashing = False

        if self.state == "entering":
            self.position.y -= 150 * dt
            if self.position.y <= 360:
                self.position.y = 360
                self.state = "hovering"
                self.timer = now

        elif self.state == "hovering":
            if now - self.timer > 150000: 
                self.state = "leaving"

        elif self.state == "leaving":
            self.position.y -= 120 * dt
            if self.position.y < -300:
                self.state = "dead"

        elif self.state == "dying":
            self.position.x += self.death_glide_speed * dt
            
            if now - self.death_interval_timer > 1000:
                self.death_interval_timer = now
                global boss_explosions, universal_explosion_frames
                boss_explosions.append(VisualExplosionParticle(self.rect.center, universal_explosion_frames, scale=5))
                for _ in range(5):
                    rx = self.rect.centerx + random.randint(-250, 250)
                    ry = self.rect.centery + random.randint(-20, 20)
                    boss_explosions.append(VisualExplosionParticle((rx, ry), universal_explosion_frames, scale=3))
            
            if self.position.x < -400:
                self.state = "dead"

        self.rect.center = (int(self.position.x), int(self.position.y))
        self.hitbox_rect.center = self.rect.center

        can_fire = (self.state == "hovering")
        for comp in self.components:
            comp.update(self.position, player_center, dt, can_fire)

    def draw(self, surface):
        if self.is_flashing:
            mask = pygame.mask.from_surface(self.visual_img)
            white_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
            surface.blit(white_surf, self.rect.topleft)
        else:
            surface.blit(self.visual_img, self.rect.topleft)

        for comp in self.components:
            comp.draw(surface)


class GamePhaseManager:
    def __init__(self):
        self.phase = "WAVE"  
        self.game_start_time = pygame.time.get_ticks()
        self.clearing_timer = 0
        self.boss = None

    def update(self, dt):
        now = pygame.time.get_ticks()
        
        if self.phase == "WAVE":
            if now - self.game_start_time > 120000:  
                self.trigger_boss_sequence()

        elif self.phase == "CLEARING":
            if now - self.clearing_timer > 5000:     
                self.phase = "BOSS"
                self.boss = MasterBossFight()

        elif self.phase == "BOSS":
            if self.boss:
                self.boss.update(dt)
                if self.boss.state == "dead":
                    self.boss = None
                    self.clearing_timer = now
                    self.phase = "POST_BOSS_GAP"
                    
        elif self.phase == "POST_BOSS_GAP":
            if pygame.time.get_ticks() - self.clearing_timer > 5000: 
                self.phase = "WAVE"
                self.game_start_time = pygame.time.get_ticks()

    def trigger_boss_sequence(self):
        if self.phase == "WAVE":
            self.phase = "CLEARING"
            self.clearing_timer = pygame.time.get_ticks()
            Enemy.enemies.clear() 


# ---- SYSTEM DECLARATIONS ----
phase_manager = GamePhaseManager()
boss_explosions = []

shoot_delay = 100 
last_shot = pygame.time.get_ticks()

def activate_powerup(powerup_type):
    """Activate the specified powerup effect"""
    global double_points_active, double_points_start, insta_kill_active, insta_kill_start, player_lives
    
    if powerup_type == "DoublePoints":
        double_points_active = True
        double_points_start = pygame.time.get_ticks()
    elif powerup_type == "Heal":
        player_lives = 20
    elif powerup_type == "InstaKill":
        insta_kill_active = True
        insta_kill_start = pygame.time.get_ticks()

def update_powerup_timers():
    """Update powerup durations and deactivate expired ones"""
    global double_points_active, insta_kill_active
    now = pygame.time.get_ticks()
    
    if double_points_active and now - double_points_start > double_points_duration:
        double_points_active = False
    
    if insta_kill_active and now - insta_kill_start > insta_kill_duration:
        insta_kill_active = False

def shoot(spawn_pos):
    global last_shot
    now = pygame.time.get_ticks()
    if now - last_shot > shoot_delay:
        last_shot = now
        Bullet(spawn_pos.x-16, spawn_pos.y, -400, bulletframes, is_enemy=False)
        Bullet(spawn_pos.x-8, spawn_pos.y, -400, bulletframes, is_enemy=False)
        Bullet(spawn_pos.x+16, spawn_pos.y, -400, bulletframes, is_enemy=False)
        Bullet(spawn_pos.x+8, spawn_pos.y, -400, bulletframes, is_enemy=False)

def spawn_enemy(e_type, x, y):
    if e_type == "E1":
        Enemy(x, y, 100, enemy1_frames, explosion_frames, hp=1, shoot_delay=4000, enemy_type="E1")
    elif e_type == "E2":
        Enemy(x, y, 100, enemy2_frames, explosion_frames, hp=2, shoot_delay=3000, enemy_type="E2")
    elif e_type == "E3":
        Enemy(x, y, 125, enemy3_frames, explosion_frames, hp=2, shoot_delay=1500, enemy_type="E3") 
    elif e_type == "E4":
        Enemy(x, y, 150, enemy4_frames, explosion_frames, hp=3, shoot_delay=1000, enemy_type="E4")

def get_formation_offsets(form_type, size):
    offsets = []
    spacing = 50
    if form_type == "horizontal":
        start_x = -((size - 1) * spacing) / 2
        for i in range(size): offsets.append((start_x + i * spacing, 0))
    elif form_type == "vertical":
        for i in range(size): offsets.append((0, -i * spacing))
    elif form_type == "v_shape":
        offsets.append((0, 0))
        for i in range(1, size):
            side = -1 if i % 2 != 0 else 1
            row = (i + 1) // 2
            offsets.append((side * row * spacing, -row * spacing))
    elif form_type == "half_v":
        side = random.choice([-1, 1])
        for i in range(size): offsets.append((side * i * spacing, -i * spacing))
    return offsets

enemy_spawn_timer = pygame.time.get_ticks()
enemy_spawn_delay = 1500 
formation_spawn_timer = pygame.time.get_ticks()
formation_spawn_delay = random.randint(8000, 15000) 
special_enemy_spawn_timer = pygame.time.get_ticks()
special_enemy_spawn_delay = random.randint(10000, 18000) 


# ---- MODULAR UI SYSTEM ----
class UIButton:
    """Modular UI Button with customizable styling"""
    def __init__(self, text, x, y, width, height, font, 
                 button_color=(50, 100, 180), border_color=(255, 255, 255), 
                 border_width=3, text_color=(255, 255, 255)):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.font = font
        self.button_color = button_color
        self.border_color = border_color
        self.border_width = border_width
        self.text_color = text_color
        self.is_selected = False
        self.rect = pygame.Rect(x, y, width, height)
    
    def update_position(self, x, y):
        """Update button position"""
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, self.width, self.height)
    
    def draw(self, surface):
        """Draw button with selection highlighting"""
        # Draw button background
        pygame.draw.rect(surface, self.button_color, self.rect)
        
        # Draw border (thicker if selected)
        border = self.border_width * 2 if self.is_selected else self.border_width
        pygame.draw.rect(surface, self.border_color, self.rect, border)
        
        # Draw text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def is_hovered(self, pos):
        """Check if mouse is hovering over button"""
        return self.rect.collidepoint(pos)


class Menu:
    """Modular Menu System for navigation"""
    def __init__(self, title, buttons, title_font=font_large):
        self.title = title
        self.buttons = buttons
        self.current_selection = 0
        self.title_font = title_font
        self.update_selection()
    
    def update_selection(self):
        """Update button selection states"""
        for i, button in enumerate(self.buttons):
            button.is_selected = (i == self.current_selection)
    
    def navigate_up(self):
        """Navigate to previous button"""
        self.current_selection = (self.current_selection - 1) % len(self.buttons)
        self.update_selection()
    
    def navigate_down(self):
        """Navigate to next button"""
        self.current_selection = (self.current_selection + 1) % len(self.buttons)
        self.update_selection()
    
    def select_current(self):
        """Return the currently selected button's action"""
        return self.buttons[self.current_selection].text
    
    def draw(self, surface):
        """Draw menu with title and buttons"""
        # Draw title
        title_surface = self.title_font.render(self.title, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(540, 80))
        surface.blit(title_surface, title_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface)


# ---- GAME STATE MANAGEMENT ----
class GameState:
    """Manages different game states"""
    MAIN_MENU = "main_menu"
    PLAYING = "playing"
    PAUSED = "paused"
    CONTROLS = "controls"
    CREDITS = "credits"

current_state = GameState.MAIN_MENU
previous_state = GameState.MAIN_MENU


# ---- MENU CREATION ----
def create_main_menu():
    """Create main menu"""
    buttons = [
        UIButton("PLAY", 340, 250, 400, 80, font_large, 
                button_color=(50, 150, 50), border_color=(100, 255, 100)),
        UIButton("CONTROLS", 340, 370, 400, 80, font_large,
                button_color=(100, 100, 180), border_color=(150, 150, 255)),
        UIButton("CREDITS", 340, 490, 400, 80, font_large,
                button_color=(150, 100, 50), border_color=(255, 180, 100))
    ]
    return Menu("THE PLANE GAME", buttons, font_huge)


def create_controls_menu():
    """Create controls menu"""
    buttons = [
        UIButton("BACK", 340, 550, 400, 80, font_large,
                button_color=(100, 50, 50), border_color=(255, 100, 100))
    ]
    menu = Menu("CONTROLS", buttons, font_huge)
    menu.controls_text = [
        "WASD / ARROW KEYS - MOVE",
        "SPACE - SHOOT",
        "B - SKIP TO BOSS (JUST FOR TESTERS)",
        "ESC - PAUSE GAME",
        "ARROW KEYS / WASD - NAVIGATE MENUS"
    ]
    return menu


def create_credits_menu():
    """Create credits menu"""
    buttons = [
        UIButton("BACK", 340, 600, 400, 80, font_large,
                button_color=(100, 50, 50), border_color=(255, 100, 100))
    ]
    menu = Menu("CREDITS", buttons, font_huge)
    menu.credits_text = [
        "GAME DESIGN",
        "[Ethan Diaz]",
        "",
        "GRAPHICS & ASSETS",
        "[Ethan Diaz, Arush Mula]",
        "",
        "MUSIC & SOUND DESIGN",
        "[Idk man]",
        "",
        "TESTERS",
        "[Zac Matthews, Ian Jimenez Pereira]",
        "",
        "DOCUMENTATION & DEVELOPMENT",
        "[Ethan Diaz, Arush Mula, Zac Matthews, Ian Jimenez Pereira]"
    ]
    return menu


def create_pause_menu():
    """Create pause menu"""
    buttons = [
        UIButton("RESUME", 340, 250, 400, 80, font_large,
                button_color=(50, 150, 50), border_color=(100, 255, 100)),
        UIButton("RESTART", 340, 370, 400, 80, font_large,
                button_color=(150, 100, 50), border_color=(255, 180, 100)),
        UIButton("MAIN MENU", 340, 490, 400, 80, font_large,
                button_color=(100, 50, 50), border_color=(255, 100, 100))
    ]
    return Menu("PAUSED", buttons, font_huge)


# Initialize menus
main_menu = create_main_menu()
controls_menu = create_controls_menu()
credits_menu = create_credits_menu()
pause_menu = create_pause_menu()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            # Menu navigation keys
            if current_state in [GameState.MAIN_MENU, GameState.CONTROLS, GameState.CREDITS]:
                if event.key in [pygame.K_UP, pygame.K_w]:
                    if current_state == GameState.MAIN_MENU:
                        main_menu.navigate_up()
                    elif current_state == GameState.CONTROLS:
                        controls_menu.navigate_up()
                    elif current_state == GameState.CREDITS:
                        credits_menu.navigate_up()
                
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    if current_state == GameState.MAIN_MENU:
                        main_menu.navigate_down()
                    elif current_state == GameState.CONTROLS:
                        controls_menu.navigate_down()
                    elif current_state == GameState.CREDITS:
                        credits_menu.navigate_down()
                
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if current_state == GameState.MAIN_MENU:
                        selection = main_menu.select_current()
                        if selection == "PLAY":
                            current_state = GameState.PLAYING
                            game_over = False
                            player_lives = 20
                            score = 0
                            kill_count = 0
                            double_points_active = False
                            insta_kill_active = False
                            position = Vector2(590, 360)
                            player_invulnerable = False
                            leftHeld = rightHeld = upHeld = downHeld = False
                            Enemy.enemies.clear()
                            Bullet.bullets.clear()
                            TrailParticle.particles.clear()
                            Powerup.powerups.clear()
                            boss_explosions.clear()
                            phase_manager = GamePhaseManager()
                            now = pygame.time.get_ticks()
                            enemy_spawn_timer = now
                            formation_spawn_timer = now
                            special_enemy_spawn_timer = now
                        elif selection == "CONTROLS":
                            current_state = GameState.CONTROLS
                        elif selection == "CREDITS":
                            current_state = GameState.CREDITS
                    
                    elif current_state == GameState.CONTROLS:
                        if controls_menu.select_current() == "BACK":
                            current_state = GameState.MAIN_MENU
                    
                    elif current_state == GameState.CREDITS:
                        if credits_menu.select_current() == "BACK":
                            current_state = GameState.MAIN_MENU
            
            # Pause menu navigation
            elif current_state == GameState.PAUSED:
                if event.key in [pygame.K_UP, pygame.K_w]:
                    pause_menu.navigate_up()
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    pause_menu.navigate_down()
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    selection = pause_menu.select_current()
                    if selection == "RESUME":
                        current_state = GameState.PLAYING
                    elif selection == "RESTART":
                        current_state = GameState.PLAYING
                        game_over = False
                        player_lives = 20
                        score = 0
                        kill_count = 0
                        double_points_active = False
                        insta_kill_active = False
                        position = Vector2(590, 360)
                        player_invulnerable = False
                        leftHeld = rightHeld = upHeld = downHeld = False
                        Enemy.enemies.clear()
                        Bullet.bullets.clear()
                        TrailParticle.particles.clear()
                        Powerup.powerups.clear()
                        boss_explosions.clear()
                        phase_manager = GamePhaseManager()
                        now = pygame.time.get_ticks()
                        enemy_spawn_timer = now
                        formation_spawn_timer = now
                        special_enemy_spawn_timer = now
                    elif selection == "MAIN MENU":
                        current_state = GameState.MAIN_MENU
                        pause_menu.current_selection = 0
                        pause_menu.update_selection()
                        game_over = False
                        player_lives = 20
                        score = 0
                        kill_count = 0
                        double_points_active = False
                        insta_kill_active = False
                        position = Vector2(590, 360)
                        player_invulnerable = False
                        leftHeld = rightHeld = upHeld = downHeld = False
                        Enemy.enemies.clear()
                        Bullet.bullets.clear()
                        TrailParticle.particles.clear()
                        Powerup.powerups.clear()
                        boss_explosions.clear()
                        phase_manager = GamePhaseManager()
            
            # In-game pause toggle
            elif current_state == GameState.PLAYING and event.key == pygame.K_ESCAPE:
                current_state = GameState.PAUSED
                pause_menu.current_selection = 0
                pause_menu.update_selection()
            
            # Game over screen - return to menu
            elif current_state == GameState.PLAYING and game_over and (event.key == pygame.K_SPACE or event.key == pygame.K_RETURN):
                current_state = GameState.MAIN_MENU
                main_menu.current_selection = 0
                main_menu.update_selection()
            
            # In-game controls
            elif current_state == GameState.PLAYING:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a: leftHeld = True
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d: rightHeld = True
                if event.key == pygame.K_UP or event.key == pygame.K_w: upHeld = True
                if event.key == pygame.K_DOWN or event.key == pygame.K_s: downHeld = True
                
                if event.key == pygame.K_b:
                    phase_manager.trigger_boss_sequence()

                if event.key == pygame.K_SPACE:    
                    plane_size = playerplaneframes[playerplanecurrentframe].get_size()
                    center_x = position.x + (plane_size[0] / 2)
                    center_y = position.y
                    shoot(Vector2(center_x, center_y))

        elif event.type == pygame.KEYUP:
            if current_state == GameState.PLAYING:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a: leftHeld = False
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d: rightHeld = False        
                if event.key == pygame.K_UP or event.key == pygame.K_w: upHeld = False
                if event.key == pygame.K_DOWN or event.key == pygame.K_s: downHeld = False

    if current_state == GameState.PLAYING and not game_over:
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
            if playerplanecurrentframe > len(playerplaneframes) - 1:
                playerplanecurrentframe = 0

        phase_manager.update(deltaTime)
        now = pygame.time.get_ticks()
        
        if phase_manager.phase == "WAVE":
            if now - enemy_spawn_timer > enemy_spawn_delay:
                enemy_spawn_timer = now
                enemy_type = random.choice(["E1", "E2", "E3", "E4"])
                x = random.randint(50, 1030)
                y = -50
                spawn_enemy(enemy_type, x, y)
                
            if now - formation_spawn_timer > formation_spawn_delay:
                formation_spawn_timer = now
                formation_spawn_delay = random.randint(8000, 15000) 
                form_type = random.choice(["horizontal", "vertical", "v_shape", "half_v"])
                size = random.randint(3, 7)
                pool_roll = random.random()
                if pool_roll < 0.90: allowed_types = ["E1", "E2"] 
                elif pool_roll < 0.95: allowed_types = ["E3"] 
                else: allowed_types = ["E4"] 
                    
                base_x = random.randint(250, 830) 
                base_y = -100
                offsets = get_formation_offsets(form_type, size)
                for ox, oy in offsets:
                    spawn_x = max(50, min(1030, base_x + ox)) 
                    spawn_y = base_y + oy
                    e_type = random.choice(allowed_types)
                    spawn_enemy(e_type, spawn_x, spawn_y)

            if now - special_enemy_spawn_timer > special_enemy_spawn_delay:
                special_enemy_spawn_timer = now
                special_enemy_spawn_delay = random.randint(10000, 18000) 
                special_enemy_type = random.choice(["B1", "B2"]) 
                random_boss_x = random.randint(100, 980)
                if special_enemy_type == "B1":
                    SpecialEnemy(random_boss_x, 800, 80, bigenemy_frames, bigenemy_explosion_frames, spinny_blade_frames, 15, 200, 5000)
                elif special_enemy_type == "B2":
                    SpecialEnemy(random_boss_x, 800, 110, boatenemy_frames, boatenemy_explosion_frames, spinny_blade_frames, 20, 200, 10000)

        # ---- COLLISION PROCESSING LOOPS ----
        for bullet in Bullet.bullets[:]:
            if isinstance(bullet, TrackingMissile) and bullet.state != "alive":
                continue

            if not bullet.is_enemy:
                for enemy in Enemy.enemies[:]:
                    if enemy.state == "alive" and bullet.rect.colliderect(enemy.rect):
                        # Apply InstaKill if active
                        if insta_kill_active:
                            enemy.hp = 1  # Set to 1 so next damage kills instantly
                        enemy.take_damage(1) 
                        if bullet in Bullet.bullets:
                            Bullet.bullets.remove(bullet)
                        break 
                
                if bullet in Bullet.bullets: 
                    for enemy_bullet in Bullet.bullets[:]:
                        if isinstance(enemy_bullet, TrackingMissile) and enemy_bullet.state == "alive":
                            if bullet.rect.colliderect(enemy_bullet.rect):
                                enemy_bullet.hp -= 1
                                if enemy_bullet.hp <= 0: enemy_bullet.explode() 
                                if bullet in Bullet.bullets: Bullet.bullets.remove(bullet)
                                break

                if bullet in Bullet.bullets and phase_manager.phase == "BOSS" and phase_manager.boss:
                    boss_obj = phase_manager.boss
                    hit_registered = False
                    
                    for comp in boss_obj.components:
                        if not comp.is_dead and bullet.rect.colliderect(comp.rect):
                            comp.take_damage(1)
                            if bullet in Bullet.bullets: Bullet.bullets.remove(bullet)
                            hit_registered = True
                            break
                    
                    if not hit_registered and boss_obj.state in ["entering", "hovering", "leaving"]:
                        if bullet.rect.colliderect(boss_obj.hitbox_rect):
                            boss_obj.take_damage(1)
                            if bullet in Bullet.bullets: Bullet.bullets.remove(bullet)
            
            elif bullet.is_enemy:
                if not player_invulnerable and bullet.rect.colliderect(player_rect):
                    player_lives -= 1
                    player_invulnerable = True
                    player_invulnerable_timer = pygame.time.get_ticks()
                    
                    if isinstance(bullet, TrackingMissile): bullet.explode() 
                    else:
                        if bullet in Bullet.bullets: Bullet.bullets.remove(bullet)
                        
                    if player_lives <= 0:
                        player_lives = 0  
                        game_over = True
        
        # ---- POWERUP COLLISION DETECTION ----
        for powerup in Powerup.powerups[:]:
            if powerup.rect.colliderect(player_rect):
                activate_powerup(powerup.powerup_type)
                if powerup in Powerup.powerups:
                    Powerup.powerups.remove(powerup)

    # ---- RENDERING ENGINE ----
    screen.fill((20, 40, 80))

    now = pygame.time.get_ticks()
    if now - ocean_anim_timer > 1000:
        ocean_anim_timer = now
        ocean_current_frame = (ocean_current_frame + 1) % len(ocean_frames)

    if current_state == GameState.PLAYING:
        ocean_scroll_y += ocean_scroll_speed * deltaTime
        if ocean_scroll_y >= 64: ocean_scroll_y -= 64 
            
    screen_w, screen_h = screen.get_size()
    for x in range(0, screen_w + 64, 64):
        for y in range(-64, screen_h + 64, 64):
            screen.blit(ocean_frames[ocean_current_frame], (x, y + int(ocean_scroll_y)))

    # Render game state specific content
    if current_state == GameState.MAIN_MENU:
        main_menu.draw(screen)
    
    elif current_state == GameState.CONTROLS:
        controls_menu.draw(screen)
        # Draw controls text
        control_y = 200
        for line in controls_menu.controls_text:
            control_surf = font_small.render(line, True, (200, 200, 200))
            screen.blit(control_surf, (150, control_y))
            control_y += 40
    
    elif current_state == GameState.CREDITS:
        credits_menu.draw(screen)
        # Draw credits text
        credit_y = 200
        for line in credits_menu.credits_text:
            if line == "":
                credit_y += 20
            else:
                credit_surf = font_small.render(line, True, (200, 200, 200))
                screen.blit(credit_surf, (150, credit_y))
                credit_y += 30
    
    elif current_state == GameState.PLAYING:
        # Draw game elements
        for particle in TrailParticle.particles[:]:
            particle.update(deltaTime if not game_over else 0)
            particle.draw(screen)

        for bullet in Bullet.bullets[:]:
            bullet.update(deltaTime if not game_over else 0)

        for enemy in Enemy.enemies[:]:
            enemy.update(deltaTime if not game_over else 0)
        
        # Update and draw powerups
        for powerup in Powerup.powerups[:]:
            powerup.update(deltaTime if not game_over else 0)
            powerup.draw(screen)
        
        # Update powerup timers
        update_powerup_timers()

        if phase_manager.phase == "BOSS" and phase_manager.boss:
            phase_manager.boss.draw(screen)

        for exp in boss_explosions[:]:
            exp.update()
            exp.draw(screen)
            if exp.finished: boss_explosions.remove(exp)

        if not game_over:
            if player_invulnerable:
                if now - player_invulnerable_timer > invulnerability_duration:
                    player_invulnerable = False
                if (now // 100) % 2 == 0:
                    screen.blit(playerplaneframes[playerplanecurrentframe], position)
            else:
                screen.blit(playerplaneframes[playerplanecurrentframe], position)

        # Draw HUD
        score_surface = font_medium.render(f"SCORE: {score}", True, (255, 255, 255))
        screen.blit(score_surface, (20, 20))

        lives_surface = font_medium.render(f"LIVES: {player_lives}", True, (255, 255, 255))
        lives_rect = lives_surface.get_rect(topright=(1060, 20))
        screen.blit(lives_surface, lives_rect)
        
        # Display active powerups
        powerup_y = 60
        if double_points_active:
            time_remaining = max(0, double_points_duration - (now - double_points_start)) // 1000
            double_points_surface = font_medium.render(f"2x POINTS: {time_remaining}s", True, (255, 200, 0))
            screen.blit(double_points_surface, (20, powerup_y))
            powerup_y += 40
        
        if insta_kill_active:
            time_remaining = max(0, insta_kill_duration - (now - insta_kill_start)) // 1000
            insta_kill_surface = font_medium.render(f"INSTA KILL: {time_remaining}s", True, (255, 0, 0))
            screen.blit(insta_kill_surface, (20, powerup_y))
        
        # Display kill count
        kill_count_surface = font_medium.render(f"KILLS: {kill_count}", True, (200, 200, 200))
        screen.blit(kill_count_surface, (20, 680))

        if phase_manager.phase == "WAVE":
            hint_surf = font_small.render("PRESS 'B' TO SKIP TO BOSS", True, (200, 200, 200))
            screen.blit(hint_surf, (350, 680))
        
        # Show pause hint
        pause_hint = font_small.render("PRESS ESC TO PAUSE", True, (150, 150, 150))
        screen.blit(pause_hint, (800, 680))
        
        # Game over screen
        if game_over:
            death_surface = font_huge.render("YOU DIED", True, (200, 30, 30))
            death_rect = death_surface.get_rect(center=(540, 300))
            screen.blit(death_surface, death_rect)
            
            restart_surface = font_large.render("PRESS SPACE TO RETURN TO MENU", True, (255, 255, 255))
            restart_rect = restart_surface.get_rect(center=(540, 400))
            screen.blit(restart_surface, restart_rect)
    
    elif current_state == GameState.PAUSED:
        pause_menu.draw(screen)

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
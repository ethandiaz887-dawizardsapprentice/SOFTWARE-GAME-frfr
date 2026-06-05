from pathlib import Path

import pygame
from pygame.math import Vector2
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

position = Vector2(590,360)



spritesheet = pygame.image.load(assets/"PlayerPlane.png")

playerplaneframes = GetDaFrames(spritesheet, (2, 3))
playerplanecurrentframe = 0

playerplanelasttick = pygame.time.get_ticks()

deltaTime = 0.1

leftHeld = False
rightHeld = False
upHeld = False
downHeld = False

speed = 300


##


class Bullet():
    bullets = []

    def __init__(self, sprite, x, y):
        super().__init__()
        Bullet.bullets.append(self)
        self.image = sprite
        self.image = pygame.transform.scale_by(self.image, 0.1)
        self.image.fill((255, 255, 0)) # Yellow
        self.position = Vector2(x, y)
        
        self.speed = -50


    def update(self, deltaTime):
        screen.blit(self.image, self.position)
        self.position.y += (self.speed * deltaTime)
        if self.position.y <= 0:
            Bullet.bullets.remove(self)
            


shoot_delay = 1 # ms
last_shot = pygame.time.get_ticks()

def shoot(spawn_pos):
    global last_shot
    now = pygame.time.get_ticks()
    if now - last_shot > shoot_delay:
        last_shot = now
        new_bullet = Bullet(pygame.image.load(assets/"BulletShot.png"), spawn_pos.x, spawn_pos.y)
        Bullet.bullets.append(new_bullet)


##

while running:
    


    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            running = False

    

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                leftHeld = True
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                rightHeld = True
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                upHeld = True
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                downHeld = True
            
            if event.key == pygame.K_SPACE:    
                plane_size = playerplaneframes[playerplanecurrentframe].get_size()
                center_x = position.x + (plane_size[0] / 2)
                center_y = position.y
                shoot(Vector2(center_x, center_y))
           
            ##
            #if event.key == pygame.K_SPACE:
             #   shoot(self=playerplanecurrentframe, bullet=last_shot)
            ##

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                leftHeld = False
            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                rightHeld = False        
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                upHeld = False
            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                downHeld = False
        
    if leftHeld:
        position.x -= speed*deltaTime
    if rightHeld:
        position.x += speed*deltaTime
    if upHeld:
        position.y -= speed*deltaTime
    if downHeld:
        position.y += speed*deltaTime

    if playerplanelasttick + 1000/24 <= pygame.time.get_ticks():
        playerplanelasttick = pygame.time.get_ticks()
        playerplanecurrentframe += 1
        if playerplanecurrentframe > len(playerplaneframes) -1:
            playerplanecurrentframe = 0



    screen.fill((119, 178, 212))

    for bullet in Bullet.bullets:
        bullet.update(deltaTime)

    screen.blit(playerplaneframes[playerplanecurrentframe], position)
    
    pygame.display.flip()

    fps = 0 # 0: no limit
    deltaTime = clock.tick(fps) /1000
    deltaTime = max(0.001, min(0.1, deltaTime))

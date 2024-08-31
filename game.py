import pygame
import random
import math

pygame.init()

# set screen size
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("pygame test")

game = None

gamemodeTitle = "title"
gamemodePlay = "game"
gamemodeScore = "score"

gamemode = gamemodeTitle


tick = 0

def title():
    global tick
    tick += 1

    pygame.draw.rect(SCREEN, (0, 0, 0), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    # draw "pyvampiresurvival" text
    font = pygame.font.Font(None, 74)
    text = font.render("PyVampireSurvival", True, (255, 255, 255))
    text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    SCREEN.blit(text, text_rect)

    # draw "press space to start" text
    font = pygame.font.Font(None, 42)
    text = font.render("Press space to start", True, (255, 255, 255))
    text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 100))
    SCREEN.blit(text, text_rect)

    pygame.draw.rect(SCREEN, (255, 255, 255), (tick, tick, 10, 10))

    if pygame.key.get_pressed()[pygame.K_SPACE]:
        startGame()
    return

class Particle:
    def __init__(self, x, y, xx, yy, color, life):
        self.x = x
        self.y = y
        self.xx = xx
        self.yy = yy
        self.color = color
        self.life = life

    def draw(self, scrollX, scrollY):
        pygame.draw.circle(SCREEN, self.color, (self.x - scrollX, self.y - scrollY), 2)

    def loop(self):
        self.x += self.xx
        self.y += self.yy
        self.xx *= 0.9
        self.yy *= 0.9
        self.life -= 1
        return self.life <= 0


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = 1000
        self.speed = 8
        self.score = 0
        self.level = 1
        self.expereince = 0

    def addExp(self, exp):
        self.expereince += exp
        if self.expereince >= self.level * 100:
            self.expereince -= self.level * 100
            self.level += 1
            self.hp = 1000

    def draw(self):
        # draw player to center of screen
        pygame.draw.circle(SCREEN, (255, 0, 0), (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2), 20)

        # draw hp bar
        pygame.draw.rect(SCREEN, (255, 0, 0), (SCREEN_WIDTH / 2 - 50, SCREEN_HEIGHT / 2 - 50, 100, 10))
        pygame.draw.rect(SCREEN, (0, 255, 0), (SCREEN_WIDTH / 2 - 50, SCREEN_HEIGHT / 2 - 50, self.hp / 10, 10))

        # draw score
        font = pygame.font.Font(None, 42)
        text = font.render("Score: " + str(self.score), True, (255, 255, 255))
        text_rect = text.get_rect(center=(200, 100))
        SCREEN.blit(text, text_rect)

        # draw level and exp
        text = font.render("Level: %d  Exp: %d " % (self.level, self.expereince), True, (255, 255, 255))
        text_rect = text.get_rect(center=(200, 150))
        SCREEN.blit(text, text_rect)



    def loop(self):
        pressed = pygame.key.get_pressed()
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            self.x -= self.speed
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            self.x += self.speed
        if pygame.key.get_pressed()[pygame.K_UP]:
            self.y -= self.speed
        if pygame.key.get_pressed()[pygame.K_DOWN]:
            self.y += self.speed

class Bullet:
    def __init__(self, x, y, xx, yy, size, color, damage, life):
        self.x = x
        self.y = y
        self.xx = xx
        self.yy = yy
        self.size = size
        self.color = color
        self.damage = damage
        self.life = life

    def draw(self, scrollX, scrollY):
        pygame.draw.circle(SCREEN, self.color, (self.x - scrollX, self.y - scrollY), self.size)

    def loop(self, scrollX, scrollY):
        self.x += self.xx
        self.y += self.yy

        for enemy in game.enemies:
            if self.x < enemy.x + enemy.enemyInfo.size and self.x > enemy.x - enemy.enemyInfo.size and self.y < enemy.y + enemy.enemyInfo.size and self.y > enemy.y - enemy.enemyInfo.size:
                enemy.hp -= self.damage
                game.addHitParticle(enemy.x, enemy.y, 5, 5)
                game.player.score += 1
                self.life -= 1
                if self.life <= 0:
                    return True
                break
        return self.x < scrollX or self.x > scrollX + SCREEN_WIDTH or self.y < scrollY or self.y > scrollY + SCREEN_HEIGHT

class Item:
    def __init__(self, x, y, idx):
        self.x = x
        self.y = y
        idx = idx % 4
        self.idx = idx
        self.life = 300
        if idx == 0:
            self.color = (32, 32, 32)
        elif idx == 1:
            self.color = (128, 64, 64)
        elif idx == 2:
            self.color = (64, 128, 96)
        elif idx == 3:
            self.color = (96, 96, 128)

    def draw(self, scrollX, scrollY):
        # draw diamond
        twinkle = (self.life % 5)+1
        color = [min(255, c*twinkle / 4) for c in self.color]
        if self.life < 30 and self.life % 2 == 0:
            color = (255, 255 ,255)
        pygame.draw.polygon(SCREEN, color, [(self.x - scrollX, self.y - scrollY - 10), (self.x - scrollX + 10, self.y - scrollY), (self.x - scrollX, self.y - scrollY + 10), (self.x - scrollX - 10, self.y - scrollY)])

    def loop(self, player):
        size = 30
        if self.x < player.x + size and self.x > player.x - size and self.y < player.y + size and self.y > player.y - size:
            player.addExp((self.idx+2) * 5)
            return True
        self.life -= 1
        return self.life <= 0

class EnemyInfo:
    def __init__(self, hp, size, speed, damage, idx):
        self.hp = hp
        self.size = size
        self.speed = speed
        self.damage = damage
        self.idx = idx
        self.color = (((idx%2)*64+127) % 256, ((idx%4)*32+95) % 256, ((idx%8)*16+127) % 256)

class Enemy:
    def __init__(self, x, y, enemyInfo):
        self.x = x
        self.y = y
        self.xx = 0
        self.yy = 0
        self.enemyInfo = enemyInfo
        self.hp = enemyInfo.hp

    def draw(self, scrollX, scrollY):
        pygame.draw.circle(SCREEN, self.enemyInfo.color, (self.x - scrollX, self.y - scrollY), self.enemyInfo.size)
        if self.hp < self.enemyInfo.hp:
            pygame.draw.rect(SCREEN, (255, 0, 0), (self.x - scrollX - self.enemyInfo.size, self.y - scrollY - self.enemyInfo.size - 10, self.enemyInfo.size * 2, 5))
            pygame.draw.rect(SCREEN, (0, 255, 0), (self.x - scrollX - self.enemyInfo.size, self.y - scrollY - self.enemyInfo.size - 10, self.hp / self.enemyInfo.hp * self.enemyInfo.size * 2, 5))

    def loop(self, player):
        speed = self.enemyInfo.speed
        if self.xx == 0 and self.yy == 0:
            if self.x < player.x:
                self.x += speed
            if self.x > player.x:
                self.x -= speed
            if self.y < player.y:
                self.y += speed
            if self.y > player.y:
                self.y -= speed
        else:
            self.x += self.xx
            self.y += self.yy
            self.xx *= 0.8
            self.yy *= 0.8
            length = (self.xx**2 + self.yy**2)**0.5
            if length < 0.1:
                self.xx = 0
                self.yy = 0

        
        damage = self.enemyInfo.damage
        size = self.enemyInfo.size
        if self.x < player.x + size and self.x > player.x - size and self.y < player.y + size and self.y > player.y - size:
            player.hp -= damage
            self.crash(player.x, player.y)
            game.addHitParticle(player.x, player.y, 10, 10)
        return
    
    # 부딪히면, 내가 상대방의 역방향으로 이동
    def crash(self, x, y):
        speed = self.enemyInfo.speed
        xx = self.x - x
        yy = self.y - y
        if xx == 0 and yy == 0:
            xx = speed
        length = (xx**2 + yy**2)**0.5
        xx *= speed * 5 / length
        yy *= speed * 5 / length
        self.xx = xx
        self.yy = yy


class Background:
    def __init__(self):
        self.grace = []
        self.graceColor = (128, 192, 128)
        for i in range(100):
            self.grace.append((random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)))

    def draw(self, scrollX, scrollY):
        pygame.draw.rect(SCREEN, (64, 128, 64), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        for grace in self.grace:
            graceX = (grace[0] - scrollX) % SCREEN_WIDTH
            graceY = (grace[1] - scrollY) % SCREEN_HEIGHT
            pygame.draw.circle(SCREEN, self.graceColor , (graceX, graceY), 2)


class Game:
    def __init__(self):
        self.player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.background = Background()
        self.enemies = []
        self.clock = 0
        self.enemyInfo = EnemyInfo(100, 20, 1, 10, 0)
        self.enemyMax = 10
        self.particles = []
        self.bullets = []
        self.items = []

    def addBullet(self, x, y, xx, yy, size, color, damage, life):
        self.bullets.append(Bullet(x, y, xx, yy, size, color, damage, life))

    def addHitParticle(self, x, y, count, scale):
        for i in range(count):
            angle = random.random() * 2 * 3.141592
            speed = random.random() * scale+1
            self.addParticle(x, y, math.cos(angle) * speed, math.sin(angle) * speed, (255, 128, 128), 10)

    def addParticle(self, x, y, xx, yy, color, life):
        self.particles.append(Particle(x, y, xx, yy, color, life))

    def addItem(self, x, y, idx):
        self.items.append(Item(x, y, idx))

    def draw(self):
        scrollX = self.player.x - SCREEN_WIDTH / 2
        scrollY = self.player.y - SCREEN_HEIGHT / 2
        self.background.draw(scrollX, scrollY)
        self.player.draw()
        for enemy in self.enemies:
            enemy.draw(scrollX, scrollY)
        for particle in self.particles:
            particle.draw(scrollX, scrollY)
        for bullet in self.bullets:
            bullet.draw(scrollX, scrollY)
        for item in self.items:
            item.draw(scrollX, scrollY)

    def fineNearestEnemy(self, x, y):
        nearest = None
        distance = 999999
        for enemy in self.enemies:
            d = (enemy.x - x)**2 + (enemy.y - y)**2
            if d < distance:
                distance = d
                nearest = enemy
        return nearest

    def loop(self):
        self.clock += 1

        self.player.loop()

        scrollX = self.player.x - SCREEN_WIDTH / 2
        scrollY = self.player.y - SCREEN_HEIGHT / 2

        enemyCreationRate = 30
        if self.clock > 1500:
            enemyCreationRate = 20
            self.enemyInfo = EnemyInfo(200, 30, 2, 20, 1)
            self.enemyMax = 30
        if self.clock > 4000:
            enemyCreationRate = 2
            self.enemyInfo = EnemyInfo(100, 20, 1, 40, 0)
            self.enemyMax = 200
        if self.clock > 9000:
            enemyCreationRate = 15
            self.enemyInfo = EnemyInfo(800, 40, 4, 30, 2)
            self.enemyMax = 10
        if self.clock > 20000:
            enemyCreationRate = 5
            self.enemyInfo = EnemyInfo(1500, 20, 4, 50, 2)
            self.enemyMax = 30
        if self.clock > 40000:
            enemyCreationRate = 3
            self.enemyInfo = EnemyInfo(2000, 10, 2, 60, 2)
            self.enemyMax = 50


        enemyCount = len(self.enemies)

        if self.clock % enemyCreationRate == 0 and enemyCount < self.enemyMax:
            # make enemy
            direction = random.randint(0, 3)
            if direction == 0: # top 
                self.enemies.append(Enemy(random.randint(0, SCREEN_WIDTH)+scrollX, -100+scrollY, self.enemyInfo))
            elif direction == 1: # right
                self.enemies.append(Enemy(SCREEN_WIDTH+100+scrollX, random.randint(0, SCREEN_HEIGHT)+scrollY, self.enemyInfo))
            elif direction == 2: # bottom
                self.enemies.append(Enemy(random.randint(0, SCREEN_WIDTH)+scrollX, SCREEN_HEIGHT+100+scrollY, self.enemyInfo))
            elif direction == 3: # left
                self.enemies.append(Enemy(-100+scrollX, random.randint(0, SCREEN_HEIGHT)+scrollY, self.enemyInfo))

        if self.clock % 15 == 0:
            # make bullet
            nearest = self.fineNearestEnemy(self.player.x, self.player.y)
            if nearest is not None:
                angle = math.atan2(nearest.y - self.player.y, nearest.x - self.player.x)
                speed = 10
                damage = 30 + int(self.player.level) * 10
                life = 1 + int(self.player.level / 3) * 2
                self.addBullet(self.player.x, self.player.y, math.cos(angle) * speed, math.sin(angle) * speed, 5, (255, 255, 255), damage, life)

        for enemy in self.enemies:
            enemy.loop(self.player)
            if enemy.hp <= 0:
                self.enemies.remove(enemy)
                self.addHitParticle(enemy.x, enemy.y, 50, 20)
                self.player.score += 10
                self.addItem(enemy.x, enemy.y, enemy.enemyInfo.idx)
            # crash
            for subEnemy in self.enemies:
                if enemy != subEnemy:
                    if enemy.x < subEnemy.x + subEnemy.enemyInfo.size and enemy.x > subEnemy.x - subEnemy.enemyInfo.size and enemy.y < subEnemy.y + subEnemy.enemyInfo.size and enemy.y > subEnemy.y - subEnemy.enemyInfo.size:
                        enemy.crash(subEnemy.x, subEnemy.y)

        for bullet in self.bullets:
            if bullet.loop(scrollX, scrollY):
                self.bullets.remove(bullet)

        for particle in self.particles:
            if particle.loop():
                self.particles.remove(particle)

        for item in self.items:
            if item.loop(self.player):
                self.items.remove(item)

        if self.player.hp <= 0:
            global gamemode
            gamemode = gamemodeScore
        return

def startGame():
    global gamemode, game
    gamemode = gamemodePlay
    game = Game()

def play():
    game.draw()
    game.loop()
    return

def score():
    game.draw()
    score = game.player.score
    font = pygame.font.Font(None, 74)
    text = font.render("Score: " + str(score), True, (255, 255, 255))
    text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
    SCREEN.blit(text, text_rect)

    font = pygame.font.Font(None, 42)
    text = font.render("Press return to restart", True, (255, 255, 255))
    text_rect = text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 100))
    SCREEN.blit(text, text_rect)

    if pygame.key.get_pressed()[pygame.K_RETURN]:
        global gamemode
        gamemode = gamemodeTitle
    return





if __name__ == "__main__":
    running = True

    clock = pygame.time.Clock()
    fps = 30
    while running:
        clock.tick(fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if gamemode == gamemodeTitle:
            title()
        elif gamemode == gamemodePlay:
            play()
        elif gamemode == gamemodeScore:
            score()
        else:
            print("Error: Unknown gamemode")
            break
        pygame.display.flip()

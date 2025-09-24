import pygame
import asyncio
import platform
import sys
import math
import random  # Moved to top since it's used in multiple places

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Super Mario World Clone - 5 World Campaign")

# Colors
WHITE = (255, 255, 255)
BLUE = (100, 150, 255)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
LAVA_RED = (255, 69, 0)

# Game states
STATE_OVERWORLD = "overworld"
STATE_LEVEL = "level"
STATE_BOSS = "boss"
game_state = STATE_OVERWORLD
current_level = None
current_world = 1

# Player settings
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 60
player_x = 50
player_y = SCREEN_HEIGHT - PLAYER_HEIGHT - 10
player_speed = 5
player_jump = -15
player_gravity = 0.8
player_velocity_y = 0
is_jumping = False
player_health = 3
player_lives = 3
player_score = 0

# Platform settings
def get_platforms_for_level(world, level):
    """Return platforms based on world and level"""
    base_ground = pygame.Rect(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
    if world == 1:  # Grasslands
        if level == 1:
            return [base_ground, pygame.Rect(200, 400, 200, 20), pygame.Rect(500, 300, 200, 20)]
        elif level == 2:
            return [base_ground, pygame.Rect(150, 450, 150, 20), pygame.Rect(350, 350, 150, 20), pygame.Rect(550, 250, 150, 20)]
        elif level == 3:
            return [base_ground, pygame.Rect(100, 400, 100, 20), pygame.Rect(300, 400, 100, 20), pygame.Rect(500, 400, 100, 20)]
        else:  # Boss arena
            return [base_ground, pygame.Rect(100, 300, 600, 20)]
    elif world == 2:  # Desert
        if level == 1:
            return [base_ground, pygame.Rect(250, 400, 150, 20), pygame.Rect(550, 350, 150, 20)]
        elif level == 2:
            return [base_ground, pygame.Rect(150, 450, 150, 20), pygame.Rect(400, 350, 150, 20)]
        elif level == 3:
            return [base_ground, pygame.Rect(100, 400, 100, 20), pygame.Rect(300, 300, 100, 20), pygame.Rect(500, 200, 100, 20)]
        else:  # Boss arena
            return [base_ground, pygame.Rect(100, 300, 600, 20)]
    elif world == 3:  # Forest - Vertical
        return [base_ground] + [pygame.Rect(200 + i*100, 500 - i*100, 100, 20) for i in range(level)]
    elif world == 4:  # Castle - With lava
        lava = pygame.Rect(0, SCREEN_HEIGHT - 60, SCREEN_WIDTH, 20)
        return [base_ground, lava] + [pygame.Rect(100 * level, 400 - level*50, 200, 20)]
    elif world == 5:  # Sky - Floating
        return [pygame.Rect(100 * i, 200 + i*50, 150, 20) for i in range(5)]
    else:  # Final boss arena
        return [base_ground, pygame.Rect(300, 400, 200, 20), pygame.Rect(100, 200, 600, 20)]

platforms = []

# Enemies and Power-ups
class Enemy:
    def __init__(self, x, y, platform):
        self.rect = pygame.Rect(x, y - 20, 30, 30)
        self.speed = 2
        self.direction = 1
        self.platform = platform

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.right > self.platform.right or self.rect.left < self.platform.left:
            self.direction *= -1

    def draw(self):
        pygame.draw.circle(screen, RED, self.rect.center, 15)

enemies = []

class PowerUp:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)

    def draw(self):
        pygame.draw.rect(screen, YELLOW, self.rect)

    def collect(self):
        global player_health
        player_health = min(3, player_health + 1)
        return True

power_ups = []

# Boss Classes
class KamekBoss:
    def __init__(self, world):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2, 100, 50, 70)
        self.health = 4 + world
        self.speed = 3
        self.direction = 1
        self.shoot_timer = 0
        self.teleport_timer = 0
        self.projectiles = []

    def update(self):
        # Fly in sine wave
        self.rect.x += self.speed * self.direction
        self.rect.y += math.sin(self.rect.x / 20) * 2
        if self.rect.right > SCREEN_WIDTH or self.rect.left < 0:
            self.direction *= -1

        # Shoot projectiles
        self.shoot_timer += 1
        if self.shoot_timer > 60:
            self.projectiles.append(pygame.Rect(self.rect.centerx, self.rect.bottom, 10, 10))
            self.shoot_timer = 0

        # Teleport
        self.teleport_timer += 1
        if self.teleport_timer > 300:
            self.rect.x = random.randint(0, SCREEN_WIDTH - 50)
            self.rect.y = random.randint(50, 200)
            self.teleport_timer = 0

        # Update projectiles
        for proj in self.projectiles[:]:
            proj.y += 5
            if proj.y > SCREEN_HEIGHT:
                self.projectiles.remove(proj)

    def take_damage(self):
        self.health -= 1
        return self.health <= 0

    def draw(self):
        pygame.draw.polygon(screen, BLUE, [(self.rect.left, self.rect.bottom), (self.rect.centerx, self.rect.top), (self.rect.right, self.rect.bottom)])
        for proj in self.projectiles:
            pygame.draw.rect(screen, GREEN, proj)

class BabyBowserBoss:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, 60, 80)
        self.health = 10
        self.phase = 1
        self.attack_timer = 0
        self.projectiles = []
        self.shockwaves = []

    def update(self):
        self.attack_timer += 1
        if self.phase == 1:  # Ground pound
            if self.attack_timer > 120:
                self.shockwaves.append(pygame.Rect(self.rect.centerx - 50, self.rect.bottom, 100, 10))
                self.attack_timer = 0
        elif self.phase == 2:  # Fire breath
            if self.attack_timer > 90:
                self.projectiles.append(pygame.Rect(self.rect.right, self.rect.centery, 20, 10))
                self.attack_timer = 0
        elif self.phase == 3:  # Flying homing
            self.rect.y -= 1
            if self.attack_timer > 60:
                self.projectiles.append(pygame.Rect(self.rect.centerx, self.rect.bottom, 10, 10))
                self.attack_timer = 0

        # Phase transition
        if self.health <= 7 and self.phase == 1:
            self.phase = 2
            self.rect.inflate_ip(20, 20)
        elif self.health <= 3 and self.phase == 2:
            self.phase = 3
            self.rect.y = 100

        # Update attacks
        for wave in self.shockwaves[:]:
            wave.inflate_ip(10, 0)
            if wave.width > SCREEN_WIDTH:
                self.shockwaves.remove(wave)
        for proj in self.projectiles[:]:
            proj.x -= 5
            if proj.x < 0:
                self.projectiles.remove(proj)

    def take_damage(self):
        self.health -= 1
        return self.health <= 0

    def draw(self):
        pygame.draw.rect(screen, RED, self.rect)
        pygame.draw.circle(screen, BLACK, (self.rect.right - 10, self.rect.top + 20), 10)
        for wave in self.shockwaves:
            pygame.draw.rect(screen, YELLOW, wave)
        for proj in self.projectiles:
            pygame.draw.rect(screen, LAVA_RED, proj)

boss = None

# Level exit
level_exit = pygame.Rect(SCREEN_WIDTH - 60, SCREEN_HEIGHT - 100, 50, 60)

# Overworld settings
OVERWORLD_PLAYER_SIZE = 20
overworld_player_pos = [100, 100]
overworld_player_speed = 5
overworld_nodes = []

# Generate nodes for 5 worlds
node_id = 0
for world in range(1, 6):
    for level in range(1, 5):
        x = 100 + (node_id % 4) * 150
        y = 100 + (node_id // 4) * 150
        level_name = f"world_{world}_level_{level}"
        overworld_nodes.append({"id": node_id, "pos": (x, y), "level": level_name, "completed": False, "world": world, "is_boss": level == 4})
        node_id += 1

# Final boss node
overworld_nodes.append({"id": node_id, "pos": (600, 600), "level": "final_boss", "completed": False, "world": 6, "is_boss": True})

overworld_paths = []
for i in range(len(overworld_nodes) - 1):
    if overworld_nodes[i]["world"] == overworld_nodes[i+1]["world"]:
        overworld_paths.append((i, i+1))
overworld_paths.append((19, 20))

current_node = 0
target_node = None
move_progress = 0

# Font for text
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# Game loop variables
clock = pygame.time.Clock()
FPS = 60
running = True

# Victory/Defeat screens
def draw_victory():
    screen.fill(GREEN)
    text = font.render("Level Complete!", True, WHITE)
    screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
    pygame.display.flip()

def draw_game_over():
    screen.fill(RED)
    text = font.render("Game Over", True, WHITE)
    screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
    pygame.display.flip()

def draw_hud():
    # Health hearts
    for i in range(player_health):
        pygame.draw.circle(screen, RED, (30 + i*40, 30), 15)
    # Score
    score_text = small_font.render(f"Score: {player_score}", True, WHITE)
    screen.blit(score_text, (10, 60))
    # Lives
    lives_text = small_font.render(f"Lives: {player_lives}", True, WHITE)
    screen.blit(lives_text, (10, 90))

def draw_overworld():
    screen.fill(BLUE)
    
    # Draw paths
    for start_id, end_id in overworld_paths:
        if overworld_nodes[start_id]["completed"] or start_id == current_node:
            start_pos = overworld_nodes[start_id]["pos"]
            end_pos = overworld_nodes[end_id]["pos"]
            pygame.draw.line(screen, WHITE, start_pos, end_pos, 5)
    
    # Draw nodes
    for node in overworld_nodes:
        color = GREEN if node["completed"] else RED if node["is_boss"] else GRAY
        pygame.draw.circle(screen, color, node["pos"], 30)
        pygame.draw.circle(screen, WHITE, node["pos"], 30, 3)
        level_text = small_font.render(f"W{node['world']}-L{node['id'] % 4 + 1 if not node['is_boss'] else 'Boss'}", True, WHITE)
        screen.blit(level_text, (node["pos"][0] - 20, node["pos"][1] - 10))
    
    # Draw player
    pygame.draw.circle(screen, YELLOW, (int(overworld_player_pos[0]), int(overworld_player_pos[1])), OVERWORLD_PLAYER_SIZE)
    
    # Instructions
    instructions = small_font.render("Arrow Keys: Move | Enter: Select | ESC: Quit", True, WHITE)
    screen.blit(instructions, (10, 10))
    
    # Current world
    world_text = small_font.render(f"World {current_world}", True, WHITE)
    screen.blit(world_text, (10, 40))

def draw_level():
    screen.fill(BLUE if current_world < 4 else GRAY if current_world == 4 else WHITE)
    
    # Draw platforms
    for platform in platforms:
        color = BROWN if current_world != 4 else LAVA_RED if platform.y > SCREEN_HEIGHT - 60 else GRAY
        pygame.draw.rect(screen, color, platform)
    
    # Draw enemies
    for enemy in enemies:
        enemy.draw()
    
    # Draw power-ups
    for pu in power_ups:
        pu.draw()
    
    # Draw exit
    if not overworld_nodes[current_node]["is_boss"]:
        pygame.draw.rect(screen, GREEN, level_exit)
        exit_text = small_font.render("EXIT", True, WHITE)
        screen.blit(exit_text, (level_exit.centerx - 20, level_exit.centery - 10))
    
    # Draw player
    pygame.draw.rect(screen, RED, (player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT))
    
    # Level name
    level_text = font.render(f"World {current_world} - Level {current_node % 4 + 1}", True, WHITE)
    screen.blit(level_text, (10, 10))
    
    # Instructions
    instructions = small_font.render("Arrows: Move | Space: Jump | ESC: Map", True, WHITE)
    screen.blit(instructions, (10, 50))
    
    draw_hud()

def draw_boss():
    draw_level()
    boss.draw()
    # Boss health bar
    pygame.draw.rect(screen, RED, (SCREEN_WIDTH // 2 - 100, 20, 200, 20))
    health_width = (boss.health / (9 if isinstance(boss, KamekBoss) else 10)) * 200
    pygame.draw.rect(screen, GREEN, (SCREEN_WIDTH // 2 - 100, 20, health_width, 20))

def handle_overworld_input(keys):
    global current_node, target_node, move_progress, game_state, current_level, platforms, player_x, player_y, player_velocity_y, current_world, boss, enemies, power_ups
    
    if target_node is None:
        connected_nodes = [end for start, end in overworld_paths if start == current_node] + [start for start, end in overworld_paths if end == current_node]
        
        if keys[pygame.K_RIGHT]:
            # Find next node to the right
            for node_id in connected_nodes:
                if node_id > current_node:
                    target_node = node_id
                    move_progress = 0
                    break
        
        if keys[pygame.K_RETURN]:
            node = overworld_nodes[current_node]
            current_world = node["world"]
            if node["is_boss"]:
                game_state = STATE_BOSS
                if node["level"] == "final_boss":
                    boss = BabyBowserBoss()
                else:
                    boss = KamekBoss(current_world)
            else:
                game_state = STATE_LEVEL
            current_level = node["level"]
            level_num = current_node % 4 + 1 if current_node < 20 else 4
            platforms = get_platforms_for_level(current_world, level_num)
            
            # Reset player position
            player_x = 50
            player_y = SCREEN_HEIGHT - PLAYER_HEIGHT - 50
            player_velocity_y = 0
            
            # Spawn enemies and power-ups
            enemies.clear()
            power_ups.clear()
            if len(platforms) > 1:
                for i in range(min(current_world + level_num, 5)):
                    enemies.append(Enemy(200 + i*100, platforms[1].top, platforms[1]))
                power_ups.append(PowerUp(400, 300))

    if target_node is not None:
        move_progress += 0.02
        if move_progress >= 1:
            current_node = target_node
            overworld_player_pos[0], overworld_player_pos[1] = overworld_nodes[current_node]["pos"]
            target_node = None
        else:
            start = overworld_nodes[current_node]["pos"]
            end = overworld_nodes[target_node]["pos"]
            overworld_player_pos[0] = start[0] + (end[0] - start[0]) * move_progress
            overworld_player_pos[1] = start[1] + (end[1] - start[1]) * move_progress

def handle_level_input(keys):
    global player_x, player_y, player_velocity_y, is_jumping, game_state
    
    if keys[pygame.K_LEFT]:
        player_x -= player_speed
        player_x = max(0, player_x)
    if keys[pygame.K_RIGHT]:
        player_x += player_speed
        player_x = min(SCREEN_WIDTH - PLAYER_WIDTH, player_x)
    if keys[pygame.K_SPACE] and not is_jumping:
        player_velocity_y = player_jump
        is_jumping = True
    if keys[pygame.K_ESCAPE]:
        game_state = STATE_OVERWORLD

def update_physics():
    global player_y, player_velocity_y, is_jumping, game_state, player_health, player_lives, player_score
    
    player_velocity_y += player_gravity
    player_y += player_velocity_y
    player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    
    is_jumping = True
    for platform in platforms:
        if player_rect.colliderect(platform) and player_velocity_y > 0 and player_rect.bottom <= platform.top + 10:
            player_y = platform.top - PLAYER_HEIGHT
            player_velocity_y = 0
            is_jumping = False
    
    # Enemy collisions
    for enemy in enemies[:]:
        if player_rect.colliderect(enemy.rect):
            if player_velocity_y > 0 and player_rect.bottom < enemy.rect.centery:
                enemies.remove(enemy)
                player_score += 100
            else:
                player_health -= 1
                if player_health <= 0:
                    player_lives -= 1
                    if player_lives <= 0:
                        game_state = STATE_OVERWORLD
                        draw_game_over()
                        pygame.time.wait(2000)
                    else:
                        player_health = 3
                        player_x, player_y = 50, SCREEN_HEIGHT - PLAYER_HEIGHT - 50
    
    # Power-up collect
    for pu in power_ups[:]:
        if player_rect.colliderect(pu.rect):
            if pu.collect():
                power_ups.remove(pu)
                player_score += 50
    
    # Fall off screen
    if player_y > SCREEN_HEIGHT:
        player_health -= 1
        if player_health <= 0:
            player_lives -= 1
            if player_lives <= 0:
                game_state = STATE_OVERWORLD
                draw_game_over()
                pygame.time.wait(2000)
            else:
                player_health = 3
        player_x, player_y = 50, SCREEN_HEIGHT - PLAYER_HEIGHT - 50
    
    # Exit check
    if not overworld_nodes[current_node]["is_boss"] and player_rect.colliderect(level_exit):
        overworld_nodes[current_node]["completed"] = True
        if (current_node + 1) % 4 == 0:
            current_world += 1
        game_state = STATE_OVERWORLD
        draw_victory()
        pygame.time.wait(1000)

def update_boss():
    global game_state, boss, player_health, player_lives
    
    boss.update()
    player_rect = pygame.Rect(player_x, player_y, PLAYER_WIDTH, PLAYER_HEIGHT)
    
    # Player attacks boss
    if player_rect.colliderect(boss.rect) and player_velocity_y > 0 and player_rect.bottom < boss.rect.centery:
        if boss.take_damage():
            overworld_nodes[current_node]["completed"] = True
            if current_node == 20:
                # Game win
                draw_victory()
                pygame.display.flip()
                pygame.time.wait(3000)
                global running
                running = False
                return
            game_state = STATE_OVERWORLD
            draw_victory()
            pygame.display.flip()
            pygame.time.wait(2000)
        player_velocity_y = player_jump / 2
    
    # Boss attacks player
    for proj in boss.projectiles[:]:
        if player_rect.colliderect(proj):
            player_health -= 1
            boss.projectiles.remove(proj)
    
    if isinstance(boss, BabyBowserBoss):
        for wave in boss.shockwaves[:]:
            if player_rect.colliderect(wave):
                player_health -= 1
                boss.shockwaves.remove(wave)
    
    if player_health <= 0:
        player_lives -= 1
        if player_lives <= 0:
            game_state = STATE_OVERWORLD
            draw_game_over()
            pygame.time.wait(2000)
        else:
            player_health = 3
            player_x, player_y = 50, SCREEN_HEIGHT - PLAYER_HEIGHT - 50

# Main game loop
async def main():
    global running, game_state, boss, overworld_player_pos
    
    # Initialize overworld player position
    overworld_player_pos = list(overworld_nodes[current_node]["pos"])
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and game_state == STATE_OVERWORLD:
                    running = False
        
        keys = pygame.key.get_pressed()
        
        if game_state == STATE_OVERWORLD:
            handle_overworld_input(keys)
            draw_overworld()
        elif game_state == STATE_LEVEL:
            handle_level_input(keys)
            update_physics()
            for enemy in enemies:
                enemy.update()
            draw_level()
        elif game_state == STATE_BOSS:
            handle_level_input(keys)
            update_physics()
            update_boss()
            if running:  # Only draw if game is still running
                draw_boss()
        
        pygame.display.flip()
        clock.tick(FPS)
        await asyncio.sleep(0)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())

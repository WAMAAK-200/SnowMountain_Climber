import pygame
import random



# =========================
# ASSET LOADING
# =========================
def load_sprite(path, scale=None):
    # handles sprite loading
    try:
        sprite = pygame.image.load(path).convert_alpha()
        if scale:
            sprite = pygame.transform.scale(sprite, scale)
        return sprite
    except:
        # Fallback colored rectangle if sprite not found
        print(f"Warning: Could not load {path}")
        surface = pygame.Surface((32, 48))
        surface.fill((255, 100, 100))
        return surface

try:
    # Player sprite
    playersp = load_sprite("player.png", (32, 48))

    # Background
    background = load_sprite("background.png", (800, 600))
    
    # Hazard sprites
    icicle_sprite = load_sprite("icicle.png", (20, 40))
    avalanche_sprite = load_sprite("avalanche.png", (800, 100))
    
    # Platform sprites
    #ice_platform = load_sprite("ice_platform.png", (100, 20))
    #rock_platform = load_sprite("rock_platform.png", (100, 20))
    
except:
    # Fallback colors if sprites not found
    playersp = pygame.Surface((32, 48))

    
    background = pygame.Surface((800, 600))
    background.fill((135, 206, 235))  # Sky blue
    
    icicle_sprite = pygame.Surface((20, 40))
    icicle_sprite.fill((200, 230, 255))

    avalanche_sprite = pygame.Surface((800, 100))
    avalanche_sprite.fill((255, 255, 255))
    


# =========================
# PLAYER CLASS
# =========================

class Player:
    # Movement & physics
    # position, velocity, acceleration
    # jump_force, gravity, climb_speed
    # is_grounded, is_climbing, is_sliding
    
    # States & abilities
    # stamina (for climbing/endurance)

    
    # Visuals
    # animation states (climbing, walking, slipping)
    # sprite management

    def __init__(self,playersp):
        # Physics
        self.position = pygame.math.Vector2(100, 540)
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = pygame.math.Vector2(0, 0)

        self.gravity = 2000
        self.jump_force = -600
        self.climb_speed = 250

        self.is_grounded = False
        self.is_climbing = False
        self.is_sliding = False
        self.move_speed = 400

        self.sprite = playersp

        self.rect = playersp.get_rect(topleft=self.position)


        # Health

        self.health = 100
        self.invinc_timer = 0
        self.invinc_dur = 0.5

    def damage(self, amount):
        if self.invinc_timer <= 0:
            self.health -= amount
            self.invinc_timer = self.invinc_dur
            return True
        return False
    
    def update(self, dt):
        if self.invinc_timer > 0:
            self.invinc_timer -= dt
# =========================
# GRAVITY SYSTEM
# =========================

def setup_player_gravity(player):
    """
    Call this once after creating the player to initialise gravity-related stuff.
    You can tweak the values to taste.
    """

    # Core gravity tuning
    player.gravity = getattr(player, "gravity", 2000.0)  # px/s^2
    player.max_fall_speed = 1400.0                       # terminal velocity

    # Variable jump height
    player.fall_gravity_multiplier = 1.4   # stronger gravity when falling
    player.low_jump_multiplier = 2.2       # stronger gravity when jump is released early

    # Coyote time (jump a tiny bit after stepping off a ledge)
    player.coyote_time = 0.12              # seconds
    player.time_since_left_ground = 0.0

    # Jump buffering (jump a tiny bit before landing)
    player.jump_buffer_time = 0.12         # seconds
    player.time_since_jump_pressed = 999.0 # large initial value

    # Landing / bounce
    player.was_grounded_last_frame = getattr(player, "is_grounded", False)
    player.landing_speed_threshold = 350.0
    player.small_bounce_factor = 0.18      # 0 = no bounce, 0.2 = gentle hop


def apply_gravity(player, delta_time, jump_pressed=False, jump_held=False, wind_x=0.0):
    """
    Advanced gravity for a platformer.

    player needs:
      position, velocity, acceleration (Vector2)
      gravity, is_grounded, is_climbing, is_sliding
      and the fields created in setup_player_gravity()

    delta_time: frame time in seconds
    """

    dt = delta_time

    # --- Update timers for coyote time & jump buffer ---
    if player.is_grounded:
        player.time_since_left_ground = 0.0
    else:
        player.time_since_left_ground += dt

    if jump_pressed:
        player.time_since_jump_pressed = 0.0
    else:
        player.time_since_jump_pressed += dt

    # --- Check if we should start a jump here (coyote + buffer) ---
    can_coyote = player.time_since_left_ground <= player.coyote_time
    buffered_jump = player.time_since_jump_pressed <= player.jump_buffer_time

    # Only start a new jump if we have a buffered jump
    # and are grounded or within coyote window
    if buffered_jump and (player.is_grounded or can_coyote) and not player.is_climbing:
        # Start jump
        player.velocity.y = player.jump_force
        player.is_grounded = False
        player.time_since_left_ground = player.coyote_time + 1.0  # kill coyote
        player.time_since_jump_pressed = player.jump_buffer_time + 1.0

    # --- Vertical acceleration: gravity vs climbing ---
    if player.is_climbing:
        # Climbing logic can override vertical motion; no gravity here
        player.acceleration.y = 0.0
    else:
        # Apply gravity; modify depending on state for nice platformer feel
        gravity = player.gravity

        if player.velocity.y > 0:  # falling
            gravity *= player.fall_gravity_multiplier
        elif player.velocity.y < 0 and not jump_held:
            # Going up but jump key released early -> low jump
            gravity *= player.low_jump_multiplier

        player.acceleration.y = gravity

    # --- Horizontal "gravity" from wind (optional) ---
    player.acceleration.x = 0.0
    if (not player.is_grounded) or player.is_sliding:
        player.acceleration.x += wind_x

    # --- Integrate acceleration -> velocity ---
    player.velocity.x += player.acceleration.x * dt
    player.velocity.y += player.acceleration.y * dt

    # Clamp fall speed
    if player.velocity.y > player.max_fall_speed:
        player.velocity.y = player.max_fall_speed

    # --- Integrate velocity -> position ---
    player.position += player.velocity * dt

    # Keep rect in sync
    if hasattr(player, "rect"):
        player.rect.topleft = (player.position.x, player.position.y)

    # --- Small bounce on landing ---
    just_landed = (not player.was_grounded_last_frame) and player.is_grounded

    if just_landed and not player.is_climbing:
        impact_speed = abs(player.velocity.y)
        if impact_speed > player.landing_speed_threshold:
            # Gentle bounce
            player.velocity.y = -player.velocity.y * player.small_bounce_factor
        else:
            # Low impact, just stop vertical motion
            player.velocity.y = 0.0

    player.was_grounded_last_frame = player.is_grounded


# =========================
# EMPTY CLASSES (partner)
# =========================

class Platform:
    # Standard platforms
    # rect/collision shape
    # surface_type (ice, rock, snow)
    # slipperiness_factor
    def __init__(self,x,y,width,height,surface):
        self.rect = pygame.Rect(x,y,width,height)
        self.surface = surface
        self.slip = 0

        if surface == "ice":
            self.slip = 0.2
            self.color = (100, 220, 255)
        else:
            self.slip = 0.8
            self.color = (100,100,100)

    def draw(self, screen):
        # Draw the platform
        pygame.draw.rect(screen, self.color, self.rect)


class Hazard:
    # Falling icicles, avalanches, crevasses
    # activation_zone
    # damage_value
    
    def __init__(self,x,y,obst_type="icicle"):
        self.obst_type = obst_type
        self.damage = 0
        self.active = True
        
        if self.obst_type == "icicle":
            self.damage = 10
            self.sprite = icicle_sprite
            self.fallsp = random.randint(300,500)
            self.rect = pygame.Rect(x, y, 20, 40)  # Add rect for collision
        elif self.obst_type == "avalanche":
            self.damage = 999
            self.sprite = avalanche_sprite
            self.fallsp = 200
            self.rect = pygame.Rect(x, y, 800, 100)  # Full width avalanche
        else:
            self.damage = 15
            self.sprite = icicle_sprite  # Fallback
            self.fallsp = random.randint(300,500)
            self.rect = pygame.Rect(x, y, 30, 30)
    
    def update(self, dt):
        # Update hazard position
        if self.obst_type in ["icicle", "rock"] and self.active:
            self.rect.y += self.fallsp * dt
            
            # Deactivate if off screen
            if self.rect.top > 600:
                self.active = False
                
        elif self.obst_type == "avalanche" and self.active:
            self.rect.y += self.fallsp * dt
    
    def draw(self, screen):
        if self.active:
            screen.blit(self.sprite, self.rect)


class HazardManager:
    # Manages spawning and updating hazards
    # Handles avalanche timer and warnings
    
    def __init__(self):
        self.hazards = []
        self.spawn_timer = 0
        self.spawn_interval = 2.0  # seconds between spawns
        self.avalanche_timer = 60.0  # 60 seconds until avalanche
        self.avalanche_active = False
        self.avalanche_warning = False
        self.warning_flash = 0
    
    def update(self, dt, player_x):
        # Update spawn timer
        self.spawn_timer += dt
        
        # Spawn random hazards if timer reached
        if self.spawn_timer >= self.spawn_interval and not self.avalanche_active:
            self.spawn_timer = 0
            self.spawn_hazard(player_x)
        
        # Update avalanche timer
        self.avalanche_timer -= dt
        
        # Check for avalanche warning
        if not self.avalanche_warning and self.avalanche_timer <= 10:
            self.avalanche_warning = True
        
        # Activate avalanche if timer reaches 0
        if self.avalanche_timer <= 0 and not self.avalanche_active:
            self.act_avalanche()
        
        # Update all hazards
        for hazard in self.hazards[:]:  # Copy list for safe removal
            hazard.update(dt)
            if not hazard.active:
                self.hazards.remove(hazard)

    def spawn_hazard(self, player_x):
        """Spawn a random hazard above the player"""
        hazard_type = random.choice(["icicle", "rock"])
        spawn_x = player_x + random.randint(-100, 100)
        spawn_x = max(0, min(spawn_x, 780))  # Keep on screen
        
        new_hazard = Hazard(spawn_x, -50, hazard_type)
        self.hazards.append(new_hazard)

    def act_avalanche(self):
        """Time's up! Time for the avalanche to kill you!"""
        if not self.avalanche_active:
            self.avalanche_active = True
            avalanche = Hazard(0, -100, "avalanche")
            avalanche.active = True
            self.hazards.append(avalanche)
            print("Tick Tock, an avalanche is coming")

    def check_collisions(self, player):
        """Check collisions between player and all hazards"""
        for hazard in self.hazards:
            if hazard.active and player.rect.colliderect(hazard.rect):
                # Damage player if not invincible
                if player.damage(hazard.damage):
                    print(f"Hit by {hazard.obst_type}! Health: {player.health}")
                    
                    # Remove small hazards on hit
                    if hazard.obst_type in ["icicle", "rock"]:
                        hazard.active = False
                
                # Avalanche is instant death
                if hazard.obst_type == "avalanche":
                    return True
        
        return False

    def draw(self, screen):
        """Draw all hazards"""
        for hazard in self.hazards:
            hazard.draw(screen)
        
        # Draw avalanche warning
        if self.avalanche_warning and not self.avalanche_active:
            # Flashing warning
            if int(pygame.time.get_ticks() / 500) % 2 == 0:
                font = pygame.font.Font(None, 48)
                warning = font.render(f"AVALANCHE IN {int(self.avalanche_timer)}s!", True, (255, 50, 50))
                screen.blit(warning, (200, 50))

class WeatherSystem:
    # wind_force/direction
    # snow_intensity (affects visibility)
    def __init__(self):
        self.wind_force = 0.0
        self.snow_intensity = 2
        self.wind = True
    
    def update_wind():
        if random.random() < 0.01:
            return random.choice([-3,0,3])
        else:
            return 0



# ==========
# FUNCTIONS
# ==========




def ice_physics(player, platform):
    # Reduced friction, sliding mechanics
    player.velocity.x *= 0.95

def check_base_collisions(player, terrain):
    # baseplate collisions (feet, head, sides)
    # Slope handling for mountain angles
    # Climbing surface contact
    
    if player.rect.colliderect(terrain.rect):
        player.position.y = terrain.rect.top - player.rect.height  # Move above terrain
        player.rect.bottom = terrain.rect.top  # Align with terrain
        player.velocity.y = 0  # Stop falling
        player.is_grounded = True
        


def check_hazards(player, hazards):
    # Crevasse detection
    # Falling object collisions
    # Avalanche zone detection
    
    if player.rect.colliderect(hazards.rect):
        return True


def generate_mountain_section(surfacelist):
    # Procedural or hand-crafted level sections
    # Mix of platforms, climbs, hazards
    platforms_list = []
    multx1 = 75
    multx2 = 100
    multy1 = 425
    multy2 = 450
    for fac in range(12):
        x = random.randint(multx1,multx2)
        y = random.randint(multy1,multy2)
        w = random.randint(80,200)
        h = random.randint(15,50)
        surf = random.choice(surfacelist)
        multx1 += 200
        multx2 += 200
        multy1 -= 50
        multy2 -= 50
        platforms_list.append(Platform(x,y,w,h,surf))

    return platforms_list




def camera_follow(player, screen_width):
    # Smooth camera tracking
    global camera_x

    # Center player horizontally
    target_x = -player.rect.centerx + 400  # 400 = half of 800px screen
    
    # Simple follow (no smoothing for jam)
    camera_x = target_x
    
    # Keep in bounds
    camera_x = min(0, camera_x)  # Don't show left of level start
    camera_x = max(-(level_width - 800), camera_x)  # Don't show right of level end
    
    return camera_x

def draw_health_bar(screen, player):
    # Draw player health bar
    bar_width = 200
    bar_height = 20
    bar_x = 10
    bar_y = 10
    
    # Background
    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
    
    # Health fill
    health_width = (player.health / player.max_health) * bar_width
    health_color = (0, 255, 0) if player.health > 50 else (255, 255, 0) if player.health > 25 else (255, 0, 0)
    pygame.draw.rect(screen, health_color, (bar_x, bar_y, health_width, bar_height))
    
    # Border
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
    
    # Health text
    font = pygame.font.Font(None, 24)
    health_text = font.render(f"Health: {player.health}/{player.max_health}", True, (255, 255, 255))
    screen.blit(health_text, (bar_x + 5, bar_y + 2))

def draw_timer(screen, hazard_manager):
    # Draw avalanche timer
    font = pygame.font.Font(None, 36)
    
    if hazard_manager.avalanche_active:
        timer_text = font.render("AVALANCHE!", True, (255, 50, 50))
    elif hazard_manager.avalanche_warning:
        timer_text = font.render(f"Avalanche: {int(hazard_manager.avalanche_timer)}s", True, (255, 150, 50))
    else:
        timer_text = font.render(f"Avalanche: {int(hazard_manager.avalanche_timer)}s", True, (255, 255, 255))
    
    screen.blit(timer_text, (600, 10))





# =========================
# MAIN GAME LOOP
# =========================


def main():
    surfacelist = ["ice","rock"]
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Arctic Platformer")
    clock = pygame.time.Clock()


    player = Player(playersp)
    terrain = Platform(0,580,300,300,"rock")
    goal = Platform(350,200,100,20,"rock")
    hazard_manager = HazardManager()
    setup_player_gravity(player)
    weather = WeatherSystem()
    weather.wind_force = 40.0  # 0 = no wind, can tweak the wind however
    plats = generate_mountain_section(surfacelist)

    # Win Condition


    game_won = False
    game_over = False

    font = pygame.font.Font(None, 36)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # seconds

        jump_pressed = False
        jump_held = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN: 
                if event.key == pygame.K_SPACE:
                    jump_pressed = True
                    player.is_grounded = False


        keys = pygame.key.get_pressed()
        jump_held = keys[pygame.K_SPACE]

        # skip if game over/won

        if not (game_won or game_over):
            moving = False
            mv_speed = player.move_speed * dt
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player.position.x -= mv_speed
                moving = True
        
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player.position.x += mv_speed
                moving = True

            # collisions (my absolute worst nightmare)
            for p in plats:
                if player.rect.colliderect(p.rect):
                    player.position.y = p.rect.top - player.rect.height
                    player.rect.bottom = p.rect.top
                    player.is_grounded = True
                    player.velocity.y = 0  
                    cur = p

                    # check if on ice
                    if p.surface == "ice":
                        player.is_sliding = True
                
            if player.is_sliding == True:
                ice_physics(player,cur)

            check_base_collisions(player, terrain)

            apply_gravity(player, dt, jump_pressed, jump_held, wind_x=weather.wind_force)

            # =====================
            # HAZARDS
            # =====================
            hazard_manager.update(dt, player.position.x)
            hazard_manager.check_collisions(player)
            
            # =====================
            # WIN/LOSE CONDITIONS
            # =====================
            if player.rect.colliderect(goal.rect):
                game_won = True
            
            if player.health <= 0 or hazard_manager.avalanche_active and player.rect.colliderect(hazard_manager.hazards[-1].rect):
                game_over = True
            
            # Update player (invincibility timer)
            player.update(dt)

            # Draw! This is not C so thankfully there should be no memory leaks here
            screen.blit(background, (0, 0))
            screen.blit(player.sprite, player.rect)

            terrain.draw(screen)

            for p in plats:
                p.draw(screen)

            pygame.display.flip()
            


    pygame.quit()


if __name__ == "__main__":
    main()

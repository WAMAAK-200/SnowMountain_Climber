import pygame
import random
import os



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

    def __init__(self):
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

        # Simple visual placeholder so the game can draw something
        self.image = pygame.Surface((32, 48))
        self.image.fill((200, 240, 255))
        self.rect = self.image.get_rect(topleft=self.position)


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

# likely will be scrapped
class ClimbingSurface:
    # Vertical surfaces you can climb
    # holds/piton_points
    # difficulty_rating
    # breakable (ice vs rock)
    pass


class Hazard:
    # Falling icicles, avalanches, crevasses
    # activation_zone
    # damage_value
    
    def __init__(self,x,y,width,height, obst_type):
        self.obst = pygame.Rect(x,y,width,height)
        self.obst_type = obst_type
        self.damage = 0

        if self.obst_type == "icicle":
            self.damage = 2
        elif self.obst_type == "avalanche":
            self.damage = 7
        else:
            self.damage = 1
        
        def spawn_haz(self):
            rng = random.randint(1,50)
            if obst_type != "avalanche":
                pygame.draw.rect(self.obst)





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

# might be scrapped
def handle_climbing(player, climbable_surface):
    # Check for holds, stamina drain, upward movement
    pass


def ice_physics(player, platform):
    # Reduced friction, sliding mechanics
    pass

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






# =========================
# MAIN GAME LOOP
# =========================


def main():
    surfacelist = ["ice","rock"]
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Arctic Platformer")
    clock = pygame.time.Clock()


    player = Player()
    terrain = Platform(0,580,300,300,"rock")
    setup_player_gravity(player)
    weather = WeatherSystem()
    weather.wind_force = 40.0  # 0 = no wind, can tweak the wind however
    plats = generate_mountain_section(surfacelist)


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
                elif event.type == pygame.KEYDOWN and (event.key == pygame.K_d or event.key == pygame.K_RIGHT):
                    player.position.x += 10
                elif event.type == pygame.KEYDOWN and (event.key == pygame.K_l or event.key == pygame.K_LEFT):
                    player.position.x -= 10

        keys = pygame.key.get_pressed()
        jump_held = keys[pygame.K_SPACE]

        # collisions (my absolute worst nightmare)
        for p in plats:
            if player.rect.colliderect(p.rect):
                player.position.y = p.rect.top - player.rect.height
                player.rect.bottom = p.rect.top
                player.is_grounded = True
                player.velocity.y = 0  

        check_base_collisions(player, terrain)

        apply_gravity(player, dt, jump_pressed, jump_held, wind_x=weather.wind_force)

        # Draw! This is not C so thankfully there should be no memory leaks here
        screen.fill((20, 30, 50))
        screen.blit(player.image, player.rect)

        terrain.draw(screen)

        for p in plats:
            p.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

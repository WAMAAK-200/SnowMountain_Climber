import pygame
import random
import os
import musicpy as mp   # keep/import only if you use it
import mixer           # same here


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
    # warmth/health (cold mechanic)
    # inventory (pickups like pitons, ropes)
    
    # Visuals
    # animation states (climbing, walking, slipping)
    # sprite management

    def __init__(self):
        # Physics
        self.position = pygame.math.Vector2(100, 100)
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
    pass


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
    # animation
    pass


class Pickup:
    # Resources to collect
    # type (piton, rope_length, warmth_boost)
    # value
    # respawn_timer
    pass


class WeatherSystem:
    # wind_force/direction
    # snow_intensity (affects visibility)
    # temperature (drains warmth over time)
    # day_night_cycle (lighting changes)
    def __init__(self):
        self.wind_force = 0.0


# =========================
# FUNCTION STUBS (partner)
# =========================

def handle_climbing(player, climbable_surface):
    # Check for holds, stamina drain, upward movement
    pass


def ice_physics(player, platform):
    # Reduced friction, sliding mechanics
    pass


def rope_swing(player, anchor_point):
    # Pendulum physics for rope mechanics
    pass


def check_collisions(player, terrain):
    # Platform collisions (feet, head, sides)
    # Slope handling for mountain angles
    # Climbing surface contact
    pass


def check_hazards(player, hazards):
    # Crevasse detection
    # Falling object collisions
    # Avalanche zone detection
    pass


def generate_mountain_section(difficulty):
    # Procedural or hand-crafted level sections
    # Mix of platforms, climbs, hazards
    pass


def camera_follow(player, screen_width):
    # Smooth camera tracking
    # Parallax backgrounds (distant peaks, clouds)
    pass


def particle_systems():
    # Snow particles (wind-affected)
    # Breath clouds in cold air
    # Snow kick-up when landing
    pass


# =========================
# MAIN GAME LOOP
# =========================

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Arctic Platformer")
    clock = pygame.time.Clock()

    player = Player()
    setup_player_gravity(player)
    weather = WeatherSystem()
    weather.wind_force = 40.0  # tweak for wind, or 0 for none

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # seconds

        jump_pressed = False
        jump_held = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                jump_pressed = True

        keys = pygame.key.get_pressed()
        jump_held = keys[pygame.K_SPACE]

        # TODO: your partner's collision code should set player.is_grounded here
        # check_collisions(player, terrain)

        apply_gravity(player, dt, jump_pressed, jump_held, wind_x=weather.wind_force)

        # --- Draw ---
        screen.fill((20, 30, 50))
        screen.blit(player.image, player.rect)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

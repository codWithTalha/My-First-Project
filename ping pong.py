import pygame
import sys
import math
import array

# --- INITIALIZATION ---
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2)

# --- CONSTANTS ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
RED = (255, 100, 100)

# Game States
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2

# --- SOUND GENERATOR ---
# Generates retro sound effects programmatically without needing external files
def generate_sound(frequency, duration, volume=0.1):
    sample_rate = 22050
    num_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * (num_samples * 2))
    for i in range(num_samples):
        t = float(i) / sample_rate
        # Create a simple square-ish wave for retro arcade feel
        value = int(math.sin(2.0 * math.pi * frequency * t) * 32767 * volume)
        buf[i*2] = value       # Left channel
        buf[i*2 + 1] = value   # Right channel
    return pygame.mixer.Sound(buffer=buf)

# Pre-generate audio effects
SOUND_PADDLE = generate_sound(440, 0.1)  # A4 note
SOUND_WALL = generate_sound(330, 0.08)   # E4 note
SOUND_SCORE = generate_sound(587, 0.25)  # D5 note

# --- GAME CLASSES ---
class Paddle:
    def __init__(self, x, y):
        self.width = 15
        self.height = 100
        self.rect = pygame.Rect(x, y - self.height // 2, self.width, self.height)
        self.speed = 7

    def move(self, up_key, down_key, keys):
        if keys[up_key] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[down_key] and self.rect.bottom < SCREEN_HEIGHT:
            self.rect.y += self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)


class Ball:
    def __init__(self):
        self.radius = 10
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - self.radius, SCREEN_HEIGHT // 2 - self.radius, self.radius * 2, self.radius * 2)
        self.speed_x = 5
        self.speed_y = 5
        self.base_speed = 5
        self.max_speed = 12

    def update(self, player1, player2):
        # Move ball
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        # Ceiling and floor collision
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.speed_y *= -1
            SOUND_WALL.play()

        # Paddle collisions
        if self.rect.colliderect(player1.rect) and self.speed_x < 0:
            self._handle_paddle_collision(player1)
        elif self.rect.colliderect(player2.rect) and self.speed_x > 0:
            self._handle_paddle_collision(player2)

    def _handle_paddle_collision(self, paddle):
        # Reverse horizontal direction
        self.speed_x *= -1
        
        # Calculate bounce angle based on where ball hits the paddle
        relative_intersect_y = (paddle.rect.y + (paddle.rect.height / 2)) - (self.rect.y + self.radius)
        normalized_intersect_y = relative_intersect_y / (paddle.rect.height / 2)
        bounce_angle = normalized_intersect_y * (math.pi / 3) # Max 60 degrees

        # Calculate new speeds while slightly accelerating the ball
        current_speed = min(math.hypot(self.speed_x, self.speed_y) * 1.05, self.max_speed)
        
        # Keep correct directional sign for X axis
        direction = -1 if self.speed_x < 0 else 1
        self.speed_x = direction * current_speed * math.cos(bounce_angle)
        self.speed_y = current_speed * -math.sin(bounce_angle)
        
        SOUND_PADDLE.play()

    def reset(self, direction):
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed_x = self.base_speed * direction
        self.speed_y = self.base_speed if pygame.time.get_ticks() % 2 == 0 else -self.base_speed

    def draw(self, screen):
        pygame.draw.ellipse(screen, WHITE, self.rect)


# --- MAIN GAME MANAGEMENT ---
class GameManager:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Classic Pong")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 40)
        self.large_font = pygame.font.SysFont("Consolas", 60)
        
        self.state = STATE_MENU
        self.score_p1 = 0
        self.score_p2 = 0
        self.winning_score = 5

        # Objects
        self.player1 = Paddle(30, SCREEN_HEIGHT // 2)
        self.player2 = Paddle(SCREEN_WIDTH - 45, SCREEN_HEIGHT // 2)
        self.ball = Ball()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if self.state == STATE_MENU:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                        self.state = STATE_PLAYING
                elif self.state == STATE_GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self.state = STATE_MENU

    def update(self):
        if self.state == STATE_PLAYING:
            keys = pygame.key.get_pressed()
            
            # Player 1 controls (W / S)
            self.player1.move(pygame.K_w, pygame.K_s, keys)
            # Player 2 controls (Up / Down Arrows)
            self.player2.move(pygame.K_UP, pygame.K_DOWN, keys)
            
            # Ball mechanics
            self.ball.update(self.player1, self.player2)

            # Scoring check
            if self.ball.rect.left <= 0:
                self.score_p2 += 1
                SOUND_SCORE.play()
                if self.score_p2 >= self.winning_score:
                    self.state = STATE_GAME_OVER
                else:
                    self.ball.reset(1) # Serve to player 2
                    
            elif self.ball.rect.right >= SCREEN_WIDTH:
                self.score_p1 += 1
                SOUND_SCORE.play()
                if self.score_p1 >= self.winning_score:
                    self.state = STATE_GAME_OVER
                else:
                    self.ball.reset(-1) # Serve to player 1

    def reset_game(self):
        self.score_p1 = 0
        self.score_p2 = 0
        self.ball.reset(1)
        self.player1.rect.y = SCREEN_HEIGHT // 2 - self.player1.height // 2
        self.player2.rect.y = SCREEN_HEIGHT // 2 - self.player2.height // 2

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == STATE_MENU:
            title_text = self.large_font.render("CLASSIC PONG", True, WHITE)
            instruction_text = self.font.render("Press SPACE to Play", True, RED)
            p1_controls = self.font.render("P1: W / S Keys", True, WHITE)
            p2_controls = self.font.render("P2: Up / Down Arrows", True, WHITE)
            
            self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))
            self.screen.blit(instruction_text, (SCREEN_WIDTH // 2 - instruction_text.get_width() // 2, 250))
            self.screen.blit(p1_controls, (SCREEN_WIDTH // 4 - p1_controls.get_width() // 2, 400))
            self.screen.blit(p2_controls, (3 * SCREEN_WIDTH // 4 - p2_controls.get_width() // 2, 400))

        elif self.state == STATE_PLAYING:
            # Draw center court line
            for y in range(0, SCREEN_HEIGHT, 40):
                pygame.draw.rect(self.screen, GRAY, (SCREEN_WIDTH // 2 - 2, y, 4, 20))

            # Draw components
            self.player1.draw(self.screen)
            self.player2.draw(self.screen)
            self.ball.draw(self.screen)

            # Draw UI Scores
            p1_surface = self.large_font.render(str(self.score_p1), True, WHITE)
            p2_surface = self.large_font.render(str(self.score_p2), True, WHITE)
            self.screen.blit(p1_surface, (SCREEN_WIDTH // 4, 30))
            self.screen.blit(p2_surface, (3 * SCREEN_WIDTH // 4 - p2_surface.get_width(), 30))

        elif self.state == STATE_GAME_OVER:
            winner = "Player 1 Wins!" if self.score_p1 >= self.winning_score else "Player 2 Wins!"
            winner_text = self.large_font.render(winner, True, WHITE)
            restart_text = self.font.render("Press SPACE for Menu", True, RED)
            
            self.screen.blit(winner_text, (SCREEN_WIDTH // 2 - winner_text.get_width() // 2, 200))
            self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 320))

        pygame.display.flip()


if __name__ == "__main__":
    game = GameManager()
    game.run()

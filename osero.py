import pygame
import sys
import random

# --- 定数 ---
WIDTH, HEIGHT = 640, 640
CELL_SIZE = WIDTH // 8
GREEN = (0, 150, 0)
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GRAY = (80, 80, 80)
FONT_COLOR = (255, 255, 0)
DIALOG_BG = (50, 50, 70)
BUTTON_COLOR = (100, 100, 150)

# プレイヤー定数
PLAYER_BLACK = 1 # 人間
PLAYER_WHITE = 2 # CPU

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT + 80))
pygame.display.set_caption("特殊ルールオセロ (プレイヤー vs CPU)")

try:
    # 文字サイズをさらに小さく #
    font = pygame.font.SysFont("MS Gothic", 24)
    dialog_font = pygame.font.SysFont("MS Gothic", 32)
except pygame.error:
    font = pygame.font.Font(None, 24)
    dialog_font = pygame.font.Font(None, 32)

# --- Board クラス (ゲームロジック) ---
class Board:
    def __init__(self):
        self.grid = [[0] * 8 for _ in range(8)]
        self.grid[3][3] = PLAYER_WHITE; self.grid[4][4] = PLAYER_WHITE
        self.grid[3][4] = PLAYER_BLACK; self.grid[4][3] = PLAYER_BLACK
        
        self.fixed_stones = set()
        self.fix_charges = {PLAYER_BLACK: 2, PLAYER_WHITE: 2}

    def opponent(self, player):
        return PLAYER_WHITE if player == PLAYER_BLACK else PLAYER_BLACK

    def can_place(self, x, y, player):
        if self.grid[y][x] != 0:
            return False
        
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8 and self.grid[ny][nx] == self.opponent(player):
                while 0 <= nx < 8 and 0 <= ny < 8:
                    nx += dx; ny += dy
                    if not (0 <= nx < 8 and 0 <= ny < 8) or self.grid[ny][nx] == 0: break
                    if self.grid[ny][nx] == player: return True
        return False

    def get_valid_moves(self, player):
        return [(x, y) for y in range(8) for x in range(8) if self.can_place(x, y, player)]

    def place_stone(self, x, y, player, fix_this_stone=False):
        self.grid[y][x] = player
        
        if fix_this_stone and self.fix_charges[player] > 0:
            self.fixed_stones.add((x, y))
            self.fix_charges[player] -= 1
        
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            stones_to_flip = []
            nx, ny = x + dx, y + dy
            while 0 <= nx < 8 and 0 <= ny < 8 and self.grid[ny][nx] == self.opponent(player):
                stones_to_flip.append((nx, ny))
                nx += dx; ny += dy
            
            if 0 <= nx < 8 and 0 <= ny < 8 and self.grid[ny][nx] == player:
                for fx, fy in stones_to_flip:
                    if (fx, fy) not in self.fixed_stones:
                        self.grid[fy][fx] = player
        return True

    def count_stones(self):
        return sum(r.count(PLAYER_BLACK) for r in self.grid), sum(r.count(PLAYER_WHITE) for r in self.grid)

# --- Game クラス (UIとゲーム進行) ---
class Game:
    def __init__(self):
        self.board = Board()
        self.current_player = PLAYER_BLACK
        self.game_over = False
        self.message = "あなたの番です (黒)"
        self.state = "playing"
        self.pending_move = None
        # CPUが固定を狙う戦略的なマス
        self.strategic_squares = {
            (0,0), (0,7), (7,0), (7,7), # 角
            (1,1), (1,6), (6,1), (6,6)  # 角の隣
        }

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if not self.game_over:
                    self.handle_event(event)
            
            if self.current_player == PLAYER_WHITE and not self.game_over and self.state == "playing":
                self.draw()
                pygame.display.flip()
                pygame.time.wait(500)
                self.ai_move()
                self.check_game_flow()
            
            self.draw()
            pygame.display.flip()
            clock.tick(30)

    def ai_move(self):
        valid_moves = self.board.get_valid_moves(PLAYER_WHITE)
        if not valid_moves: return

        best_move, max_flips = None, -1
        for move in valid_moves:
            flips = self.count_flips_for_move(move[0], move[1], PLAYER_WHITE)
            if flips > max_flips:
                max_flips = flips
                best_move = move
        
        fix_it = (best_move in self.strategic_squares and self.board.fix_charges[PLAYER_WHITE] > 0)
        
        self.board.place_stone(best_move[0], best_move[1], PLAYER_WHITE, fix_this_stone=fix_it)
        self.current_player = PLAYER_BLACK

    def count_flips_for_move(self, x, y, player):
        flips = 0
        for dx, dy in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            stones_to_flip = []
            nx, ny = x + dx, y + dy
            while 0 <= nx < 8 and 0 <= ny < 8 and self.board.grid[ny][nx] == self.board.opponent(player):
                stones_to_flip.append((nx, ny))
                nx += dx; ny += dy
            if 0 <= nx < 8 and 0 <= ny < 8 and self.board.grid[ny][nx] == player:
                flips += len(stones_to_flip)
        return flips

    def draw(self):
        screen.fill(GREEN)
        for i in range(9):
            pygame.draw.line(screen, BLACK, (i*CELL_SIZE,0), (i*CELL_SIZE,HEIGHT), 2)
            pygame.draw.line(screen, BLACK, (0,i*CELL_SIZE), (WIDTH,i*CELL_SIZE), 2)
        
        for y in range(8):
            for x in range(8):
                if self.board.grid[y][x] != 0:
                    color = BLACK if self.board.grid[y][x] == PLAYER_BLACK else WHITE
                    center = (x*CELL_SIZE+CELL_SIZE//2, y*CELL_SIZE+CELL_SIZE//2)
                    pygame.draw.circle(screen, color, center, CELL_SIZE//2-4)
                    if (x,y) in self.board.fixed_stones:
                        pygame.draw.circle(screen, FONT_COLOR, center, 8)
        
        ui_rect = pygame.Rect(0, HEIGHT, WIDTH, 80)
        pygame.draw.rect(screen, GRAY, ui_rect)
        
        msg_surf = font.render(self.message, True, FONT_COLOR)
        screen.blit(msg_surf, (20, HEIGHT + 10))
        
        fix_info = f"固定権: あなた {self.board.fix_charges[PLAYER_BLACK]} | CPU {self.board.fix_charges[PLAYER_WHITE]}"
        fix_surf = font.render(fix_info, True, FONT_COLOR)
        screen.blit(fix_surf, (20, HEIGHT + 45))
        
        b, w = self.board.count_stones()
        score_text = f"あなた(黒):{b} CPU(白):{w}"
        score_surf = font.render(score_text, True, FONT_COLOR)
        score_rect = score_surf.get_rect(centery=ui_rect.centery, right=WIDTH-20)
        screen.blit(score_surf, score_rect)

        if self.state == "awaiting_fix_choice":
            self.draw_choice_dialog()

    def draw_choice_dialog(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); s.fill((0,0,0,128)); screen.blit(s,(0,0))
        self.dialog_rect = pygame.Rect(WIDTH//2-200, HEIGHT//2-100, 400, 200)
        pygame.draw.rect(screen, DIALOG_BG, self.dialog_rect, border_radius=15)
        q_text = dialog_font.render("この石を固定しますか？", True, WHITE)
        screen.blit(q_text, (self.dialog_rect.centerx - q_text.get_width()//2, self.dialog_rect.y + 30))
        self.yes_button = pygame.Rect(self.dialog_rect.x+50, self.dialog_rect.y+110, 120, 50)
        self.no_button = pygame.Rect(self.dialog_rect.x+230, self.dialog_rect.y+110, 150, 50)
        pygame.draw.rect(screen, BUTTON_COLOR, self.yes_button, border_radius=10)
        pygame.draw.rect(screen, BUTTON_COLOR, self.no_button, border_radius=10)
        yes_text = dialog_font.render("はい(Y)", True, WHITE)
        no_text = dialog_font.render("いいえ(N)", True, WHITE)
        screen.blit(yes_text, (self.yes_button.centerx-yes_text.get_width()//2, self.yes_button.centery-yes_text.get_height()//2))
        screen.blit(no_text, (self.no_button.centerx-no_text.get_width()//2, self.no_button.centery-no_text.get_height()//2))

    def process_player_choice(self, fix_it):
        x, y = self.pending_move
        self.board.place_stone(x, y, PLAYER_BLACK, fix_this_stone=fix_it)
        self.state = "playing"
        self.pending_move = None
        self.current_player = PLAYER_WHITE
        self.check_game_flow()

    def handle_event(self, event):
        if self.current_player == PLAYER_BLACK:
            if self.state == "playing":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos[0] // CELL_SIZE, event.pos[1] // CELL_SIZE
                    if self.board.can_place(x, y, PLAYER_BLACK):
                        if self.board.fix_charges[PLAYER_BLACK] > 0:
                            self.state = "awaiting_fix_choice"
                            self.pending_move = (x, y)
                        else:
                            self.board.place_stone(x, y, PLAYER_BLACK, False)
                            self.current_player = PLAYER_WHITE
                            self.check_game_flow()

            elif self.state == "awaiting_fix_choice":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.yes_button.collidepoint(event.pos): self.process_player_choice(True)
                    elif self.no_button.collidepoint(event.pos): self.process_player_choice(False)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y: self.process_player_choice(True)
                    elif event.key == pygame.K_n: self.process_player_choice(False)

    def check_game_flow(self):
        self.update_message()
        if not self.board.get_valid_moves(self.current_player):
            opponent = self.board.opponent(self.current_player)
            if not self.board.get_valid_moves(opponent):
                self.game_over = True; self.end_game()
            else:
                self.message = f"{'あなた' if self.current_player == PLAYER_BLACK else 'CPU'}はパス"
                self.draw(); pygame.display.flip(); pygame.time.wait(1000)
                self.current_player = opponent
                self.update_message()

    def update_message(self):
        if not self.game_over:
            self.message = "あなたの番です (黒)" if self.current_player == PLAYER_BLACK else "CPUの番です (白)"

    def end_game(self):
        b, w = self.board.count_stones()
        winner = "あなたの勝ち" if b > w else "CPUの勝ち" if w > b else "引き分け"
        self.message = f"ゲーム終了！ {winner} ({b}-{w})"

if __name__ == "__main__":
    game = Game()
    game.run()
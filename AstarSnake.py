import random
import numpy as np
import pygame
import pickle
import time
import heapq


# color class
class Color:
    def __init__(self):
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.red = (255, 0, 0)
        self.yellow = (255, 255, 0)
        self.green = (0, 255, 0)


class VisualSnake:
    def __init__(self):
        # whether to show episode number at the top
        self.show_episode = False
        self.episode = None

        # scale adjusts size of whole board (use 1.0 or 2.0)
        self.scale = 1
        self.game_width = int(1500 * self.scale)
        self.game_height = int(690 * self.scale)

        # padding for score & episode
        self.padding = int(30 * self.scale)
        self.screen_width = self.game_width
        self.screen_height = self.game_height + self.padding

        self.snake_size = int(30 * self.scale)
        self.food_size = int(30 * self.scale)
        self.bomb_size = int(30 * self.scale)
        self.snake_speed = 40

        self.bombs = []

        self.snake_coords = []
        self.snake_length = 1
        self.dir = "right"
        self.board = np.zeros((self.game_height // self.snake_size, self.game_width // self.snake_size))

        self.game_close = False

        # starting location for the snake
        self.x1 = self.game_width / 2
        self.y1 = self.game_height / 2 + self.padding

        self.r1, self.c1 = self.coords_to_index(self.x1, self.y1)
        self.board[self.r1][self.c1] = 1

        self.c_change = 1
        self.r_change = 0

        self.food_r, self.food_c = self.generate_food()
        self.board[self.food_r][self.food_c] = 2
        pygame.init()
        self.color = Color()

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("bahnschrift", int(18 * self.scale))
        self.last_dir = None
        self.step("down")

    def print_score(self, score):
        value = self.font.render(f"Score: {score}", True, self.color.white)
        self.screen.blit(value, [500 * self.scale, 10])


    def draw_snake(self):
        for i in range(len(self.snake_coords) - 1, -1, -1):
            r, c = self.snake_coords[i]
            x, y = self.index_to_coords(r, c)
            if i == len(self.snake_coords) - 1:
                # head square color
                pygame.draw.rect(self.screen, self.color.green, [x, y, self.snake_size, self.snake_size])
            else:
                pygame.draw.rect(self.screen, self.color.yellow, [x, y, self.snake_size, self.snake_size])

    def game_end_message(self):
        # Clear the screen (fill with background color)
        self.screen.fill((0, 0, 0))  # Black background

        # Render "Game Over" message
        game_over_text = self.font.render(f"Game Over! Score: {self.snake_length - 1}, Want to try again?", True, (255, 0, 0))  # Red color
        self.screen.blit(game_over_text, [self.game_width / 3+65, self.game_height / 3])

        # Render "Retry" button
        retry_text = self.font.render("Retry", True, (255, 255, 255))  # White color
        retry_rect = retry_text.get_rect(center=(self.game_width / 2 - 100, self.game_height / 2))
        pygame.draw.rect(self.screen, (0, 255, 0), retry_rect.inflate(20, 10))  # Green background
        self.screen.blit(retry_text, retry_rect)

        # Render "Exit" button
        exit_text = self.font.render("Exit", True, (255, 255, 255))  # White color
        exit_rect = exit_text.get_rect(center=(self.game_width / 2 + 100, self.game_height / 2))
        pygame.draw.rect(self.screen, (255, 0, 0), exit_rect.inflate(20, 10))  # Red background
        self.screen.blit(exit_text, exit_rect)

        # Update the display
        pygame.display.flip()

        # Handle button clicks
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if retry_rect.collidepoint(mouse_pos):
                        return "restart"

                    elif exit_rect.collidepoint(mouse_pos):
                        return "quit"

    # is there danger in this square (body or wall or bomb)
    def is_unsafe(self, r, c):
        if self.valid_index(r, c):
            if self.board[r][c] == 1 or self.board[r][c] == 3:
                return 1
            return 0
        else:
            return 1


    def valid_index(self, r, c):
        return 0 <= r < len(self.board) and 0 <= c < len(self.board[0])

    # board coordinates <==> row, column conversions
    def index_to_coords(self, r, c):
        x = c * self.snake_size
        y = r * self.snake_size + self.padding
        return (x, y)

    def coords_to_index(self, x, y):
        r = int((y - self.padding) // self.snake_size)
        c = int(x // self.snake_size)
        return (r, c)

    # randomly place food
    def generate_food(self):
        food_c = int(round(random.randrange(0, self.game_width - self.food_size) / self.food_size))
        food_r = int(round(random.randrange(0, self.game_height - self.food_size) / self.food_size))
        if self.board[food_r][food_c] != 0:
            food_r, food_c = self.generate_food()
        return food_r, food_c

    def generate_bomb(self):
        bomb_c = int(round(random.randrange(0, self.game_width - self.bomb_size) / self.bomb_size))
        bomb_r = int(round(random.randrange(0, self.game_height - self.bomb_size) / self.bomb_size))
        if self.board[bomb_r][bomb_c] != 0:
            bomb_r, bomb_c = self.generate_bomb()
        return bomb_r, bomb_c

    def game_over(self):
        return self.game_close


    def printBombs(self):
        for bomb in self.bombs:
            bomb_c,bomb_r = bomb
            bomb_x, bomb_y = self.index_to_coords(bomb_r, bomb_c)
            pygame.draw.rect(self.screen, self.color.white, [bomb_x, bomb_y, self.bomb_size, self.bomb_size])

    def step(self, action):

        for event in pygame.event.get():
            pass

        # take action
        self.last_dir = self.dir
        if action == "left" and (self.dir != "right" or self.snake_length == 1):
            self.c_change = -1
            self.r_change = 0
            self.dir = "left"
        elif action == "right" and (self.dir != "left" or self.snake_length == 1):
            self.c_change = 1
            self.r_change = 0
            self.dir = "right"
        elif action == "up" and (self.dir != "down" or self.snake_length == 1):
            self.r_change = -1
            self.c_change = 0
            self.dir = "up"
        elif action == "down" and (self.dir != "up" or self.snake_length == 1):
            self.r_change = 1
            self.c_change = 0
            self.dir = "down"

        if self.c1 >= self.game_width // self.snake_size or self.c1 < 0 or self.r1 >= self.game_height // self.snake_size or self.r1 < 0:
            self.game_close = True
        self.c1 += self.c_change
        self.r1 += self.r_change

        self.screen.fill(self.color.black)
        pygame.draw.rect(self.screen, (255, 255, 255), (0, self.padding, self.game_width, self.game_height), 1)

        food_x, food_y = self.index_to_coords(self.food_r, self.food_c)
        pygame.draw.rect(self.screen, self.color.red, [food_x, food_y, self.food_size, self.food_size])

        self.printBombs()

        self.snake_coords.append((self.r1, self.c1))

        if self.valid_index(self.r1, self.c1):
            self.board[self.r1][self.c1] = 1

        if len(self.snake_coords) > self.snake_length:
            rd, cd = self.snake_coords[0]
            del self.snake_coords[0]
            if self.valid_index(rd, cd):
                self.board[rd][cd] = 0

        for r, c in self.snake_coords[:-1]:
            if r == self.r1 and c == self.c1:
                self.game_close = True

        self.draw_snake()
        self.print_score(self.snake_length - 1)
        pygame.display.update()

        # snake ate the food
        if self.c1 == self.food_c and self.r1 == self.food_r:
            self.food_r, self.food_c = self.generate_food()
            self.board[self.food_r][self.food_c] = 2
            bomb_r, bomb_c =self.generate_bomb()
            self.board[bomb_r][bomb_c] = 3
            self.bombs.append((bomb_c,bomb_r))
            pygame.display.update()
            self.snake_length += 1

    def run_game(self):
        while not self.game_over():
            # AI: Calculate the next move using A*
            obstacles = []
            foodCord = None
            for i in range(len(self.board)):
                for j in range(len(self.board[0])):
                    if self.board[i][j] in (1,3):
                        obstacles.append((j,i))
                    if self.board[i][j] == 2:
                        foodCord = (j,i)

            path = a_star((self.c1,self.r1), foodCord, set(obstacles))
            direction = ""
            if path:
                next_position = path[0]
                dx = next_position[0] - self.c1
                dy = next_position[1] - self.r1

                if dx > 0:
                    direction = "right"
                elif dx < 0:
                    direction = "left"
                elif dy > 0:
                    direction = "down"
                elif dy < 0:
                    direction = "up"

            self.step(direction)
            self.clock.tick(self.snake_speed)

        if self.game_over() == True:
            # snake dies
            self.screen.fill(self.color.black)
            pygame.draw.rect(self.screen, (255, 255, 255), (0, self.padding, self.game_width, self.game_height), 1)
            ret = self.game_end_message()
            self.print_score(self.snake_length - 1)
            pygame.display.update()
            #time.sleep(5)
            return ret

        return self.snake_length


def a_star(start, goal, obstacles):
    """Perform A* pathfinding with forward checking to improve AI decision-making."""
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            return reconstruct_path(came_from, current)

        neighbors = get_neighbors(current)
        for neighbor in neighbors:
            if neighbor in obstacles or not is_future_safe(neighbor, obstacles):
                continue  # Avoid unsafe moves

            tentative_g_score = g_score[current] + 1

            if tentative_g_score < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                if neighbor not in [item[1] for item in open_set]:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return []  # No path found


def is_future_safe(pos, obstacles):
    """
    Performs a flood-fill check to ensure that moving to `pos` does not result in
    getting the snake trapped in an enclosed space.
    """
    x, y = pos
    visited = set()
    queue = [pos]
    free_space = 0

    while queue:
        px, py = queue.pop(0)
        if (px, py) in visited or (px, py) in obstacles:
            continue

        visited.add((px, py))
        free_space += 1

        # Stop checking if enough free space is available
        if free_space > 5:
            return True

        for nx, ny in get_neighbors((px, py)):
            if (nx, ny) not in visited and (nx, ny) not in obstacles:
                queue.append((nx, ny))

    return False  # Not enough free space, likely a dead-end

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def reconstruct_path(came_from, current):
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path


def get_neighbors(position):
    x, y = position
    neighbors = [
        (x - 1, y),
        (x + 1, y),
        (x, y - 1),
        (x, y + 1),
    ]
    return [(nx, ny) for nx, ny in neighbors if 0 <= nx < VS.game_width // VS.snake_size and 0 <= ny < VS.game_height // VS.snake_size]


VS = VisualSnake()
ret = VS.run_game()
while type(ret) is str and ret == "restart":
    pygame.quit()
    VS = VisualSnake()
    ret = VS.run_game()

pygame.quit()

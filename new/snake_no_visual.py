import random
import numpy as np
import pickle
import math

# a copy of visualsnake.py but without the PyGame

class LearnSnake:
    def __init__(self):
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
        self.survived = 0

        self.step()

    def get_state(self):
        head_r, head_c = self.snake_coords[-1]
        state = []
        state.append(int(self.dir == "left"))
        state.append(int(self.dir == "right"))
        state.append(int(self.dir == "up"))
        state.append(int(self.dir == "down"))
        state.append(int(self.food_r < head_r))
        state.append(int(self.food_r > head_r))
        state.append(int(self.food_c < head_c))
        state.append(int(self.food_c > head_c))
        state.append(self.is_unsafe(head_r + 1, head_c))
        state.append(self.is_unsafe(head_r - 1, head_c))
        state.append(self.is_unsafe(head_r, head_c + 1))
        state.append(self.is_unsafe(head_r, head_c - 1))
        return tuple(state)

    def is_unsafe(self, r, c):
        if self.valid_index(r, c):
            if self.board[r][c] == 1 or self.board[r][c] == 3:
                return 1
            return 0
        else:
            return 1

    def get_dist(self, r1, c1, r2, c2):
        return ((r2 - r1) ** 2 + (c2 - c1) ** 2) ** 0.5

    def valid_index(self, r, c):
        return 0 <= r < len(self.board) and 0 <= c < len(self.board[0])

    def coords_to_index(self, x, y):
        r = int((y - self.padding) // self.snake_size)
        c = int(x // self.snake_size)
        return (r, c)

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

    def step(self, action="None"):
        if action == "None":
            action = random.choice(["left", "right", "up", "down"])
        else:
            action = ["left", "right", "up", "down"][action]

        reward = 0

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

        if self.c1 >= self.screen_width // self.snake_size or self.c1 < 0 or self.r1 >= self.screen_height // self.snake_size or self.r1 < 0:
            self.game_close = True
        self.c1 += self.c_change
        self.r1 += self.r_change

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

        if self.c1 == self.food_c and self.r1 == self.food_r:
            self.food_r, self.food_c = self.generate_food()
            self.board[self.food_r][self.food_c] = 2
            bomb_r, bomb_c = self.generate_bomb()
            self.board[bomb_r][bomb_c] = 3
            self.bombs.append((bomb_c, bomb_r))
            self.snake_length += 1
            reward = 1  # food eaten, so +1 reward
        else:
            rh1, ch1 = self.snake_coords[-1]
            if len(self.snake_coords) == 1:
                rh2, ch2 = rh1, ch1
            else:
                rh2, ch2 = self.snake_coords[-1]

        # death = -10 reward
        if self.game_close:
            reward = -10
        self.survived += 1

        return self.get_state(), reward, self.game_close

    # run game using given episode (from saved q tables)
    # no visual - just returns snake length
    def run_game(self, episode):
        filename = f"pickle/{episode}.pickle"
        with open(filename, 'rb') as file:
            table = pickle.load(file)
        current_length = 2
        steps_unchanged = 0
        while not self.game_over():
            state = self.get_state()
            action = np.argmax(table[state])
            if steps_unchanged == 1000:
                break
            self.step(action)
            if self.snake_length != current_length:
                steps_unchanged = 0
                current_length = self.snake_length
            else:
                steps_unchanged += 1

        return self.snake_length
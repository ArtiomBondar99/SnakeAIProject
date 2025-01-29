import random
import numpy as np
import pygame
import pickle
import time
import math

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
        self.survived = 0
        pygame.init()
        self.color = Color()

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("bahnschrift", int(18 * self.scale))
        self.last_dir = None
        self.step()

    def print_score(self, score):
        value = self.font.render(f"Score: {score}", True, self.color.white)
        self.screen.blit(value, [500 * self.scale, 10])

    def print_episode(self):
        if self.show_episode:
            value = self.font.render(f"Episode: {self.episode}", True, self.color.white)
            self.screen.blit(value, [10, 10])

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
        game_over_text = self.font.render(f"Game Over! Score: {self.snake_length - 1}, Want to try again?", True,
                                          (255, 0, 0))  # Red color
        self.screen.blit(game_over_text, [self.game_width / 3 + 65, self.game_height / 3])

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

    # is there danger in this square (body or wall)
    def is_unsafe(self, r, c):
        if self.valid_index(r, c):
            if self.board[r][c] == 1 or self.board[r][c] == 3:
                return 1
            return 0
        else:
            return 1

    def distanceFunc(self,cordA, cordB):
        return math.sqrt((cordB[0] - cordA[0]) ** 2 + (cordB[1] - cordA[1]) ** 2)

    def directionFunc(self,cordA, cordB):
        directionDic = {"left": 0, "right": 0, "up": 0, "down": 0}
        xDirectionDelta = cordB[0] - cordA[0]  # 3  -7
        yDirectionDelta = cordB[1] - cordA[1]  # 1
        totalDirection = abs(xDirectionDelta) + abs(yDirectionDelta)
        if xDirectionDelta > 0:
            directionDic["right"] = abs(xDirectionDelta) / max(totalDirection, 1)
        else:
            directionDic["left"] = abs(xDirectionDelta) / max(totalDirection, 1)

        if yDirectionDelta < 0:
            directionDic["up"] = abs(yDirectionDelta) / max(totalDirection, 1)
        else:
            directionDic["down"] = abs(yDirectionDelta) / max(totalDirection, 1)
        return directionDic

    def foodDirection(self):
        snakeHead = self.snake_coords[0]
        foodCord = (self.food_c,self.food_r)
        distance = self.distanceFunc(snakeHead, foodCord)
        directionDic = self.directionFunc(snakeHead, foodCord)
        directionString = ""
        maxDirection = -1
        for key, value in directionDic.items():
            if value > maxDirection:
                maxDirection = value
                directionString = key

        return distance, directionString

    def bombDirection(self):
        snakeHead = self.snake_coords[0]
        totalDistance = 0
        for bomb in self.bombs:
            totalDistance += self.distanceFunc(snakeHead, bomb)

        averageDistance = totalDistance / max(len(self.bombs), 1)

        totalDirectionDic = {"left": 0, "right": 0, "up": 0, "down": 0}
        for bomb in self.bombs:
            direction = self.directionFunc(snakeHead, bomb)
            totalDirectionDic["left"] += direction["left"]
            totalDirectionDic["right"] += direction["right"]
            totalDirectionDic["down"] += direction["down"]
            totalDirectionDic["up"] += direction["up"]

        directionString = ""
        lowestDirection = 10 ** 1000
        for key, value in totalDirectionDic.items():
            if value < lowestDirection:
                lowestDirection = value
                directionString = key

        return averageDistance, directionString

    def wallsDirection(self):
        snakeHead = self.snake_coords[0]
        wallDistanceRight = (self.game_width//self.snake_size - 1) - snakeHead[0]
        wallDistanceLeft = snakeHead[0]
        wallDistanceUp = snakeHead[1]
        wallDistanceDown = (self.game_height//self.snake_size - 1) - snakeHead[1]
        distanceList = [wallDistanceRight, wallDistanceLeft, wallDistanceUp, wallDistanceDown]
        maxDistance = max(distanceList)
        directionIndex = distanceList.index(maxDistance)
        if directionIndex == 0:
            return wallDistanceRight, "right"
        elif directionIndex == 1:
            return wallDistanceLeft, "left"
        elif directionIndex == 2:
            return wallDistanceUp, "up"
        return wallDistanceDown, "down"

    def bodyDirection(self):
        snakeHead = self.snake_coords[0]
        totalDistance = 0
        for snakeBody in self.snake_coords:
            totalDistance += self.distanceFunc(snakeHead, snakeBody)
        averageDistance = totalDistance / len(self.snake_coords)

        totalDirectionDic = {"left": 0, "right": 0, "up": 0, "down": 0}
        for snakeBody in self.snake_coords:
            direction = self.directionFunc(snakeHead, snakeBody)
            totalDirectionDic["left"] += direction["left"]
            totalDirectionDic["right"] += direction["right"]
            totalDirectionDic["down"] += direction["down"]
            totalDirectionDic["up"] += direction["up"]

        directionString = ""
        lowestDirection = 10 ** 1000
        for key, value in totalDirectionDic.items():
            if value < lowestDirection:
                lowestDirection = value
                directionString = key

        return averageDistance, directionString

    def getNextDirectionState(self):
        foodDistance, foodDirectionString = self.foodDirection()
        bombDistance, bombDirectionString = self.bombDirection()
        wallDistance, wallDirectionString = self.wallsDirection()
        bodyDistance, bodyDirectionString = self.bodyDirection()
        nextDirection = {"up": 0, "down": 0, "left": 0, "right": 0}
        nextDirection[foodDirectionString] += 20
        nextDirection[bombDirectionString] += 2
        nextDirection[wallDirectionString] += 1
        nextDirection[bodyDirectionString] += 10

        nextDirection["up"] /= 33
        nextDirection["down"] /= 33
        nextDirection["left"] /= 33
        nextDirection["right"] /= 33

        return max(nextDirection, key=nextDirection.get)


    # returns tuple of 12 features
    def get_state(self):
        overAllBestDirection = {"left": 0, "right": 1, "up": 2, "down": 3}[self.getNextDirectionState()]
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
        state.append(overAllBestDirection)
        return tuple(state)

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


    def step(self, action="None"):
        if action == "None":
            action = random.choice(["left", "right", "up", "down"])
        else:
            action = ["left", "right", "up", "down"][action]

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
        self.print_episode()
        pygame.display.update()

        # snake ate the food
        if self.c1 == self.food_c and self.r1 == self.food_r:
            self.food_r, self.food_c = self.generate_food()
            self.board[self.food_r][self.food_c] = 2
            bomb_r, bomb_c = self.generate_bomb()
            self.board[bomb_r][bomb_c] = 3
            self.bombs.append((bomb_c, bomb_r))
            pygame.display.update()
            self.snake_length += 1
        self.survived += 1

    def run_game(self, episode):
        self.show_episode = True
        self.episode = episode
        self.print_episode()
        pygame.display.update()

        # pass in pickle file with q table (stored in directory pickle with file name being episode #.pickle)
        filename = f"pickle/{episode}.pickle"
        with open(filename, 'rb') as file:
            table = pickle.load(file)
        time.sleep(5)
        current_length = 2
        steps_unchanged = 0
        while not self.game_over():
            if self.snake_length != current_length:
                steps_unchanged = 0
                current_length = self.snake_length
            else:
                steps_unchanged += 1

            state = self.get_state()
            action = np.argmax(table[state])
            action = min(action,3)
            if steps_unchanged == 1000:
                # stop if snake hasn't eaten anything in 1000 episodes (stuck in a loop)
                break
            self.step(action)
            self.clock.tick(self.snake_speed)
        if self.game_over() == True:
            # snake dies
            self.screen.fill(self.color.black)
            pygame.draw.rect(self.screen, (255, 255, 255), (0, self.padding, self.game_width, self.game_height), 1)
            ret = self.game_end_message()
            self.print_episode()
            self.print_score(self.snake_length - 1)
            pygame.display.update()
            return ret
            #time.sleep(5)
            #pygame.quit()
        return self.snake_length



VS = VisualSnake()
ret = VS.run_game(10000)
while type(ret) is str and ret == "restart":
    pygame.quit()
    VS = VisualSnake()
    ret = VS.run_game(10000)

pygame.quit()
from tkinter import *
import random
import time
import math
import numpy as np
import pygame
import pickle

GAME_WIDTH = 1500
GAME_HEIGHT = 700
SPEED = 150
SPACE_SIZE = 50
GAME_ROWS = GAME_HEIGHT // SPACE_SIZE
GAME_COLUMNS = GAME_WIDTH // SPACE_SIZE
BODY_PARTS = 1
HEAD_COLOR = "#FFD700"
BODY_COLOR = "#00FF00"
TAIL_COLOR = "#8B0000"
FOOD_COLOR = "#FF0000"
BOMB_COLOR = "#FFFFFF"
BACKGROUND_COLOR = "#000000"

maxScore = 0
score = 0
direction = 'down'
label = None
canvas = None
window = None

q_table = {}
state = {}  # שומר על המצבים
alpha = 0.1
gamma = 0.9
epsilon = 1.0
epsilon_decay = 0.995
min_epsilon = 0.05
episodes = 10000


def choose_action(directionState):
    # Convert `directionState` to a hashable key
    directionState_key = tuple(sorted(directionState.items()))

    if random.uniform(0, 1)+1 < epsilon:  # Exploration
        return random.choice(["up", "down", "left", "right"])
    else:  # Exploitation
        # Use the hashable key to fetch Q-values
        q_values = q_table.get(directionState_key, directionState) #{"up": 0.01, "down": 0.01, "left": 0.01, "right": 0.01})
        return max(q_values, key=q_values.get)


def updateQTable(directionState, action, reward, direction_next_state):
    # Convert `directionState` and `direction_next_state` to tuples (hashable format)
    directionState_key = tuple(sorted(directionState.items()))
    direction_next_state_key = tuple(sorted(direction_next_state.items()))

    # Get the max Q-value for the next state
    maxFutureQ = max(q_table.get(direction_next_state_key, {'up': 0, 'down': 0, 'left': 0, 'right': 0}).values())

    # Get the current Q-value for the current state and action
    currentQ = q_table.get(directionState_key, {}).get(action, 0)

    # Calculate the new Q-value
    newQ = (1 - alpha) * currentQ + alpha * (reward + gamma * maxFutureQ)

    # Update the Q-table
    if directionState_key not in q_table:
        q_table[directionState_key] = {}
    q_table[directionState_key][action] = newQ


def saveQtable(i):
    with open(f'snakePickle/{i}.pickle', "wb") as f:
        pickle.dump(q_table, f)


def loadQtable(i):
    global q_table
    try:
        with open(f'snakePickle/{i}.pickle', 'rb') as f:
            q_table = pickle.load(f)
    except FileNotFoundError:
        q_table = {}


def NextTurn(stateDirection, state, total_reward, perform_action):
    # Perform an action and update the state
    # בחירת פעולה
    action = choose_action(stateDirection)

    # ביצוע פעולה וקבלת המצב הבא והתגמול
    next_state, reward, done, nextDirection = perform_action(state, action)

    # עדכון ה-Q-Table
    updateQTable(stateDirection, action, reward, nextDirection)

    # עדכון מצב
    stateDirection = nextDirection
    state = next_state
    total_reward += reward

    if not done:
        # Schedule the next turn
        window.after(SPEED, NextTurn, stateDirection, state, total_reward, perform_action)
    else:
        # Game over
        GameOver()
    return total_reward


def run_episode(getNextDirectionState, perform_action):
    global epsilon
    state = restart_run()
    stateDirection = getNextDirectionState(state["snake"], state["food"], state["bombs"])
    total_reward = 0
    total_reward += NextTurn(stateDirection, state, total_reward, perform_action)

    # הפחתת epsilon
    epsilon = max(min_epsilon, epsilon * epsilon_decay)
    return total_reward


def run_simulator():
    def run_episodes(i=0):

        """Recursive function to run multiple episodes."""
        global episodes
        global alpha
        alpha = max(0.1, 1.0 / (1.0 + i))  # Decrease learning rate as the number of episodes increases
        if i < episodes:
            totalReward = run_episode(getNextDirectionState, perform_action)
            print(f"Episode {i + 1}/{episodes} - Total Reward: {totalReward}")
            if (i < 500 and i % 10 == 0) or (i >= 500 and i < 1000 and i % 200 == 0) or (i >= 1000 and i % 500 == 0):
                saveQtable(i)
            window.after(10000, run_episodes, i + 1)  # Schedule the next episode
        else:
            print("Simulation complete!")

    loadQtable(9500)  # Load the Q-table from a file
    run_episodes()  # Start the first episode
    print("final max score:", maxScore)


# ---------------------------------------------------------------------------------------------------------------------------------------


class Snake:
    def __init__(self, other=None):
        if other == None:
            self.body_size = BODY_PARTS
            self.coordinates = []
            self.squares = []
            for i in range(0, BODY_PARTS):
                self.coordinates.append([GAME_WIDTH // 2, GAME_HEIGHT // 2])

            for index, (x, y) in enumerate(self.coordinates):
                if index == 0:
                    color = HEAD_COLOR
                else:
                    color = BODY_COLOR
                square = canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=color, tag="snake")
                self.squares.append(square)
        else:
            self.coordinates = other.coordinates.copy()
            self.squares = other.squares.copy()
            self.body_size = other.body_size

        # for x,y in self.coordinates:
        #     square = canvas.create_rectangle(x,y,x+SPACE_SIZE,y+SPACE_SIZE,fill=SNAKE_COLOR,tag="snake")
        #     self.squares.append(square)


class Food:
    def __init__(self, bombs=None, snake=None, other=None):
        if other is None:
            if bombs is None:
                bombs = []
            if snake is None:
                snake_coordinates = []
            else:
                snake_coordinates = snake.coordinates
            while True:
                x = random.randint(0, (GAME_WIDTH // SPACE_SIZE) - 1) * SPACE_SIZE
                y = random.randint(0, (GAME_HEIGHT // SPACE_SIZE) - 1) * SPACE_SIZE
                if all(bomb.coordinates != [x, y] for bomb in bombs) and all(
                        sCoord != [x, y] for sCoord in snake_coordinates):
                    break
            self.coordonates = [x, y]
            canvas.create_oval(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=FOOD_COLOR, tag="food")
        else:
            self.coordonates = other.coordonates.copy()


class Bomb:
    def __init__(self, food=None, bombs=None, snake=None, other=None):
        if other == None:
            if bombs is None:
                bombs = []
            if snake is None:
                snake_coordinates = []
            else:
                snake_coordinates = snake.coordinates
            while True:
                x = random.randint(0, (GAME_WIDTH // SPACE_SIZE) - 1) * SPACE_SIZE
                y = random.randint(0, (GAME_HEIGHT // SPACE_SIZE) - 1) * SPACE_SIZE
                # if [x, y] != food.coordonates and all(bomb.coordinates != [x, y] for bomb in bombs) and [x, y] not in snake_coordinates:
                if [x, y] != food.coordonates and all(bomb.coordinates != [x, y] for bomb in bombs) and all(
                        sCoord != [x, y] for sCoord in snake_coordinates):
                    # if all(fo.coordinates != [x, y] for fo in food) and all(bomb.coordinates != [x, y] for bomb in bombs) and all(sCoord != [x, y] for sCoord in snake_coordinates):
                    break
            self.coordinates = [x, y]
            canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=BOMB_COLOR, tag="bomb")
        else:
            self.coordinates = other.coordinates.copy()


def cloneState(curState):
    state = {}
    state["currentDirection"] = curState["currentDirection"]
    state["snake"] = Snake(curState["snake"])
    state["food"] = Food(1, 1, curState["food"])
    state["bombs"] = []
    for bomb in curState["bombs"]:
        state["bombs"].append(Bomb(1, 1, 1, bomb))
    return state


def perform_action(state, action):
    global label
    global canvas
    global direction
    nextState = cloneState(state)
    snake = nextState["snake"]
    x, y = snake.coordinates[0]
    direction = action
    if direction == "up":
        y -= SPACE_SIZE

    elif direction == "down":
        y += SPACE_SIZE

    elif direction == "left":
        x -= SPACE_SIZE

    elif direction == "right":
        x += SPACE_SIZE

    snake.coordinates.insert(0, (x, y))
    head_square = canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=HEAD_COLOR, tags="snake")
    snake.squares.insert(0, head_square)

    food = nextState["food"]
    bombs = nextState["bombs"]
    reward = 0
    if x == food.coordonates[0] and y == food.coordonates[1]:
        reward += 10
        global score
        score += 1
        global maxScore
        if score > maxScore:
            maxScore = score
            print("current max score:", maxScore)
        label.config(text="Score:{}".format(score))
        canvas.delete("food")
        food = Food(bombs=bombs, snake=snake)
        nextState["food"] = food
        bombs.append(Bomb(food=food, bombs=bombs, snake=snake))

    else:
        reward -= 0.1
        tail_square = snake.squares[-1]
        canvas.itemconfig(tail_square, fill=TAIL_COLOR)

        del snake.coordinates[-1]
        del snake.squares[-1]
        canvas.delete(tail_square)

    distance_to_food = distanceFunc([x, y], food.coordonates)
    if distance_to_food < distanceFunc(snake.coordinates[0], food.coordonates):
        reward += 0.5  # Encourage movements that reduce distance to food

    for square in snake.squares[1:]:
        canvas.itemconfig(square, fill=BODY_COLOR)

    over = False
    if CheckCollisions(snake, bombs):
        GameOver()
        over = True
        reward -= 99

    nextDirection = getNextDirectionState(snake, food, bombs)
    return nextState, reward, over, nextDirection


def ChangeDirection(new_direction):
    global direction
    if new_direction == 'left':
        if direction != 'right':
            direction = new_direction

    elif new_direction == 'right':
        if direction != 'left':
            direction = new_direction

    elif new_direction == 'up':
        if direction != 'down':
            direction = new_direction

    elif new_direction == 'down':
        if direction != 'up':
            direction = new_direction


def CheckCollisions(snake, bombs):
    x, y = snake.coordinates[0]

    if x < 0 or x >= GAME_WIDTH:
        print("Game Over! Snake hit the wall.")
        return True
    elif y < 0 or y >= GAME_HEIGHT:
        print("Game Over! Snake hit the wall.")
        return True

    for body_part in snake.coordinates[1:]:
        if x == body_part[0] and y == body_part[1]:
            print("Game Over! Snake hit itself.")
            return True

    for bomb in bombs:
        if x == bomb.coordinates[0] and y == bomb.coordinates[1]:
            print("Game Over! Snake hit a bomb.")
            return True

    return False


# def GameOver():
#    canvas.delete(ALL)
#    canvas.create_text(canvas.winfo_width()/2,canvas.winfo_height()/2, font=('consolas',70), text="GAME OVER",fill="red", tags= "gameover")

# Function to handle Retry button
def restart_run():
    canvas.delete("all")  # Clear the canvas
    return restart_game()  # Call your game start logic


# Function to handle Close button
def close_game():
    window.destroy()  # Close the entire application


def GameOver():
    # Clear the canvas
    canvas.delete("all")


def distanceFunc(cordA, cordB):
    return math.sqrt((cordB[0] - cordA[0]) ** 2 + (cordB[1] - cordA[1]) ** 2)


def directionFunc(cordA, cordB):
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


def foodDirection(snake, food):
    snakeHead = snake.coordinates[0]
    foodCord = food.coordonates
    distance = distanceFunc(snakeHead, foodCord)
    directionDic = directionFunc(snakeHead, foodCord)
    directionString = ""
    maxDirection = -1
    for key, value in directionDic.items():
        if value > maxDirection:
            maxDirection = value
            directionString = key

    return distance, directionString


def bombDirection(snake, bombs):
    snakeHead = snake.coordinates[0]
    totalDistance = 0
    for bomb in bombs:
        totalDistance += distanceFunc(snakeHead, bomb.coordinates)

    averageDistance = totalDistance / max(len(bombs), 1)

    totalDirectionDic = {"left": 0, "right": 0, "up": 0, "down": 0}
    for bomb in bombs:
        direction = directionFunc(snakeHead, bomb.coordinates)
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


def wallsDirection(snake):
    snakeHead = snake.coordinates[0]
    wallDistanceRight = (GAME_COLUMNS - 1) - snakeHead[0]
    wallDistanceLeft = snakeHead[0]
    wallDistanceUp = snakeHead[1]
    wallDistanceDown = (GAME_ROWS - 1) - snakeHead[1]
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


def bodyDirection(snake):
    snakeHead = snake.coordinates[0]
    totalDistance = 0
    for snakeBody in snake.coordinates:
        totalDistance += distanceFunc(snakeHead, snakeBody)
    averageDistance = totalDistance / len(snake.coordinates)

    totalDirectionDic = {"left": 0, "right": 0, "up": 0, "down": 0}
    for snakeBody in snake.coordinates:
        direction = directionFunc(snakeHead, snakeBody)
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


def getNextDirectionState(snake, food, bombs):
    foodDistance, foodDirectionString = foodDirection(snake, food)
    bombDistance, bombDirectionString = bombDirection(snake, bombs)
    wallDistance, wallDirectionString = wallsDirection(snake)
    bodyDistance, bodyDirectionString = bodyDirection(snake)
    nextDirection = {"up": 0, "down": 0, "left": 0, "right": 0}
    nextDirection[foodDirectionString] += 20
    nextDirection[bombDirectionString] += 2
    nextDirection[wallDirectionString] += 1
    nextDirection[bodyDirectionString] += 10

    nextDirection["up"] /= 33
    nextDirection["down"] /= 33
    nextDirection["left"] /= 33
    nextDirection["right"] /= 33

    return nextDirection


def restart_game():
    global score
    global direction
    global label
    score = 0
    label.config(text="Score:{}".format(score))

    direction = 'down'
    state = {}
    state["currentDirection"] = direction
    state["snake"] = Snake()
    state["food"] = Food()
    state["bombs"] = []
    return state


def initGraphic():
    global window
    window = Tk()
    window.title("Snake game")
    window.resizable(False, FALSE)
    global label
    global canvas
    label = Label(window, text="Score:{}".format(score), font=('consolas', 40))
    label.pack()

    canvas = Canvas(window, bg=BACKGROUND_COLOR, height=GAME_HEIGHT, width=GAME_WIDTH)
    canvas.pack()

    window.update()
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    score_height = window.winfo_screenheight()

    x = int((screen_width / 2) - (window_width / 2))
    y = int((score_height / 2) - (score_height / 2))

    window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    # window.bind("<Left>", lambda event: ChangeDirection('left'))
    # window.bind("<Right>", lambda event: ChangeDirection('right'))
    # window.bind("<Up>", lambda event: ChangeDirection('up'))
    # window.bind("<Down>", lambda event: ChangeDirection('down'))

    # window.mainloop()


def main():
    initGraphic()
    run_simulator()
    window.mainloop()


main()
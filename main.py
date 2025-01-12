from tkinter import *
import random

GAME_WIDTH = 1500
GAME_HEIGHT = 700
SPEED = 100
SPACE_SIZE = 50
BODY_PARTS = 1
HEAD_COLOR = "#FFD700"
BODY_COLOR = "#00FF00"
TAIL_COLOR = "#8B0000"
FOOD_COLOR = "#FF0000"
BOMB_COLOR = "#FFFFFF"
BACKGROUND_COLOR = "#000000"


class Snake:
    def __init__(self):
        self.body_size = BODY_PARTS
        self.coordinates = []
        self.squares = []
        for i in range(0,BODY_PARTS):
            self.coordinates.append([0,0])

        for index,(x,y) in enumerate(self.coordinates):
            if index == 0:
                color = HEAD_COLOR
            else:
                color = BODY_COLOR
            square = canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=color, tag="snake")
            self.squares.append(square)


        # for x,y in self.coordinates:
        #     square = canvas.create_rectangle(x,y,x+SPACE_SIZE,y+SPACE_SIZE,fill=SNAKE_COLOR,tag="snake")
        #     self.squares.append(square)


class Food:
    def __init__(self):
        x = random.randint(0, (GAME_WIDTH // SPACE_SIZE) - 1) * SPACE_SIZE
        y = random.randint(0, (GAME_HEIGHT // SPACE_SIZE) - 1) * SPACE_SIZE
        self.coordonates = [x, y]
        canvas.create_oval(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=FOOD_COLOR, tag="food")


class Bomb:
    def __init__(self):
        x = random.randint(0,(GAME_WIDTH // SPACE_SIZE)-1) * SPACE_SIZE
        y = random.randint(0,(GAME_HEIGHT // SPACE_SIZE)-1) * SPACE_SIZE
        self.coordinates = [x,y]
        canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=BOMB_COLOR, tag="bomb")






def NextTurn(snake,food,bombs):
    x,y = snake.coordinates[0]

    if direction == "up":
        y -= SPACE_SIZE

    elif direction == "down":
        y += SPACE_SIZE

    elif direction == "left":
        x -= SPACE_SIZE

    elif direction == "right":
        x += SPACE_SIZE

    snake.coordinates.insert(0,(x,y))
    head_square = canvas.create_rectangle(x,y, x + SPACE_SIZE, y+SPACE_SIZE , fill=HEAD_COLOR,tags="snake")
    snake.squares.insert(0,head_square)


    if x == food.coordonates[0] and y == food.coordonates[1]:
        global score
        score += 1
        label.config(text="Score:{}".format(score))
        canvas.delete("food")
        food = Food()
        bombs.append(Bomb())

    else:
         tail_square = snake.squares[-1]
         canvas.itemconfig(tail_square, fill=TAIL_COLOR)
         del snake.coordinates[-1]
         del snake.squares[-1]
         canvas.delete(tail_square)

    for square in snake.squares[1:]:
        canvas.itemconfig(square,fill =BODY_COLOR)

    if CheckCollisions(snake,bombs):
        GameOver()
    else:
        window.after(SPEED, NextTurn, snake, food,bombs)


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




def CheckCollisions(snake,bombs):
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



def GameOver():
    canvas.delete(ALL)
    canvas.create_text(canvas.winfo_width()/2,canvas.winfo_height()/2, font=('consolas',70), text="GAME OVER",fill="red", tags= "gameover")



window = Tk()
window.title("Snake game")
window.resizable(False,FALSE)

score = 0
direction = 'down'

label = Label(window,text="Score:{}".format(score), font=('consolas',40))
label.pack()

canvas = Canvas(window,bg= BACKGROUND_COLOR,height=GAME_HEIGHT,width=GAME_WIDTH)
canvas.pack()

window.update()
window_width = window.winfo_width()
window_height = window.winfo_height()
screen_width = window.winfo_screenwidth()
score_height = window.winfo_screenheight()

x = int((screen_width/2) - ( window_width/2))
y = int((score_height/2) - ( score_height/2))

window.geometry(f"{window_width}x{window_height}+{x}+{y}")


window.bind("<Left>", lambda event: ChangeDirection('left'))
window.bind("<Right>", lambda event: ChangeDirection('right'))
window.bind("<Up>", lambda event: ChangeDirection('up'))
window.bind("<Down>", lambda event: ChangeDirection('down'))
snake = Snake()
food = Food()
bombs = []
NextTurn(snake,food,bombs)


window.mainloop()

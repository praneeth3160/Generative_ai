import turtle
import colorsys

screen = turtle.Screen()
screen.bgcolor("black")

t = turtle.Turtle()

screen.colormode(255)

for i in range(150):
    hue = (0.12 - i / 150 * 0.2) % 1
    r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)

    t.pencolor(int(r * 255), int(g * 255), int(b * 255))

    t.forward(i * 2.8)
    t.right(165)

turtle.done()
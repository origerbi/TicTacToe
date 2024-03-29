#!python3.9
import os
import socket
import sys
from tkinter import *
from tkinter.colorchooser import askcolor
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"  # hide the pygame support prompt
import pygame
import select

is_closing = False
def play_sound(sound):
    """
    Plays a sound file
    :param: sound: The sound to play.
    """
    pygame.mixer.init()  # initialise the pygame
    pygame.mixer.music.load(sound)
    pygame.mixer.music.play()


def set_sign(server, button):
    """
    Sets the sign of the button.
    :param: server: The server socket.
    :param: button: The button to set the sign of.
    """
    row = button.x - 1  # Row of the button
    column = button.y - 1
    sent_message = "SIGN " + str(row) + " " + str(column)
    server.send(sent_message.encode())


class CustomButton:
    def __init__(self, x, y, server, play_area):
        self.x = x
        self.y = y
        self.button = Button(play_area, text="", width=10, height=5, command=lambda: set_sign(server, self))


def play_again(server):
    """
    Sends a play again message to the server.
    :param server: The server socket.
    """
    server.send("RESET".encode())
    frame.destroy()


def choose_color():
    """
    Chooses the color of the X and O signs.
    """
    global x_color
    global o_color
    x_color = askcolor(title="Choose X color")
    if is_closing:
        return
    o_color = askcolor(title="Choose O color")
    frame.pack()


def decode_message(server, incoming_message):
    """
    Decodes the incoming message and performs the appropriate action.
    :param: server: The server socket.
    :param: incoming_message: The message to decode.
    """
    global is_closing
    global status_label
    global buttons
    global play_again_button
    global frame
    if incoming_message.startswith("CREATE"):
        starting_char = incoming_message.split(" ")[1]
        play_sound('sounds/create.wav')
        root.title(sys.argv[1] + " VS " + sys.argv[2])
        frame = Frame(root, width=500, height=500)
        Label(frame, text="Tic Tac Toe", font=('Ariel', 25)).pack()
        status_label = Label(frame, text=starting_char + " player turn", font=('Ariel', 15), bg='green', fg='snow')
        status_label.pack(fill=X)
        play_area = Frame(frame, width=300, height=300, bg='white')
        root.attributes("-topmost", True)
        play_area.pack(pady=10, padx=10, expand=True, fill=BOTH)
        buttons = []
        for i in range(1, 4):
            for j in range(1, 4):
                button = CustomButton(i, j, server, play_area)
                buttons.append(button)
                button.button.grid(row=i, column=j, sticky="NSEW")
                play_area.grid_columnconfigure(j, weight=1)
                play_area.grid_rowconfigure(i, weight=1)
        play_again_button = Button(frame, text="Play Again", command=lambda: play_again(server))
        server.send(("PLAYERS " + sys.argv[1] + " " + sys.argv[2]).encode())
        choose_color()
        root.mainloop()
    elif incoming_message.startswith("SET"):
        data = incoming_message.split(" ")
        buttons[(int(data[1]) - 1) * 3 + int(data[2]) - 1].button.configure(text=data[3], bg='snow', fg=x_color[1] if data[3] == "X" else o_color[1])
    elif incoming_message.startswith("TURN"):
        status_label.configure(text=incoming_message.split(" ")[1] + " player turn")
        play_sound('sounds/turn.wav')
    elif incoming_message.startswith("WIN"):
        status_label.configure(text=incoming_message.split(" ")[1] + " won the game!!")
        play_sound('sounds/victory.wav')
        play_again_button.pack()
    elif incoming_message == "DRAW":
        status_label.configure(text="DRAW you are both losers")
        play_sound('sounds/draw.wav')
        play_again_button.pack()
    elif incoming_message == "QUIT":
        s.send("CLOSE".encode())
        s.close()
        is_closing = True
        root.destroy()


def loop():
    read_list, _, _ = select.select([s], [], [], 0.03)
    root.after(10, loop)
    if len(read_list) == 0:
        return
    message = s.recv(1024)
    message = message.decode()
    messages = message.split("#")
    for msg in messages:
        decode_message(s, msg)


# --- main ---
if __name__ == "__main__":
    host = '127.0.0.1'
    port = 8080
    try:
        s = socket.socket()
        s.connect((host, port))
        root = Tk()
        root.resizable(True, True)
        loop()
        s.send("CLOSE".encode())
        s.close()
    except:
        pass

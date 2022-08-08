#!python3.9

import socket
import sys
import tkinter as tk

import pygame
import select
def play_sound(sound):
    '''
    @param sound: The sound to play.
    Plays a sound file
    '''

    pygame.mixer.init()  # initialise the pygame
    pygame.mixer.music.load(sound)
    pygame.mixer.music.play()


def set_sign(server, button):
    row = button.x - 1  # Row of the button
    column = button.y - 1
    sent_message = "SIGN " + str(row) + " " + str(column)
    server.send(sent_message.encode())


class CustomButton:
    def __init__(self, x, y, server, play_area):
        self.x = x
        self.y = y
        self.button = tk.Button(play_area, text="", width=10, height=5, command=lambda: set_sign(server, self))


def decode_message(server, incoming_message):
    global status_label
    global buttons
    if incoming_message == "CREATE":
        play_sound('sounds/create.wav')
        root.title("Tic Tac Toe")
        tk.Label(root, text="Tic Tac Toe", font=('Ariel', 25)).pack()
        status_label = tk.Label(root, text="X player turn", font=('Ariel', 15), bg='green', fg='snow')
        status_label.pack(fill=tk.X)
        play_area = tk.Frame(root, width=300, height=300, bg='white')
        root.attributes("-topmost", True)
        play_area.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)
        buttons = []
        for i in range(1, 4):
            for j in range(1, 4):
                button = CustomButton(i, j, server, play_area)
                buttons.append(button)
                button.button.grid(row=i, column=j, sticky="NSEW")
                play_area.grid_columnconfigure(j, weight=1)
                play_area.grid_rowconfigure(i, weight=1)
        server.send(("PLAYERS " + sys.argv[1] + " " + sys.argv[2]).encode())
        root.mainloop()
    elif incoming_message.startswith("SET"):
        data = incoming_message.split(" ")
        buttons[(int(data[1]) - 1) * 3 + int(data[2]) - 1].button.configure(text=data[3], bg='snow', fg='black')
    elif incoming_message.startswith("TURN"):
        status_label.configure(text=incoming_message.split(" ")[1] + " player turn")
        play_sound('sounds/turn.wav')
    elif incoming_message.startswith("WIN"):
        status_label.configure(text=incoming_message.split(" ")[1] + " won the game!!")
        play_sound('sounds/victory.wav')
    elif incoming_message == "DRAW":
        status_label.configure(text="DRAW you are both losers")
        play_sound('sounds/draw.wav')


def loop():
    readList, a, b = select.select([s], [], [], 0.03)
    root.after(10, loop)
    if len(readList) == 0:
        return
    message = s.recv(1024)
    message = message.decode()
    messages = message.split("#")
    for msg in messages:
        decode_message(s, msg)


# --- main ---

host = '127.0.0.1'
port = 8080

s = socket.socket()
s.connect((host, port))
print("Connected to the server")
root = tk.Tk()
root.resizable(True, True)
loop()
s.send("CLOSE".encode())
s.close()
# def play_again():
#     current_chr = 'X'
#     for point in XO_points:
#         point.button.configure(state=tk.NORMAL)
#         point.reset()
#     status_label.configure(text="X's turn")
#     play_again_button.pack_forget()
#
#
# play_again_button = tk.Button(root, text='Play again', font=('Ariel', 15), command=play_again)
#
# status_label.configure(text="X won!")
#
#
# self.button.grid(row=row, column=col)
# self.button.configure(text=current_chr, bg='snow', fg='black')
#
# def disable_game():
#     for point in XO_points:
#         point.button.configure(state=tk.DISABLED)
#     play_again_button.pack()

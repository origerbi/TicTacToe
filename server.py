#!python3.9
import socket
import subprocess
import sys
import threading
import tkinter as tk
from collections import defaultdict

import select


class WinningPossibility:
    def __init__(self, x1, y1, x2, y2, x3, y3):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.x3 = x3
        self.y3 = y3

    def check(self, points):
        p1_satisfied = False
        p2_satisfied = False
        p3_satisfied = False
        for point in points:
            if point.x == self.x1 and point.y == self.y1:
                p1_satisfied = True
            elif point.x == self.x2 and point.y == self.y2:
                p2_satisfied = True
            elif point.x == self.x3 and point.y == self.y3:
                p3_satisfied = True
        return all([p1_satisfied, p2_satisfied, p3_satisfied])


winning_possibilities = [
    WinningPossibility(1, 1, 1, 2, 1, 3),
    WinningPossibility(2, 1, 2, 2, 2, 3),
    WinningPossibility(3, 1, 3, 2, 3, 3),
    WinningPossibility(1, 1, 2, 1, 3, 1),
    WinningPossibility(1, 2, 2, 2, 3, 2),
    WinningPossibility(1, 3, 2, 3, 3, 3),
    WinningPossibility(1, 1, 2, 2, 3, 3),
    WinningPossibility(3, 1, 2, 2, 1, 3)
]


class XOPoint:
    def __init__(self, row, col):
        self.x = row
        self.y = col
        self.value = None

    def set(self, game):
        '''
        Sets the value of the point to the current player's value
        '''

        if not self.value:
            self.value = game.charTurn
            if game.charTurn == "X":
                game.X_points.append(self)
                msg = "#SET " + str(self.x) + " " + str(self.y) + " X"
                game.connection.send(msg.encode())
                game.charTurn = "O"
                msg = "#TURN O"
                game.connection.send(msg.encode())
            elif game.charTurn == "O":
                game.O_points.append(self)
                msg = "#SET " + str(self.x) + " " + str(self.y) + " O"
                game.connection.send(msg.encode())
                game.charTurn = "X"
                msg = "#TURN X"
                game.connection.send(msg.encode())
            game.check_win()

    def reset(self, game):
        game.connectionO.send("#SET " + self.x + " " + self.y + " -")
        if self.value == "X":
            game.X_points.remove(self)
        elif self.value == "O":
            game.O_points.remove(self)
        self.value = None


class Game:

    def run_game(self):
        while True:
            message = self.connection.recv(1024)
            message = message.decode()
            if message.startswith("SIGN") and self.is_running:
                data = message.split(" ")
                self.XO_points[int(data[1]) * 3 + int(data[2])].set(self)
            if message.startswith("CLOSE"):
                self.is_running = False
                break
            if message.startswith("PLAYERS"):
                self.playerX = message.split(" ")[1]
                self.playerO = message.split(" ")[2]

    def __init__(self, conn):
        self.playerO = None
        self.playerX = None
        self.XO_points = []
        self.X_points = []
        self.O_points = []
        self.connection = conn
        self.charTurn = "X"
        self.is_running = True
        for x in range(1, 4):
            for y in range(1, 4):
                self.XO_points.append(XOPoint(x, y))
        message = "#CREATE"
        message = message.encode()
        self.connection.send(message)
        self.run_game()

    def check_win(self):
        '''
        Checks if there is a winner or draw
        '''

        for possibility in winning_possibilities:
            if possibility.check(self.X_points):
                msg = "#WIN X"
                self.connection.send(msg.encode())
                winning_clients[self.playerX] += 1
                self.is_running = False
                return
            elif possibility.check(self.O_points):
                msg = "#WIN O"
                self.connection.send(msg.encode())
                winning_clients[self.playerO] += 1
                self.is_running = False
                return
        if len(self.X_points) + len(self.O_points) == 9:
            msg = "#DRAW"
            self.connection.send(msg.encode())
            self.is_running = False


# --- functions ---

def handle_client(conn):
    print("[thread] starting")
    Game(conn)


def loop():
    root.after(100, loop)
    r, w, e = select.select([s], [], [], 0.01)
    if len(r) > 0:
        connection, address = s.accept()
        thread = threading.Thread(target=handle_client, args=(connection,))
        thread.start()
        all_threads.append(thread)

def start_client():
    text1 = textField_client1.get("1.0", "end-1c")
    text2 = textField_client2.get("1.0", "end-1c")
    if text1 and text2 and text1 != text2:
        subprocess.Popen([sys.executable, 'client.py'] + [text1, text2])
        textField_client1.delete("1.0", "end")
        textField_client2.delete("1.0", "end")
    print(winning_clients)


winning_clients = defaultdict(int)
# --- main ---

host = '0.0.0.0'
port = 8080

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
             1)  # solution for "[Error 89] Address already in use". Use before bind()
s.bind((host, port))
s.listen(1)

all_threads = []
root = tk.Tk()
root.title("Tic Tac Toe SERVER")
# Create text widget and specify size.
textField_client1 = tk.Text(root, height=2, width=25)
textField_client2 = tk.Text(root, height=2, width=25)
# Create label
l = tk.Label(root, text="Enter name of X player:")
l.config(font=("Courier", 14))
l.pack()
textField_client1.pack()
l = tk.Label(root, text="Enter name of O player:")
l.config(font=("Courier", 14))
l.pack()
textField_client2.pack()
start_client_button = tk.Button(root, width=10, height=3, text="Start client", command=start_client)
start_client_button.pack()
root.resizable(True, True)
root.after(10, loop)
root.mainloop()
for t in all_threads:
    t.join()
s.close()

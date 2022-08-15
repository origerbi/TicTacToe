import datetime
import socket
import subprocess
import sys
import threading
import time
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
        """
        checks if the points are in the winning possibility

        :param points: list of points
        :return: True if the points are in the winning possibility, False otherwise
        """

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


winning_clients = defaultdict(int)

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
        """
        :param row: row number of point in grid
        :param col: column number of point in grid
        """

        self.x = row
        self.y = col
        self.value = None

    def set(self, game):
        """
        Sets the value of the point to the current player's value and sends message to client to switch turns(if set a piece).
        """

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


class Game:

    def __init__(self, conn, number, label, button):
        """
        initializes the game and sends to client message of create, which tells the client to create it's GUI.
        :param conn: connection socket
        :param number: game's number
        :param label: label representing the game status in the GUI of the server
        :param button: button for force closing the game in the GUI of the server
        """

        self.playerO = None
        self.playerX = None
        self.winner = None
        self.XO_points = []
        self.X_points = []
        self.O_points = []
        self.date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.label = label
        self.button = button
        self.button.configure(command=self.force_close)
        self.game_number = number
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

    def run_game(self):
        time.sleep(0.1)
        while True:
            message = self.connection.recv(1024)
            message = message.decode()
            if message.startswith("SIGN") and self.is_running:
                data = message.split(" ")
                self.XO_points[int(data[1]) * 3 + int(data[2])].set(self)
            if message.startswith("CLOSE"):
                self.is_running = False
                if self.winner is None:
                    self.label.config(text=str(
                        self.game_number) + ". " + self.date + " PlayerX: " + self.playerX + " PlayerO: " + self.playerO + " Game closed by client")
                break
            if message.startswith("PLAYERS"):
                self.playerX = message.split(" ")[1]
                self.playerO = message.split(" ")[2]
                self.label.config(text=str(
                    self.game_number) + ". " + self.date + " PlayerX: " + self.playerX + " PlayerO: " + self.playerO + " STATUS: RUNNING")
        self.button.destroy()

    def force_close(self):
        """
        Closes the game and sends a message to the client to close the game
        """

        self.is_running = False
        message = "QUIT"
        self.label.config(text=str(
            self.game_number) + ". " + self.date + " PlayerX: " + self.playerX + " PlayerO: " + self.playerO + " Game closed by server")
        self.winner = "SERVER"
        self.button.destroy()
        message = message.encode()
        self.connection.send(message)

    def check_win(self):
        """
        Checks if there is a winner or draw.
        Send messages appropriately to the client and removes the force close button from the server gui.
        """

        for possibility in winning_possibilities:
            if possibility.check(self.X_points):
                msg = "#WIN X"
                self.connection.send(msg.encode())
                winning_clients[self.playerX] += 1
                self.winner = self.playerX
                self.label.config(text=str(
                    self.game_number) + ". " + self.date + " PlayerX: " + self.playerX + " PlayerO: " + self.playerO + " STATUS: WINNER -  " + self.winner)
                self.is_running = False
                self.button.destroy()
                return
            elif possibility.check(self.O_points):
                msg = "#WIN O"
                self.connection.send(msg.encode())
                winning_clients[self.playerO] += 1
                self.winner = self.playerO
                self.label.config(text=str(
                    self.game_number) + ". " + self.date + " PlayerX: " + self.playerX + " PlayerO: " + self.playerO + " STATUS: WINNER -  " + self.winner)
                self.is_running = False
                self.button.destroy()
                return
        if len(self.X_points) + len(self.O_points) == 9:
            msg = "#DRAW"
            self.connection.send(msg.encode())
            self.winner = "Draw"
            self.label.config(text=str(
                self.game_number) + ". " + self.date + " PlayerX: " + self.playerX + " PlayerO: " + self.playerO + " STATUS: DRAW")
            self.button.destroy()
            self.is_running = False


# --- functions ---

def handle_client(conn):
    """
    starts a new game for the client that connected to the server. it does it on a new thread. adds the option to force close the game.
    :param conn: the connection socket to the server
    """
    global client_num
    client_num += 1
    label = tk.Label(root, text="", font=("Helvetica", 12))
    label.pack()
    b = tk.Button(root, width=10, height=1, text="FORCE CLOSE")
    b.pack()
    Game(conn, client_num, label, b)


def loop():
    """
    Main loop for checking new clients that want to connect to the server.
    checks for new connections every 0.1 seconds and updates the leaderboard.
    """

    root.after(100, loop)
    read, _, _ = select.select([s], [], [], 0.01)
    if len(read) > 0:
        connection, address = s.accept()
        thread = threading.Thread(target=handle_client, args=(connection,))
        thread.start()
        all_threads.append(thread)
    # update leaderboard
    leaderboard_label.config(text="Leaderboard:")
    for client in dict(sorted(winning_clients.items(), key=lambda x: x[1], reverse=True)):
        leaderboard_label.config(text=leaderboard_label["text"] + "\n" + client + ": " + str(winning_clients[client]))


def start_client(text_field_client1, text_field_client2):
    """
    starts the client with the names specified in the text fields, confirms they are valid names beforehand.
    :param text_field_client1: text field of competitor 1 (player X)
    :param text_field_client2: text field of competitor 2 (player O)
    """

    text1 = text_field_client1.get("1.0", "end-1c")
    text2 = text_field_client2.get("1.0", "end-1c")
    if text1 and text2 and text1 != text2:
        subprocess.Popen([sys.executable, 'client.py'] + [text1, text2])
        text_field_client1.delete("1.0", "end")
        text_field_client2.delete("1.0", "end")


# initializing GUI of the server
def init_gui():
    """
    Initializes the GUI of the server
    """

    global root
    root = tk.Tk()
    root.title("Tic Tac Toe SERVER")
    # Create text fields for clients names
    text_field_client1 = tk.Text(root, height=2, width=25)
    text_field_client2 = tk.Text(root, height=2, width=25)
    # Create label
    l = tk.Label(root, text="Enter name of X player:")
    l.config(font=("Courier", 14))
    l.pack()
    text_field_client1.pack()
    l = tk.Label(root, text="Enter name of O player:")
    l.config(font=("Courier", 14))
    l.pack()
    text_field_client2.pack()
    start_client_button = tk.Button(root, width=10, height=3, text="Start client",
                                    command=lambda: start_client(text_field_client1, text_field_client2))
    start_client_button.pack()
    games_label = tk.Label(root, text="Games:")
    games_label.config(font=("Courier", 14))
    games_label.pack()
    global leaderboard_label
    leaderboard_label = tk.Label(root, text="Leaderboard", font=("Helvetica", 12))
    leaderboard_label.pack(side=tk.RIGHT)
    root.resizable(True, True)
    root.after(10, loop)
    root.mainloop()


# --- main ---

if __name__ == "__main__":
    host = '0.0.0.0'
    port = 8080
    client_num = 0
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
                 1)  # solution for "[Error 89] Address already in use". Use before bind()
    s.bind((host, port))
    s.listen(1)
    all_threads = []
    init_gui()
    for t in all_threads:
        t.join()
    s.close()

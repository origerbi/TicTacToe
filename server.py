#!python3.9

import datetime
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
from collections import defaultdict
import select


def read_winners():
    """
    Reads the winners.txt file and returns a dictionary with the winners and their number of wins.
    """

    winners = defaultdict(int)
    with open("winners.txt", "r") as file:
        if file.readline() == "":
            return winners
        for line in file:
            line = line.split(" ")
            winners[line[0]] = int(line[1])
    return winners

def write_winners(winners):
    """
    Writes the winners.txt file with the winners and their number of wins.
    :param: winners: the dictionary with the winners and their number of wins
    """

    with open("winners.txt", "w") as file:
        for winner in winners:
            file.write(winner + " " + str(winners[winner]) + "\n")

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
        checks if the points are in the winning possibility.

        :param: points: list of points.
        :return: True if the points are in the winning possibility, False otherwise.
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


winning_clients = read_winners()
games_list = []
root = tk.Tk()
closing = False
root.attributes("-topmost", True)
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
        :param: row: row number of point in grid
        :param: col: column number of point in grid
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

    def __init__(self, conn, number):
        """
        initializes the game and sends to client message of create, which tells the client to create its GUI.
        :param: conn: connection socket
        :param number: game's number
        """

        self.playerO = None
        self.playerX = None
        self.winner = None
        self.XO_points = []
        self.X_points = []
        self.O_points = []
        self.date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.label = ""
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
            if closing:
                self.connection.send("QUIT".encode())
            r, _, _ = select.select([self.connection], [], [], 0.1)
            if len(r) > 0:
                message = self.connection.recv(1024)
                message = message.decode()
                if message.startswith("SIGN") and self.is_running:
                    data = message.split(" ")
                    self.XO_points[int(data[1]) * 3 + int(data[2])].set(self)
                if message.startswith("CLOSE"):
                    self.is_running = False
                    if self.winner is None:
                        self.label = str(
                            self.game_number) + ". " + self.date + " PlayerX: " + self.playerX + " PlayerO: " + self.playerO + " Game closed by client"
                    break
                if message.startswith("PLAYERS"):
                    self.playerX = message.split(" ")[1]
                    self.playerO = message.split(" ")[2]
                    self.label = str(
                        self.game_number) + ". " + self.date + " PlayerX: " + self.playerX + " PlayerO: " + self.playerO + " STATUS: RUNNING"

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
                self.label = str(
                    self.game_number) + ". " + self.date + " PlayerX: " + self.playerX + " PlayerO: " + self.playerO + " STATUS: WINNER -  " + self.winner
                self.is_running = False
                return
            elif possibility.check(self.O_points):
                msg = "#WIN O"
                self.connection.send(msg.encode())
                winning_clients[self.playerO] += 1
                self.winner = self.playerO
                self.label = str(
                    self.game_number) + ". " + self.date + " PlayerX: " + self.playerX + " PlayerO: " + self.playerO + " STATUS: WINNER -  " + self.winner
                self.is_running = False
                return
        if len(self.X_points) + len(self.O_points) == 9:
            msg = "#DRAW"
            self.connection.send(msg.encode())
            self.winner = "Draw"
            self.label = str(
                self.game_number) + ". " + self.date + " PlayerX: " + self.playerX + " PlayerO: " + self.playerO + " STATUS: DRAW"
            self.is_running = False

def handle_client(conn):
    """
    starts a new game for the client that connected to the server. it does it on a new thread. adds the option to force close the game.
    :param: conn: the connection socket to the server
    """
    global client_num
    client_num += 1
    games_list.append(Game(conn, client_num))


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


def start_client(text_field_client1, text_field_client2):
    """
    starts the client with the names specified in the text fields, confirms they are valid names beforehand.
    :param: text_field_client1: text field of competitor 1 (player X)
    :param: text_field_client2: text field of competitor 2 (player O)
    """

    text1 = text_field_client1.get("1.0", "end-1c")
    text2 = text_field_client2.get("1.0", "end-1c")
    if text1 == text2:
        same_name_label = tk.Label(root, text="Names cannot be the same",bg='RED')
        same_name_label.pack()
        root.after(2000, lambda:  same_name_label.destroy())
    if text1 and text2 and text1 != text2:
        subprocess.Popen([sys.executable, 'client.py'] + [text1, text2])
        text_field_client1.delete("1.0", "end")
        text_field_client2.delete("1.0", "end")


def display_leaderboard(display_frame, list_box):
    '''
    displays the leaderboard in the list box.
    :param display_frame: the frame to display the leaderboard in
    :param list_box: the list box to display the leaderboard in'''
    try:
        display_frame.pack_info()
    except tk.TclError:
        display_frame.pack()
    list_box.delete(0, tk.END)
    list_box.insert(tk.END, "Leaderboard:")
    for key in dict(sorted(winning_clients.items(), reverse=True)):
        list_box.insert(tk.END, key + ": " + str(winning_clients[key]))


def display_games(display_frame, list_box):
    '''
    displays the games in the list box.
    :param display_frame: the frame to display the games in
    :param list_box: the list box to display the games in'''
    try:
        display_frame.pack_info()
    except tk.TclError:
        display_frame.pack()
    list_box.delete(0, tk.END)
    list_box.insert(tk.END, "Games:")
    for game in games_list:
        list_box.insert(tk.END, game.label)


def init_gui():
    """
    Initializes the GUI of the server
    """
    root.title("Tic Tac Toe SERVER")
    # Create text fields for clients names
    text_field_client1 = tk.Text(root, height=2, width=25)
    text_field_client2 = tk.Text(root, height=2, width=25)
    # Create label
    label_x = tk.Label(root, text="Enter name of X player:")
    label_x.config(font=("Courier", 14))
    label_x.pack()
    text_field_client1.pack()
    label_o = tk.Label(root, text="Enter name of O player:")
    label_o.config(font=("Courier", 14))
    label_o.pack()
    text_field_client2.pack()
    start_client_button = tk.Button(root, width=15, height=2, text="Start client",
                                    command=lambda: start_client(text_field_client1, text_field_client2))
    start_client_button.pack()
    display_frame = tk.Frame(root, width=800, height=400)
    scrollbar = tk.Scrollbar(display_frame)
    list_box = tk.Listbox(display_frame, yscrollcommand=scrollbar.set, width=80, height=20)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    list_box.pack(side=tk.LEFT, fill=tk.BOTH)
    display_leaderboard_button = tk.Button(root, width=15, height=2, text="Display leaderboard",
                                           command=lambda: display_leaderboard(display_frame, list_box))
    display_leaderboard_button.pack()
    display_games_button = tk.Button(root, width=15, height=2, text="Display games",
                                     command=lambda: display_games(display_frame, list_box))
    display_games_button.pack()
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
    closing = True
    for t in all_threads:
        t.join()
    s.close()
    write_winners(winning_clients)

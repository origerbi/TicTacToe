#!python3.9

import datetime
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
from collections import defaultdict
import select


def read_winners():
    """
    Reads the winners.txt file and returns a dictionary with the winners and their number of wins.
    """

    winners = defaultdict(int)
    with open("winners.txt", "r") as file:
        for line in file:
            if line == "":
                break
            line = line.split(" ")
            winners[line[0]] = int(line[1])
    return winners


def read_games():
    """
    Reads the games.txt file and returns a dictionary with the games and their winner.
    """
    global client_num
    with open("games.txt", "r") as file:
        line = file.readline()
        if line == "":
            client_num = 0
            return
        client_num = int(line)
        for line in file:
            old_games.append(line)


def write_winners(winners):
    """
    Writes the winners.txt file with the winners and their number of wins.
    :param: winners: the dictionary with the winners and their number of wins
    """

    with open("winners.txt", "w") as file:
        for winner in winners:
            file.write(winner + " " + str(winners[winner]) + "\n")


def write_games(games):
    """
    Writes the games.txt file with the games and their winner.
    :param games: the games and their winner
    """

    with open("games.txt", "w") as file:
        file.write(str(client_num) + "\n")
        for game in old_games:
            file.write(game)
        for game in games:
            file.write(game.label + "\n")


class WinningPossibility:
    """
    A basic class to represent a winning possibility of X and O.
    """
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
old_games = []
client_num = 0
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
    """
    A basic class to represent a cell in the grid.
    """
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
    """
    A class to represent a game session, contains all the logic of the game and the game's listener.
    """

    def __init__(self, conn, number, starting_player="X"):
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
        self.starting_player = starting_player
        self.charTurn = starting_player
        self.is_running = True
        for x in range(1, 4):
            for y in range(1, 4):
                self.XO_points.append(XOPoint(x, y))
        message = "#CREATE " + starting_player
        message = message.encode()
        self.connection.send(message)

    def run_game(self):
        """
        runs the game logic and listens to the client's messages.
        """
        global client_num
        time.sleep(0.1)
        while True:
            if closing:
                self.connection.send("QUIT".encode())
            r, _, _ = select.select([self.connection], [], [], 0.1)
            if len(r) > 0:
                try:
                    message = self.connection.recv(1024)
                    message = message.decode()
                except ConnectionAbortedError:
                    message = "CLOSE"
                if message.startswith("SIGN") and self.is_running:
                    data = message.split(" ")
                    self.XO_points[int(data[1]) * 3 + int(data[2])].set(self)
                if message.startswith("CLOSE"):
                    self.is_running = False
                    if self.winner is None:
                        self.label = str(
                            self.game_number) + "#" + self.date + "#" + self.playerX + "#" + self.playerO + "#Game closed by client"
                    break
                if message.startswith("PLAYERS"):
                    self.playerX = message.split(" ")[1]
                    self.playerO = message.split(" ")[2]
                    self.label = str(
                        self.game_number) + "#" + self.date + "#" + self.playerX + "#" + self.playerO + "#RUNNING"
                if message.startswith("RESET"):
                    client_num += 1
                    game = Game(self.connection, client_num, "O" if self.starting_player == "X" else "X")
                    games_list.append(game)
                    game.run_game()
                    break

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
                    self.game_number) + "#" + self.date + "#" + self.playerX + "#" + self.playerO + "#WINNER -  " + self.winner
                self.is_running = False
                return
            elif possibility.check(self.O_points):
                msg = "#WIN O"
                self.connection.send(msg.encode())
                winning_clients[self.playerO] += 1
                self.winner = self.playerO
                self.label = str(
                    self.game_number) + "#" + self.date + "#" + self.playerX + "#" + self.playerO + "#WINNER -  " + self.winner
                self.is_running = False
                return
        if len(self.X_points) + len(self.O_points) == 9:
            msg = "#DRAW"
            self.connection.send(msg.encode())
            self.winner = "Draw"
            self.label = str(
                self.game_number) + "#" + self.date + "#" + self.playerX + "#" + self.playerO + "#DRAW"
            self.is_running = False


def handle_client(conn):
    """
    starts a new game for the client that connected to the server. it does it on a new thread. adds the option to force close the game.
    :param: conn: the connection socket to the server
    """
    global client_num
    client_num += 1
    game = Game(conn, client_num)
    games_list.append(game)
    game.run_game()


def loop():
    """
    Main loop for checking new clients that want to connect to the server.
    checks for new connections every 0.1 seconds.
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
    global error_label
    error_label = tk.Label(root, text="", fg="red")
    text1 = text_field_client1.get("1.0", "end-1c")
    text2 = text_field_client2.get("1.0", "end-1c")
    if text1 == "" or text2 == "":
        error_label = tk.Label(root, text="Names cannot be the empty", bg='RED')
        error_label.pack()
    elif text1 == text2:
        error_label = tk.Label(root, text="Names cannot be the same", bg='RED')
        error_label.pack()
    else:
        error_label.destroy()
        subprocess.Popen([sys.executable, 'client.py'] + [text1, text2])

    text_field_client1.delete("1.0", "end")
    text_field_client2.delete("1.0", "end")


def display_leaderboard(display_frame, list_box):
    """
    displays the leaderboard in the list box.
    :param: display_frame: the frame to display the leaderboard in
    :param: list_box: the list box to display the leaderboard in
    """
    try:
        display_frame.pack_info()
    except tk.TclError:
        display_frame.pack()
    list_box.delete(*list_box.get_children())
    list_box["columns"] = "Wins"
    list_box.heading("#0", text="Player Name", anchor=tk.W)
    list_box.heading("Wins", text="Wins", anchor=tk.W)
    for key in dict(sorted(winning_clients.items(), reverse=False)).keys():
        list_box.insert(parent='', index='end', iid=key, text=key, values=(winning_clients[key]))


def display_games(display_frame, list_box):
    """
    displays the games in the list box.
    :param: display_frame: the frame to display the games in
    :param: list_box: the list box to display the games in
    """
    try:
        display_frame.pack_info()
    except tk.TclError:
        display_frame.pack()
    list_box.delete(*list_box.get_children())
    list_box["columns"] = ("Date", "PlayerX", "PlayerO", "Status")
    list_box.heading("#0", text="Game Number", anchor=tk.W)
    list_box.heading("Date", text="Date", anchor=tk.W)
    list_box.heading("PlayerX", text="PlayerX", anchor=tk.W)
    list_box.heading("PlayerO", text="PlayerO", anchor=tk.W)
    list_box.heading("Status", text="Status", anchor=tk.W)

    for game in old_games:
        strings = game.split("#")
        list_box.insert(parent='', index='end', iid=strings[0], text=strings[0], values=(strings[1], strings[2], strings[3], strings[4]))
    for game in games_list:
        strings = game.label.split("#")
        list_box.insert(parent='', index='end', iid=strings[0], text=strings[0], values=(strings[1], strings[2], strings[3], strings[4]))


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
    list_box = tk.ttk.Treeview(display_frame, yscrollcommand=scrollbar.set)
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
    read_games()
    host = '0.0.0.0'
    port = 8080
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # solution for "[Error 89] Address already in use". Use before bind()
    s.bind((host, port))
    s.listen(1)
    all_threads = []
    init_gui()
    closing = True
    for t in all_threads:
        t.join()
    s.close()
    write_winners(winning_clients)
    write_games(games_list)

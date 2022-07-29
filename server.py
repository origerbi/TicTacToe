import socket
import threading
import time
from subprocess import Popen

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

    def set(self, game, char):
        if not self.value and char == game.charTurn:
            self.value = char
            if char == "X":
                game.X_points.append(self)
                game.connectionO.send("SET " + self.x + " " + self.y + " X")
                game.connectionX.send("SET " + self.x + " " + self.y + " X")
                game.charTurn = "O"
                game.connectionX.send("TURN")
                game.connectionO.send("TURN")
            elif char == "O":
                game.O_points.append(self)
                game.connectionO.send("SET " + self.x + " " + self.y + " O")
                game.connectionX.send("SET " + self.x + " " + self.y + " O")
                game.charTurn = "X"
                game.connectionX.send("TURN")
                game.connectionO.send("TURN")
            game.check_win()

    def reset(self, game):
        game.connectionO.send("SET " + self.x + " " + self.y + " -")
        game.connectionX.send("SET " + self.x + " " + self.y + " -")
        if self.value == "X":
            game.X_points.remove(self)
        elif self.value == "O":
            game.O_points.remove(self)
        self.value = None


class Game:
    def __init__(self, conn_x, conn_o):
        # Popen(['python', 'client.py'])

        self.XO_points = []
        self.X_points = []
        self.O_points = []
        self.connectionX = conn_x
        self.connectionO = conn_o
        self.charTurn = "X"
        for x in range(1, 4):
            for y in range(1, 4):
                XOPoint(x, y)
        message = "CREATE X"
        message = message.encode()
        self.connectionX.send(message)
        message = "CREATE O"
        message = message.encode()
        self.connectionO.send(message)

    def check_win(self):
        for possibility in winning_possibilities:
            if possibility.check(self.X_points):
                self.connectionX.send("WIN")
                self.connectionO.send("LOSE")
                return
            elif possibility.check(self.O_points):
                self.connectionO.send("WIN")
                self.connectionX.send("LOSE")
                return
        if len(self.X_points) + len(self.O_points) == 9:
            self.connectionX.send("DRAW")
            self.connectionO.send("DRAW")


# --- functions ---

def handle_client(conn_x, conn_o):
    print("[thread] starting")
    Game(conn_x, conn_o)


# --- main ---

host = '0.0.0.0'
port = 8080

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
             1)  # solution for "[Error 89] Address already in use". Use before bind()
s.bind((host, port))
s.listen(1)

all_threads = []
try:
    while True:
        print("Waiting for client")
        connectionX, addressX = s.accept()
        print("Waiting for another client")
        connectionO, addressO = s.accept()
        t = threading.Thread(target=handle_client, args=(connectionX, connectionO))
        t.start()

        all_threads.append(t)
except KeyboardInterrupt:
    print("Stopped by Ctrl+C")
finally:
    if s:
        s.close()
    for t in all_threads:
        t.join()

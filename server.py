import socket
import threading


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
            if message.startswith("SIGN"):
                data = message.split(" ")
                self.XO_points[int(data[1])*3+int(data[2])].set(self)

    def __init__(self, conn):
        self.XO_points = []
        self.X_points = []
        self.O_points = []
        self.connection = conn
        self.charTurn = "X"
        for x in range(1, 4):
            for y in range(1, 4):
                self.XO_points.append(XOPoint(x, y))
        message = "#CREATE"
        message = message.encode()
        self.connection.send(message)
        self.run_game()

    def check_win(self):
        for possibility in winning_possibilities:
            if possibility.check(self.X_points):
                msg = "#WIN X"
                self.connection.send(msg.encode())
                return
            elif possibility.check(self.O_points):
                msg = "#WIN O"
                self.connection.send(msg.encode())
                return
        if len(self.X_points) + len(self.O_points) == 9:
            msg = "#DRAW"
            self.connection.send(msg.encode())


# --- functions ---

def handle_client(conn):
    print("[thread] starting")
    Game(conn)


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
        connection, address = s.accept()
        t = threading.Thread(target=handle_client, args=(connection,))
        t.start()

        all_threads.append(t)
except KeyboardInterrupt:
    print("Stopped by Ctrl+C")
finally:
    if s:
        s.close()
    for t in all_threads:
        t.join()

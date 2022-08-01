import socket
import tkinter as tk
import sys

def setSign(server, button):
    row    = button.x      # Row of the button
    column = button.y
    message = "SIGN " + str(row) + str(column)
    server.send(message.encode())
    pass

class customButton:
    def __init__(self, x, y, server, play_area):
        self.x = x
        self.y = y
        self.button = tk.Button(play_area, text="", width=10, height=5, command=lambda :setSign(server, self))

def decode_message(server):
    if message == "CREATE":
        global status_label
        global buttons
        root.title("Tic Tac Toe")
        tk.Label(root, text="Tic Tac Toe", font=('Ariel', 25)).pack()
        status_label = tk.Label(root, text="X player turn", font=('Ariel', 15), bg='green', fg='snow')
        status_label.pack(fill=tk.X)
        play_area = tk.Frame(root, width=300, height=300, bg='white')
        root.attributes("-topmost", True)
        play_area.pack(pady=10, padx=10)
        buttons = []
        for i in range(1,4):
            for j in range(1,4):
                button = customButton(i,j, server, play_area)
                buttons.append(button)
                button.button.grid(row=i, column=j)
        root.mainloop()


# --- main ---

host = '127.0.0.1'
port = 8080

s = socket.socket()
s.connect((host, port))
print("Connected to the server")
root = tk.Tk()
root.resizable(False, False)
while True:
    message = s.recv(1024)
    message = message.decode()
    decode_message(s)
    if root.state != "normal":
        break
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


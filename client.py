import socket
import tkinter as tk
import sys

def setSign():
    pass
def decode_message():
    if message.startswith("CREATE"):
        global status_label
        global buttons
        root.title("Tic Tac Toe")
        tk.Label(root, text="Tic Tac Toe", font=('Ariel', 25)).pack()
        strings = message.split(" ")
        messageTurn = ''
        if strings[1] == "X":
            status_label = tk.Label(root, text="Your turn", font=('Ariel', 15), bg='green', fg='snow')
        else:
            status_label = tk.Label(root, text="Enemy turn", font=('Ariel', 15), bg='green', fg='snow')
        status_label.pack(fill=tk.X)
        play_area = tk.Frame(root, width=300, height=300, bg='white')
        play_area.pack(pady=10, padx=10)
        buttons = []
        for i in range(1,4):
            for j in range(1,4):
                buttons.append(tk.Button(play_area, text="", width=10, height=5, command=setSign))
                buttons[(i-1)*3+(j-1)].grid(row=i, column=j)
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
    decode_message()
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


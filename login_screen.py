import tkinter as tk
from tkinter import messagebox

def build_login_screen(root, client, on_login_success):
    frame = tk.Frame(root)

    tk.Label(frame, text="User ID", font=("Helvetica", 12)).grid(row=0, column=0, padx=5, pady=5)
    tk.Label(frame, text="Password", font=("Helvetica", 12)).grid(row=1, column=0, padx=5, pady=5)

    entry_id = tk.Entry(frame, font=("Helvetica", 12))
    entry_password = tk.Entry(frame, show="*", font=("Helvetica", 12))

    entry_id.grid(row=0, column=1, padx=5, pady=5)
    entry_password.grid(row=1, column=1, padx=5, pady=5)

    def attempt_login():
        user_id = entry_id.get()
        password = entry_password.get()

        login_message = f"LOGIN,{user_id},{password}"
        client.send(login_message.encode())
        response = client.recv(1024).decode()

        if response.startswith("LOGIN_SUCCESS"):
            worker_name = response.split(',')[1]
            on_login_success(worker_name)
        else:
            messagebox.showerror("Login", "Login failed!")

    tk.Button(frame, text="Login", command=attempt_login, font=("Helvetica", 12)).grid(row=2, columnspan=2, pady=10)

    return frame
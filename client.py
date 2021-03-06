import socket
import threading
import time
import tkinter
import tkinter.scrolledtext
from tkinter import simpledialog

# Server IP
HOST = '127.0.0.1'
# Server port
PORT = 9090
# Text color options
COLORS = ['Black', 'Blue', 'Yellow', 'Purple', 'Orange', 'Brown', 'Cyan']


class User:

    def __init__(self, host, port):
        # Client's connection socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to server
        self.socket.connect((host, port))

        # Username
        self.username = None
        # Check to determine if username is valid (not taken by another)

        # Connected users
        self.connected_users = []
        # User to privately chat with
        self.selected_user = None

        # Establish chat window
        self.chat_window = tkinter.Tk()
        self.chat_window.title('Simple Chat App')
        self.chat_window.configure(bg='lightgray')
        # When user closes window, call exit() to end the thread
        self.chat_window.protocol('WM_DELETE_WINDOW', self.exit)
        self.chat_window.withdraw()

        # Tkinter frame for GUI object positioning
        self.frame = tkinter.Frame(self.chat_window)
        self.frame.grid(row=0, column=0)

        # Establish input area and chat log
        self.input_area = tkinter.Text(self.frame, height=2)
        self.chat_log = tkinter.scrolledtext.ScrolledText(self.frame)
        # Disable text box so user cannot alter chat output display
        self.chat_log.config(state='disabled', bg='lightgray')
        # Tags for special colored messages
        self.chat_log.tag_config('new_user', foreground='green')
        self.chat_log.tag_config('user_disconnect', foreground='red')

        # Create list of connected users
        self.users_list = tkinter.scrolledtext.ScrolledText(self.frame, width=15, height=20)
        self.users_list.config(state='disabled')

        # Input label
        self.input_label = tkinter.Label(self.frame, text='Message')
        self.input_label.config(font=('Arial', 14))

        # Client's color selection
        self.color = tkinter.StringVar()
        self.color.set('Black')

        # Ask user to input a username and sets that input to this variable
        self.ask_for_username()

        # Flag to only run receive() loop if user should be receiving (user is connected to chat)
        self.receiving = True

        # Open client to receiving messages
        self.handle_incoming_messages()

    def select_user(self, event):
        print('Selecting user')
        # get the index of the mouse click
        index = self.users_list.index("@%s,%s" % (event.x, event.y))

        # Check each username to see if user selected it
        for username in self.connected_users:
            tag_indices = list(self.users_list.tag_ranges(username))

            # Iterate through
            for start, end in zip(tag_indices[0::2], tag_indices[1::2]):
                # Check if username found in mouse click
                if self.users_list.compare(start, '<=', index) and self.users_list.compare(index, '<', end):
                    # Gets user's selection
                    selection = self.users_list.get(start, end)
                    user = ''
                    # Remove newline characters from selection
                    for char in selection:
                        if char == "\n":
                            break
                        user += char
                    # Select user if user not selected, else deselect
                    self.selected_user = user if self.selected_user != user else None
                    # If user selecting, change background to indicate selection
                    if self.selected_user is not None:
                        self.users_list.tag_config(user, background='lightgray')
                        self.input_label.config(text=f'Message (To {user})')
                    # Deselecting, revert components
                    else:
                        self.users_list.tag_config(user, background='white')
                        self.input_label.config(text='Message')

    def ask_for_username(self, message=None):
        """
        Displays a dialog window asking for the user to input a username.
        :param message: the message to display to the user
        :return:
        """
        if message is None:
            message = 'Please enter a username.'
        self.username = simpledialog.askstring('Username', f'Welcome to Chat App!\n{message}',
                                               parent=self.chat_window)
        # User presses 'OK' without entering anything, ask again
        if self.username == '':
            self.ask_for_username()
        # Retry with new username
        if message == 'Invalid username, try again.':
            self.socket.send(self.username.encode('utf-8'))

    def access_chat(self):
        """
        Begins the process of receiving chat messages and displays the chat window.
        :return:
        """
        # Thread to handle receiving broadcasts from the server
        receive_thread = threading.Thread(target=self.handle_incoming_messages)

        # Begin thread to receive messages
        receive_thread.start()

        # Display chat window
        self.display_chat()

    def display_chat(self):
        """
        Displays the chat window.
        :return:
        """
        # Set chat window to be visible now that user has selected a username
        self.chat_window.deiconify()

        # Chat label
        chat_label = tkinter.Label(self.frame, text='Chat')
        chat_label.config(font=('Arial', 14))

        # Users label
        users_label = tkinter.Label(self.frame, text='Online Users\n(Click a user to message privately)')
        users_label.config(font=('Arial', 12))

        # 'Send' button
        send_button = tkinter.Button(self.frame, text='Send', command=self.send_message)
        send_button.config(font=('Arial', 11), width=10)

        # Color label
        color_label = tkinter.Label(self.frame, text='Your Text Color')
        color_label.config(font=('Arial', 12))

        # Function for updating user text color
        def send_color(color):
            self.socket.send(f'{self.username}_COLOR={color.lower()}'.encode('utf-8'))

        # Create text color selector
        color_selector = tkinter.OptionMenu(self.frame, self.color, command=send_color, *COLORS)

        # Set grids
        chat_label.grid(row=0, column=0)
        users_label.grid(row=0, column=1, padx=(0, 20))
        self.chat_log.grid(row=1, column=0, padx=20, pady=5)
        self.users_list.grid(row=1, column=1, padx=20)
        self.input_label.grid(row=2, column=0)
        self.input_area.grid(row=3, column=0, padx=10, pady=10)
        send_button.grid(row=3, column=1)
        color_label.grid(row=4, column=1, pady=(0, 10))
        color_selector.grid(row=5, column=1, pady=(0, 10))

        # Begin loop
        self.chat_window.mainloop()

    def handle_incoming_messages(self):
        """
        While the user is connected, looks for messages to handle from the server.
        :return:
        """
        # If user is connected, loop to check for messages to receive
        while self.receiving:
            # Check socket for incoming messages from server
            try:
                # Message received from server
                message = self.socket.recv(1024).decode('utf-8')
                print(f'CLIENT RECEIVING {message}')
                # If server is asking for user's username:
                if message == 'REQUEST_USERNAME':
                    self.socket.send(self.username.encode('utf-8'))
                # Username declared valid
                elif message == 'VALID_USERNAME':
                    self.access_chat()
                # Username declared invalid
                elif message == 'INVALID_USERNAME':
                    self.ask_for_username('Invalid username, try again.')
                # Message notifying user that they have connected to the chat successfully
                elif message == f'Connected to chat as {self.username}\n':
                    self.chat_log.config(state='normal')
                    self.chat_log.insert('end', message)
                # Server sending data regarding all connecting users
                elif 'CONNECTED_USERS: ' in message:
                    users = message[17:]
                    username = ''
                    self.users_list.config(state='normal')
                    # Empty current list
                    self.users_list.delete('0.0', 'end')
                    # Empty current list of connected users
                    self.connected_users = []
                    for char in users:
                        if char == ' ':
                            self.connected_users.append(username)
                            # Add user to list
                            if username == self.username:
                                username += ' (You)'
                            # Create unique tag to allow for selection and private messaging with user
                            self.users_list.tag_config(username)
                            self.users_list.tag_bind(username, '<Button-1>', self.select_user)
                            print(username)
                            self.users_list.insert('end', username + '\n\n', username)
                            username = ''
                        else:
                            username = username + char
                    self.users_list.config(state='disabled')
                # Else, receiving a message that needs to be colored (user joins, user leaves, user's sent message)
                else:
                    # Set state to normal to allow for chat log to be updated
                    self.chat_log.config(state='normal')
                    # Insert message with appropriate color
                    if 'has joined the chat.\n' in message:
                        color = 'green'
                    elif 'has left the chat.\n' in message:
                        color = 'red'
                    # Normal message w/ user's color attached
                    else:
                        color = ''
                        substring = 0
                        for char in message:
                            substring += 1
                            if char == '_':
                                break
                            else:
                                color = color + char
                        # Actual message
                        message = message[substring:]
                    # Insert message with coloring matching user's selection for themselves
                    self.chat_log.tag_config(color, foreground=color)
                    self.chat_log.insert('end', message, color)
                # Scroll to the end
                self.chat_log.yview('end')
                # Disable text box to prevent user entry
                self.chat_log.config(state='disabled')
            # Error occurring, break
            except InterruptedError:
                break
            except ConnectionAbortedError:
                break

    def send_message(self):
        """
        Sends a message to the server based on user's input.
        :return:
        """
        # Gets text input, removing final character (final character is by default a newline)
        message = self.input_area.get('0.0', 'end-1c')
        # If input not empty, send the message and delete the text from the entry box
        if len(message) > 0:
            if self.selected_user is not None:
                print(f"DIRECT MESSAGING WITH {self.selected_user}")
                message = f'CHAT_WITH_{self.selected_user} ' + message
            self.socket.send(message.encode('utf-8'))
            self.input_area.delete('0.0', 'end')

    def exit(self):
        """
        Exits the program.
        :return:
        """
        # No longer receiving broadcasts from server
        self.receiving = False
        # Destroy the chat window
        self.chat_window.destroy()
        # Close the connection
        self.socket.close()
        # Then exit the program
        exit(0)


if __name__ == '__main__':
    # Create User instance to initialize connection to server socket
    user = User(HOST, PORT)

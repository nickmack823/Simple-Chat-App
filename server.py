import socket
import threading
import time

# The host IP (default IPV4 address here)
HOST = '127.0.0.1'

# The port number
PORT = 9090

# This is the reference to the socket itself which is an endpoint in communication b/w programs
# AF_INET denotes ipv4, SOCK_STREAM denotes TCP connection type (connection-oriented, not connectionless server)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Binds the host name and port number to the socket
address = (HOST, PORT)
server.bind(address)

# Creates a queue for potential connections
server.listen()

# Lists to store clients and their respective usernames
clients = []
usernames = []
# Dictionary to store text colors for each user
colors = {}


def broadcast_message(message):
    """
    Broadcasts a message to all connected users.
    :param message: the message to broadcast
    :return:
    """
    # Broadcast message to each connected client
    for client in clients:
        client.send(message)


def handle_client(client):
    """
    Handles a user's sent message if user is available. Else, removes user and ends thread.
    :param client: the user to receive message from
    :return:
    """
    while True:
        # Get user's username
        i = clients.index(client)
        username = usernames[i]
        # Try to receive and broadcast a message from the user
        try:
            message = client.recv(1024).decode()
            # If user has selected a new color
            if f'{username}_COLOR=' in message:
                i = 0
                for char in message:
                    i += 1
                    if char == '=':
                        break
                # Change the appropriate key value to their selected color
                color = message[i:]
                colors[username] = color
            # If user sending a normal message
            else:
                # Get their color
                color = colors[username]
                # Send the message with their color
                broadcast_message(f'{color}_{username}: {message}\n'.encode('utf-8'))
        # If unable to handle user (user disconnects, crashes, etc.), remove user from list and close their connection
        except ConnectionResetError:
            # Remove the client
            remove_client(client)
            # Leave function (and thread)
            break


def receive_connections():
    """
    Receives and accepts connection requests from potential users.
    :return:
    """
    print('Server started and running.')
    while True:
        # Accepts connection request from a client and gets their socket (user) and address (address_
        client, client_address = server.accept()
        print(f'Connection from {client_address} accepted.')

        # Create thread to handle user login
        attempt_login_thread = threading.Thread(target=login, args=(client,))
        attempt_login_thread.start()


def login(client):
    """
    Handles user login attempts by looping in a separate thread until either a valid (unique) username is given or
    the user closes the login window.
    :param client: client to handle login for
    :return:
    """
    # Send the initial message to user to request the declaration of a username
    client.send('REQUEST_USERNAME'.encode('utf-8'))
    while True:
        # The user's username input
        username = client.recv(1024).decode('utf-8')

        # If user hits 'Cancel' on the popup asking for a username, continue
        if len(username) == 0:
            break

        # If username is already taken, request user to input a valid username
        if username in usernames:
            client.send('INVALID_USERNAME'.encode('utf-8'))
            continue
        # Username valid, continue on
        else:
            # Notify client of username validity
            client.send('VALID_USERNAME'.encode('utf-8'))
            time.sleep(1)

            # Add to lists and color dictionary
            usernames.append(username)
            clients.append(client)
            # Default text color here
            colors[username] = 'black'

            # Send out messages to the chat log notifying of user's joining
            client.send(f'Connected to chat as {username}\n'.encode('utf-8'))
            time.sleep(1)
            broadcast_message(f'{username} has joined the chat.\n'.encode('utf-8'))

            # Update user list
            update_user_list()

            # New thread for handling with the current user as an argument ('user,' treated as a tuple)
            thread = threading.Thread(target=handle_client, args=(client,))
            thread.start()

            print(f'Client username: {username}')
            break


def update_user_list():
    """
    Updates the list of connected users for clients.
    :return:
    """
    users = 'CONNECTED_USERS: '
    for user in usernames:
        users = users + user + ' '

    # TODO: Explore alternatives to 'sleeping' in order to prevent cluttered streams to client (for all time.sleep()
    #  occurrences)
    time.sleep(1)

    # Sends users list to clients
    broadcast_message(users.encode('utf-8'))


def remove_client(client):
    """
    Removes the given client from consideration.
    :param client: the client to remove
    :return:
    """
    # Close client connection
    client.close()
    # Remove client and username from their lists
    username = usernames[clients.index(client)]
    clients.remove(client)
    usernames.remove(username)
    # Update connected user list for clients
    update_user_list()

    # Notify users that someone has left
    broadcast_message(f'{username} has left the chat.\n'.encode('utf-8'))

if __name__ == '__main__':
    print('Starting chat app server...')
    receive_connections()

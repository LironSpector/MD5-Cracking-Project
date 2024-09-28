import socket
import json
import threading


# Constants
TARGET_HASH = 'EC9C0F7EDCC18A98B1F31853B1813301'
START_NUMBER = 0
END_NUMBER = 1 * 10 ** 10 - 1
BLOCK_SIZE_PER_CORE = 200000

# Global variables
lock = threading.Lock()
current_number = START_NUMBER
found = False
found_number = None

clients = []
assigned_work = {}


def register_client(conn, addr, message):
    """
    Registers a client by storing its connection and core count.

    Args:
        conn (socket.socket): The client's socket connection.
        addr (tuple): The client's address.
        message (dict): The registration message containing core count.
    """
    client_cores = message.get('cores', 1)  # Default to 1 if cores not provided
    with lock:
        clients.append({'conn': conn, 'cores': client_cores})
    print(f"Registered client {addr} with {client_cores} cores.")
    return client_cores


def assign_work(conn, client_cores):
    """
    Assigns a block of work to a client based on its core count.

    Args:
        conn (socket.socket): The client's socket connection.
        client_cores (int): Number of cores available on the client.

    Returns:
        dict: The work details if work is assigned, None otherwise.
    """
    global current_number
    with lock:
        # Remove any previous work assigned to this client
        if conn in assigned_work:
            assigned_work.pop(conn)

        if found:
            # If the target number has already been found, instruct the client to stop
            send_message(conn, {'type': 'stop'})
            return None

        block_size = BLOCK_SIZE_PER_CORE * client_cores
        start = current_number
        end = min(current_number + block_size - 1, END_NUMBER)

        if start > END_NUMBER:
            # No more work to assign
            send_message(conn, {'type': 'no_work'})
            return None

        current_number = end + 1
        work = {'start': start, 'end': end}
        assigned_work[conn] = work

    # Send the assigned work to the client
    work_message = {
        'type': 'work',
        'start': work['start'],
        'end': work['end'],
        'target_hash': TARGET_HASH
    }
    send_message(conn, work_message)
    return work


def handle_found(conn, message):
    """
    Handles the case when a client reports finding the target number.

    Args:
        conn (socket.socket): The client's socket connection.
        message (dict): The message containing the found number.
    """
    global found, found_number
    with lock:
        if conn in assigned_work:
            assigned_work.pop(conn)

        if not found:
            found = True
            found_number = message['number']
            print(f"Found number: {found_number}")

    # Notify all clients to stop processing
    notify_all_clients()


def handle_client(conn, addr):
    """
    Handles communication with a connected client.

    Args:
        conn (socket.socket): The socket connection to the client.
        addr (tuple): The address of the client.
    """
    global current_number, found
    print(f"Client {addr} connected.")
    buffer = ""
    client_cores = 1  # Default to 1 core if not specified
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break  # Client disconnected

            buffer += data
            while '\n' in buffer:
                message_str, buffer = buffer.split('\n', 1)
                try:
                    message = json.loads(message_str)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error from {addr}: {e}")
                    continue

                if message['type'] == 'register':
                    client_cores = register_client(conn, addr, message)

                elif message['type'] == 'request_work':
                    assign_work(conn, client_cores)

                elif message['type'] == 'found':
                    handle_found(conn, message)

    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        cleanup_client(conn, addr)


def cleanup_client(conn, addr):
    """
    Cleans up resources when a client disconnects.

    Args:
        conn (socket.socket): The client's socket connection.
        addr (tuple): The client's address.
    """
    with lock:
        if conn in assigned_work:
            work = assigned_work.pop(conn)
            # Reassign the start number to avoid lost work
        clients[:] = [c for c in clients if c['conn'] != conn]
    conn.close()
    print(f"Client {addr} disconnected.")


def notify_all_clients():
    """
    Notifies all connected clients to stop processing.
    """
    with lock:
        for client in clients:
            try:
                send_message(client['conn'], {'type': 'stop'})
            except Exception as e:
                print(f"Error notifying client: {e}")


def send_message(conn, message):
    """
    Sends a JSON message to a client over the socket connection.

    Args:
        conn (socket.socket): The socket connection to the client.
        message (dict): The message to send.
    """
    try:
        message_str = json.dumps(message) + '\n'
        conn.sendall(message_str.encode())
    except Exception as e:
        print(f"Error sending message: {e}")


def server_main(host='0.0.0.0', port=5000):
    """
    Main server function that accepts client connections and starts client handler threads.

    Args:
        host (str): The host IP address to bind the server socket to.
        port (int): The port number to bind the server socket to.
    """
    global found
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    server.settimeout(1.0)
    print(f"Server listening on {host}:{port}")

    try:
        while not found:
            try:
                conn, addr = server.accept()
                client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                client_thread.start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("Server shutting down due to KeyboardInterrupt.")
    finally:
        server.close()
        if found:
            print(f"Number {found_number} found. Shutting down server.")
        else:
            print("Server shutting down.")


if __name__ == "__main__":
    server_main()

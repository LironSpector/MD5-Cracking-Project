import socket
import hashlib
import multiprocessing
import os
import sys
import json


def worker(start, end, target_hash, result_queue):
    """
    Worker function that searches for the target hash within a given range.
    Computes MD5 hashes of numbers in the specified range and compares them with the target hash.
    If the target hash is found, puts the corresponding number into the result queue.

    Args:
        start (int): The start of the range to search.
        end (int): The end of the range to search.
        target_hash (str): The target MD5 hash to find.
        result_queue (multiprocessing.Queue): Queue to communicate the found number back to the main process.
    """
    for number in range(start, end + 1):
        num_str = f"{number:010d}"  # Format number as a 10-digit zero-padded string
        hash_result = hashlib.md5(num_str.encode()).hexdigest().upper()
        if hash_result == target_hash:
            result_queue.put(num_str)
            return


def send_message(conn, message):
    """
    Sends a JSON-encoded message over the socket connection.

    Args:
        conn (socket.socket): The socket connection to the server.
        message (dict): The message to send.
    """
    try:
        message_str = json.dumps(message) + '\n'
        conn.sendall(message_str.encode())
    except Exception as e:
        print(f"Error sending message: {e}")


def receive_message(conn):
    """
    Receives a JSON-encoded message from the socket connection.

    Args:
        conn (socket.socket): The socket connection to the server.

    Returns:
        dict: The decoded message, or None if an error occurs.
    """
    try:
        data = conn.recv(4096).decode()
        if not data:
            return None
        return json.loads(data)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None


def process_work(server_host, server_port, cores):
    """
    Main client function that connects to the server, requests work, and processes it.
    Utilizes multiple CPU cores by spawning worker processes.

    Args:
        server_host (str): The server's hostname or IP address.
        server_port (int): The server's port number.
        cores (int): Number of CPU cores to utilize.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_host, server_port))
        register_message = {'type': 'register', 'cores': cores}
        send_message(s, register_message)

        buffer = ""
        while True:
            # Request work from the server
            request_message = {'type': 'request_work', 'cores': cores}
            send_message(s, request_message)

            data = s.recv(4096).decode()
            if not data:
                break

            buffer += data
            while '\n' in buffer:
                message_str, buffer = buffer.split('\n', 1)
                try:
                    message = json.loads(message_str)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error from server: {e}")
                    continue

                if message['type'] == 'work':
                    # Received a block of work
                    start = message['start']
                    end = message['end']
                    target_hash = message.get('target_hash')
                    if not target_hash:
                        print("No target hash received.")
                        return

                    print(f"Received work: {start} - {end}")

                    total = end - start + 1
                    per_process = total // cores
                    processes_list = []
                    result_queue = multiprocessing.Queue()

                    # Start worker processes
                    for i in range(cores):
                        process_start = start + i * per_process
                        process_end = start + (i + 1) * per_process - 1 if i < cores - 1 else end
                        p = multiprocessing.Process(target=worker,
                                                    args=(process_start, process_end, target_hash, result_queue))
                        processes_list.append(p)
                        p.start()

                    found_number = None
                    while True:
                        try:
                            # Check if any worker found the number
                            found_number = result_queue.get_nowait()
                            break
                        except multiprocessing.queues.Empty:
                            # Exit loop if all processes have finished
                            if all(not p.is_alive() for p in processes_list):
                                break

                    # Terminate all worker processes
                    for p in processes_list:
                        p.terminate()

                    if found_number:
                        # Notify the server that the number was found
                        found_message = {'type': 'found', 'number': found_number}
                        send_message(s, found_message)
                        print(f"Found the number: {found_number}")
                        return

                elif message['type'] == 'stop':
                    # Server instructs to stop processing
                    print("Received stop signal from server.")
                    return

                elif message['type'] == 'no_work':
                    # No more work available from the server
                    print("No more work available. Exiting.")
                    return


def get_cpu_cores():
    """
    Returns the number of CPU cores available on the system.

    Returns:
        int: Number of CPU cores.
    """
    return os.cpu_count()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client.py [server_host] [server_port]")
        sys.exit(1)

    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    cores = get_cpu_cores()
    process_work(server_host, server_port, cores)

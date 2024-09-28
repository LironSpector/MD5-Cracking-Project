
# Distributed Hash Brute-Force Solver

## Project Overview

This project implements a **Distributed Hash Brute-Force Solver** using Python's `socket` and `multiprocessing` modules. The system is designed in a **server-client** architecture to collaboratively find a 10-digit number that generates a specified MD5 hash. The server distributes work to multiple clients connected over a network, each leveraging their multi-core CPU capabilities for efficient and parallel processing. The design also allows dynamic client registration and robust handling of work allocation, ensuring that computational resources are utilized effectively.

### Key Features

- **Distributed Computing**: The server divides the brute-force workload among multiple clients.
- **Multi-core Utilization**: Clients use all available CPU cores for processing to maximize efficiency.
- **Dynamic Work Allocation**: The server dynamically assigns number ranges to clients based on their processing capabilities.
- **Robust Communication**: Communication between server and clients is managed using sockets, with JSON-encoded messages for simplicity and clarity.
- **Scalability**: Designed to handle multiple clients connecting and processing data concurrently.

## Table of Contents
- [Requirements](#requirements)
- [Setup and Installation](#setup-and-installation)
- [Running the Server](#running-the-server)
- [Running the Client](#running-the-client)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

## Requirements

To run this project, ensure you have the following installed on your system:
- Python 3.6+
- Required Python modules: `socket`, `json`, `hashlib`, `multiprocessing`, `threading`
- Network access for client-server communication

## Setup and Installation

1. Clone the repository to your local machine:
    ```bash
    git clone https://github.com/yourusername/distributed-hash-solver.git
    cd distributed-hash-solver
    ```

2. (Optional) It is recommended to use a virtual environment for this project. Create and activate a virtual environment:
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows: env\Scripts\activate
    ```

3. (Optional) Install any additional dependencies (if needed):
    ```bash
    pip install -r requirements.txt
    ```
    *Note*: A `requirements.txt` file can be generated if this project grows to include external modules in the future.

## Running the Server

1. To start the server, run the following command:
    ```bash
    python server.py
    ```
    By default, the server binds to `0.0.0.0` and port `5000`. This allows it to accept connections from any network interface.

2. If you wish to specify a different host or port, modify the `server_main` function within `server.py`.

3. **Server Output**: The server will print logs to the console as clients connect, register, and receive work. It will also display the number when found, stopping all further processing.

## Running the Client

1. Clients need to know the server's IP address and port to connect. To run a client, use the following command:
    ```bash
    python client.py [server_host] [server_port]
    ```
    Replace `[server_host]` with the IP address of the server (e.g., `127.0.0.1` for local testing) and `[server_port]` with the port number (e.g., `5000`).

2. The client will automatically detect the number of CPU cores on the system and use them to parallelize the processing workload.

3. **Client Output**: The client will log messages indicating the work range received from the server and display the number if it successfully finds the target hash.

## Project Structure

```plaintext
distributed-hash-solver/
│
├── server.py          # Main server script for managing client connections and distributing work.
├── client.py          # Main client script for connecting to the server and performing the hash computations.
├── README.md          # Documentation and project overview.
└── requirements.txt   # (Optional) List of dependencies for easy installation.
```

### Code Highlights

- **Server**:
  - Uses threading to handle multiple client connections concurrently.
  - Employs locks (`threading.Lock()`) to prevent race conditions when accessing shared resources like `current_number`.
  - Dynamically adjusts work allocation based on the number of cores each client has.
- **Client**:
  - Utilizes multiprocessing to leverage all available CPU cores on the host machine.
  - Manages communication with the server using JSON-encoded messages for clear and structured data transfer.

## Troubleshooting

- **Client Connection Issues**:
  - Ensure the client has network access to the server.
  - Verify that the server is running and is listening on the correct IP and port.
  - Check for firewall rules that might be blocking the connection.

- **Performance**:
  - Adjust `BLOCK_SIZE_PER_CORE` in `server.py` if work distribution seems inefficient. A smaller block size may be useful for testing, while a larger block size could enhance performance in a real distributed environment.
  
- **Exception Handling**:
  - Both server and client scripts contain exception handling to catch and log errors such as network interruptions or JSON parsing failures. Check the console output for specific error messages to aid in debugging.

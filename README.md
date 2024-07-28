# Thistle Server: Async REST and MQTT Server

Thistle Server is an asynchronous Python REST server with MQTT capabilities for handling communication between Arduino/ESP32 sensors and a React frontend. The server is designed to be highly resilient, structured for production settings, and scalable.

## Features

- Asynchronous REST API using FastAPI
- MQTT integration for sensor data communication
- Server-Sent Events (SSE) for real-time updates
- PostgreSQL database for data storage
- Message processing system
- Logging and error handling
- Configurable via environment variables

## Prerequisites

- Python 3.11+
- PostgreSQL
- MQTT Broker (e.g., Mosquitto)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/thistle_server.git
   cd thistle_server
   ```

2. Create a virtual environment and install dependencies:
   ```
   make setup
   ```

3. Copy the example environment file and edit it with your settings:
   ```
   cp .env.example .env
   nano .env
   ```

4. Set up the PostgreSQL database:
   ```
   createdb thistle_server
   ```

## Running the Server

To run the server in development mode:

```
make run
```

The server will be available at `http://localhost:8000`.

## API Documentation

Once the server is running, you can access the API documentation at `http://localhost:8000/docs`.

## Testing

To run the test suite:

```
make test
```

## Deployment

For production deployment, it's recommended to use a process manager like systemd. A sample systemd service file (`server.service`) is provided in the repository.

1. Copy the service file to the systemd directory:
   ```
   sudo cp server.service /etc/systemd/system/
   ```

2. Edit the service file to match your environment:
   ```
   sudo nano /etc/systemd/system/server.service
   ```

3. Start the service:
   ```
   sudo systemctl start thistle_server
   ```

4. Enable the service to start on boot:
   ```
   sudo systemctl enable thistle_server
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
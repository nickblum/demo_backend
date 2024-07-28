# Comprehensive Async REST and MQTT Server Project Document

## 1. Project Overview

Develop an asynchronous Python REST server with MQTT capabilities for handling communication between Arduino/ESP32 sensors and a React frontend. The server should be highly resilient, structured for production settings, and scalable.

## 2. Project Structure

```
project_root/
│
├── server/
│   ├── pipmodules/  # Virtual environment directory
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── mqtt_handler.py
│   ├── rest_handler.py
│   ├── sse_handler.py
│   ├── message_processor.py
│   ├── logger.py
│   └── utils.py
│
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   ├── test_mqtt_handler.py
│   ├── test_rest_handler.py
│   ├── test_sse_handler.py
│   ├── test_message_processor.py
│   └── test_logger.py
│
├── logs/
│   └── server.log
│
├── .env
├── .env.example
├── .gitignore
├── Makefile
├── requirements.txt
├── README.md
└── server.service
```

## 3. Core Technologies

- Language: Python 3.11+
- Web Framework: FastAPI
- ASGI Server: Uvicorn
- MQTT Client: Paho MQTT
- Database: PostgreSQL or SQLite (with raw SQL, no ORM)
- Testing: pytest
- Environment Management: python-dotenv, pydantic

## 4. Key Features and Requirements

### 4.1 MQTT Integration

- Handle MQTT connections using Paho MQTT
- Process incoming sensor data from Arduino/ESP32 devices
- Implement JSON format for MQTT packets
- One subscribe topic and one publish topic specified in .env file
- Store all incoming MQTT messages in the database
- Implement reconnection logic with exponential backoff for MQTT broker connection failures

### 4.2 Database Operations

- Use raw SQL queries (no ORM)
- Implement functions for database initialization and data insertion
- Store all incoming MQTT messages in the database
- Implement connection pooling for efficient database operations
- Handle database connection failures with appropriate retry logic

### 4.3 Message Processing

- Implement a message processor that runs at intervals specified in .env
- Query database for unprocessed messages
- Support manipulating and forwarding event information via SSE to the frontend
- Support triggering MQTT publishing based on processed messages
- Allow for running other scripts based on processed messages
- Mark processed messages in the database
- Implement error handling and logging for message processing failures

### 4.4 REST API

Implement the following endpoints:

1. POST /api/v1/packets
   - Submit a new packet
   - Validate against MQTT packet schema
   - Store in database and publish immediately
   - Return 201 Created on success with packet ID
   - Handle validation errors (400 Bad Request)

2. GET /api/v1/ping
   - Server health check
   - Return 200 OK with server status and timestamp

3. GET /api/v1/rereadenv
   - Re-read and apply updated environment variables
   - Return 200 OK on successful update
   - Handle and log any errors during update process

4. GET /api/v1/messages
   - Retrieve messages based on various criteria (recent, time window, key-value pair)
   - Support query parameters: limit, start_time, end_time, key, value
   - Return 200 OK with array of message objects and total count
   - Handle invalid query parameters (400 Bad Request)

- Implement rate limiting on all endpoints
- Use FastAPI for automatic request validation and API documentation

### 4.5 Server-Sent Events (SSE)

- Implement SSE for pushing updates to the frontend
- Create an endpoint for SSE connections
- Send events based on processed message criteria
- Handle connection failures and reconnections gracefully

### 4.6 Logging

- Implement rolling log system with a single log file: server.log
- Use Python's built-in logging module with RotatingFileHandler
- Configure log rotation based on file size and backup count
- Include log level, timestamp, log type, and relevant context in log messages
- Log all significant events (server lifecycle, MQTT activities, message processing, API interactions, SSE events)
- Log all errors and exceptions with tracebacks
- Allow configuration of log levels, file path, and rotation settings in .env file
- Ensure sensitive information is not logged in plain text

### 4.7 Configuration and Environment

- Use .env file for storing credentials and configuration
- Implement a config.py using Pydantic for type-safe configuration management
- Include configurations for server, database, MQTT, logging, and message processing
- Implement configuration validation on application startup

### 4.8 MQTT Packet Schema

- Design a JSON schema for MQTT packets
- Include fields for device_id, timestamp, measurements (e.g., temperature, humidity), status, and battery level
- Implement validation for incoming packets against this schema

### 4.9 Error Handling

- Implement robust error handling throughout the application
- Define and use consistent error codes for different types of failures
- Implement proper exception handling for all external interactions (database, MQTT, file operations)
- Return appropriate HTTP error codes for API failures
- Log all errors with sufficient context for debugging

### 4.10 Testing

- Implement a comprehensive pytest suite
- Achieve minimum 80% code coverage
- Include unit tests for all utility functions and helpers
- Implement integration tests for database operations
- Create API endpoint tests using FastAPI's TestClient
- Mock external services (MQTT broker) in tests
- Implement performance tests for message processing function

### 4.11 Deployment

- Target Environment: Fedora Linux
- Create a systemd service file (server.service) for automatic startup
- Provide step-by-step deployment instructions
- Include database setup and schema migration steps

### 4.12 Security Considerations

- Use HTTPS for all API communications
- Implement API key authentication for endpoints
- Use TLS for MQTT connections
- Store passwords and sensitive data as encrypted environment variables
- Implement rate limiting on API endpoints
- Regularly update dependencies and apply security patches

### 4.13 Performance and Scalability

- Design with scalability in mind for handling multiple sensors and clients
- Utilize asynchronous programming for improved performance
- Implement caching for frequently accessed data
- Design database schema with potential future sharding in mind
- Set performance targets:
  - API response time: < 100ms for 95% of requests
  - Message processing: Handle 1000 messages/minute
  - MQTT publish latency: < 500ms

### 4.14 Monitoring and Alerting

- Implement a health check endpoint
- Set up monitoring for server resources, API metrics, MQTT connection status, and message queue length
- Configure alerts for critical issues (server unresponsive, high error rate, processing backlog)

### 4.15 Documentation

- Maintain a comprehensive README.md
- Include inline comments and docstrings for key functions and classes
- Document API endpoints, including request/response formats and error codes
- Provide deployment and configuration guides

## 5. Implementation Guidelines

1. Follow PEP 8 style guide for Python code
2. Use type hints throughout the codebase
3. Implement proper exception handling and provide meaningful error messages
4. Write modular and reusable code, adhering to SOLID principles
5. Optimize database queries and MQTT message processing for performance
6. Ensure all sensitive information is stored securely
7. Implement proper connection management for MQTT and database
8. Use async and await keywords consistently for asynchronous operations
9. Implement a clean separation of concerns between different modules
10. Follow the specified logging format and use appropriate log levels
11. Adhere to the performance expectations and design with scalability in mind
12. Implement all security measures as described in the security considerations section

## 6. Development and Deployment Process

1. Set up the project structure and virtual environment
2. Implement the configuration management and validation system
3. Set up the database and create the specified schema
4. Develop the core MQTT functionality for handling sensor data
5. Implement the message processor with the specified interval-based execution
6. Develop REST API endpoints as specified
7. Implement SSE for pushing updates to the frontend
8. Implement the logging system as specified
9. Write comprehensive tests for all components
10. Implement monitoring and alerting mechanisms
11. Set up the systemd service for deployment on Fedora Linux
12. Conduct thorough testing, including performance and security testing
13. Prepare documentation including setup instructions and API documentation
14. Perform a code review to ensure all guidelines and best practices are followed
15. Conduct a final security audit before deployment

This comprehensive project document provides detailed specifications and guidelines for implementing the async REST and MQTT server project. It covers all aspects of the project, including structure, requirements, technologies, and implementation details. The requirements are explicit and clear, while allowing flexibility in the specific implementation approaches.

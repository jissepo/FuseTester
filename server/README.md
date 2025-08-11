# FuseTester HTTP Server

A lightweight Node.js HTTP server for receiving and storing fuse monitoring data from the FuseTester Python application.

## Features

- **Lightweight SQLite database** for data storage
- **RESTful API** with POST and GET endpoints
- **DateTime filtering** for data queries
- **Health check endpoint** for monitoring
- **Graceful shutdown** handling
- **CORS and security** middleware

## Installation

```bash
cd server
npm install
```

## Usage

### Development
```bash
npm run dev  # Uses nodemon for auto-restart
```

### Production
```bash
npm start
```

The server runs on port 3000 by default (or PORT environment variable).

## API Endpoints

### 1. Health Check
```http
GET /health
```

Returns server status and timestamp.

### 2. Data Ingestion (POST)
```http
POST /data
Content-Type: application/json

{
  "timestamp": "2025-08-10T12:00:00.000Z",
  "device_id": "fusetester-001",
  "readings": {
    "3": 12.45,
    "4": 11.92,
    "5": 12.01
  },
  "battery": 12.8,
  "system_info": {
    "memory_percent": 45.2,
    "cpu_temp": 42.3,
    "uptime_seconds": 86400
  }
}
```

**Response:**
```json
{
  "success": true,
  "reading_id": 123,
  "fuses_recorded": 3,
  "battery_voltage": 12.8
}
```

### 3. Data Query (GET)
```http
GET /data?start=2025-08-10T00:00:00Z&end=2025-08-10T23:59:59Z&device_id=fusetester-001
```

**Query Parameters:**
- `start` (optional): ISO datetime string for start filtering
- `end` (optional): ISO datetime string for end filtering  
- `device_id` (optional): Filter by specific device

**Response:**
```json
{
  "success": true,
  "count": 2,
  "query_params": {
    "start": "2025-08-10T00:00:00Z",
    "end": "2025-08-10T23:59:59Z"
  },
  "data": [
    {
      "id": 123,
      "timestamp": "2025-08-10T12:00:00.000Z",
      "device_id": "fusetester-001",
      "battery_voltage": 12.8,
      "created_at": "2025-08-10 12:00:01",
      "system_info": {
        "memory_percent": 45.2,
        "cpu_temp": 42.3,
        "uptime_seconds": 86400
      },
      "fuse_readings": {
        "3": 12.45,
        "4": 11.92,
        "5": 12.01
      }
    }
  ]
}
```

### 4. Statistics
```http
GET /stats
```

Returns database statistics including total readings, device count, battery averages, etc.

## Database Schema

The server uses SQLite with two main tables:

### `readings` table
- `id` - Primary key
- `timestamp` - Reading timestamp (from Python app)
- `device_id` - Device identifier
- `battery_voltage` - Battery voltage reading
- `created_at` - Server insertion timestamp
- `system_memory_percent` - Memory usage
- `system_cpu_temp` - CPU temperature
- `system_uptime_seconds` - System uptime

### `fuse_readings` table  
- `id` - Primary key
- `reading_id` - Foreign key to readings table
- `fuse_number` - Fuse number (3-64, excluding ground/battery)
- `voltage` - Fuse voltage reading

## Configuration

Environment variables:
- `PORT` - Server port (default: 3000)

## Python Client Integration

The server is designed to work with the FuseTester Python application. Update your `.env` file:

```bash
SERVER_URL=http://localhost:3000/data
API_KEY=optional-bearer-token
HTTP_TIMEOUT=10
MAX_BUFFER_SIZE=100
DEVICE_ID=fusetester-001
```

## Security

- Helmet middleware for basic security headers
- CORS enabled for cross-origin requests
- Input validation for required fields
- SQL injection protection via parameterized queries

## Database File

The SQLite database file (`fusetester.db`) is created automatically in the server directory.

## Monitoring

- Health check endpoint for uptime monitoring
- Console logging for all data operations
- Graceful shutdown on SIGINT
- Database connection status logging

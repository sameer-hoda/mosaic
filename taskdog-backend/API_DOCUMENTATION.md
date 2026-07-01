# TaskDog Backend API Documentation

## Overview

TaskDog is a task management UI that allows users to review AI-generated task nudges and either send them to task owners via WhatsApp or ignore them. The backend provides REST API endpoints for the frontend.

## API Base URL

```
http://localhost:3001/api/
```

All endpoints are prefixed with `/api/`.

## Authentication

Currently, the API does not require authentication. This can be enabled with JWT tokens by uncommenting the authentication headers in the frontend API calls.

## Endpoints

### 1. GET /api/tasks

Fetches the list of pending tasks that need review.

#### Request
```http
GET /api/tasks
Content-Type: application/json
```

#### Response

**Status: 200 OK**

```json
{
  "tasks": [
    {
      "id": 1,
      "index": 1,
      "chat_name": "Long tail daily reports",
      "title": "RuPay Slowdown & NPCI Delays",
      "urgency": "🔥9/10",
      "owner": "@Rakesh",
      "due_date": "Next business day 6 PM IST",
      "next_step": "Connect with the NPCI team directly after Wednesday for an update.",
      "nudge": "Rakesh, please connect with the NPCI team directly after Wednesday for an update on the RuPay progress.",
      "source": "2025-11-03 11:57:39+05:30",
      "confidence": 95
    }
  ],
  "stats": {
    "total_tasks": 25,
    "completed_tasks": 1,
    "remaining_tasks": 24
  }
}
```

### 2. POST /api/send

Sends a nudge message to the task owner via WhatsApp.

#### Request
```http
POST /api/send
Content-Type: application/json
```

**Body:**
```json
{
  "task_id": 1,
  "message": "Rakesh, please connect with the NPCI team...",
  "chat_name": "Long tail daily reports",
  "group_jid": "1234567890@g.us"
}
```

#### Response

**Status: 200 OK**
```json
{
  "ok": true
}
```

**Status: 400 Bad Request (if required fields missing)**
```json
{
  "ok": false,
  "error": "task_id and message are required"
}
```

**Status: 500 Internal Server Error (if WhatsApp bridge fails)**
```json
{
  "ok": false,
  "error": "Failed to send message: [error message]"
}
```

### 3. POST /api/ignore

Marks a task as ignored (user chose not to send the nudge).

#### Request
```http
POST /api/ignore
Content-Type: application/json
```

**Body:**
```json
{
  "task_id": 1
}
```

#### Response

**Status: 200 OK**
```json
{
  "ok": true
}
```

**Status: 400 Bad Request (if task_id missing)**
```json
{
  "ok": false,
  "error": "task_id is required"
}
```

### 4. GET /api/history

Gets task action history for the user.

#### Request
```http
GET /api/history
Content-Type: application/json
```

#### Response

**Status: 200 OK**
```json
{
  "history": [
    {
      "id": 1,
      "task_id": 5,
      "user_id": "default_user",
      "action": "send",
      "message": "Rahul, can you please investigate the significant drop...",
      "timestamp": "2025-11-09T18:30:00.123456"
    }
  ]
}
```

### 5. POST /api/login

Authenticates a user and returns a JWT token.

#### Request
```http
POST /api/login
Content-Type: application/json
```

**Body:**
```json
{
  "username": "admin",
  "password": "password"
}
```

#### Response

**Status: 200 OK**
```json
{
  "ok": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": 1,
  "username": "admin"
}
```

**Status: 401 Unauthorized (if credentials invalid)**
```json
{
  "ok": false,
  "error": "Invalid credentials"
}
```

### 6. POST /api/register

Registers a new user.

#### Request
```http
POST /api/register
Content-Type: application/json
```

**Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password"
}
```

#### Response

**Status: 200 OK**
```json
{
  "ok": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": 2,
  "username": "newuser"
}
```

## Data Models

### Task
```typescript
interface Task {
  id: number;           // Unique task identifier
  index: number;        // Display order (1-indexed)
  chat_name: string;    // WhatsApp group/chat name
  title: string;        // Task title/summary
  urgency: string;      // Urgency level (e.g., "🔥9/10")
  owner: string;        // Task owner (e.g., "@Rakesh")
  due_date: string;     // Deadline in human-readable format
  next_step: string;    // Suggested next action
  nudge: string;        // Pre-generated nudge message
  source: string;       // Timestamp or source reference
  confidence: number;   // AI confidence score (0-100)
}
```

### ApiResponse
```typescript
interface ApiResponse {
  ok: boolean;
  error?: string;
}
```

### TasksResponse
```typescript
interface TasksResponse {
  tasks: Task[];
  stats: {
    total_tasks: number;
    completed_tasks: number;
    remaining_tasks: number;
  };
}
```

## Frontend Integration

To connect the frontend to this API, update the `.env` file in the frontend directory:

```bash
VITE_API_URL=http://localhost:3001
```

The frontend will automatically use this API URL instead of the mock data when this environment variable is set.

## Database Schema

The backend uses SQLite with the following tables:

### tasks table
- id (INTEGER PRIMARY KEY)
- index_num (INTEGER)
- chat_name (TEXT)
- title (TEXT)
- urgency (TEXT)
- owner (TEXT)
- due_date (TEXT)
- next_step (TEXT)
- nudge (TEXT)
- source (TEXT)
- confidence (INTEGER)
- status (TEXT) - 'pending', 'sent', or 'ignored'
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

### task_history table
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- task_id (INTEGER)
- user_id (TEXT)
- action (TEXT) - 'send' or 'ignore'
- message (TEXT)
- timestamp (TIMESTAMP)

### users table
- id (INTEGER PRIMARY KEY AUTOINCREMENT)
- username (TEXT UNIQUE)
- email (TEXT UNIQUE)
- password_hash (TEXT)
- created_at (TIMESTAMP)
- last_login (TIMESTAMP)

## Error Handling

The API follows standard HTTP status codes:
- 200: Success
- 400: Bad Request (client error)
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

All error responses follow the format: `{ "ok": false, "error": "error message" }`

## Setup and Deployment

1. Install dependencies: `pip3 install -r requirements.txt`
2. Start the server: `python3 app.py`
3. The server will be available at `http://localhost:3001`

The backend is designed to work with the existing WhatsApp bridge running on port 5000.
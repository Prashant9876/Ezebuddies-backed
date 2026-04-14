# FastAPI Backend (EZeBuddies)

## API Base

Set one base URL and reuse all curls:

```bash
API_BASE="https://api.ezebuddies.com"
```

## Endpoints

- `GET /health`
- `POST /login`
- `GET /users/{user_id}/devices/data` (JWT required)
- `POST /planner` (JWT required)
- `GET /get_sinchai_planer` (JWT required)
- `POST /update_sinchai_planer` (JWT required)
- `POST /historical_data` (JWT required)
- `POST /change_relay_state` (JWT required)
- `POST /Estop` (JWT required)
- `POST /SOP_data` (JWT required)
- `POST /forgot-password`
- `GET /reset-password?token=...`
- `POST /reset-password`

## Full Curl Collection

### 1) Health

```bash
curl -X GET "$API_BASE/health"
```

### 2) Login

```bash
curl -X POST "$API_BASE/login" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "Prakash_farms",
    "password": "Pk@12345"
  }'
```

Sample success response:

```json
{
  "access_token": "<JWT_ACCESS_TOKEN>",
  "token_type": "bearer",
  "user_id": "Prakash_farms",
  "name": "Prashant Singh",
  "email": "prashantkumar74887@gmail.com",
  "solutions": [
    {
      "solution_name": "Vatavaran Monitor",
      "devices": [
        {
          "device_id": "IFTHC1180000001",
          "device_name": "Enviroment_Intel",
          "device_type": "Sensors",
          "is_active": true,
          "deployed_at": "room1"
        }
      ]
    }
  ]
}
```

### 3) Save token in shell variable

```bash
TOKEN=$(curl -sS -X POST "$API_BASE/login" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"Prakash_farms","password":"Pk@12345"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
echo "$TOKEN"
```

### 4) Get realtime device data

```bash
curl -X GET "$API_BASE/users/Prakash_farms/devices/data" \
  -H "Authorization: Bearer $TOKEN"
```

### 5) Planner API

`section` is the collection name inside `User_Data`.

```bash
curl -X POST "$API_BASE/planner" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "token_type": "bearer",
    "user_id": "Prakash_farms",
    "section": "user_vatavaran_planner"
  }'
```

### 5.1) Get sinchai planner

```bash
curl -G "$API_BASE/get_sinchai_planer" \
  -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "token_type=bearer" \
  --data-urlencode "user_id=Prakash_farms" \
  --data-urlencode "section=user_sinchai_planner"
```

Sample success response:

```json
{
  "user_id": "Prakash_farms",
  "farm_id": "1",
  "section": "user_sinchai_planner",
  "No_of_valves": 4,
  "mode": "Manual",
  "schedules": [
    {
      "schedule_no": 1,
      "schedule_name": "Morning Irrigation Updated",
      "start_time": "06:30",
      "irrigation_duration_min": 25,
      "valves": ["Valve 1", "Valve 2", "Valve 3"],
      "days": ["Mon", "Tue", "Wed", "Fri"],
      "enabled": true
    }
  ]
}
```

### 5.2) Update sinchai planner (update existing + add new schedules)

```bash
curl -X POST "$API_BASE/update_sinchai_planer" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": "Prakash_farms",
    "mode": "Auto",
    "No_of_valves": 4,
    "schedules": [
      {
        "schedule_no": 1,
        "schedule_name": "Morning Irrigation",
        "start_time": "06:00",
        "irrigation_duration_min": 20,
        "valves": ["Valve 1", "Valve 3"],
        "days": ["Mon", "Wed", "Fri"],
        "enabled": true,
        "ec_lower_limit": 1.2,
        "ec_upper_limit": 2.0,
        "ph_lower_limit": 5.8,
        "ph_upper_limit": 6.2
      },
      {
        "schedule_no": 3,
        "schedule_name": "Night Irrigation",
        "start_time": "22:00",
        "irrigation_duration_min": 10,
        "valves": ["Valve 4"],
        "days": ["Sun"],
        "enabled": false,
        "ec_lower_limit": 1.2,
        "ec_upper_limit": 2.0,
        "ph_lower_limit": 5.8,
        "ph_upper_limit": 6.2
      }
    ]
  }'
```

Sample success response:

```json
{
  "message": "Sinchai planner updated successfully",
  "user_id": "Prakash_farms",
  "section": "user_sinchai_planner",
  "mode": "Manual",
  "No_of_valves": 4,
  "schedules": [
    {
      "schedule_no": 1,
      "schedule_name": "Morning Irrigation",
      "start_time": "06:00",
      "irrigation_duration_min": 20,
      "valves": ["Valve 1", "Valve 3"],
      "days": ["Mon", "Wed", "Fri"],
      "enabled": true,
      "ec_lower_limit": 1.2,
      "ec_upper_limit": 2.0,
      "ph_lower_limit": 5.8,
      "ph_upper_limit": 6.2
    }
  ],
  "updated_count": 1,
  "added_count": 1
}
```

### 5.3) Historical data

```bash
curl -X POST "$API_BASE/historical_data" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": "Prakash_farms",
    "device_id": "IFTHC1180000001",
    "device_name": "Enviroment_Intel",
    "time_range": {
      "value": 1
    }
  }'
```

Sample success response:

```json
{
  "user_id": "Prakash_farms",
  "device_id": "IFTHC1180000001",
  "device_name": "Enviroment_Intel",
  "time_range_days": 1.0,
  "bucket_minutes": 60,
  "total_points": 25,
  "data": [
    {
      "timestamp": "2026-03-30T10:00:00+00:00",
      "payload": {
        "Humidity": 69.154,
        "Etemp": 31.115,
        "CO2": 83.077
      }
    }
  ]
}
```

### 6) Change relay state (MQTT publish)

Publishes to topic: `farm/Sub/{user_id}` with `CMD: "Act_State_Update"`.

```bash
curl -X POST "$API_BASE/change_relay_state" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": "Prakash_farms",
    "device_id": "IFFNC1180000001",
    "button_name": "fan1",
    "state": "on"
  }'
```

Sample success response:

```json
{
  "success": true,
  "message": "Relay state update published",
  "topic": "farm/Sub/Prakash_farms",
  "payload": {
    "CMD": "Act_State_Update",
    "user_id": "Prakash_farms",
    "device_id": "IFFNC1180000001",
    "button_name": "fan1",
    "state": "on"
  }
}
```

### 7) E-Stop (MQTT publish)

Publishes to topic: `farm/Sub/{user_id}` with `CMD: "E_Stop"`.

```bash
curl -X POST "$API_BASE/Estop" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": "Prakash_farms",
    "solution_name": "Vatavaran Monitor"
  }'
```

Sample success response:

```json
{
  "success": true,
  "message": "E-Stop command published",
  "topic": "farm/Sub/Prakash_farms",
  "payload": {
    "CMD": "E_Stop",
    "user_id": "Prakash_farms",
    "solution_name": "Vatavaran Monitor"
  }
}
```

### 8) Forgot password by user_id

```bash
curl -X POST "$API_BASE/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "ritesh_farms"
  }'
```

### 8.1) SOP data for one or more crops

Reads from `SOP_DB_NAME.SOP_COLLECTION_NAME` (default: `User_Data.Crop_SOP`).

```bash
curl -X POST "$API_BASE/SOP_data" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": "Prakash_farms",
    "crop_names": ["Capsicum", "Tomato", "Cucumber"]
  }'
```

### 9) Forgot password by email

```bash
curl -X POST "$API_BASE/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "prashantkumar74887@gmail.com"
  }'
```

### 10) Open reset page from token

```bash
curl -X GET "$API_BASE/reset-password?token=<RESET_TOKEN>"
```

### 11) Submit reset password form

```bash
curl -X POST "$API_BASE/reset-password" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "token=<RESET_TOKEN>" \
  --data-urlencode "new_password=NewPassword@123" \
  --data-urlencode "confirm_password=NewPassword@123"
```

## Environment variables (summary)

```bash
MONGO_URI=
APP_ENV=production

LOGIN_DB_NAME=User_Data
LOGIN_COLLECTION=user_login
REALTIME_DB_NAME=realtime_data
HISTORICAL_DB_NAME=IoT_datas
HISTORICAL_COLLECTION_NAME=Sensors

JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=86400
JWT_ISSUER=device-login-api
JWT_AUDIENCE=device-login-clients

RESET_PASSWORD_COLLECTION=reset_password
RESET_TOKEN_EXPIRY_MINUTES=15
PASSWORD_RESET_BASE_URL=https://api.ezebuddies.com

SMTP_HOST=smtp.hostinger.com
SMTP_PORT=465
SMTP_USERNAME=contact@ezebuddies.com
SMTP_PASSWORD=
SMTP_FROM_EMAIL=contact@ezebuddies.com
SMTP_USE_TLS=false
SMTP_USE_SSL=true

MQTT_HOST=broker.emqx.io
MQTT_PORT=1883
MQTT_USERNAME=EzeBuddies_device
MQTT_PASSWORD=EzeBuddies@2025
MQTT_CLIENT_ID=ezebuddies-backend
MQTT_KEEPALIVE=60
MQTT_QOS=1
```

## Notes

- Login response returns `solutions` (not `devices`) at top level.
- `/users/{user_id}/devices/data`, `/planner`, `/get_sinchai_planer`, `/update_sinchai_planer`, `/historical_data`, `/change_relay_state`, and `/Estop` require `Authorization: Bearer <token>`.
- For protected routes, `user_id` in payload/path must match JWT subject.




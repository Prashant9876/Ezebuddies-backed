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
- `POST /change_relay_state` (JWT required)
- `POST /Estop` (JWT required)
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
- `/users/{user_id}/devices/data`, `/planner`, `/change_relay_state`, and `/Estop` require `Authorization: Bearer <token>`.
- For protected routes, `user_id` in payload/path must match JWT subject.







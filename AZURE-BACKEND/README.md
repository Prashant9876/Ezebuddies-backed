# FastAPI JWT Login API + Azure App Service (Free Plan)

## Project structure

```text
app/
  api/routes/auth.py
  core/config.py
  core/security.py
  db/mongodb.py
  models/user.py
  schemas/auth.py
  services/auth_service.py
  main.py
```

## MongoDB user document format

This API expects documents like:

```json
{
  "_id": "user03",
  "user_id": "U1003",
  "name": "Amit Kumar",
  "email": "amit@example.com",
  "password_hash": "$2b$12$...",
  "devices": [
    {
      "device_id": "device_GHI012",
      "device_name": "Garage Sensor",
      "device_type": "Sensors",
      "is_active": true
    }
  ]
}
```

## API endpoints

- `GET /health`
- `POST /login`
- `GET /users/{user_id}/devices/data` (JWT protected)
- `POST /forgot-password`
- `GET /reset-password?token=...` (HTML form)
- `POST /reset-password` (HTML form submit)

Request body for `/login`:

```json
{
  "user_id": "U1003",
  "password": "plain-password"
}
```

Success response (`200`):

```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer",
  "user_id": "U1003",
  "name": "Amit Kumar",
  "email": "amit@example.com",
  "devices": [
    {
      "device_id": "device_GHI012",
      "device_name": "Garage Sensor",
      "device_type": "Sensors",
      "is_active": true
    },
    {
      "device_id": "device_JKL345",
      "device_name": "Garden Sensor",
      "device_type": "Actuators",
      "is_active": true
    }
  ]
}
```

If user ID/password is wrong, API returns `401`.

Forgot password request:

```bash
curl -X POST http://127.0.0.1:8000/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"user_id":"ritesh_farms"}'
```

or

```bash
curl -X POST http://127.0.0.1:8000/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"amit@example.com"}'
```

This sends a reset email from company SMTP (`contact@ezebuddies.com`) with a one-time token link valid for 15 minutes.

Fetch all device data for logged-in user:

```bash
curl -X GET http://127.0.0.1:8000/users/U1003/devices/data \
  -H "Authorization: Bearer <access_token>"
```

Example response:

```json
{
  "user_id": "U1003",
  "source_database": "realtime_data",
  "source_collection": "U1003",
  "total_records": 2,
  "records": [
    {
      "_id": "69baf863806559e5ccb145fb",
      "CO2": 802,
      "Device_Id": "IFTHC1180000001",
      "Etemp": 22.4,
      "Humidity": 86,
      "DN": "THC"
    },
    {
      "_id": "69baf863806559e5ccb145fc",
      "ac": "on",
      "fan5": "on",
      "DN": "AFC",
      "Device_Id": "IFFNC1180000001"
    }
  ]
}
```

## Local run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export MONGO_URI="<your-mongodb-connection-string>"
export APP_ENV="production"
export LOGIN_DB_NAME="User_Data"
export LOGIN_COLLECTION="user_login"
export JWT_SECRET_KEY="use-a-strong-secret"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRES_MINUTES="60"
export JWT_ISSUER="device-login-api"
export JWT_AUDIENCE="device-login-clients"
export REALTIME_DB_NAME="realtime_data"
export RESET_PASSWORD_COLLECTION="reset_password"
export RESET_TOKEN_EXPIRY_MINUTES="15"
export PASSWORD_RESET_BASE_URL="https://your-app.azurewebsites.net"
export DEVICE_DATA_FETCH_LIMIT="100"
export MONGO_SERVER_SELECTION_TIMEOUT_MS="5000"
export MONGO_CONNECT_TIMEOUT_MS="10000"
export MONGO_SOCKET_TIMEOUT_MS="10000"
export CORS_ALLOWED_ORIGINS="https://your-frontend.example.com"
export SMTP_HOST="smtp.your-provider.com"
export SMTP_PORT="587"
export SMTP_USERNAME="contact@ezebuddies.com"
export SMTP_PASSWORD="<smtp-password>"
export SMTP_FROM_EMAIL="contact@ezebuddies.com"
export SMTP_USE_TLS="true"
export BCRYPT_ROUNDS="10"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Test:

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U1003","password":"your-password"}'
```

## Deploy to Azure App Service Free (F1)

Prerequisites:
- Azure CLI login (`az login`)
- MongoDB URI (Atlas or other)

Create Azure resources:

```bash
RG_NAME="fastapi-free-rg"
LOCATION="centralindia"
PLAN_NAME="fastapi-free-plan"
APP_NAME="fastapi-login-<unique-name>"

az group create --name $RG_NAME --location $LOCATION
az appservice plan create --name $PLAN_NAME --resource-group $RG_NAME --sku F1 --is-linux
az webapp create --resource-group $RG_NAME --plan $PLAN_NAME --name $APP_NAME --runtime "PYTHON|3.12"
```

Configure startup command:

```bash
az webapp config set \
  --resource-group $RG_NAME \
  --name $APP_NAME \
  --startup-file "bash startup.sh"
```

Configure app settings:

```bash
az webapp config appsettings set \
  --resource-group $RG_NAME \
  --name $APP_NAME \
  --settings \
  MONGO_URI="<your-mongodb-connection-string>" \
  APP_ENV="production" \
  LOGIN_DB_NAME="User_Data" \
  LOGIN_COLLECTION="user_login" \
  JWT_SECRET_KEY="<strong-secret>" \
  JWT_ALGORITHM="HS256" \
  JWT_EXPIRES_MINUTES="60" \
  JWT_ISSUER="device-login-api" \
  JWT_AUDIENCE="device-login-clients" \
  REALTIME_DB_NAME="realtime_data" \
  RESET_PASSWORD_COLLECTION="reset_password" \
  RESET_TOKEN_EXPIRY_MINUTES="15" \
  PASSWORD_RESET_BASE_URL="https://$APP_NAME.azurewebsites.net" \
  DEVICE_DATA_FETCH_LIMIT="100" \
  MONGO_SERVER_SELECTION_TIMEOUT_MS="5000" \
  MONGO_CONNECT_TIMEOUT_MS="10000" \
  MONGO_SOCKET_TIMEOUT_MS="10000" \
  CORS_ALLOWED_ORIGINS="https://your-frontend.example.com" \
  SMTP_HOST="smtp.your-provider.com" \
  SMTP_PORT="587" \
  SMTP_USERNAME="contact@ezebuddies.com" \
  SMTP_PASSWORD="<smtp-password>" \
  SMTP_FROM_EMAIL="contact@ezebuddies.com" \
  SMTP_USE_TLS="true" \
  BCRYPT_ROUNDS="10"
```

Deploy code:

```bash
zip -r app.zip . -x ".venv/*" "__pycache__/*" ".git/*"
az webapp deployment source config-zip \
  --resource-group $RG_NAME \
  --name $APP_NAME \
  --src app.zip
```

Test after deploy:

```bash
curl https://$APP_NAME.azurewebsites.net/health
curl -X POST https://$APP_NAME.azurewebsites.net/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"U1003","password":"your-password"}'
curl -X GET https://$APP_NAME.azurewebsites.net/users/U1003/devices/data \
  -H "Authorization: Bearer <access_token>"
```

## Notes

- Free plan (`F1`) sleeps when idle, so first request can be slow.
- Store a real bcrypt hash in `password_hash`.
- Use a strong `JWT_SECRET_KEY`.
- Set `APP_ENV=production` on Azure; app will fail startup if using default JWT secret in production.
- Login API reads from `LOGIN_DB_NAME` and `LOGIN_COLLECTION`.
- Device data API reads from `REALTIME_DB_NAME`, with collection name equal to `user_id`.
- Reset tokens are stored in `User_Data.reset_password` and deleted after successful reset.








# 1) Login API
curl -X POST "https://fastapi-login-0319012745.azurewebsites.net/login" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"ritesh_farms","password":"alpha1212"}'
# 2) Devices Data API (replace <ACCESS_TOKEN> with token from login response)
curl -X GET "https://fastapi-login-0319012745.azurewebsites.net/users/ritesh_farms/devices/data" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

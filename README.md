# Strava Running Dashboard

A personal running dashboard that pulls activity data from Strava's API to provide customised analytics beyond what Strava offers natively. (Learning Project)

---

## Prerequisites

- Python 3.9+
- Java (required by Swagger Codegen to generate the API client)
- [Swagger Codegen CLI](https://github.com/swagger-api/swagger-codegen?tab=readme-ov-file#prerequisites) — download the JAR or install via Homebrew:
  ```bash
  brew install swagger-codegen
  ```

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd RunningDash
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate the Strava Swagger client

The Strava API client is generated from their official Swagger spec and is not included in the repository.

```bash
chmod +x setup_swagger.sh
./setup_swagger.sh
```

This will download the Strava Swagger spec, generate a Python client into `./swagger_client/`, and install it into your virtual environment.

### 5. Create a Strava API application

1. Go to [strava.com/settings/api](https://www.strava.com/settings/api)
2. Create a new application
3. Set the **Authorization Callback Domain** to `localhost`
4. Note your **Client ID** and **Client Secret**

### 6. Create a `.env` file

Create a `.env` file in the project root with the following keys:

```env
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_ACCESS_TOKEN=
STRAVA_REFRESH_TOKEN=
```

Leave `STRAVA_ACCESS_TOKEN` and `STRAVA_REFRESH_TOKEN` blank for now — they are filled in automatically during the OAuth flow below.

### 7. Initialise the database

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 8. Run the app

```bash
python app.py
```

### 9. Authorise with Strava (first run only)

Visit the following URL in your browser, replacing `YOUR_CLIENT_ID` with your value:

```
https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost:5000/exchange_token&scope=activity:read_all
```

Strava will redirect you back to the app, which will automatically save your access and refresh tokens to the `.env` file. Tokens are refreshed automatically on each sync after this.

### 10. Sync your activities

Visit [http://localhost:5000/sync_activities](http://localhost:5000/sync_activities) to pull your activities from Strava into the local database.

---

## Environment Variables

| Variable | Description |
|---|---|
| `STRAVA_CLIENT_ID` | Your Strava app's Client ID |
| `STRAVA_CLIENT_SECRET` | Your Strava app's Client Secret |
| `STRAVA_ACCESS_TOKEN` | OAuth access token (set automatically) |
| `STRAVA_REFRESH_TOKEN` | OAuth refresh token (set automatically) |

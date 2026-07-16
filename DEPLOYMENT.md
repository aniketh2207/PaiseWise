# PaiseWise Deployment & Build Guide

Follow these instructions to deploy the FastAPI backend and build a sideloadable Android APK for personal use.

---

## Step 1: Prepare and Deploy the Backend

The backend is built with FastAPI. You can host it on any cloud platform supporting Python/Procfile execution, such as **Railway** or **Render**.

### 1. Required Environment Variables

Configure the following environment variables in your cloud hosting dashboard (Railway/Render):

| Variable Name | Description | Example / Default |
|---|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string (Production database) | `postgresql://user:password@host/dbname` |
| `GEMINI_API_KEY` | Your Google Gemini API Key | `AIzaSy...` |
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token | `xoxb-...` |
| `SLACK_APP_TOKEN` | Slack App-Level Token (Socket Mode) | `xapp-...` |
| `GMAIL_TOKEN_JSON` | **Base64-encoded** content of `token.json` (See Step 2 below) | *(Base64 string)* |
| `PORT` | Dynamic port injected by the host platform | *(Handled automatically by Railway/Render)* |
| `UPLOADS_DIR` | Directory for statement uploads | `./uploads` |
| `REPORTS_DIR` | Directory for reports storage | `./reports` |

---

## Step 2: Headless Gmail OAuth Token Setup (`GMAIL_TOKEN_JSON`)

Because headless cloud servers cannot open a local browser window to run the interactive Gmail authorization flow, we must reuse your local authentication token.

1. Locate your locally generated `token.json` in the root of the project. If it doesn't exist, run the email sender or generator scripts once locally to authorize and create it.
2. Convert the contents of `token.json` to a Base64 string.
   - **On Windows (PowerShell):**
     ```powershell
     [Convert]::ToBase64String([System.IO.File]::ReadAllBytes("token.json"))
     ```
   - **On macOS/Linux (Terminal):**
     ```bash
     base64 -i token.json -o -
     ```
3. Copy the output base64 string and set it as the value of the `GMAIL_TOKEN_JSON` environment variable in your cloud platform's dashboard.
4. On backend startup, the server will decode this value and write it back to disk automatically.

---

## Step 3: Configure Frontend API Endpoint

Once your backend is successfully deployed, get its production URL (e.g. `https://paisewise-backend.up.railway.app`).

1. Open the file [frontend/src/constants/api.ts](file:///e:/paisewise/frontend/src/constants/api.ts).
2. Replace `"https://REPLACE_WITH_DEPLOYED_BACKEND_URL"` with your actual deployed backend URL:
   ```typescript
   export const API_BASE_URL = "https://paisewise-backend.up.railway.app";
   ```
3. Save the file.

---

## Step 4: Build the Sideloadable Android APK

The frontend is an Expo/React Native app. We use **EAS (Expo Application Services)** to compile it into a sideloadable APK file.

1. Open a terminal and navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Make sure you have the EAS CLI installed and you are logged into your Expo account:
   ```bash
   npm install -g eas-cli
   eas login
   ```
3. Run the EAS build command using the configured `preview` profile:
   ```bash
   eas build --platform android --profile preview
   ```
4. This command will output a QR code and a direct URL to download the `.apk` file once the cloud build completes.

---

## Step 5: Sideload the APK onto your Android Phone

1. Scan the QR code or visit the download URL provided by the EAS build output on your Android device to download the `.apk` file.
2. Locate the downloaded file in your device's downloads folder.
3. Open/install the `.apk` file.
4. If prompted with a warning about installing apps from unknown sources, choose **Settings**, toggle on **"Allow from this source"** (for Chrome/Files/etc.), then go back and tap **Install**.

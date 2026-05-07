# Quick Start: Google SSO Integration

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install Dependencies
Ensure your environment is set up:
```bash
pip install -r requirements.txt
```

### Step 2: Get Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable **Google+ API** and **Google Identity Toolkit API**.
4. Create **OAuth 2.0 Client ID** (Web application).
5. Add authorized redirect URIs:
   - Local testing: `http://localhost:8501`

### Step 3: Configure .env File

Update your `.env` file in the root directory with the credentials:

```env
GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-client-secret"
OAUTH_REDIRECT_URI="http://localhost:8501"
```

### Step 4: Run the Application

```bash
streamlit run main.py
```

### Step 5: Test Login

1. Navigate to `http://localhost:8501`
2. Click **"🔐 Login with Google"** button
3. Sign in with your allowed Google account
4. You're in! 🎉

## 📋 System Capabilities

### Architecture Updates:
- ✅ **Libraries:** Google OAuth integrations established.
- ✅ **UI Routing:** OAuth callback handling built into Streamlit flow.
- ✅ **Security:** Domain restrictions enforced at the application level.

### Authentication Features:
- ✅ **Dual-Auth:** Side-by-side login options (Password OR Google).
- ✅ **Domain Enforcement:** Restrict login to specific email domains (e.g., `@gmail.com` or corporate domains).
- ✅ **Dynamic RBAC:** Automatic provisioning of Admin rights based on SSO email verification.

## 🔐 Provisioning Google Users as Admins

To grant a user Admin capabilities (like uploading PDFs and retraining the vector database) via SSO, edit your `config.yaml` at the root level:

```yaml
google_oauth:
  enabled: true
  allowed_domain: "gmail.com"
  admin_google_users:
    - your.email@gmail.com
```

## 🎯 Important Security Notes

- Existing local hashed username/password logins function independently of SSO.
- Google SSO users are provisioned as regular users by default unless explicitly listed in `admin_google_users`.
- Ensure your `.env` file is never committed to version control.

## 🆘 Troubleshooting

**Issue:** "OAuth not configured" warning on the login page.
**Fix:** Ensure `GOOGLE_CLIENT_ID` is properly set in your `.env` file.

**Issue:** Authentication fails or loops.
**Fix:** Verify the `OAUTH_REDIRECT_URI` matches exactly between your Google Cloud Console and your `.env` file.

**Issue:** "Only allowed email addresses" error.
**Fix:** Check the `allowed_domain` parameter in `config.yaml` and ensure the testing email matches.
```
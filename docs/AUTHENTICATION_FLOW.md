
# Authentication Flow Diagrams

## 1. Google SSO Authentication Flow

```text
┌──────────────────────────────────────────────────────────────────────┐
│                     User Visits Chatbot                              │
│                  http://localhost:8501                               │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       Login Page                                     │
│  ┌─────────────────────┐    ┌──────────────────────┐                │
│  │ Username/Password   │    │  Google Sign-In      │                │
│  │                     │    │                      │                │
│  │ [Username]          │    │ Sign in with your    │                │
│  │ [Password]          │    │ @gmail.com account   │                │
│  │ [Login Button]      │    │                      │                │
│  │                     │    │ [🔐 Login with      │                │
│  └─────────────────────┘    │     Google]          │                │
│                             └──────────────────────┘                │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  Username/Password      │   │  Google SSO Selected    │
│  Login Selected         │   │                         │
└──────────┬──────────────┘   └──────────┬──────────────┘
           │                              │
           ▼                              ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  Validate Credentials   │   │ Generate OAuth URL      │
│  from config.yaml       │   │ with state parameter    │
└──────────┬──────────────┘   └──────────┬──────────────┘
           │                              │
           ▼                              ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│  Authentication         │   │  Redirect to Google     │
│  Success/Failure        │   │  Login Page             │
└──────────┬──────────────┘   └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  User Enters Google     │
           │                  │  Credentials            │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  Google Verifies        │
           │                  │  Credentials            │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  User Grants            │
           │                  │  Permissions            │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  Google Redirects Back  │
           │                  │  with Authorization     │
           │                  │  Code                   │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  Exchange Code for      │
           │                  │  ID Token               │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  Verify ID Token        │
           │                  │  & Extract Email        │
           │                  └──────────┬──────────────┘
           │                              │
           │                              ▼
           │                  ┌─────────────────────────┐
           │                  │  Check if Email         │
           │                  │  matches allowed        │
           │                  │  domain in config       │
           │                  └──────────┬──────────────┘
           │                              │
           │                    ┌─────────┴──────────┐
           │                    │                    │
           │                    ▼                    ▼
           │         ┌──────────────────┐  ┌──────────────────┐
           │         │  Email Valid     │  │  Email Invalid   │
           │         │  (e.g. gmail)    │  │  Reject & Show   │
           │         └────────┬─────────┘  │  Error Message   │
           │                  │            └──────────────────┘
           │                  ▼
           │         ┌──────────────────┐
           │         │  Check if Admin  │
           │         │  (config.yaml)   │
           │         └────────┬─────────┘
           │                  │
           └──────────────────┴──────────────────┐
                                                  │
                                                  ▼
                                    ┌───────────────────────┐
                                    │  Set Session State:   │
                                    │  - authenticated: True│
                                    │  - user_info          │
                                    │  - auth_method        │
                                    │  - is_admin           │
                                    └──────────┬────────────┘
                                               │
                                               ▼
                                    ┌───────────────────────┐
                                    │  Redirect to Main     │
                                    │  Chatbot Interface    │
                                    └───────────────────────┘
```

## 2. Session Management

```text
┌─────────────────────────────────────────────┐
│          Session State Variables            │
├─────────────────────────────────────────────┤
│  st.session_state.authenticated  = True/False│
│  st.session_state.user_info      = {        │
│      'name': 'User Name',                   │
│      'email': 'user@gmail.com'              │
│  }                                          │
│  st.session_state.auth_method    = 'google' │
│                                  or 'password'│
│  st.session_state.is_admin       = True/False│
│  st.session_state.chat_history   = [...]    │
│  st.session_state.messages       = [...]    │
└─────────────────────────────────────────────┘
```

## 3. Admin Role Assignment

```text
                    ┌─────────────────┐
                    │  User Logged In │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ Password Login   │      │  Google SSO      │
    └────────┬─────────┘      └────────┬─────────┘
             │                         │
             ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │ Check username   │      │ Check email in   │
    │ in admin_users   │      │ admin_google_    │
    │ list             │      │ users list       │
    └────────┬─────────┘      └────────┬─────────┘
             │                         │
             └────────────┬────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │  Set is_admin    │
                │  flag            │
                └────────┬─────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
            ▼                         ▼
    ┌──────────────┐          ┌──────────────┐
    │ is_admin =   │          │ is_admin =   │
    │ True         │          │ False        │
    └──────┬───────┘          └──────┬───────┘
           │                         │
           ▼                         ▼
    ┌──────────────┐          ┌──────────────┐
    │ Show Admin   │          │ Show User    │
    │ Role Toggle  │          │ Interface    │
    │ in Sidebar   │          │ Only         │
    └──────────────┘          └──────────────┘
```

## 4. File Organization

```text
rag-chatbot/
│
├── docs/                        # Setup documentation
│   ├── AUTHENTICATION_FLOW.md
│   └── QUICK_START_SSO.md
│
├── static/                      # Web UI Assets
│
├── main.py                      # Main Streamlit UI & Auth Logic
├── trainapp.py                  # Core AI Engine & RAG Pipeline
├── flaskapp.py                  # REST API Endpoints
│
├── config.yaml                  # Hashed credentials & Auth Settings
├── .env                         # API Keys (Ignored in Git)
├── requirements.txt             # Python Dependencies
└── .gitignore                   # Git exclusion rules
```

## 5. Security Layers

```text
┌─────────────────────────────────────────────────────┐
│              Layer 1: Network Level                 │
│  - HTTPS (Production)                               │
│  - Localhost binding for testing                    │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         Layer 2: Application Level                  │
│  - Session Management (Streamlit)                   │
│  - CORS Configuration (Flask)                       │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         Layer 3: Authentication                     │
│  - Werkzeug Cryptographic Password Hashing          │
│  - Google OAuth Token Verification                  │
│  - Domain Restriction                               │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         Layer 4: Authorization                      │
│  - Role-Based Access Control (RBAC)                 │
│  - Admin vs User Permissions                        │
│  - Feature-Level Access Control                     │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│         Layer 5: Data Protection                    │
│  - Environment Variables (.env)                     │
│  - API Key Management                               │
│  - No Plaintext Credentials in Code                 │
└─────────────────────────────────────────────────────┘
```
```

---

### **2. `QUICK_START_SSO.md`**

```markdown
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
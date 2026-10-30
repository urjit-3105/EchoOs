# 📖 ECHO WorkforceOS - REST API Reference

Base URL: `http://localhost:8000/api/v1`

---

## 🔑 Authentication (`/auth`)

### `POST /auth/register`
Creates a new user account and returns a Bearer access token.
- **Request Body**:
  ```json
  {
    "email": "user@echo-workforceos.com",
    "password": "Password123!",
    "full_name": "Jane Doe",
    "role": "admin"
  }
  ```
- **Response** (200 OK):
  ```json
  {
    "user": { "id": "u-1", "email": "user@echo-workforceos.com", "role": "admin" },
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

### `POST /auth/login`
Authenticates email + password credential and returns JWT access token.
- **Request Body**:
  ```json
  {
    "email": "admin@echo-workforceos.com",
    "password": "EchoDemo123!"
  }
  ```
- **Response** (200 OK): `TokenResponse`

### `POST /auth/magic-link`
Generates and dispatches a passwordless sign-in token to the requested email.

### `POST /auth/magic-link/verify`
Exchanges a magic link token for an authenticated user session.

### `GET /auth/me`
Returns the currently authenticated user profile based on Bearer token claims.

### `POST /auth/logout`
Stateless logout response instructing client to clear local storage token.

---

## 🏢 Organizations (`/organizations`)

### `GET /organizations/current`
Returns metadata and settings for the active tenant organization.

### `POST /organizations`
Initializes a new enterprise tenant organization.

### `PATCH /organizations/current`
Updates organization settings (branding, policies, rules).

---

## 👥 Employees (`/employees`)

### `GET /employees`
Lists all employees for the organization with optional filtering by status or department.

### `POST /employees`
Creates an employee record manually.

### `GET /employees/{id}`
Fetches employee profile details and onboarding compliance status.

### `PATCH /employees/{id}`
Updates employee status, department, manager, or profile fields.

### `GET /employees/stats`
Returns workforce telemetry (total employees, onboarding status counts, department breakdown).

---

## ✉️ Invitations (`/invitations`)

### `GET /invitations`
Lists pending and sent employee invitations.

### `POST /invitations`
Dispatches an onboarding invitation email and generates token + QR code.
- **Request Body**:
  ```json
  {
    "first_name": "Jordan",
    "last_name": "Lee",
    "email": "jordan.lee@example.com",
    "department": "Engineering",
    "job_title": "Staff Engineer",
    "role": "employee",
    "organization_id": "org-1"
  }
  ```

### `GET /invitations/{id}/qr`
Returns base64 data URL for the invitation's accept QR code.

### `POST /invitations/{id}/resend`
Resends invitation email and increments reminder counter.

---

## 🌐 Public Employee Portal (`/portal`)

*Public endpoints - authenticated by the unique invitation token in URL path.*

### `GET /portal/{token}`
Resolves invitation details, employee name, and organization branding.

### `POST /portal/{token}/profile`
Saves employee profile fields submitted during self-service onboarding.

### `GET /portal/{token}/documents`
Returns required document checklist for the employee's job role.

### `POST /portal/{token}/documents?document_type={type}`
Uploads passport, ID, or tax form document. Accepts multipart form file data.

### `POST /portal/{token}/accept-terms`
Records employee policy review and terms acceptance.

### `GET /portal/{token}/progress`
Returns live 5-stage onboarding progress bar data.

---

## ⚙️ Workflows & Agents (`/workflow` & `/agents`)

### `GET /workflow`
Lists active and past onboarding workflows across the workforce.

### `GET /workflow/{id}`
Returns full workflow details, active stage, and child task status graph.

### `POST /workflow/{id}/pause`
Pauses execution of a running workflow.

### `POST /workflow/{id}/resume`
Resumes execution of a paused workflow.

### `GET /agents`
Returns active AI Agent fleet status (Planner, Verification, Execution, Monitoring).

---

## 🔔 Notifications (`/notifications`)

### `GET /notifications`
Returns real-time alert and activity notifications for the user.

### `POST /notifications/{id}/read`
Marks a specific notification as read.

### `POST /notifications/read-all`
Marks all user notifications as read.

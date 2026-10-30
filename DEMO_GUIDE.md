# 🎬 ECHO WorkforceOS - Live Hackathon Demo Guide

Follow this step-by-step 3-minute script to demonstrate **ECHO WorkforceOS** live to hackathon judges or stakeholders.

---

## 🔑 Demo Credentials

- **Admin / HR Login**: `admin@echo-workforceos.com`
- **Password**: `EchoDemo123!`
- **Frontend App**: `http://localhost:3000`
- **Backend API Docs**: `http://localhost:8000/docs`

---

## 📜 3-Minute Live Hackathon Script

### Minute 1: The Executive View (Dashboard & Fleet)
1. **Login**: Navigate to `http://localhost:3000/login` and sign in with admin credentials.
2. **Dashboard**: Point out the live telemetry metrics:
   - Total Workforce Count
   - Active Onboarding Stages
   - Average Compliance Score (98.4%)
3. **AI Agent Fleet**: Click **AI Agent Fleet** (`/agents`). Highlight that 5 autonomous agents (Planner, Verification, Execution, Monitoring, Manager) are actively running in the background.

---

### Minute 2: HR Employee Invitation & Public Self-Service Portal
1. **Invite Employee**: Click **Invite Employee** (`/employees/invite`).
   - Enter Name: `Alex Morgan`
   - Email: `alex.morgan@demo.local`
   - Department: `Engineering`
   - Click **Send Invitation**.
2. **QR Code & Outbox**: Show the instantly generated QR code modal.
3. **Public Employee Portal**: Open a new browser tab to `http://localhost:3000/portal/{token}`.
   - Show branding & welcome screen.
   - Click **Accept Invitation & Review Terms**.
   - Fill out phone and emergency contact on the Profile Step.
   - On the Document Upload Step, upload a sample Passport PDF file.

---

### Minute 3: Autonomous Multi-Agent Execution & Self-Healing
1. **Multi-Agent Trigger**: Explain that submitting documents fires `EmployeeDocumentsSubmitted` on the EventBus.
2. **Planner Agent**: Planner Agent generates a 13-step DAG execution plan tailored for `Engineering`.
3. **Verification & Execution Agents**:
   - Verification Agent validates document authenticity.
   - Execution Agent executes tool plugins (dispatches email outbox, provisions Slack handle, creates Jira ticket).
4. **Realtime Update**: Return to the main HR Dashboard tab without refreshing. Point out that Alex Morgan's status has automatically updated to **ACTIVE** with notifications in the header bell feed.
5. **Self-Healing Simulation**: Show how temporary tool failures trigger `RetryManager` exponential backoff retries and human escalation notifications.

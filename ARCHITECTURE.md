# 📐 ECHO WorkforceOS - Architecture Documentation

This document provides a deep architectural walkthrough of **ECHO WorkforceOS**, covering the multi-agent framework, state management model, workflow execution pipeline, event bus, and database persistence layer.

---

## 1. High-Level Architecture

```mermaid
graph TB
    subgraph Client Layer
        FE[Next.js App Router]
        Portal[Employee Public Portal]
    end

    subgraph API & Control Layer
        FastAPI[FastAPI Gateway]
        Middleware[JWT / RBAC Middleware]
        Router[API Route Modules]
    end

    subgraph Service Layer
        AuthSvc[Auth Service]
        OnboardSvc[Onboarding Service]
        DocSvc[Document Service]
        NotifSvc[Notification Service]
    end

    subgraph Orchestrator & Multi-Agent Core
        Orchestration[Onboarding Orchestrator]
        Engine[Workflow Engine]
        RetryMgr[Retry & Escalation Manager]
        Planner[Planner Agent]
        Verifier[Verification Agent]
        Executor[Execution Agent]
        Monitor[Monitoring Agent]
    end

    subgraph Tool Plugins
        PluginRegistry[Tool Plugin Registry]
        Email[Email Plugin]
        Slack[Slack Plugin]
        Jira[Jira Plugin]
        Calendar[Calendar Plugin]
        Storage[Storage Plugin]
    end

    subgraph Persistence Layer
        DBAdapter{Database Adapter}
        SQLite[(SQLite Engine)]
        Supabase[(Supabase Client)]
    end

    FE -->|REST API| FastAPI
    Portal -->|Token REST API| FastAPI
    FastAPI --> Middleware
    Middleware --> Router
    Router --> Service Layer
    Service Layer --> Orchestration
    Orchestration --> Engine
    Engine --> Planner
    Engine --> Verifier
    Engine --> Executor
    Engine --> Monitor
    Executor --> PluginRegistry
    PluginRegistry --> Email
    PluginRegistry --> Slack
    PluginRegistry --> Jira
    PluginRegistry --> Calendar
    PluginRegistry --> Storage
    Service Layer --> DBAdapter
    Engine --> DBAdapter
    DBAdapter --> SQLite
    DBAdapter --> Supabase
```

---

## 2. Multi-Agent AI Framework

ECHO WorkforceOS implements a **Deterministic Multi-Agent State Machine**. Instead of relying solely on unconstrained LLM loops, agents operate over structured Pydantic state contracts (`ContextState`, `TaskState`, `ExecutionPlanState`, `VerificationReportState`).

```mermaid
sequenceDiagram
    autonumber
    participant Portal as Employee Portal
    participant EventBus as Async EventBus
    participant Orch as Onboarding Orchestrator
    participant Planner as Planner Agent
    participant Verifier as Verification Agent
    participant Executor as Execution Agent
    participant Monitor as Monitoring Agent

    Portal->>EventBus: Publish EmployeeDocumentsSubmitted
    EventBus->>Orch: Trigger start_for_employee(employee_id)
    Orch->>Planner: run(ContextState)
    Planner-->>Orch: Return ExecutionPlanState (DAG of 13 tasks)
    
    loop For each task tier in DAG
        Orch->>Verifier: evaluate(ContextState)
        Verifier-->>Orch: VerificationReportState (Passed / Info Required)
        
        alt Verification Passed
            Orch->>Executor: execute(TaskState)
            Executor->>Plugin: Dispatch to Email / Slack / Jira
            Plugin-->>Executor: Plugin Result
            Executor-->>Orch: Task Success
        else Transient Error / Failure
            Orch->>Monitor: handle_failure(TaskState)
            Monitor-->>Orch: Retry Action (Exponential Backoff)
        end
    end
    
    Orch->>EventBus: Publish WorkflowCompleted
    EventBus->>Portal: Employee Status -> ACTIVE
```

---

## 3. Workflow State Machine Diagram

```mermaid
stateDiagram-v2
    [*] --> Invited: HR creates invitation
    Invited --> Accepted: Employee accepts token
    Accepted --> ProfilePending: Employee opens portal
    ProfilePending --> DocumentsPending: Profile saved
    DocumentsPending --> Verifying: Documents uploaded
    
    Verifying --> RunningWorkflow: OnboardingOrchestrator starts
    
    state RunningWorkflow {
        [*] --> Planning: PlannerAgent generates DAG
        Planning --> ExecutingTasks: Plan generated
        ExecutingTasks --> PausedForApproval: Manager approval required
        PausedForApproval --> ExecutingTasks: Approval granted
        ExecutingTasks --> WorkflowCompleted: All tasks finished
    }
    
    WorkflowCompleted --> Active: Employee onboarded
    Active --> [*]
```

---

## 4. Request & Execution Sequence Flow

```mermaid
sequenceDiagram
    participant HR as HR Admin
    participant Frontend as Next.js Dashboard
    participant API as FastAPI Router
    participant Service as Invitation Service
    participant Outbox as Email Outbox DB
    
    HR->>Frontend: Fill Employee Invite Form
    Frontend->>API: POST /api/v1/invitations
    API->>Service: InvitationService.create(...)
    Service->>Service: Generate Secure Token & Expiry
    Service->>Outbox: Record Email in email_outbox
    Service->>API: Return invitation payload + QR Code
    API-->>Frontend: HTTP 200 OK
    Frontend-->>HR: Display Invitation QR Code & Link
```

---

## 5. Database Schema (SQLite / Postgres)

### Core Tables

#### `employees`
- `id` (VARCHAR / UUID, Primary Key)
- `organization_id` (VARCHAR, Foreign Key)
- `first_name` (VARCHAR, NOT NULL)
- `last_name` (VARCHAR, NOT NULL)
- `email` (VARCHAR, UNIQUE, NOT NULL)
- `phone` (VARCHAR)
- `department` (VARCHAR)
- `job_title` (VARCHAR)
- `role` (VARCHAR, Default: `'employee'`)
- `status` (VARCHAR, Default: `'invited'`)
- `profile` (JSON / Text)
- `profile_completed` (BOOLEAN)
- `terms_accepted_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)

#### `invitations`
- `id` (VARCHAR / UUID, Primary Key)
- `organization_id` (VARCHAR)
- `employee_id` (VARCHAR, Foreign Key)
- `email` (VARCHAR, NOT NULL)
- `token` (VARCHAR, UNIQUE, NOT NULL)
- `role` (VARCHAR)
- `status` (VARCHAR, Default: `'pending'`)
- `expires_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)

#### `workflows`
- `id` (VARCHAR / UUID, Primary Key)
- `organization_id` (VARCHAR)
- `employee_id` (VARCHAR, Foreign Key)
- `template_id` (VARCHAR)
- `name` (VARCHAR)
- `status` (VARCHAR, Default: `'pending'`)
- `current_stage` (VARCHAR)
- `progress` (INTEGER, Default: 0)
- `context` (JSON)
- `created_at` (TIMESTAMP)

#### `tasks`
- `id` (VARCHAR / UUID, Primary Key)
- `workflow_id` (VARCHAR, Foreign Key)
- `task_id` (VARCHAR)
- `name` (VARCHAR)
- `assigned_agent` (VARCHAR)
- `tool_name` (VARCHAR)
- `status` (VARCHAR, Default: `'pending'`)
- `input_data` (JSON)
- `output_data` (JSON)
- `retry_policy` (JSON)
- `created_at` (TIMESTAMP)

#### `documents`
- `id` (VARCHAR / UUID, Primary Key)
- `employee_id` (VARCHAR, Foreign Key)
- `document_type` (VARCHAR, NOT NULL)
- `file_name` (VARCHAR)
- `file_path` (VARCHAR)
- `file_url` (VARCHAR)
- `content_type` (VARCHAR)
- `status` (VARCHAR, Default: `'uploaded'`)
- `created_at` (TIMESTAMP)

---

## 6. Resilience & Self-Healing

1. **Exponential Backoff**: `RetryManager` evaluates task failures against the `RetryState` policy (`attempts < max_retries`). Delay scales dynamically (`initial_delay * backoff_factor ^ attempts`).
2. **Escalation Routing**: When retries are exhausted, the orchestrator transitions the task to `escalate`, logs an audit entry, and pushes an actionable alert notification to HR administrators.
3. **Stalled Workflow Recovery**: Background scheduler runs `OnboardingOrchestrator.recover_stalled()` every 60 seconds to detect and re-enter stranded execution loops post-server restart.

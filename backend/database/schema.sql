-- ============================================================================
-- ECHO WorkforceOS - Supabase schema
-- Run once in the Supabase SQL editor (Dashboard -> SQL Editor -> New query).
-- Safe to re-run: every statement is idempotent.
-- ============================================================================

create extension if not exists "pgcrypto";

-- ----------------------------------------------------------------------------
-- Tenancy & identity
-- ----------------------------------------------------------------------------
create table if not exists organizations (
    id            text primary key default gen_random_uuid()::text,
    name          text not null,
    slug          text unique not null,
    industry      text,
    size          text,
    logo_url      text,
    timezone      text default 'UTC',
    settings      jsonb default '{}'::jsonb,
    policies      jsonb default '{}'::jsonb,
    created_at    timestamptz default now(),
    updated_at    timestamptz default now()
);

create table if not exists users (
    id                text primary key default gen_random_uuid()::text,
    organization_id   text references organizations(id) on delete cascade,
    email             text unique not null,
    full_name         text,
    password_hash     text,
    supabase_user_id  text,
    role              text not null default 'employee',
    employee_id       text,
    is_active         boolean default true,
    email_verified    boolean default false,
    last_login_at     timestamptz,
    created_at        timestamptz default now(),
    updated_at        timestamptz default now()
);
create index if not exists users_org_idx on users(organization_id);

-- ----------------------------------------------------------------------------
-- Workforce
-- ----------------------------------------------------------------------------
create table if not exists employees (
    id                   text primary key default gen_random_uuid()::text,
    organization_id      text references organizations(id) on delete cascade,
    first_name           text not null,
    last_name            text not null,
    email                text unique not null,
    phone                text,
    department           text,
    role                 text,
    job_title            text,
    employment_type      text default 'full_time',
    manager_id           text,
    status               text default 'invited',
    onboarding_date      timestamptz,
    start_date           timestamptz,
    profile              jsonb default '{}'::jsonb,
    profile_completed    boolean default false,
    terms_accepted_at    timestamptz,
    policies_reviewed_at timestamptz,
    activated_at         timestamptz,
    created_at           timestamptz default now(),
    updated_at           timestamptz default now()
);
create index if not exists employees_org_idx on employees(organization_id);
create index if not exists employees_status_idx on employees(status);

create table if not exists invitations (
    id               text primary key default gen_random_uuid()::text,
    organization_id  text references organizations(id) on delete cascade,
    employee_id      text references employees(id) on delete cascade,
    email            text not null,
    token            text unique not null,
    role             text default 'employee',
    department       text,
    job_title        text,
    status           text default 'pending',
    invited_by       text,
    message          text,
    expires_at       timestamptz not null,
    accepted_at      timestamptz,
    reminder_count   integer default 0,
    last_reminder_at timestamptz,
    created_at       timestamptz default now(),
    updated_at       timestamptz default now()
);
create index if not exists invitations_token_idx on invitations(token);
create index if not exists invitations_status_idx on invitations(status);

-- ----------------------------------------------------------------------------
-- Workflow & orchestration
-- ----------------------------------------------------------------------------
create table if not exists workflows (
    id               text primary key default gen_random_uuid()::text,
    organization_id  text references organizations(id) on delete cascade,
    employee_id      text references employees(id) on delete cascade,
    template_id      text,
    name             text not null,
    status           text default 'pending',
    current_stage    text,
    progress         integer default 0,
    state            jsonb default '{}'::jsonb,
    context          jsonb default '{}'::jsonb,
    error_message    text,
    started_at       timestamptz,
    completed_at     timestamptz,
    created_at       timestamptz default now(),
    updated_at       timestamptz default now()
);
create index if not exists workflows_employee_idx on workflows(employee_id);
create index if not exists workflows_status_idx on workflows(status);

create table if not exists agents (
    id                     text primary key default gen_random_uuid()::text,
    name                   text unique not null,
    role_description       text,
    capabilities           jsonb default '[]'::jsonb,
    is_active              boolean default true,
    total_executions       integer default 0,
    successful_executions  integer default 0,
    failed_executions      integer default 0,
    avg_duration_seconds   double precision default 0,
    last_active_at         timestamptz,
    created_at             timestamptz default now()
);

create table if not exists tasks (
    id                text primary key default gen_random_uuid()::text,
    workflow_id       text references workflows(id) on delete cascade,
    agent_id          text references agents(id) on delete set null,
    agent_name        text,
    task_key          text,
    name              text not null,
    description       text,
    tool_name         text,
    status            text default 'pending',
    priority          integer default 0,
    dependencies      jsonb default '[]'::jsonb,
    input_data        jsonb default '{}'::jsonb,
    result            jsonb,
    error_message     text,
    retries           integer default 0,
    max_retries       integer default 3,
    requires_approval boolean default false,
    started_at        timestamptz,
    completed_at      timestamptz,
    created_at        timestamptz default now(),
    updated_at        timestamptz default now()
);
create index if not exists tasks_workflow_idx on tasks(workflow_id);
create index if not exists tasks_status_idx on tasks(status);

create table if not exists agent_executions (
    id               text primary key default gen_random_uuid()::text,
    workflow_id      text,
    task_id          text,
    agent_name       text not null,
    action           text not null,
    status           text default 'running',
    input_data       jsonb default '{}'::jsonb,
    output_data      jsonb default '{}'::jsonb,
    reasoning        text,
    llm_provider     text,
    error_message    text,
    attempt          integer default 1,
    duration_seconds double precision default 0,
    started_at       timestamptz default now(),
    completed_at     timestamptz
);
create index if not exists agent_exec_workflow_idx on agent_executions(workflow_id);
create index if not exists agent_exec_agent_idx on agent_executions(agent_name);

create table if not exists execution_logs (
    id           text primary key default gen_random_uuid()::text,
    workflow_id  text references workflows(id) on delete cascade,
    task_id      text,
    agent_id     text,
    action       text not null,
    level        text default 'info',
    details      jsonb default '{}'::jsonb,
    timestamp    timestamptz default now()
);
create index if not exists execution_logs_workflow_idx on execution_logs(workflow_id);

create table if not exists execution_plans (
    id                 text primary key default gen_random_uuid()::text,
    workflow_id        text references workflows(id) on delete cascade,
    plan_data          jsonb not null,
    critical_path      jsonb default '[]'::jsonb,
    estimated_duration integer default 0,
    status             text default 'generated',
    created_at         timestamptz default now(),
    updated_at         timestamptz default now()
);
create index if not exists execution_plans_workflow_idx on execution_plans(workflow_id);

create table if not exists planning_logs (
    id          text primary key default gen_random_uuid()::text,
    workflow_id text references workflows(id) on delete cascade,
    action      text not null,
    reason      text,
    details     jsonb default '{}'::jsonb,
    timestamp   timestamptz default now()
);

create table if not exists workflow_templates (
    id              text primary key default gen_random_uuid()::text,
    organization_id text,
    key             text,
    name            text not null,
    description     text,
    version         text default '1.0.0',
    definition      jsonb not null,
    is_active       boolean default true,
    created_at      timestamptz default now()
);
create index if not exists workflow_templates_key_idx on workflow_templates(key);

-- ----------------------------------------------------------------------------
-- Compliance & documents
-- ----------------------------------------------------------------------------
create table if not exists documents (
    id                text primary key default gen_random_uuid()::text,
    organization_id   text,
    employee_id       text references employees(id) on delete cascade,
    document_type     text not null,
    file_name         text not null,
    file_type         text not null,
    file_size         integer default 0,
    storage_path      text,
    storage_url       text not null,
    status            text default 'uploaded',
    required          boolean default true,
    validation_errors jsonb default '[]'::jsonb,
    extracted_data    jsonb default '{}'::jsonb,
    expiry_date       timestamptz,
    verified_at       timestamptz,
    verified_by       text,
    uploaded_at       timestamptz default now()
);
create index if not exists documents_employee_idx on documents(employee_id);

create table if not exists verification_reports (
    id                   text primary key default gen_random_uuid()::text,
    workflow_id          text not null,
    employee_id          text,
    overall_status       text not null,
    confidence_score     double precision default 0,
    missing_documents    jsonb default '[]'::jsonb,
    invalid_documents    jsonb default '[]'::jsonb,
    required_corrections jsonb default '[]'::jsonb,
    compliance_findings  jsonb default '[]'::jsonb,
    warnings             jsonb default '[]'::jsonb,
    recommendations      jsonb default '[]'::jsonb,
    next_action          text default 'WAIT',
    reasoning            text,
    created_at           timestamptz default now()
);
create index if not exists verification_workflow_idx on verification_reports(workflow_id);

create table if not exists approvals (
    id               text primary key default gen_random_uuid()::text,
    organization_id  text,
    workflow_id      text not null,
    task_id          text,
    employee_id      text,
    title            text not null,
    description      text,
    reason           text,
    status           text default 'pending',
    requested_by     text default 'Manager Agent',
    required_role    text default 'hr',
    approver_id      text,
    approver_email   text,
    comments         text,
    payload          jsonb default '{}'::jsonb,
    reminder_count   integer default 0,
    last_reminder_at timestamptz,
    escalated_at     timestamptz,
    expires_at       timestamptz,
    resolved_at      timestamptz,
    created_at       timestamptz default now(),
    updated_at       timestamptz default now()
);
create index if not exists approvals_status_idx on approvals(status);
create index if not exists approvals_workflow_idx on approvals(workflow_id);

-- ----------------------------------------------------------------------------
-- Comms & audit
-- ----------------------------------------------------------------------------
create table if not exists notifications (
    id              text primary key default gen_random_uuid()::text,
    organization_id text,
    user_id         text,
    employee_id     text,
    workflow_id     text,
    type            text not null,
    category        text default 'workflow',
    title           text not null,
    message         text not null,
    action_url      text,
    metadata_json   jsonb default '{}'::jsonb,
    is_read         boolean default false,
    created_at      timestamptz default now()
);
create index if not exists notifications_read_idx on notifications(is_read);
create index if not exists notifications_org_idx on notifications(organization_id);

create table if not exists email_outbox (
    id            text primary key default gen_random_uuid()::text,
    to_email      text not null,
    subject       text not null,
    body_text     text,
    body_html     text,
    template      text,
    status        text default 'queued',
    provider      text,
    error_message text,
    sent_at       timestamptz,
    created_at    timestamptz default now()
);

create table if not exists audit_logs (
    id              text primary key default gen_random_uuid()::text,
    organization_id text,
    user_id         text,
    actor           text,
    actor_type      text default 'system',
    action          text not null,
    resource_type   text not null,
    resource_id     text not null,
    changes         jsonb,
    ip_address      text,
    timestamp       timestamptz default now()
);
create index if not exists audit_logs_resource_idx on audit_logs(resource_type, resource_id);
create index if not exists audit_logs_time_idx on audit_logs(timestamp desc);

-- ----------------------------------------------------------------------------
-- Realtime: broadcast row changes to the dashboard
-- ----------------------------------------------------------------------------
do $$
declare
    t text;
begin
    foreach t in array array[
        'organizations','employees','invitations','workflows','tasks',
        'agent_executions','execution_logs','documents','approvals',
        'notifications','audit_logs','verification_reports'
    ]
    loop
        begin
            execute format('alter publication supabase_realtime add table %I', t);
        exception when others then
            null; -- already a member of the publication
        end;
    end loop;
end $$;

-- ----------------------------------------------------------------------------
-- Row level security
--
-- The FastAPI backend uses the service-role key and therefore bypasses RLS.
-- These permissive policies exist so the browser (anon key) can subscribe to
-- realtime changes. Tighten them before any production deployment.
-- ----------------------------------------------------------------------------
do $$
declare
    t text;
begin
    foreach t in array array[
        'organizations','users','employees','invitations','workflows','agents',
        'tasks','agent_executions','execution_logs','execution_plans',
        'planning_logs','workflow_templates','documents','verification_reports',
        'approvals','notifications','email_outbox','audit_logs'
    ]
    loop
        execute format('alter table %I enable row level security', t);
        execute format('drop policy if exists echo_read_all on %I', t);
        execute format(
            'create policy echo_read_all on %I for select to anon, authenticated using (true)', t
        );
    end loop;
end $$;

-- ----------------------------------------------------------------------------
-- Storage bucket for employee documents
-- ----------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('echo-documents', 'echo-documents', true)
on conflict (id) do nothing;

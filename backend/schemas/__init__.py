"""Pydantic request/response models, grouped by domain.

Every model is re-exported here so routes can do
``from schemas import LoginRequest, EmployeeResponse`` without caring which
themed module actually defines it.
"""

from schemas.approvals import (
    ApprovalDecision,
    ApprovalRequestCreate,
    ApprovalResponse,
)
from schemas.auth import (
    LoginRequest,
    MagicLinkRequest,
    MagicLinkVerifyRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from schemas.common import (
    DashboardStats,
    ErrorResponse,
    MessageResponse,
    PaginatedResponse,
)
from schemas.documents import (
    DocumentChecklistItem,
    DocumentResponse,
    DocumentStatusUpdate,
    DocumentUploadRequest,
)
from schemas.employees import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    ProfileCompletionRequest,
)
from schemas.invitations import (
    InvitationAcceptRequest,
    InvitationCreate,
    InvitationCreateResponse,
    InvitationResponse,
)
from schemas.notifications import (
    NotificationCreate,
    NotificationResponse,
)
from schemas.organizations import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from schemas.workflows import (
    OnboardingProgressResponse,
    TaskResponse,
    WorkflowActionRequest,
    WorkflowResponse,
)

__all__ = [
    # auth
    "LoginRequest",
    "RegisterRequest",
    "MagicLinkRequest",
    "MagicLinkVerifyRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "TokenResponse",
    "UserResponse",
    # organizations
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    # employees
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeResponse",
    "ProfileCompletionRequest",
    # invitations
    "InvitationCreate",
    "InvitationResponse",
    "InvitationAcceptRequest",
    "InvitationCreateResponse",
    # documents
    "DocumentUploadRequest",
    "DocumentResponse",
    "DocumentChecklistItem",
    "DocumentStatusUpdate",
    # workflows
    "WorkflowResponse",
    "WorkflowActionRequest",
    "TaskResponse",
    "OnboardingProgressResponse",
    # approvals
    "ApprovalRequestCreate",
    "ApprovalResponse",
    "ApprovalDecision",
    # notifications
    "NotificationCreate",
    "NotificationResponse",
    # common
    "PaginatedResponse",
    "MessageResponse",
    "DashboardStats",
    "ErrorResponse",
]

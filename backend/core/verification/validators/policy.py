from typing import Dict, Any, List
from core.state.models import ContextState
from core.verification.rules import RuleEngine

class PolicyValidator:
    """
    Validates organization-specific compliance rules (e.g., Background Checks).
    """

    @staticmethod
    def validate(context: ContextState) -> Dict[str, Any]:
        role = context.employee.role
        findings = []
        
        if RuleEngine.requires_background_check(role):
            # Check if background check was completed. 
            # We assume this would be tracked in global variables or completed tasks.
            bg_check_status = context.global_variables.get("background_check_status", "missing")
            if bg_check_status != "passed":
                findings.append(f"Background check is required for role '{role}' but current status is '{bg_check_status}'.")
                
        return {
            "is_valid": len(findings) == 0,
            "findings": findings
        }

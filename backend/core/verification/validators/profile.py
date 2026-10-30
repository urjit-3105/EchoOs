from typing import List, Dict, Any
from core.state.models import ContextState
from core.verification.rules import RuleEngine

class ProfileValidator:
    """
    Validates that the Employee profile contains all required fields.
    """
    
    @staticmethod
    def validate(context: ContextState) -> Dict[str, Any]:
        missing_fields = []
        employee_data = context.employee.model_dump()
        
        required_fields = RuleEngine.get_required_profile_fields()
        
        for field in required_fields:
            if not employee_data.get(field):
                missing_fields.append(field)
                
        return {
            "is_valid": len(missing_fields) == 0,
            "missing_fields": missing_fields
        }

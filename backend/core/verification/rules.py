import yaml
import os
from typing import Dict, Any, List
from core.logger.structured import get_logger

logger = get_logger(__name__)

class RuleEngine:
    """
    Loads and provides validation rules from configuration files.
    """
    _rules: Dict[str, Any] = {}

    @classmethod
    def load_rules(cls, filepath: str = "config/rules.yaml"):
        """Loads verification rules into memory."""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            full_path = os.path.join(base_path, filepath)
            
            with open(full_path, "r") as f:
                cls._rules = yaml.safe_load(f)
                logger.info("Verification rules loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load rules from {filepath}", exc_info=e)
            cls._rules = {"policies": {"global": {"required_documents": [], "required_profile_fields": []}}}

    @classmethod
    def get_required_documents(cls, department: str = None) -> List[str]:
        """Returns the list of required documents based on global and departmental policies."""
        if not cls._rules:
            cls.load_rules()
            
        docs = set(cls._rules.get("policies", {}).get("global", {}).get("required_documents", []))
        
        if department:
            dept_docs = cls._rules.get("policies", {}).get("departments", {}).get(department, {}).get("required_documents", [])
            docs.update(dept_docs)
            
        return list(docs)

    @classmethod
    def get_required_profile_fields(cls) -> List[str]:
        """Returns global required profile fields."""
        if not cls._rules:
            cls.load_rules()
        return cls._rules.get("policies", {}).get("global", {}).get("required_profile_fields", [])
        
    @classmethod
    def requires_background_check(cls, role: str = None) -> bool:
        if not cls._rules:
            cls.load_rules()
        if role:
            return cls._rules.get("policies", {}).get("roles", {}).get(role, {}).get("requires_background_check", False)
        return False

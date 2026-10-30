from typing import List, Dict, Any
from datetime import datetime, timezone
from core.state.models import ContextState, DocumentState
from core.verification.rules import RuleEngine

class DocumentValidator:
    """
    Validates presence and validity of required documents.
    """

    @staticmethod
    def validate(context: ContextState) -> Dict[str, Any]:
        department = context.employee.department
        required_doc_types = RuleEngine.get_required_documents(department)
        
        # Load uploaded documents from global_variables or a specific state map
        # We assume the Orchestrator/API populated ContextState.global_variables["documents"]
        # as a list of DocumentState dicts.
        uploaded_docs_raw = context.global_variables.get("documents", [])
        uploaded_docs = [DocumentState(**doc) if isinstance(doc, dict) else doc for doc in uploaded_docs_raw]
        
        uploaded_types = {doc.type for doc in uploaded_docs}
        
        missing_docs = []
        invalid_docs = []
        
        for req_type in required_doc_types:
            if req_type not in uploaded_types:
                missing_docs.append(req_type)
        
        for doc in uploaded_docs:
            # Check expiry
            if doc.expiry_date and doc.expiry_date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                invalid_docs.append(f"{doc.type} is expired")
            # Check status
            if doc.verification_status == "rejected":
                invalid_docs.append(f"{doc.type} was rejected")
                
        return {
            "is_valid": len(missing_docs) == 0 and len(invalid_docs) == 0,
            "missing_docs": missing_docs,
            "invalid_docs": invalid_docs
        }

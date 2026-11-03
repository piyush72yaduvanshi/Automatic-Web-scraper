"""Tool Registry for AI Agents.

Defines safe, scoped, deterministic Python tools that agents are permitted to invoke.
Agents do not have unrestricted database or network access; they access capabilities
through explicit tool schemas with argument validation.
"""

from typing import Dict, Any, Callable, List, Optional
import json
import logging
from sqlalchemy.orm import Session

from app.models.business_lead import BusinessLead
from app.models.crm import Company, Contact, Deal, CRMTask
from app.models.orchestration import KnowledgeDocument

logger = logging.getLogger(__name__)


class ToolDefinition:
    def __init__(self, name: str, description: str, parameters: Dict[str, Any], func: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    def execute(self, **kwargs) -> Any:
        return self.func(**kwargs)


class ToolRegistry:
    """Central registry of agent-accessible executable tools."""

    _tools: Dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, name: str, description: str, parameters: Dict[str, Any]):
        def decorator(func: Callable):
            cls._tools[name] = ToolDefinition(name, description, parameters, func)
            return func
        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[ToolDefinition]:
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in cls._tools.values()
        ]

    @classmethod
    def execute_tool(cls, name: str, **kwargs) -> Any:
        tool = cls.get(name)
        if not tool:
            raise ValueError(f"Tool '{name}' is not registered.")
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            logger.warning(f"Error executing tool '{name}': {e}")
            return {"error": str(e), "success": False}


# -------------------------------------------------------------
# Core Deterministic Tools
# -------------------------------------------------------------
@ToolRegistry.register(
    name="search_leads_db",
    description="Search existing discovered leads in database by keyword, city, or status.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search keyword for business name or category"},
            "city": {"type": "string", "description": "City filter"},
            "status": {"type": "string", "description": "Lead status filter"},
        },
    },
)
def search_leads_db(db: Session, query: Optional[str] = None, city: Optional[str] = None, status: Optional[str] = None, limit: int = 10):
    q = db.query(BusinessLead)
    if query:
        q = q.filter(BusinessLead.business_name.ilike(f"%{query}%") | BusinessLead.category.ilike(f"%{query}%"))
    if city:
        q = q.filter(BusinessLead.city.ilike(f"%{city}%"))
    if status:
        q = q.filter(BusinessLead.status == status)
    leads = q.limit(limit).all()
    return [
        {
            "id": str(l.id),
            "name": l.business_name,
            "category": l.category,
            "city": l.city,
            "qualification_score": l.qualification_score,
            "status": l.qualification_status,
        }
        for l in leads
    ]


@ToolRegistry.register(
    name="query_crm_pipeline",
    description="Get current CRM pipeline deal values and stage summaries.",
    parameters={"type": "object", "properties": {}},
)
def query_crm_pipeline(db: Session):
    deals = db.query(Deal).filter(Deal.status == "open").all()
    total_val = sum(d.amount for d in deals)
    return {
        "active_deals_count": len(deals),
        "total_pipeline_value": total_val,
        "deals": [{"title": d.title, "amount": d.amount, "stage": d.stage.name if d.stage else None} for d in deals[:10]],
    }


@ToolRegistry.register(
    name="calculate_icp_score",
    description="Calculate mathematical weighted ICP fit score based on factor scores.",
    parameters={
        "type": "object",
        "properties": {
            "fit_score": {"type": "number"},
            "pain_score": {"type": "number"},
            "timing_score": {"type": "number"},
            "reachability_score": {"type": "number"},
            "evidence_score": {"type": "number"},
        },
        "required": ["fit_score", "pain_score", "reachability_score"],
    },
)
def calculate_icp_score(
    fit_score: float,
    pain_score: float,
    reachability_score: float,
    timing_score: float = 50.0,
    evidence_score: float = 50.0,
):
    score = (
        fit_score * 0.25 +
        pain_score * 0.25 +
        timing_score * 0.20 +
        reachability_score * 0.15 +
        evidence_score * 0.15
    )
    return {
        "composite_score": round(score, 1),
        "status": "Qualified" if score >= 70 else ("Maybe" if score >= 45 else "Rejected"),
    }


"""API endpoints for Specialized AI Agents and Orchestration."""

from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from sqlalchemy import desc

from app.core.database import get_db
from app.core.security import verify_api_key
from app.core.rate_limiter import limiter
from app.core.config import settings
from app.ai.agents.specialized import AgentRegistry
from app.ai.orchestrator.orchestrator import AIOrchestrator
from app.models.orchestration import AgentRun

router = APIRouter(prefix="/agents", tags=["ai_agents"])


@router.get("")
def list_agents():
    """List all 15 specialized AI agents, roles, and tool permissions."""
    return AgentRegistry.list_agents()


@router.post("/{agent_name}/execute")
@limiter.limit(settings.RATE_LIMIT_AI_AGENTS)
async def execute_agent(
    request: Request,
    agent_name: str,
    payload: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Execute a single specialized AI agent with provided input parameters."""
    try:
        return await AIOrchestrator.execute_agent(agent_name, payload, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution error: {str(e)}")


@router.post("/workflow")
@limiter.limit(settings.RATE_LIMIT_AI_AGENTS)
async def run_workflow(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """Execute an end-to-end autonomous multi-agent sales workflow."""
    goal = payload.get("goal")
    if not goal:
        raise HTTPException(status_code=400, detail="goal is required")
    return await AIOrchestrator.run_autonomous_workflow(goal, db)


@router.get("/runs")
def list_agent_runs(
    agent_name: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List telemetry history of agent execution runs."""
    q = db.query(AgentRun)
    if agent_name:
        q = q.filter(AgentRun.agent_name == agent_name)
    runs = q.order_by(desc(AgentRun.created_at)).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "agent_name": r.agent_name,
            "task_type": r.task_type,
            "status": r.status,
            "duration_ms": r.duration_ms,
            "error_message": r.error_message,
            "created_at": r.created_at.isoformat(),
        }
        for r in runs
    ]


@router.get("/runs/{run_id}")
def get_agent_run(run_id: str, db: Session = Depends(get_db)):
    """Fetch complete input, output, and execution steps for a single run."""
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return {
        "id": str(run.id),
        "agent_name": run.agent_name,
        "task_type": run.task_type,
        "status": run.status,
        "input_parameters": run.input_parameters,
        "output_data": run.output_data,
        "error_message": run.error_message,
        "duration_ms": run.duration_ms,
        "created_at": run.created_at.isoformat(),
    }


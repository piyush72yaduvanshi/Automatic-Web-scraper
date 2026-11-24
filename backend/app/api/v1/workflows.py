"""FastAPI Router for Native Python Workflow Engine (Zero n8n)."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.workflow_engine_service import WorkflowEngineService

router = APIRouter(prefix="/workflows", tags=["Workflows (Native Python)"], dependencies=[Depends(verify_api_key)])


@router.get("")
def list_workflow_definitions(active_only: bool = False, db: Session = Depends(get_db)):
    """List declarative workflow definitions."""
    return WorkflowEngineService.list_definitions(db=db, active_only=active_only)


@router.post("")
def create_workflow_definition(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Create a new declarative workflow definition."""
    try:
        return WorkflowEngineService.create_definition(data=data, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{workflow_id}/trigger")
async def trigger_workflow(
    workflow_id: str,
    payload: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
):
    """Manually trigger execution of a workflow."""
    try:
        return await WorkflowEngineService.execute_workflow(
            workflow_id=workflow_id,
            trigger_event="MANUAL",
            input_payload=payload,
            db=db,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/executions")
def list_workflow_executions(
    workflow_id: Optional[str] = None,
    status: Optional[str] = None,
    trigger_event: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Query workflow execution history and states.
    
    - **workflow_id**: Filter by specific workflow ID
    - **status**: Filter by execution status (RUNNING, COMPLETED, FAILED, etc.)
    - **trigger_event**: Filter by trigger event (NEW_LEAD, UNSUBSCRIBE, REPLY_CLASSIFIED, MANUAL, etc.)
    - **limit**: Maximum number of executions to return
    
    Returns execution history with workflow name, status, step results, and timestamps.
    """
    return WorkflowEngineService.list_executions(
        db=db,
        workflow_id=workflow_id,
        status=status,
        trigger_event=trigger_event,
        limit=limit,
    )


@router.post("/executions/{execution_id}/retry")
async def retry_execution(execution_id: str, db: Session = Depends(get_db)):
    """Manually retry a failed workflow execution."""
    try:
        return await WorkflowEngineService.retry_execution(execution_id=execution_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/executions/{execution_id}/cancel")
def cancel_execution(execution_id: str, db: Session = Depends(get_db)):
    """Cancel an active or waiting workflow execution."""
    try:
        return WorkflowEngineService.cancel_execution(execution_id=execution_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


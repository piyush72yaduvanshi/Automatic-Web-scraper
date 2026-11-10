"""Native Python Workflow Automation Engine (Strictly Zero n8n).

Provides event-driven and scheduled workflow orchestration, step execution,
conditional branching, retries, failure handling, and PostgreSQL execution tracking.
"""

from typing import Dict, Any, List, Optional
import json
import uuid
import logging
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.models.workflow import WorkflowDefinition, WorkflowExecution, WorkflowEvent
from app.models.orchestration import AuditLog
from app.models.outreach import OutreachApproval, SuppressionRecord
from app.models.crm import CRMTask, Activity

logger = logging.getLogger(__name__)


class WorkflowEngineService:
    """Master native Python workflow engine."""

    # Supported Trigger Types
    TRIGGERS = [
        "MANUAL",
        "SCHEDULED",
        "NEW_LEAD",
        "LEAD_ENRICHED",
        "LEAD_QUALIFIED",
        "CAMPAIGN_APPROVED",
        "INCOMING_MESSAGE",
        "REPLY_CLASSIFIED",
        "FOLLOWUP_DUE",
        "UNSUBSCRIBE",
        "HEALTH_CHANGED",
    ]

    # Supported Action Types
    ACTIONS = [
        "AI_AGENT",
        "QUALIFY_LEAD",
        "RESEARCH_COMPANY",
        "STAGE_OUTREACH",
        "CREATE_CRM_TASK",
        "CREATE_CRM_DEAL",
        "PAUSE_SEQUENCE",
        "SUPPRESS_CONTACT",
        "GENERATE_REPORT",
        "CONDITIONAL_BRANCH",
        "LOG_ACTIVITY",
    ]

    @classmethod
    def list_definitions(cls, db: Session, active_only: bool = False) -> List[Dict[str, Any]]:
        """List workflow definitions."""
        cls.seed_default_workflows_if_empty(db)
        q = db.query(WorkflowDefinition)
        if active_only:
            q = q.filter(WorkflowDefinition.is_active.is_(True))
        defs = q.order_by(WorkflowDefinition.name).all()
        return [
            {
                "id": str(d.id),
                "name": d.name,
                "description": d.description,
                "version": d.version,
                "trigger_type": d.trigger_type,
                "trigger_config": json.loads(d.trigger_config) if d.trigger_config else {},
                "steps": json.loads(d.steps_json) if d.steps_json else [],
                "is_active": d.is_active,
                "timeout_seconds": d.timeout_seconds,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in defs
        ]

    @classmethod
    def create_definition(cls, data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Create a new declarative workflow definition."""
        name = data.get("name", "Untitled Workflow")
        trigger_type = data.get("trigger_type", "MANUAL")
        if trigger_type not in cls.TRIGGERS:
            raise ValueError(f"Invalid trigger_type. Must be one of: {cls.TRIGGERS}")

        steps = data.get("steps", [])
        if not steps:
            raise ValueError("Workflow must contain at least one step")

        w_def = WorkflowDefinition(
            name=name,
            description=data.get("description", ""),
            version=1,
            trigger_type=trigger_type,
            trigger_config=json.dumps(data.get("trigger_config", {})),
            input_schema=json.dumps(data.get("input_schema", {})),
            steps_json=json.dumps(steps),
            retry_config=json.dumps(data.get("retry_config", {"max_retries": 2, "backoff_seconds": 5})),
            timeout_seconds=data.get("timeout_seconds", 300),
            is_active=data.get("is_active", True),
        )
        db.add(w_def)
        db.commit()
        db.refresh(w_def)

        return {
            "id": str(w_def.id),
            "name": w_def.name,
            "trigger_type": w_def.trigger_type,
            "status": "CREATED",
        }

    @classmethod
    async def emit_event(
        cls,
        event_type: str,
        payload: Dict[str, Any],
        db: Session,
    ) -> List[Dict[str, Any]]:
        """
        Event Bus: Records event and automatically triggers matching active workflows.
        """
        # 1. Record event
        ev = WorkflowEvent(
            event_type=event_type,
            payload=json.dumps(payload),
            processed=False,
        )
        db.add(ev)
        db.commit()

        # 2. Find matching active workflow definitions
        cls.seed_default_workflows_if_empty(db)
        matching_defs = db.query(WorkflowDefinition).filter(
            WorkflowDefinition.trigger_type == event_type,
            WorkflowDefinition.is_active.is_(True),
        ).all()

        results = []
        for w_def in matching_defs:
            res = await cls.execute_workflow(
                workflow_id=w_def.id,
                trigger_event=event_type,
                input_payload=payload,
                db=db,
            )
            results.append(res)

        ev.processed = True
        db.commit()
        return results

    @classmethod
    async def execute_workflow(
        cls,
        workflow_id: Any,
        trigger_event: str,
        input_payload: Dict[str, Any],
        db: Session,
    ) -> Dict[str, Any]:
        """Execute a workflow instance step-by-step with state persistence."""
        w_def = db.query(WorkflowDefinition).filter(WorkflowDefinition.id == uuid.UUID(str(workflow_id))).first()
        if not w_def:
            raise ValueError(f"Workflow definition '{workflow_id}' not found")

        # Create execution record
        execution = WorkflowExecution(
            workflow_id=w_def.id,
            trigger_event=trigger_event,
            status="RUNNING",
            input_payload=json.dumps(input_payload),
            step_results=json.dumps({}),
            start_time=datetime.utcnow(),
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        steps = json.loads(w_def.steps_json) if w_def.steps_json else []
        step_results = {}
        current_step_idx = 0
        max_step_executions = max(len(steps) * 4, 60)
        executed_step_count = 0

        try:
            while current_step_idx < len(steps):
                executed_step_count += 1
                if executed_step_count > max_step_executions:
                    raise RuntimeError(
                        f"Workflow step limit exceeded ({max_step_executions} iterations). "
                        f"Execution terminated to prevent infinite loop."
                    )

                step = steps[current_step_idx]
                step_id = step.get("step_id", f"step_{current_step_idx + 1}")
                action_type = step.get("action_type")
                config = step.get("config", {})

                execution.current_step_id = step_id
                db.commit()

                # Execute action
                res = await cls._execute_step_action(
                    action_type=action_type,
                    config=config,
                    input_payload=input_payload,
                    step_results=step_results,
                    db=db,
                )
                step_results[step_id] = res

                # Check if approval requested
                if res.get("status") == "WAITING_FOR_APPROVAL":
                    execution.status = "WAITING_FOR_APPROVAL"
                    execution.step_results = json.dumps(step_results)
                    db.commit()
                    return {
                        "execution_id": str(execution.id),
                        "workflow_name": w_def.name,
                        "status": "WAITING_FOR_APPROVAL",
                        "current_step": step_id,
                        "step_results": step_results,
                    }

                # Conditional Branching
                if action_type == "CONDITIONAL_BRANCH":
                    condition = config.get("condition", "True")
                    eval_result = res.get("branch_evaluation", True)
                    next_step_id = config.get("next_step_true" if eval_result else "next_step_false")
                    if next_step_id:
                        found_idx = next((i for i, s in enumerate(steps) if s.get("step_id") == next_step_id), None)
                        if found_idx is not None:
                            current_step_idx = found_idx
                            continue

                current_step_idx += 1

            execution.status = "COMPLETED"
            execution.completion_time = datetime.utcnow()
            execution.step_results = json.dumps(step_results)
            db.commit()

            return {
                "execution_id": str(execution.id),
                "workflow_name": w_def.name,
                "status": "COMPLETED",
                "step_results": step_results,
                "started_at": execution.start_time.isoformat() if execution.start_time else None,
                "completed_at": execution.completion_time.isoformat() if execution.completion_time else None,
            }

        except Exception as e:
            logger.error(f"Error in workflow '{w_def.name}' execution {execution.id}: {str(e)}", exc_info=True)
            execution.status = "FAILED"
            execution.error_info = str(e)
            execution.completion_time = datetime.utcnow()
            execution.step_results = json.dumps(step_results)
            db.commit()

            return {
                "execution_id": str(execution.id),
                "workflow_name": w_def.name,
                "status": "FAILED",
                "error": str(e),
                "step_results": step_results,
            }

    @classmethod
    async def _execute_step_action(
        cls,
        action_type: str,
        config: Dict[str, Any],
        input_payload: Dict[str, Any],
        step_results: Dict[str, Any],
        db: Session,
    ) -> Dict[str, Any]:
        """Dispatch a single step action."""
        if action_type == "AI_AGENT":
            agent_name = config.get("agent_name", "workflow_planning_agent")
            from app.ai.agents.specialized import AgentRegistry
            agent = AgentRegistry.get_agent(agent_name)
            if not agent:
                return {"status": "FAILED", "error": f"Agent {agent_name} not found"}
            prompt_input = {**input_payload, **config.get("parameters", {})}
            res = await agent.execute(prompt_input, db)
            return {"status": "SUCCESS", "agent": agent_name, "output": res.get("result")}

        elif action_type == "QUALIFY_LEAD":
            lead_id = input_payload.get("lead_id") or config.get("lead_id")
            if not lead_id:
                return {"status": "SKIPPED", "reason": "No lead_id provided in payload"}
            from app.services.lead_qualification_service import LeadQualificationService
            q_res = await LeadQualificationService.qualify_lead(lead_id=str(lead_id), db=db)
            return {"status": "SUCCESS", "qualification": q_res}

        elif action_type == "RESEARCH_COMPANY":
            lead_id = input_payload.get("lead_id") or config.get("lead_id")
            from app.services.company_intelligence_service import CompanyIntelligenceService
            r_res = await CompanyIntelligenceService.analyze_company(lead_id=str(lead_id) if lead_id else None, db=db)
            return {"status": "SUCCESS", "research": r_res}

        elif action_type == "STAGE_OUTREACH":
            recipient = input_payload.get("recipient") or input_payload.get("email") or config.get("recipient")
            if not recipient:
                return {"status": "SKIPPED", "reason": "No recipient email provided"}
            approval = OutreachApproval(
                action_type="SEND_EMAIL",
                recipient_destination=recipient,
                subject=config.get("subject", "Follow up from Sales Team"),
                body_content=config.get("body", "Hi, following up on our previous conversation."),
                status="PENDING",
            )
            db.add(approval)
            db.commit()
            return {"status": "WAITING_FOR_APPROVAL", "approval_id": str(approval.id)}

        elif action_type == "CREATE_CRM_TASK":
            title = config.get("title", f"Workflow Task: {input_payload.get('event_type', 'Action Required')}")
            task = CRMTask(
                title=title,
                description=config.get("description", str(input_payload)),
                priority=config.get("priority", "medium"),
                status="pending",
            )
            db.add(task)
            db.commit()
            return {"status": "SUCCESS", "task_id": str(task.id), "title": task.title}

        elif action_type == "SUPPRESS_CONTACT":
            recipient = input_payload.get("recipient") or input_payload.get("email") or config.get("recipient")
            if recipient:
                existing = db.query(SuppressionRecord).filter(SuppressionRecord.recipient == recipient.lower().strip()).first()
                if not existing:
                    sup = SuppressionRecord(
                        recipient=recipient.lower().strip(),
                        channel="ALL",
                        reason=config.get("reason", "WORKFLOW_AUTOMATION"),
                    )
                    db.add(sup)
                    db.commit()
            return {"status": "SUCCESS", "suppressed_recipient": recipient}

        elif action_type == "CONDITIONAL_BRANCH":
            # Evaluates simple boolean rules on previous results or payload
            field = config.get("field", "")
            target_value = config.get("value")
            operator = config.get("operator", "==")

            actual_val = input_payload.get(field)
            if operator == "==":
                matched = actual_val == target_value
            elif operator == ">=":
                matched = float(actual_val or 0) >= float(target_value or 0)
            elif operator == "contains":
                matched = str(target_value).lower() in str(actual_val or "").lower()
            else:
                matched = bool(actual_val)

            return {"status": "SUCCESS", "branch_evaluation": matched}

        elif action_type == "LOG_ACTIVITY":
            act = Activity(
                activity_type="SYSTEM",
                title=config.get("title", "Workflow Activity"),
                description=config.get("description", "Workflow step executed."),
            )
            db.add(act)
            db.commit()
            return {"status": "SUCCESS", "activity_id": str(act.id)}

        return {"status": "UNKNOWN_ACTION", "action_type": action_type}

    @classmethod
    def list_executions(
        cls,
        db: Session,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        trigger_event: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Query workflow execution history."""
        q = db.query(WorkflowExecution).options(joinedload(WorkflowExecution.definition))
        if workflow_id:
            q = q.filter(WorkflowExecution.workflow_id == uuid.UUID(str(workflow_id)))
        if status:
            q = q.filter(WorkflowExecution.status == status)
        if trigger_event:
            q = q.filter(WorkflowExecution.trigger_event == trigger_event)

        execs = q.order_by(WorkflowExecution.created_at.desc()).limit(limit).all()
        return [
            {
                "id": str(e.id),
                "workflow_id": str(e.workflow_id),
                "workflow_name": e.definition.name if e.definition else "Unknown",
                "trigger_event": e.trigger_event,
                "status": e.status,
                "current_step_id": e.current_step_id,
                "retry_count": e.retry_count,
                "start_time": e.start_time.isoformat() if e.start_time else None,
                "completion_time": e.completion_time.isoformat() if e.completion_time else None,
                "error_info": e.error_info,
                "step_results": json.loads(e.step_results) if e.step_results else {},
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in execs
        ]

    @classmethod
    async def retry_execution(cls, execution_id: str, db: Session) -> Dict[str, Any]:
        """Manually retry a failed or stalled execution."""
        ex = db.query(WorkflowExecution).filter(WorkflowExecution.id == uuid.UUID(str(execution_id))).first()
        if not ex:
            raise ValueError(f"Execution '{execution_id}' not found")

        ex.retry_count += 1
        ex.status = "RUNNING"
        ex.error_info = None
        db.commit()

        input_payload = json.loads(ex.input_payload) if ex.input_payload else {}
        return await cls.execute_workflow(
            workflow_id=ex.workflow_id,
            trigger_event=ex.trigger_event,
            input_payload=input_payload,
            db=db,
        )

    @classmethod
    def cancel_execution(cls, execution_id: str, db: Session) -> Dict[str, Any]:
        """Cancel an active or waiting workflow execution."""
        ex = db.query(WorkflowExecution).filter(WorkflowExecution.id == uuid.UUID(str(execution_id))).first()
        if not ex:
            raise ValueError(f"Execution '{execution_id}' not found")

        ex.status = "CANCELLED"
        ex.completion_time = datetime.utcnow()
        db.commit()
        return {"id": str(ex.id), "status": "CANCELLED"}

    @classmethod
    def seed_default_workflows_if_empty(cls, db: Session) -> None:
        """Seed pre-configured native Python automation workflows."""
        count = db.query(WorkflowDefinition).count()
        if count > 0:
            return

        default_workflows = [
            {
                "name": "Auto-Qualify Newly Discovered Leads",
                "description": "Triggered when a new lead is ingested. Researches digital footprint and calculates 5-factor ICP score.",
                "trigger_type": "NEW_LEAD",
                "steps": [
                    {
                        "step_id": "research",
                        "name": "Research Company",
                        "action_type": "RESEARCH_COMPANY",
                        "config": {},
                    },
                    {
                        "step_id": "qualify",
                        "name": "Calculate ICP Score",
                        "action_type": "QUALIFY_LEAD",
                        "config": {},
                    },
                ],
            },
            {
                "name": "Escalate Interested Inbound Reply",
                "description": "Triggered when prospect reply is classified as INTERESTED. Instantly creates an urgent CRM task and activity.",
                "trigger_type": "REPLY_CLASSIFIED",
                "steps": [
                    {
                        "step_id": "check_interest",
                        "name": "Verify Positive Intent",
                        "action_type": "CONDITIONAL_BRANCH",
                        "config": {
                            "field": "classification",
                            "operator": "==",
                            "value": "INTERESTED",
                            "next_step_true": "create_urgent_task",
                            "next_step_false": "log_note",
                        },
                    },
                    {
                        "step_id": "create_urgent_task",
                        "name": "Create Urgent Sales Task",
                        "action_type": "CREATE_CRM_TASK",
                        "config": {
                            "title": "URGENT: Interested Prospect Inbound Reply",
                            "priority": "urgent",
                            "description": "Inbound prospect expressed interest. Review conversation and schedule demo call immediately.",
                        },
                    },
                    {
                        "step_id": "log_note",
                        "name": "Log General Reply Note",
                        "action_type": "LOG_ACTIVITY",
                        "config": {"title": "Inbound reply received and cataloged."},
                    },
                ],
            },
            {
                "name": "Enforce Suppression on Unsubscribe Event",
                "description": "Triggered on UNSUBSCRIBE signal. Adds recipient to global suppression and cancels pending sequence steps.",
                "trigger_type": "UNSUBSCRIBE",
                "steps": [
                    {
                        "step_id": "suppress",
                        "name": "Global Suppression Record",
                        "action_type": "SUPPRESS_CONTACT",
                        "config": {"reason": "USER_UNSUBSCRIBE_REQUEST"},
                    },
                    {
                        "step_id": "log_audit",
                        "name": "Log Compliance Event",
                        "action_type": "LOG_ACTIVITY",
                        "config": {"title": "Contact permanently suppressed upon unsubscribe request."},
                    },
                ],
            },
        ]

        for w in default_workflows:
            db_def = WorkflowDefinition(
                name=w["name"],
                description=w["description"],
                version=1,
                trigger_type=w["trigger_type"],
                steps_json=json.dumps(w["steps"]),
                is_active=True,
            )
            db.add(db_def)
        db.commit()
        logger.info("Seeded default native Python workflows.")


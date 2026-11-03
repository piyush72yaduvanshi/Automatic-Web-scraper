"""Master AI Orchestration Engine.

Coordinates multi-step sales workflows, agent routing, tool execution, human approval boundaries,
and error recovery across the 15 specialized agents.
"""

from typing import Dict, Any, List, Optional
import json
import logging
from sqlalchemy.orm import Session

from app.ai.agents.specialized import AgentRegistry
from app.models.orchestration import AgentRun, AuditLog
from app.models.outreach import OutreachApproval

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """Master workflow coordinator and agent dispatcher."""

    @classmethod
    async def execute_agent(
        cls,
        agent_name: str,
        input_data: Dict[str, Any],
        db: Session,
    ) -> Dict[str, Any]:
        """Dispatch a task to a single specialized agent."""
        agent = AgentRegistry.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: '{agent_name}'. Available: {[a['name'] for a in AgentRegistry.list_agents()]}")
        return await agent.execute(input_data, db)

    @classmethod
    async def run_autonomous_workflow(
        cls,
        user_goal: str,
        db: Session,
        auto_execute_safe_steps: bool = True,
    ) -> Dict[str, Any]:
        """
        End-to-end autonomous workflow orchestration:
        1. Decomposes goal into plan
        2. Executes internal deterministic and intelligence steps
        3. Enqueues any outbound communications for human approval
        """
        planner = AgentRegistry.get_agent("workflow_planning_agent")
        plan_result = await planner.execute({"request": user_goal}, db)
        plan_data = plan_result.get("result", {})

        workflow_name = plan_data.get("workflow_name", "Autonomous Workflow")
        steps = plan_data.get("steps", [])

        execution_results = []
        for step in steps:
            agent_name = step.get("agent")
            action_desc = step.get("action_description", "")
            requires_approval = step.get("requires_human_approval", False)

            if requires_approval or "send" in action_desc.lower() or "outreach" in action_desc.lower():
                # Enqueue for human approval
                approval = OutreachApproval(
                    action_type="AUTONOMOUS_WORKFLOW_ACTION",
                    recipient_destination="Target Prospects",
                    subject=f"Workflow Action: {action_desc}",
                    body_content=f"Proposed Action for workflow '{workflow_name}': {action_desc}",
                    evidence_context=f"Workflow Goal: {user_goal}",
                    status="PENDING",
                )
                db.add(approval)
                db.commit()
                execution_results.append({
                    "step": step.get("step_number"),
                    "agent": agent_name,
                    "status": "QUEUED_FOR_HUMAN_APPROVAL",
                    "approval_id": str(approval.id),
                    "action": action_desc,
                })
            elif auto_execute_safe_steps and agent_name:
                agent = AgentRegistry.get_agent(agent_name)
                if agent:
                    res = await agent.execute({"goal": user_goal, "step_action": action_desc}, db)
                    execution_results.append({
                        "step": step.get("step_number"),
                        "agent": agent_name,
                        "status": "COMPLETED" if res.get("success") else "FAILED",
                        "result": res.get("result"),
                    })
                else:
                    execution_results.append({
                        "step": step.get("step_number"),
                        "agent": agent_name,
                        "status": "SKIPPED_UNKNOWN_AGENT",
                    })

        # Record audit log
        log = AuditLog(
            action="WORKFLOW_EXECUTED",
            entity_type="workflow",
            details=json.dumps({"goal": user_goal, "name": workflow_name, "steps_count": len(steps)}),
        )
        db.add(log)
        db.commit()

        return {
            "workflow_name": workflow_name,
            "goal": user_goal,
            "total_steps": len(steps),
            "execution_log": execution_results,
        }

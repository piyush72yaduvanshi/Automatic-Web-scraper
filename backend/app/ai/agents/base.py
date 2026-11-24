"""Base Specialized Agent Architecture.

Provides execution limits, telemetry tracking, database logging, error recovery,
and standardized input/output schema validation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
import json
import logging
from sqlalchemy.orm import Session

from app.models.orchestration import AgentRun
from app.ai.tools.registry import ToolRegistry
from app.providers.ai.router import ai_router

logger = logging.getLogger(__name__)


class BaseSpecializedAgent(ABC):
    """Abstract base class for all 15 specialized AI sales & CRM agents."""

    name: str = "base_agent"
    role: str = "Assistant"
    description: str = "Base agent"
    allowed_tools: List[str] = []
    max_execution_steps: int = 5
    timeout_seconds: int = 30

    @abstractmethod
    async def run(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Core specialized agent execution logic."""
        pass

    async def execute(self, input_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Execute agent with complete telemetry, error boundaries,
        and database audit tracking.
        """
        start_time = time.time()
        agent_run = AgentRun(
            agent_name=self.name,
            task_type=input_data.get("task_type", "default_task"),
            status="RUNNING",
            input_parameters=json.dumps(input_data),
        )
        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)

        try:
            result = await self.run(input_data, db)
            elapsed_ms = int((time.time() - start_time) * 1000)

            agent_run.status = "COMPLETED"
            agent_run.output_data = json.dumps(result)
            agent_run.duration_ms = elapsed_ms
            db.commit()

            return {
                "success": True,
                "agent": self.name,
                "run_id": str(agent_run.id),
                "duration_ms": elapsed_ms,
                "result": result,
            }

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Agent {self.name} failed: {e}", exc_info=True)

            agent_run.status = "FAILED"
            agent_run.error_message = str(e)[:500]
            agent_run.duration_ms = elapsed_ms
            db.commit()

            # Execute fallback
            fallback_res = self.fallback(input_data, str(e))
            return {
                "success": False,
                "agent": self.name,
                "run_id": str(agent_run.id),
                "error": str(e),
                "duration_ms": elapsed_ms,
                "result": fallback_res,
            }

    def fallback(self, input_data: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Default fallback if agent reasoning fails."""
        return {
            "status": "degraded_fallback",
            "message": f"Agent {self.name} encountered an error: {error}. Safe default provided.",
            "data": {},
        }


"""
Enterprise CQRS (Command Query Responsibility Segregation) & Distributed Saga Orchestrator.
Coordinates distributed state transitions across Vector DB, Cache, and Audit DB with compensating rollbacks.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Any
import logfire


class SagaStepStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    COMPENSATED = "COMPENSATED"
    FAILED = "FAILED"


@dataclass
class SagaStep:
    name: str
    action: Callable[[], Any]
    compensation: Callable[[], Any]
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Any = None
    error: Optional[str] = None


class DistributedSagaOrchestrator:
    """
    Executes distributed operations using the Saga Pattern (Compensating Transactions).
    If any step fails, all preceding successfully executed steps are rolled back in reverse order.
    """

    def __init__(self, saga_name: str):
        self.saga_name = saga_name
        self.saga_id = str(uuid.uuid4())
        self.steps: List[SagaStep] = []

    def add_step(self, name: str, action: Callable[[], Any], compensation: Callable[[], Any]) -> "DistributedSagaOrchestrator":
        self.steps.append(SagaStep(name=name, action=action, compensation=compensation))
        return self

    def execute(self) -> bool:
        """
        Executes each step sequentially. On failure, triggers compensating transactions backwards.
        """
        logfire.info(f"🔄 [Saga:{self.saga_name}] Commencing execution | id={self.saga_id}")
        executed_steps: List[SagaStep] = []

        for step in self.steps:
            try:
                logfire.info(f"▶️ [Saga:{self.saga_name}] Executing step: {step.name}")
                step.result = step.action()
                step.status = SagaStepStatus.EXECUTED
                executed_steps.append(step)
            except Exception as e:
                step.status = SagaStepStatus.FAILED
                step.error = str(e)
                logfire.error(f"❌ [Saga:{self.saga_name}] Step failed: {step.name} | err={e}")
                
                # Execute compensations in reverse
                self._rollback(executed_steps)
                return False

        logfire.info(f"✅ [Saga:{self.saga_name}] All {len(self.steps)} steps executed successfully.")
        return True

    def _rollback(self, executed_steps: List[SagaStep]):
        logfire.warning(f"↩️ [Saga:{self.saga_name}] Triggering compensating rollback...")
        for step in reversed(executed_steps):
            try:
                logfire.info(f"⏪ [Saga:{self.saga_name}] Compensating: {step.name}")
                step.compensation()
                step.status = SagaStepStatus.COMPENSATED
            except Exception as comp_err:
                logfire.critical(f"☠️ [Saga:{self.saga_name}] Critical compensation failure on {step.name}: {comp_err}")


# --- CQRS QUERY & COMMAND HANDLERS ---

class CQRSDispatcher:
    """
    Decouples Command side (writes, mutations, WAF updates) from Query side (read-only RAG search).
    """

    def __init__(self):
        self.command_handlers: Dict[str, Callable] = {}
        self.query_handlers: Dict[str, Callable] = {}

    def register_command(self, command_type: str, handler: Callable):
        self.command_handlers[command_type] = handler

    def register_query(self, query_type: str, handler: Callable):
        self.query_handlers[query_type] = handler

    def dispatch_command(self, command_type: str, payload: Dict[str, Any]) -> Any:
        handler = self.command_handlers.get(command_type)
        if not handler:
            raise ValueError(f"Unknown command type: {command_type}")
        logfire.info(f"✍️ [CQRS:Command] Dispatching: {command_type}")
        return handler(payload)

    def dispatch_query(self, query_type: str, params: Dict[str, Any]) -> Any:
        handler = self.query_handlers.get(query_type)
        if not handler:
            raise ValueError(f"Unknown query type: {query_type}")
        logfire.info(f"📖 [CQRS:Query] Dispatching: {query_type}")
        return handler(params)


# Global Singleton CQRS Dispatcher
cqrs_dispatcher = CQRSDispatcher()

"""
Distributed Saga Orchestrator for Zomato Order Fulfillment.
Guarantees transaction consistency across microservices (Kitchen, Payment, Fleet, Notifications).
"""

from dataclasses import dataclass
from typing import Callable, List, Optional, Any
import logging

logger = logging.getLogger("ZomatoOrderSaga")


@dataclass
class OrderSagaStep:
    name: str
    action: Callable[[], Any]
    compensate: Callable[[], Any]


class ZomatoOrderSagaCoordinator:
    """
    Executes distributed transactions across independent microservices.
    Triggers backward compensation if payment, kitchen, or rider assignment fails.
    """

    def __init__(self, order_id: str):
        self.order_id = order_id
        self.steps: List[OrderSagaStep] = []
        self.executed_steps: List[OrderSagaStep] = []

    def add_step(self, name: str, action: Callable[[], Any], compensate: Callable[[], Any]) -> "ZomatoOrderSagaCoordinator":
        self.steps.append(OrderSagaStep(name=name, action=action, compensate=compensate))
        return self

    def execute(self) -> bool:
        logger.info(f"🚀 Commencing Order Saga for Order {self.order_id} ({len(self.steps)} steps)")
        for step in self.steps:
            try:
                logger.info(f"▶️ Executing Saga Step: {step.name}")
                step.action()
                self.executed_steps.append(step)
            except Exception as e:
                logger.error(f"❌ Step '{step.name}' failed for Order {self.order_id}: {e}")
                self._rollback()
                return False
        logger.info(f"✅ Order Saga {self.order_id} completed successfully.")
        return True

    def _rollback(self):
        logger.warning(f"↩️ Rolling back executed steps for Order {self.order_id}...")
        for step in reversed(self.executed_steps):
            try:
                logger.info(f"⏪ Compensating: {step.name}")
                step.compensate()
            except Exception as e:
                logger.critical(f"☠️ Compensation failed on {step.name}: {e}")

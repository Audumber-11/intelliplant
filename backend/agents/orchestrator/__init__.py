import asyncio
import uuid
import json
import random
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable, Set
from collections import defaultdict, deque

from .schemas import (
    AgentMessage, AgentHealth, AgentType, AgentStatus, MessagePriority,
    OrchestratorDecision, MonitoringConfig, SystemStatus
)


class LLMReasoningEngine:
    """LLM-powered reasoning for agent decisions."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._use_mock = not bool(api_key)

    async def reason(self, context: str, options: List[str] = None) -> Dict[str, Any]:
        if self._use_mock:
            await asyncio.sleep(0.05)
            return self._mock_reason(context, options)

        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            prompt = f"""Given the following industrial safety context, make a decision.
Context: {context}
Respond with JSON: {{"decision": "...", "confidence": 0.0-1.0, "reasoning": "...", "actions": [...]}}"""
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            return json.loads(response.content[0].text)
        except Exception:
            return self._mock_reason(context, options)

    def _mock_reason(self, context: str, options: List[str] = None) -> Dict[str, Any]:
        risk_keywords = ["critical", "emergency", "fire", "leak", "explosion", "fatality", "high"]
        has_risk = any(kw in context.lower() for kw in risk_keywords)

        if has_risk:
            return {
                "decision": "escalate_to_emergency",
                "confidence": round(random.uniform(0.8, 0.95), 2),
                "reasoning": "Critical risk indicators detected requiring immediate escalation",
                "actions": [
                    {"agent": "emergency", "action": "activate_response", "priority": "critical"},
                    {"agent": "cctv", "action": "focus_zone", "priority": "high"},
                    {"agent": "iot_gateway", "action": "increase_polling", "priority": "high"},
                ],
            }

        return {
            "decision": "monitor_and_log",
            "confidence": round(random.uniform(0.6, 0.85), 2),
            "reasoning": "No critical indicators detected, continuing standard monitoring",
            "actions": [
                {"agent": "risk_engine", "action": "continue_monitoring", "priority": "low"},
            ],
        }


class AgentOrchestrator:
    """Orchestrator that coordinates all agents with autonomous decision-making."""

    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        self.llm = LLMReasoningEngine()
        self.message_queue: deque = deque(maxlen=5000)
        self.decisions: List[OrchestratorDecision] = []
        self.agent_health: Dict[AgentType, AgentHealth] = {}
        self.message_handlers: Dict[AgentType, List[Callable]] = defaultdict(list)
        self._running = False
        self._start_time = datetime.utcnow()
        self._task_count = 0
        self._error_count = 0

        for agent_type in AgentType:
            self.agent_health[agent_type] = AgentHealth(
                agent_id=agent_type,
                status=AgentStatus.IDLE,
                last_active=datetime.utcnow(),
            )

    def register_handler(self, agent_type: AgentType, handler: Callable):
        self.message_handlers[agent_type].append(handler)

    def send_message(self, msg: AgentMessage):
        self.message_queue.append(msg)

    async def broadcast(self, message_type: str, payload: Dict[str, Any],
                        priority: MessagePriority = MessagePriority.MEDIUM):
        for agent_type in AgentType:
            if agent_type == AgentType.ORCHESTRATOR:
                continue
            msg = AgentMessage(
                message_id=str(uuid.uuid4()),
                source_agent=AgentType.ORCHESTRATOR,
                target_agent=agent_type,
                message_type=message_type,
                priority=priority,
                payload=payload,
                timestamp=datetime.utcnow(),
            )
            self.send_message(msg)

    async def run_cycle(self):
        """One orchestration cycle: process messages, evaluate, decide, dispatch."""
        self._task_count += 1
        processed = []

        while self.message_queue:
            msg = self.message_queue.popleft()
            handlers = self.message_handlers.get(msg.target_agent, [])
            for handler in handlers:
                try:
                    await handler(msg)
                except Exception as e:
                    self._error_count += 1
                    agent = self.agent_health[msg.target_agent]
                    agent.error_count += 1
                    agent.status = AgentStatus.ERROR
            processed.append(msg)

        context = self._build_context()
        if self.config.llm_reasoning:
            decision = await self.llm.reason(context)
            dec = OrchestratorDecision(
                decision_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                trigger="monitoring_cycle",
                reasoning=decision.get("reasoning", ""),
                actions=decision.get("actions", []),
                confidence=decision.get("confidence", 0.5),
            )
            self.decisions.append(dec)

            for action in decision.get("actions", []):
                try:
                    agent_type = AgentType(action["agent"])
                    msg = AgentMessage(
                        message_id=str(uuid.uuid4()),
                        source_agent=AgentType.ORCHESTRATOR,
                        target_agent=agent_type,
                        message_type=action["action"],
                        priority=MessagePriority(action.get("priority", "medium")),
                        payload=action,
                        timestamp=datetime.utcnow(),
                    )
                    self.send_message(msg)
                except (ValueError, KeyError):
                    pass

        await self._update_health()

    def _build_context(self) -> str:
        health_parts = []
        for agent_type, health in self.agent_health.items():
            health_parts.append(f"{agent_type.value}: {health.status.value} ({health.task_count} tasks)")
        return "System context:\n" + "\n".join(health_parts) + \
               f"\nMessages queued: {len(self.message_queue)}" + \
               f"\nDecisions made: {len(self.decisions)}" + \
               f"\nErrors: {self._error_count}"

    async def _update_health(self):
        for agent_type in self.agent_health:
            health = self.agent_health[agent_type]
            if health.status == AgentStatus.ERROR:
                health.status = AgentStatus.DEGRADED
            health.last_active = datetime.utcnow()
            health.task_count = self._task_count

    async def start_background_monitoring(self):
        """Starts the autonomous background monitoring loop."""
        self._running = True
        cycle = 0
        while self._running:
            cycle += 1
            try:
                if cycle % 3 == 0:
                    await self.broadcast(
                        "status_check",
                        {"cycle": cycle, "timestamp": str(datetime.utcnow())},
                        MessagePriority.LOW,
                    )
                await self.run_cycle()
            except Exception as e:
                self._error_count += 1
            await asyncio.sleep(self.config.interval_seconds)

    def stop(self):
        self._running = False

    def get_system_status(self) -> SystemStatus:
        critical = sum(1 for d in self.decisions[-50:]
                      if any(a.get("priority") == "critical" for a in d.actions))
        return SystemStatus(
            overall_status="healthy" if self._error_count < 10 else "degraded",
            agents=list(self.agent_health.values()),
            active_decisions=sum(1 for d in self.decisions[-20:]
                                if d.confidence < 0.8),
            messages_in_queue=len(self.message_queue),
            uptime_hours=round((datetime.utcnow() - self._start_time).total_seconds() / 3600, 2),
            last_orchestration=datetime.utcnow() if self._task_count > 0 else None,
            critical_alerts_active=critical,
            llm_enabled=self.config.llm_reasoning,
        )

    def get_recent_decisions(self, n: int = 10) -> List[OrchestratorDecision]:
        return list(reversed(self.decisions[-n:]))

    def get_agent_details(self, agent_type: AgentType) -> Optional[AgentHealth]:
        return self.agent_health.get(agent_type)

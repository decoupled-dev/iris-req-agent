"""Simulated model. Plays the part of an LLM turn by turn, using only what tools have returned.

A policy per agent (app/runtime/simulation) decides the next turn from the transcript, so the
loop, tools, prompts, and result schema are exercised exactly as a real provider would.
"""

from __future__ import annotations

import json
import os
import random
import time

from ..simulation import POLICIES
from ..types import ModelRequest, ModelTurn, Usage


def _tokens(obj) -> int:
    text = obj if isinstance(obj, str) else json.dumps(obj, default=str)
    return max(1, len(text) // 4)


class SimulatedProvider:
    name = "simulated"

    def __init__(self, latency_ms: list[int] | tuple[int, int] = (350, 1200), seed: int = 7,
                 failure_rate: float = 0.0):
        env = os.environ.get("SEW1_SIM_LATENCY_MS")
        self.latency = (int(env), int(env)) if env is not None else tuple(latency_ms)
        self.failure_rate = failure_rate
        self.seed = seed

    def generate(self, request: ModelRequest) -> ModelTurn:
        policy = POLICIES.get(request.agent_id)
        if policy is None:
            raise RuntimeError(f"No simulation policy for {request.agent_id}")
        rng = random.Random(f"{self.seed}:{request.agent_id}:{len(request.messages)}:{time.time_ns()}")
        if self.failure_rate and rng.random() < self.failure_rate:
            raise RuntimeError("Simulated provider error: upstream overloaded (retryable)")
        turn = policy(request)
        latency = rng.randint(*self.latency) if self.latency[1] else 0
        time.sleep(latency / 1000)
        turn.latency_ms = latency
        turn.usage = Usage(
            input_tokens=_tokens(request.system) + sum(_tokens(m.model_dump()) for m in request.messages)
            + sum(_tokens(t.model_dump()) for t in request.tools),
            output_tokens=_tokens(turn.thinking) + _tokens(turn.text)
            + sum(_tokens(c.input) for c in turn.tool_calls),
        )
        turn.stop_reason = "tool_use" if turn.tool_calls else "end_turn"
        return turn

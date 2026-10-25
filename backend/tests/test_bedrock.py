"""Companion cognition talks to a Bedrock AgentCore harness; tools stay local."""

import json
import threading

import pytest

from app.agents import AGENTS
from app.agents.bedrock import BedrockHarnessAgent, session_id
from app.models import RunContext, RunStatus


def _stream(events):
    return {"stream": events}


def _tool_use(*calls):
    events = [{"messageStart": {"role": "assistant"}}]
    for i, (name, payload) in enumerate(calls):
        events += [
            {"contentBlockStart": {"contentBlockIndex": i, "start": {
                "toolUse": {"toolUseId": f"tu_{name}", "name": name, "type": "tool_use"}}}},
            {"contentBlockDelta": {"contentBlockIndex": i, "delta": {"toolUse": {"input": json.dumps(payload)}}}},
            {"contentBlockStop": {"contentBlockIndex": i}},
        ]
    events += [
        {"messageStop": {"stopReason": "tool_use"}},
        {"metadata": {"usage": {"inputTokens": 12, "outputTokens": 4}, "metrics": {"latencyMs": 30}}},
    ]
    return events


class FakeClient:
    def __init__(self, streams):
        self.streams = list(streams)
        self.calls = []

    def invoke_harness(self, **kwargs):
        self.calls.append(kwargs)
        return _stream(self.streams.pop(0))


def _ctx():
    return RunContext(run_id="run_abcd1234", agent_id="companion_cognition",
                      project={"name": "In-car voice assistant", "target_cognitive_level": "CL5"},
                      requirements=[], dependency_runs=[])


def test_session_id_meets_agentcore_rules():
    sid = session_id("run_abcd1234")
    assert 33 <= len(sid) <= 100
    assert sid[0].isalnum()


def test_harness_tool_round_trip_submits_result():
    proposal = {
        "title": "Grounding", "statement": "The voice assistant shall ground an answer in a source.",
        "rationale": "A partner does not invent vehicle state.", "source": "find_cog_01",
        "category": "SYS-COG", "priority": "Must", "verification_method": "Test",
        "acceptance_criteria": "An answer with no source is refused.", "cognitive_capability": ["COG-01"],
    }
    submit = {"summary": "Target CL5, register specifies CL0.",
              "findings": [{"id": "find_cog_01", "title": "COG-01", "statement": "not covered",
                            "source": "Companion cognition (v1)"}],
              "proposals": [proposal], "metrics": {"specified_before": "CL0", "gaps": 1}}
    client = FakeClient([
        _tool_use(("get_capability_catalog", {}), ("get_cognitive_coverage", {})),
        _tool_use(("submit_result", submit)),
    ])
    trace = []
    result = BedrockHarnessAgent(AGENTS["companion_cognition"], {
        "harness_arn": "arn:aws:bedrock-agentcore:ap-southeast-2:825457798894:harness/CompanionCognition-6M6lAgDhf6",
        "region": "ap-southeast-2", "qualifier": "DEFAULT",
    }, client=client).run(_ctx(), threading.Event(), lambda kind, data: trace.append(kind))

    assert result.status == RunStatus.succeeded
    assert result.metrics["specified_before"] == "CL0"
    assert result.metrics["provider"] == "bedrock-agentcore"
    assert result.proposals[0].source == "find_cog_01"
    assert client.calls[0]["qualifier"] == "DEFAULT"
    assert client.calls[0]["runtimeSessionId"] == client.calls[1]["runtimeSessionId"]
    names = [t["name"] for t in client.calls[0]["tools"]]
    assert names == ["get_capability_catalog", "get_cognitive_coverage", "list_requirements", "submit_result"]
    returned = client.calls[1]["messages"][-1]["content"]
    assert {block["toolResult"]["toolUseId"] for block in returned} == {
        "tu_get_capability_catalog", "tu_get_cognitive_coverage"}
    assert trace[0] == "start"
    assert "tool_call" in trace and "result" in trace


def test_harness_error_event_fails_the_turn():
    client = FakeClient([[{"runtimeClientError": {"message": "Access denied"}}]])
    with pytest.raises(RuntimeError, match="Access denied"):
        BedrockHarnessAgent(AGENTS["companion_cognition"], {
            "harness_arn": "arn:aws:bedrock-agentcore:ap-southeast-2:825457798894:harness/CompanionCognition-6M6lAgDhf6",
        }, client=client).run(_ctx(), threading.Event(), lambda *_: None)

# Remote agent contract

Any agent can run in the workbench process or on another host. AWS, Google Cloud, and a lab server are the same from the workbench: an HTTPS endpoint that speaks this contract.

The workbench is usable with every agent set to `local`. Remote mode is configuration, not a prerequisite.

## Configuration

Local file, one block per agent:

```yaml
agents:
  gdpr_privacy:
    mode: local
  oem_feature_research:
    mode: remote
    endpoint: https://agent.example.com/v1/agents/oem_feature_research
    auth_env: OEM_AGENT_TOKEN
```

`auth_env` names an environment variable. The workbench sends its value as a bearer token. The file stores the variable name, not the secret.

## Start a run

`POST {endpoint}/runs`

```json
{
  "run_id": "run_8f3a",
  "agent_id": "oem_feature_research",
  "project": {
    "name": "In-car voice assistant",
    "deployment_assumption": "AAOS or QNX, undecided",
    "target_cognitive_level": "CL5"
  },
  "register": [],
  "dependency_runs": []
}
```

`register` is the current requirement list (id, statement, state, version, cognitive_capability). `dependency_runs` contains the latest succeeded findings and proposals from agents this one depends on. Research agents receive an empty `dependency_runs`.

Response:

```json
{
  "run_id": "run_8f3a",
  "status": "accepted"
}
```

The worker executes after this response. The workbench marks the card running.

## Poll status

`GET {endpoint}/runs/{run_id}`

While working:

```json
{
  "run_id": "run_8f3a",
  "status": "running"
}
```

On success:

```json
{
  "run_id": "run_8f3a",
  "status": "succeeded",
  "summary": "Compared four production assistants and proposed 12 requirements.",
  "findings": [
    {
      "id": "find_oem_001",
      "title": "MBUX multi-zone voice",
      "statement": "Mercedes-Benz MBUX supports speaking to different seats.",
      "source": "Knowledge pack: Production assistants",
      "confidence": "high"
    }
  ],
  "proposals": [
    {
      "id": "SYS-FUNC-020",
      "title": "Seat-aware dialogue",
      "statement": "The voice assistant shall attribute a command to the speaking seat.",
      "rationale": "Rear passengers must be able to control their own climate without changing the driver's zone.",
      "source": "find_oem_001",
      "category": "SYS-FUNC",
      "priority": "Should",
      "preliminary_asil": "",
      "asil_note": "",
      "cognitive_capability": ["COG-01"],
      "standard_references": [],
      "verification_method": "Test",
      "acceptance_criteria": "A rear-seat climate command does not change the driver temperature setpoint.",
      "change_note": "Initial proposal"
    }
  ]
}
```

The compliance gate sends `"proposals": []` and adds `"metrics": {"specified_cognitive_level": "CL2", "uncovered": ["COG-08", …]}`.

Agent IDs: `google_assistant_reference`, `oem_feature_research`, `customer_expectations`, `companion_cognition`, `requirements_synthesis`, `gdpr_privacy`, `driver_distraction`, `safety_cybersecurity`, `compliance_gate`.

On failure:

```json
{
  "run_id": "run_8f3a",
  "status": "failed",
  "summary": "Knowledge source unavailable.",
  "findings": [],
  "proposals": []
}
```

## Cancel

`POST {endpoint}/runs/{run_id}/cancel`

The worker stops if it still can, and the next poll returns `"status": "cancelled"`. The workbench also marks the run cancelled locally if the worker does not answer.

## Status values

`accepted` on the POST only. Poll status is `queued`, `running`, `succeeded`, `failed`, or `cancelled`.

## Local agents

The in-process agent returns the same success object. The orchestrator writes it into the run log. The UI cannot tell from the proposal whether the author was local or remote; the run log records `mode`.

## Models in a worker

A worker may run the same agent loop, prompts, and tools as the workbench ([11-agent-runtime.md](11-agent-runtime.md)) against any provider. Whatever it calls, it returns the JSON fields above, never writes baselined statements, and leaves accept and reject to the workbench.

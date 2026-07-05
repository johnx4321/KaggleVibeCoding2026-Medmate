# MedMate Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Web UI (Chat Interface)                     │
│              app/static/index.html (FastAPI served)              │
└──────────────────────────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────▼─────────────────┐
                    │     FastAPI Server (Port 8000)     │
                    │  Mode: DEMO (no key) | LIVE (key)  │
                    └──────────────────┬─────────────────┘
                                       │
                    ┌──────────────────▼─────────────────┐
                    │   DEMO Mode (Deterministic)       │
                    │   orchestrator_demo.py             │
                    │   - Keyword routing                │
                    │   - No LLM required                │
                    └──────────────────┬─────────────────┘
                                       │
                                  [OR]│[OR]
                                       │
                    ┌──────────────────▼─────────────────┐
                    │   LIVE Mode (Gemini LLM)          │
                    │   Google ADK Runner                │
                    │   - Full multi-agent system        │
                    │   - Requires GOOGLE_API_KEY        │
                    └──────────────────┬─────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                          │                          │
            ▼                          ▼                          ▼
     ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
     │  Root Agent     │       │  Root Agent     │       │  Root Agent     │
     │  (Coordinator)  │       │  (Coordinator)  │       │  (Coordinator)  │
     │                 │       │                 │       │                 │
     │  Instruction:   │       │  Instruction:   │       │  Instruction:   │
     │  "Route to      │       │  "Route to      │       │  "Route to      │
     │   specialists"  │       │   specialists"  │       │   specialists"  │
     │                 │       │                 │       │                 │
     │  Security:      │       │  Security:      │       │  Security:      │
     │  - PII redact   │       │  - PII redact   │       │  - PII redact   │
     │  - Guardrails   │       │  - Guardrails   │       │  - Guardrails   │
     └────────┬────────┘       │  - Confirm      │       │  - Confirm      │
              │                 │  - Disclaimer   │       │  - Disclaimer   │
              │                 └─────────────────┘       └─────────────────┘
              │
    ┌─────────┴──────────┬──────────────┬─────────────┐
    │                    │              │             │
    ▼                    ▼              ▼             ▼
┌──────────────┐  ┌──────────────┐  ┌───────────┐  ┌────────────────┐
│Intake Agent  │  │Interaction   │  │Scheduler  │  │ Memory Store   │
│              │  │Agent         │  │Agent      │  │ (Persistent)   │
│Tools:        │  │              │  │           │  │                │
│- add_med     │  │Tools:        │  │Tools:     │  │ ~/.medmate/    │
│- remove_med  │  │- check_      │  │- build_   │  │ profile.json   │
│- list_meds   │  │  interactions│  │  schedule │  │                │
│- add_allergy │  │- lookup_     │  │- get_next │  │Contains:       │
│- add_cond    │  │  drug_info   │  │  doses    │  │- medications[] │
│              │  │              │  │- export_  │  │- allergies[]   │
│Calls: memory │  │Calls: MCP    │  │  schedule │  │- conditions[]  │
│store         │  │server        │  │           │  │- timestamps    │
└──────────────┘  └──────────────┘  │Calls:     │  └────────────────┘
                                    │memory     │
                                    │store      │
                                    └───────────┘

                          ┌─────────────────────┐
                          │    MCP Server       │
                          │  (stdio-based)      │
                          │                     │
                          │  Tools:             │
                          │  - check_           │
                          │    interactions     │
                          │  - lookup_drug_info │
                          │                     │
                          │  Data source:       │
                          │  interactions.json  │
                          └─────────────────────┘
```

## Data Flow Example: "Check Interactions"

```
User Input: "Check interactions"
       │
       ▼
┌─────────────────────────────┐
│ FastAPI /chat endpoint      │
│ Mode: DEMO or LIVE?         │
└────────────┬────────────────┘
             │
       ┌─────┴──────┐
       │            │
       ▼            ▼
    DEMO        LIVE
    [Demo       [ADK
     Orchest-   Runner]
     rator]
       │            │
       │            ▼
       │       Root Agent
       │       routes to
       │       Interaction
       │       Agent
       │            │
       └─────┬──────┘
             │
             ▼
   Interaction Agent
   calls: check_interactions(drugs=[])
             │
       ┌─────┴──────┐
       │            │
       ▼            ▼
    DEMO      LIVE (MCP)
    [Local    [MCP Server
     func]     python
              subprocess]
             │            │
             └─────┬──────┘
                   │
                   ▼
       Check interactions.json
       for drug pairs
                   │
                   ▼
       Return: {interaction_count, severity, notes}
                   │
                   ▼
       Agent formats response:
       "🚨 Found X interaction(s)..."
                   │
                   ▼
       FastAPI returns JSON
                   │
                   ▼
       Web UI displays in chat
```

## Components

### Web Frontend (`app/static/index.html`)
- Simple chat interface
- Sends POST requests to `/chat` endpoint
- Displays responses with markdown formatting
- Shows mode badge (DEMO or LIVE)

### API Server (`app/server.py`)
- FastAPI with `/chat`, `/health`, `/profile` endpoints
- Switches between DEMO and LIVE mode based on env var
- Serves static files

### DEMO Mode (`app/orchestrator_demo.py`)
- Deterministic keyword-based router
- Calls same tools as LIVE mode
- No LLM—perfect for offline verification
- Fully functional for video demos

### LIVE Mode (ADK + Gemini)
- Google ADK `LlmAgent` with Gemini model
- Multi-agent coordination
- Full reasoning capability
- Requires `GOOGLE_API_KEY` env var

### Agents (`medmate/agent.py`, `medmate/sub_agents/*.py`)
- Root coordinator agent
- 3 specialist sub-agents
- Each has own instruction, tools, LLM calls
- Security callbacks applied at root level

### Tools (`medmate/tools/*.py`)
- FunctionTool wrappers around core logic
- Profile tools: CRUD for medications, allergies, conditions
- Schedule tools: daily timeline, next doses, iCal export
- Interaction tools: local and MCP-based lookups

### Memory Store (`medmate/memory/store.py`)
- JSON-based persistent profile
- Located at `~/.medmate/profile.json`
- Loaded into agent context each session
- Enables long-term state across conversations

### Security Layer (`medmate/security/`)
- PII redaction: strip emails, phones, SSNs, etc.
- Medical guardrail: intercept unsafe requests
- Tool validation: confirm destructive operations
- Callbacks injected into ADK agent

### MCP Server (`mcp_server/server.py`)
- Runs as stdio subprocess
- FastMCP SDK (official MCP library)
- Tools: `check_interactions`, `lookup_drug_info`
- Optional; demo works without it

### Data (`medmate/data/interactions.json`)
- Curated list of common drug-drug interactions
- Each entry: {drug_a, drug_b, severity, note}
- Clearly labeled "illustrative"
- Can be swapped for live pharmacy API

## Deployment Paths

### Local Development
```
python -m uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

### Docker
```
docker build -t medmate .
docker run -e MEDMATE_MODE=demo -p 8000:8000 medmate
```

### Google Cloud Run
```
gcloud build submit --tag gcr.io/PROJECT_ID/medmate
gcloud run deploy medmate --image gcr.io/PROJECT_ID/medmate --allow-unauthenticated
```

## Security Architecture

```
┌────────────────────────────────────────┐
│  User Input (Chat Message)             │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  before_model_callback                 │
│  ├─ PII Redaction (email, phone, SSN)  │
│  ├─ Safety Guardrail Check             │
│  │  └─ If unsafe: return disclaimer    │
│  └─ Pass through to model              │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  Agent Reasoning (Gemini in LIVE mode) │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  before_tool_callback                  │
│  ├─ Validate tool arguments            │
│  ├─ For destructive tools: confirm     │
│  └─ Allow or block execution           │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  Tool Execution                        │
│  (profile, schedule, interaction)      │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  after_model_callback                  │
│  └─ Append medical disclaimer          │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  User Output (Response)                │
└────────────────────────────────────────┘
```

## Testing Strategy

- **Unit tests** (`test_tools.py`): Tool logic, memory store, interactions
- **Security tests** (`test_guardrails.py`): PII redaction, guardrails, callbacks
- **Integration tests** (`test_orchestrator.py`): DEMO mode end-to-end
- **No network mocks**: Uses real interactions.json, real memory store
- **24 tests, all passing**

## Future Enhancements

- [ ] Full MCP integration (agents call MCP server directly)
- [ ] Pharmacy API integration (refill tracking)
- [ ] SMS/email reminders
- [ ] Doctor sharing (read-only access)
- [ ] Mobile app
- [ ] HIPAA compliance

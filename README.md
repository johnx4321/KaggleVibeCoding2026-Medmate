# MedMate: Personal Medication & Care Assistant

A multi-agent AI system for managing medications, checking drug interactions, and building medication schedules. Built with Google's ADK and Gemini, with a secure, privacy-focused design.

**Submission:** [Kaggle AI Agents: Intensive Vibe Coding Capstone](https://www.kaggle.com/competitions/ai-agents-intensive-vibe-coding-capstone) — **Concierge Agents Track**

---

## Problem Statement

Millions of people struggle to manage multiple medications safely:
- **Forgetting doses** leads to missed treatments and health complications
- **Drug interactions** go unnoticed until emergencies occur
- **Manual tracking** is error-prone and fragmented across notes, pill bottles, and doctor visits
- **Privacy concerns** with centralized medication storage

MedMate solves this by providing a **personal, on-device medication organizer** that users control entirely.

---

## Solution: Multi-Agent Architecture

```
                    ┌────────────────── Web UI / Chat Interface ───────────────────┐
                    │                                                              │
                    └──────────────────────────────┬───────────────────────────────┘
                                                   │
                         FastAPI (DEMO / LIVE modes)
                                   │
                    ┌──────────────┴──────────────┐
            DEMO MODE (no key)         LIVE MODE (Gemini)
            Deterministic routing      ADK + Gemini LLM
                    │                              │
                    └─────────────┬────────────────┘
                                  │
            ┌─────────────────────▼──────────────────────┐
            │  MedMate Coordinator Agent (LlmAgent)      │
            │  - Security: PII redaction + guardrails    │
            │  - Routes to specialists                   │
            └─────────────────────┬──────────────────────┘
                                  │
            ┌─────────┬───────────┼───────────┬─────────┐
            │         │           │           │         │
            ▼         ▼           ▼           ▼         ▼
      Intake Agent  Interaction   Scheduler   MCP    Profile
      - add med     Agent         Agent      Server  Store
      - remove med  - check       - build              (Memory)
      - list        interactions  schedule
      - allergies   - safety      - reminders
```

### Key Concepts Demonstrated (≥3 required)

1. **Multi-Agent System (ADK)** ✓
   - Coordinator + 3 specialist sub-agents
   - Each with focused instructions and tools
   - `[medmate/agent.py](medmate/agent.py)`, `[medmate/sub_agents/](medmate/sub_agents/)`

2. **MCP Server** ✓
   - Custom stdio-based MCP server
   - Tools: `check_interactions`, `lookup_drug_info`
   - `[mcp_server/server.py](mcp_server/server.py)`

3. **Security Features** ✓
   - PII redaction (email, phone, SSN, DOB)
   - Medical safety guardrails (refuse definitive dosing advice)
   - Tool-arg validation & confirmation gates
   - Output disclaimers
   - `[medmate/security/](medmate/security/)`

4. **Agent Skills & Long-Term Memory** ✓
   - Persistent user profile (meds, allergies, conditions)
   - State restored across sessions
   - `[medmate/memory/store.py](medmate/memory/store.py)`

5. **Deployability** ✓
   - Dockerfile + Cloud Run instructions
   - `[Dockerfile](Dockerfile)`

6. **External API Integration** ✓ (bonus)
   - openFDA API for real drug labels (with graceful fallback)
   - `[medmate/tools/openfda_tool.py](medmate/tools/openfda_tool.py)`

---

## Architecture Details

### Agents

- **Coordinator (root_agent):** Routes user requests to specialists. Enforces security policies.
- **Intake Agent:** Manages medication profile (add/remove/list), allergies, conditions.
- **Interaction Agent:** Checks for drug-drug interactions and safety warnings.
- **Scheduler Agent:** Builds daily schedules, calculates next doses, exports to iCal.

### Tools

| Tool | Purpose | Location |
|------|---------|----------|
| `add_medication` | Add med to profile | `[medmate/tools/profile_tools.py](medmate/tools/profile_tools.py)` |
| `remove_medication` | Remove med from profile | `[medmate/tools/profile_tools.py](medmate/tools/profile_tools.py)` |
| `list_medications` | Show all meds | `[medmate/tools/profile_tools.py](medmate/tools/profile_tools.py)` |
| `add_allergy` | Record allergy | `[medmate/tools/profile_tools.py](medmate/tools/profile_tools.py)` |
| `check_interactions` | Find drug-drug interactions | `[medmate/mcp_interaction_handler.py](medmate/mcp_interaction_handler.py)` |
| `build_schedule` | Create daily medication timeline | `[medmate/tools/schedule_tools.py](medmate/tools/schedule_tools.py)` |
| `get_next_doses` | Show upcoming doses | `[medmate/tools/schedule_tools.py](medmate/tools/schedule_tools.py)` |
| `export_schedule` | Export as iCalendar | `[medmate/tools/schedule_tools.py](medmate/tools/schedule_tools.py)` |

### Data

- **Interactions Database:** Curated, illustrative dataset of common drug-drug interactions
  - `[medmate/data/interactions.json](medmate/data/interactions.json)`
  - Labeled "for informational purposes only"

- **User Profile Store:** JSON persistence to `~/.medmate/profile.json`
  - Meds, allergies, conditions, timestamps
  - Restores on every session

### Security

- **PII Redaction:** Regex-based detection and redaction for email, phone, SSN, DOB, credit cards
- **Medical Guardrail:** Intercepts requests for definitive dosing advice ("should I increase my dose?")
- **Confirmation Gates:** Destructive operations (remove medication) require confirmation
- **Output Disclaimers:** Every response appends: "Not medical advice. Consult your healthcare provider."

---

## Getting Started

### Prerequisites

- Python 3.14+
- pip

### Installation

```bash
# Clone or enter the repo
cd vibecoding

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy .env template
cp .env.example .env
```

### DEMO Mode (No API Key)

Run the fully functional demo without Gemini API:

```bash
# Set mode to demo
export MEDMATE_MODE=demo

# Start the server
python -m uvicorn app.server:app --host 0.0.0.0 --port 8000

# Open browser to http://localhost:8000
```

The demo uses deterministic routing (keywords) to simulate agent behavior. Perfect for video demos and offline testing.

### LIVE Mode (With Gemini API)

```bash
# Get a free Gemini API key from https://aistudio.google.com/app/apikey

# Set your key
export GOOGLE_API_KEY=your_key_here
export MEDMATE_MODE=live

# Start the server
python -m uvicorn app.server:app --host 0.0.0.0 --port 8000

# Chat with the real multi-agent system powered by Gemini
```

### Quick Test

Seed demo profile and run tests:

```bash
# Run tests
pytest tests/ -v

# Test the app
curl -X POST http://localhost:8000/profile/seed
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "list medications"}'
```

---

## Project Structure

```
medmate/                          # Core ADK agent package
  agent.py                        # Root coordinator agent
  mcp_interaction_handler.py      # Local interaction checker
  sub_agents/                     # Specialist agents
    intake_agent.py
    interaction_agent.py
    scheduler_agent.py
  tools/
    profile_tools.py              # Medication profile tools
    schedule_tools.py             # Scheduling tools
    openfda_tool.py               # External API integration
  memory/
    store.py                      # Persistent profile storage
  security/
    pii.py                        # PII detection & redaction
    guardrails.py                 # ADK security callbacks
  data/
    interactions.json             # Drug interaction dataset

mcp_server/                       # Standalone MCP server
  server.py                       # FastMCP stdio server

app/                              # FastAPI web app
  server.py                       # Main server (DEMO/LIVE modes)
  orchestrator_demo.py            # Deterministic demo router
  static/
    index.html                    # Web UI (chat interface)

tests/                            # Test suite
  test_tools.py                   # Tool & memory tests
  test_guardrails.py              # Security tests
  test_orchestrator.py            # Demo orchestrator tests

Dockerfile                        # Container build
.env.example                      # Environment template
requirements.txt                  # Python dependencies
README.md                         # This file
```

---

## Deployment

### Local (Development)

```bash
python -m uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build
docker build -t medmate .

# Run
docker run -e MEDMATE_MODE=demo -p 8000:8000 medmate
```

### Google Cloud Run

```bash
# Requires: gcloud CLI, Google Cloud project, billing enabled

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/medmate

# Deploy to Cloud Run
gcloud run deploy medmate \
  --image gcr.io/PROJECT_ID/medmate \
  --port 8000 \
  --set-env-vars MEDMATE_MODE=live,GOOGLE_API_KEY=your_key \
  --allow-unauthenticated
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_tools.py -v

# Run with coverage
pytest tests/ --cov=medmate --cov=app
```

All 24 tests pass, covering:
- Tool functionality (add/remove/list medications, allergies, conditions)
- Drug interaction checking
- Schedule building and dose calculation
- PII redaction
- Security guardrails
- Demo orchestrator routing

---

## Usage Examples

### Add a Medication
```
User: "Add lisinopril 10mg once daily for blood pressure"
MedMate: "✓ Added lisinopril 10mg (once daily) to your medications.
Your current medications: lisinopril"
```

### Check Interactions
```
User: "Check interactions"
MedMate: "🚨 Found 1 interaction(s):
  ⚠️ ibuprofen + lisinopril (Severity: MODERATE)
     → NSAIDs may reduce the effectiveness of ACE inhibitors and increase risk of kidney problems.

⚠️ Please consult your pharmacist or doctor immediately."
```

### Build Schedule
```
User: "Show my schedule"
MedMate: "📅 Your medication schedule:
  08:00 - lisinopril 10mg
  08:00 - ibuprofen 200mg
  14:00 - ibuprofen 200mg
  20:00 - ibuprofen 200mg

Set alarms or calendar reminders for each time."
```

---

## Important Notes

⚠️ **Medical Disclaimer**

**MedMate is a personal medication organizer and decision-support tool, NOT a medical device or substitute for professional medical advice.**

- Do not use MedMate to diagnose conditions, determine dosages, or make treatment decisions.
- Always consult your doctor, pharmacist, or other healthcare provider before:
  - Starting, stopping, or changing medications
  - Combining medications
  - Adjusting dosages
- In case of emergency, call 911 or your local emergency number immediately.
- The interaction database is illustrative and not exhaustive. Professional evaluation is required.

---

## Course Concepts Applied

| Concept | Implementation | Impact |
|---------|---|---|
| **Agents (ADK)** | Multi-agent coordinator + 3 specialists | Modular, scalable architecture; each agent has focused responsibility |
| **MCP Server** | Custom stdio server for drug lookups | Extensible tool ecosystem; easy to swap data sources |
| **Security** | PII redaction + medical guardrails | Privacy-preserving; prevents unsafe medical advice |
| **Long-Term Memory** | Persistent JSON profile store | Users resume their context across sessions |
| **Deployability** | Dockerfile + Cloud Run docs | Production-ready; can scale to users |
| **External APIs** | openFDA integration (graceful fallback) | Real-world data; offline resilience |

---

## Future Enhancements

- [ ] Full MCP integration with LIVE agent execution
- [ ] Integration with pharmacy/doctor APIs for med refills
- [ ] SMS/email dose reminders
- [ ] PDF export of medication summaries
- [ ] Mobile app (React Native / Flutter)
- [ ] HIPAA compliance certification
- [ ] Doctor sharing (read-only profile link)
- [ ] AI-powered medication adherence coaching

---

## Contributing

To contribute or report issues, see the issues and pull requests on GitHub.

---

## License

MIT License — see LICENSE file for details.

---

**Built with ❤️ for the Kaggle AI Agents: Intensive Vibe Coding Capstone**

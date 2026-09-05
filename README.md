# 🤖 Zyron — A Local, Tool-Using AI Assistant

<p align="center">
  <img src="assets/zyron-banner.svg" alt="Zyron — Personal AI Assistant">
</p>

<p align="center">
  <strong>A local-first AI assistant built around dynamic capability discovery, grounded arguments, safe tool execution, persistent memory, and voice interaction.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13-blue?style=flat-square&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/tests-34%20passing-brightgreen?style=flat-square&logo=pytest&logoColor=white">
  <img src="https://img.shields.io/badge/AI-local--first%20(Ollama)-2563eb?style=flat-square">
  <img src="https://img.shields.io/badge/platform-Windows-informational?style=flat-square&logo=windows&logoColor=white">
</p>

---

Zyron is a **from-scratch LLM tool-calling system**: a local AI model (via Ollama) plans which registered capability to run, an argument-validation layer checks the plan before anything executes, and the assistant asks for missing information instead of guessing.

There's no agent framework underneath — the planning loop, capability discovery, parameter inference, argument grounding, and validation logic are built in Python.

> **Design principle:** when information is missing, Zyron asks — it never silently invents a value.

The project focuses on being **predictable, extensible, testable, and safety-conscious** rather than adding features for their own sake.

---

## 📑 Table of Contents

- [What This Project Demonstrates](#-what-this-project-demonstrates)
- [System Architecture](#️-system-architecture)
- [Engineering Highlight: Automatic Parameter Inference](#-engineering-highlight-automatic-parameter-inference)
- [AI Planning](#-ai-planning)
- [Dynamic Capability Planning](#-dynamic-capability-planning)
- [Argument Safety](#️-argument-safety)
- [Multi-Argument Clarification](#-multi-argument-clarification)
- [Safe Execution & Confirmation](#️-safe-execution--confirmation)
- [Persistent Memory](#-persistent-memory)
- [Voice Interaction](#️-voice-interaction)
- [Web Search](#-web-search)
- [System & File Capabilities](#-system--file-capabilities)
- [Technology Stack](#️-technology-stack)
- [Repository Structure](#-repository-structure)
- [Testing](#-testing)
- [Getting Started](#-getting-started)
- [Configuration](#️-configuration)
- [Design Philosophy](#-design-philosophy)
- [Roadmap](#️-roadmap)
- [Project Status](#-project-status)
- [Contributing](#-contributing)
- [Contact / Support](#-contact--support)
- [About Me](#-about-me)
- [License](#-license)

---

## 🎯 What This Project Demonstrates

| Skill | How it shows up in the code |
|---|---|
| **LLM tool-calling architecture** | Hand-built plan → validate → execute loop against a local model — no agent framework |
| **Reflection-based API design** | `ToolRegistry` derives parameter names, types, and required/optional status from a function's signature and type hints |
| **Dynamic capability discovery** | The planner works against registered capabilities rather than a large hard-coded command list |
| **Defensive input validation** | Plans are checked for missing required arguments, unknown arguments, and ungrounded values before execution |
| **Safe file handling** | File operations include path-safety checks and sensitive operations use confirmation |
| **SQL parameterization** | SQLite persistence uses parameterized queries in the memory layer |
| **Multi-turn state handling** | Missing arguments can be collected across subsequent user messages |
| **Test discipline** | 34 automated tests pass across argument safety, clarification, routing, application, file, and regression behavior |

---

## 🏗️ System Architecture

Zyron follows a layered design built around **capabilities** rather than a large collection of hard-coded commands.

```text
                         ┌──────────────────────┐
                         │         User          │
                         │     Text / Voice      │
                         └───────────┬──────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │     Zyron Router      │
                         └───────────┬──────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │      Zyron Agent      │
                         │                       │
                         │ Planning · Grounding  │
                         │      Validation       │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │     Tool Registry     │
                         │ Registered Capabilities│
                         └───────────┬───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
                 System            File             Web
                 Tools             Tools           Search
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │  Safety / Control    │
                         │ Validation +         │
                         │ Confirmation         │
                         └───────────┬──────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │      Execution       │
                         └───────────┬──────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │       Response       │
                         └──────────────────────┘
```

### Request Lifecycle

```text
User Request
     ↓
Capability Discovery
     ↓
AI Planning
     ↓
Argument Grounding
     ↓
Argument Validation
     ↓
Clarification if Required
     ↓
Confirmation if Required
     ↓
Controlled Execution
     ↓
Response
```

The key architectural boundary is that **the language model can propose a plan, but the application controls whether that plan is valid and executable** — AI interpretation never has direct access to execution.

---

## 🧠 Engineering Highlight: Automatic Parameter Inference

One of the key design decisions in Zyron is reducing manual schema maintenance.

The `ToolRegistry` can inspect a Python function's signature and derive parameter information from its type hints and defaults.

For example:

```python
def _infer_parameters(self, function):
    parameters = {}
    signature = inspect.signature(function)

    for name, param in signature.parameters.items():
        if name in {"self", "cls"}:
            continue

        annotation = param.annotation
        param_type = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
        }.get(annotation, "string")

        parameters[name] = {
            "type": param_type,
            "required": param.default is inspect.Parameter.empty,
        }

    return parameters
```

This creates a direct relationship between:

```text
Python Function → Function Signature → Tool Metadata → AI Planning → Argument Validation
```

The result is less manual schema duplication and a capability system that can evolve with the underlying Python functions.

---

## 🧠 AI Planning

Zyron uses **Ollama** as its local AI engine.

Current configuration:

```text
Model: phi4-mini
Endpoint: http://localhost:11434/api/generate
```

The AI layer interprets user requests and determines which registered capability should be used. The planner is constrained to the capabilities actually available through Zyron's tool registry.

The intended flow is:

```text
Natural-language request → Local LLM → Structured capability plan → Application validation → Execution or clarification
```

The model therefore acts as a planning component rather than being given unrestricted control over system operations.

---

## 🧭 Dynamic Capability Planning

The planner separates:

```text
What the user wants
        ↓
Which capability can perform it
        ↓
Which arguments are required
        ↓
Which arguments are available
        ↓
Whether the arguments are valid
        ↓
Execution
```

The planner is instructed to:

- use only registered capabilities
- never invent capabilities
- never invent parameter names
- never guess missing values
- use values grounded in the user's request
- leave missing required arguments absent
- request clarification when required information is missing

This allows capabilities to be added through the registry without continuously expanding a large hard-coded command router.

---

## 🛡️ Argument Safety

A major design goal of Zyron is preventing the AI planner from silently inventing arguments.

Example:

```text
User: "Calculate 10 multiplied"
```

If the capability requires:

```text
value
multiplier
```

Zyron should **not** silently assume `multiplier = 1`. Instead:

```text
I need 'multiplier' before I can continue.
Please provide it.
```

The important boundary is:

```text
AI Interpretation → Argument Grounding → Required Argument Validation → Clarification if Missing → Execution
```

This behavior is enforced by the validation flow and covered by automated tests.

---

## 💬 Multi-Argument Clarification

Zyron supports clarification when multiple required arguments are missing.

Example:

```text
User: "Perform the action for test@example.com"
```

Suppose the capability requires:

```text
recipient
subject
body
```

Zyron can recognize that `recipient` is available while `subject` and `body` are missing, and respond:

```text
I need 'subject' and 'body' before I can use 'fake_action'.
Please provide them.
```

The user can then provide the missing information across subsequent messages. Only after the required arguments are available should the capability execute. This behavior is covered by dedicated automated tests.

---

## 🛡️ Safe Execution & Confirmation

Some capabilities can modify the local environment and therefore require an additional control layer.

Sensitive operations such as `Write`, `Delete`, and `Rename` use confirmation before execution.

Conceptually:

```text
User Request → Capability Planning → Argument Validation → Sensitive Operation?
   → YES → Ask for Confirmation → User Confirms → Authorized Plan → Controlled Execution
```

The key principle is:

> **A plan is not automatically authorization.**

For file-writing operations, Zyron also protects against accidental overwrites unless overwrite is explicitly authorized through the confirmation flow.

---

## 💾 Persistent Memory

Zyron includes a **SQLite-backed conversation memory system**. The memory layer separates normal conversation history from explicit memories.

### Conversation History
Recent conversation messages are retained according to the configured conversation limit.

### Explicit Memories
User-requested memories are stored separately and are not removed by the normal conversation-history limit.

Supported operations include: `Remember`, `Forget`, `Forget by ID`, `Clear`.

The local memory database is stored inside the `data/` directory. Runtime data is excluded from version control.

The memory layer uses parameterized SQLite queries rather than constructing SQL statements from user-provided values.

---

## 🎙️ Voice Interaction

Zyron includes a local voice pipeline for speech-based interaction.

### Speech Recognition
**Faster-Whisper** is used for local speech-to-text processing. The voice input system includes microphone recording, audio calibration, speech detection, silence handling, audio validation, and transcription.

### Speech Synthesis
**Piper TTS** is used to generate spoken responses. Local voice-model files are kept outside the Git repository.

> Voice features may require system-level audio dependencies such as PortAudio or ffmpeg depending on the operating system.

Zyron is currently developed and tested on Windows. Voice output and application launching use Windows-specific APIs.

---

## 🌐 Web Search

Zyron includes a web-search capability based on **DuckDuckGo search results**. This allows Zyron to retrieve external information when a request requires current web data instead of relying entirely on the local language model.

---

## 💻 System & File Capabilities

### System Information
Zyron can expose system information such as CPU, RAM, disk, and battery information, current time/date, computer name, and system status — provided through the application's registered capabilities.

### Application Launching
Applications are launched through a controlled allow-list rather than allowing arbitrary executable paths to be passed directly to the operating system.

### File Management
Supported filesystem operations include `Create`, `Read`, `Write`, `Delete`, `Rename`. File operations include path-safety checks, and sensitive operations are protected through the confirmation workflow.

---

## 🛠️ Technology Stack

| Category | Technology |
|---|---|
| Language | Python 3.13 |
| Local AI Runtime | Ollama |
| AI Model | phi4-mini |
| AI Communication | HTTP / Requests |
| Speech-to-Text | Faster-Whisper |
| Text-to-Speech | Piper TTS |
| Database | SQLite |
| System Information | psutil |
| Audio Input | SoundDevice |
| Testing | PyTest |
| Version Control | Git & GitHub |
| Target Platform | Windows |

---

## 📂 Repository Structure

```text
Zyron/
│
├── assets/
│   ├── zyron-banner.svg
│   └── zyron-icon.svg
│
├── .gitignore
├── README.md
├── requirements.txt
│
├── src/
│   └── zyron/
│       │
│       ├── ai/
│       │   ├── __init__.py
│       │   └── ollama_client.py
│       │
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── ai.py
│       │   ├── app_manager.py
│       │   ├── file_manager.py
│       │   ├── general.py
│       │   ├── system.py
│       │   └── web_search.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── agent.py
│       │   ├── command_processor.py
│       │   ├── memory.py
│       │   ├── memory_commands.py
│       │   ├── router.py
│       │   ├── state.py
│       │   ├── tool_loader.py
│       │   └── tool_registry.py
│       │
│       ├── main.py
│       ├── voice.py
│       ├── voice_assistant.py
│       ├── voice_input.py
│       └── whisper_input.py
│
└── tests/
    ├── performance/
    │   └── speed_test.py
    │
    ├── regression/
    │   ├── regression_test.py
    │   ├── regression_test_phase2.py
    │   └── regression_test_phase3.py
    │
    ├── test_argument_safety.py
    ├── test_clarification_e2e.py
    ├── test_clarification_safety.py
    ├── test_multi_argument_clarification.py
    ├── test_required_argument_validation.py
    └── test_router_regression.py
```

---

## 🧪 Testing

Testing is an important part of Zyron's development. The automated test suite covers argument safety, clarification safety, end-to-end clarification, multi-argument clarification, required argument validation, router regression, application management, file management, regression scenarios, and performance-related development checks.

### Latest Full Test Result

```text
34 passed
0 failed
```

Run the complete suite:
```bash
python -m pytest -q
```

Run with detailed output:
```bash
python -m pytest -v
```

Run argument-safety tests:
```bash
python -m pytest tests/test_argument_safety.py -v
```

Run multi-argument clarification tests:
```bash
python -m pytest tests/test_multi_argument_clarification.py -v
```

The test suite provides a reproducible checkpoint for the current v0.1 architecture.

> No GitHub CI pipeline is currently configured.

---

## 🚀 Getting Started

Zyron is currently built and tested on **Windows**.

### Prerequisites
- Python 3.13
- Git
- Ollama
- `phi4-mini`
- Microphone for voice input
- Required system-level audio dependencies when using voice features

### 1. Clone the Repository
```bash
git clone https://github.com/Mustaq7892/Zyron.git
cd Zyron
```

### 2. Create the Python Environment
```bash
python -m venv .venv313
```

Activate it in Windows PowerShell:
```powershell
.\.venv313\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Prepare Ollama
Install Ollama and make the required local model available:
```bash
ollama pull phi4-mini
```
Make sure the Ollama service is running before starting Zyron.

### 5. Run Zyron
From the project root:
```bash
python -m src.zyron.main
```

---

## ⚙️ Configuration

The current implementation keeps several configuration values in source rather than exposing a formal environment-driven configuration interface.

Areas represented in the current implementation include:
- Ollama endpoint
- model name
- memory database location
- audio/runtime behavior

Moving these settings into a centralized configuration system or environment variables is planned for a future version.

---

## 🔐 Design Philosophy

### 🏠 Local-First
Inference is designed around a locally running Ollama engine rather than requiring every interaction to be sent to a remote AI service.

### 🧩 Explicit Capabilities
The agent can only execute capabilities registered with the `ToolRegistry`.

### 🎯 Grounded Arguments
Values should come from the user's request rather than being invented by the planner.

### 🛡️ Validate Before Execution
Plans and arguments are checked before execution.

### 💬 Clarify Instead of Guessing
When required information is missing, Zyron asks the user rather than silently assuming a value.

### 🔒 Confirmation for Sensitive Operations
Operations that can modify the local environment require an additional confirmation step.

### 🧱 Separate Planning from Execution
The AI helps determine what the user is asking for, while the application determines what is valid and what can actually execute.

### 🧪 Test Important Behavior
Safety-sensitive routing, argument validation, clarification, file operations, application behavior, and regression scenarios are covered by automated tests.

---

## 🗺️ Roadmap

**Architecture**
- Split the Agent module into dedicated planning, validation, clarification, and execution components
- Continue improving capability discovery and planning reliability
- Improve separation of runtime responsibilities

**Configuration**
- Move Ollama endpoint and model settings to environment variables
- Improve audio/runtime configuration
- Introduce a clearer centralized configuration interface

**Testing & Reliability**
- Convert additional manual regression/performance checks into asserting `pytest` tests
- Expand automated coverage
- Add a GitHub CI workflow
- Continue performance and reliability improvements

**Platform & Interaction**
- Extend beyond Windows
- Improve voice interaction
- Improve memory management
- Expand system capabilities
- Continue strengthening safety controls

**Product Experience**
- Add a polished terminal/demo recording
- Improve developer documentation
- Add a formal `LICENSE` file before formally releasing the project under an open-source license

---

## 📌 Project Status

### Zyron v0.1 — Safe MVP

Zyron has reached a **stable, tested MVP checkpoint**. The current foundation includes local LLM planning, dynamic capability discovery, tool registration, argument grounding, argument validation, multi-turn clarification, confirmation-based sensitive operations, controlled application execution, controlled file operations, SQLite-backed memory, local speech recognition, local text-to-speech, web search, and automated testing.

The project is currently **paused at this stable checkpoint** while the surrounding software engineering and data engineering portfolio is being developed. Development can resume from this tested foundation.

---

## 🤝 Contributing

This is currently a solo portfolio project, and formal contribution guidelines have not yet been defined. If you'd like to report a bug or suggest an improvement, please open an issue on the [GitHub repository](https://github.com/Mustaq7892/Zyron/issues).

---

## 📬 Contact / Support

The primary project home is the GitHub repository: [github.com/Mustaq7892/Zyron](https://github.com/Mustaq7892/Zyron). You can also reach out via [LinkedIn](https://www.linkedin.com/in/shaik-mustaq-915741254/).

---

## 👨‍💻 About Me

Hi, I'm **Shaik Mustaq** — a Software Engineer with **2+ years of professional experience**, with interests across:
- Software Development
- Data Engineering
- Python
- SQL
- AI-assisted systems
- Automation

Zyron is where I explored how LLM tool-calling can be built from the ground up rather than relying entirely on an agent framework.

The project gave me hands-on experience with LLM planning, capability-based architecture, reflection and parameter inference, argument grounding, validation, multi-turn clarification, safety and authorization flows, filesystem and application integration, SQLite persistence, voice processing, and automated testing.

I build practical projects to strengthen my software engineering and data engineering skills through implementation.

<p align="left">
  <a href="https://www.linkedin.com/in/shaik-mustaq-915741254/">
    <img src="https://img.shields.io/badge/LinkedIn-Connect-ffffff?style=plastic&logo=linkedin&logoColor=0A66C2&labelColor=0A66C2">
  </a>
</p>

---

## 📄 License

A formal open-source license has not yet been added to the repository. The project may be released under the **MIT License** in the future once the corresponding `LICENSE` file is added.

---

<p align="center">
  ⭐ If you find Zyron interesting, consider giving the repository a Star.
</p>

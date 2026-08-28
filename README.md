# 🤖 Zyron — Personal AI Assistant

<p align="center">
  <img src="assets/zyron-banner.svg" alt="Zyron — Personal AI Assistant">
</p>

Welcome to **Zyron**, a local-first **Personal AI Assistant** built with Python and designed to combine intelligent task planning, dynamic capability discovery, safe tool execution, persistent memory, and voice interaction into a single system.

Zyron is designed around a simple principle:

> **When information is missing, Zyron should ask rather than guess.**

Instead of relying entirely on hard-coded commands, Zyron can determine which registered capability is relevant to a user's request, construct a tool plan, validate its arguments, ask for missing information when necessary, and execute the approved capability.

The project focuses on building an assistant that is not only capable, but also **predictable, extensible, testable, and safety-conscious**.

---

# 🏗️ System Architecture

Zyron follows a layered architecture built around **capabilities** rather than a large collection of hard-coded commands.

```text
                         ┌─────────────────────┐
                         │       User          │
                         │   Text / Voice      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Zyron Router     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Zyron Agent     │
                         │                     │
                         │ Capability Planning │
                         │ Argument Grounding  │
                         │ Argument Validation│
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Tool Registry     │
                         │                     │
                         │ Registered          │
                         │ Capabilities       │
                         └──────────┬──────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
         System Tools         File Tools          Web Search
                │                   │                   │
                └───────────────────┼───────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │     Execution       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      Response       │
                         └─────────────────────┘
```

### 🔄 Request Lifecycle

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
Safe Execution
     ↓
Response
```

---

# 📖 Project Overview

Zyron is being developed as a personal AI assistant that can interact with the user's computer and external information sources through a controlled capability system.

The project currently brings together:

- Local AI reasoning
- Dynamic capability discovery
- Tool registration
- Argument validation
- Multi-step clarification
- Persistent conversation memory
- Voice input
- Voice output
- Web search
- System information
- Application management
- File management
- Automated safety and regression testing

The architecture is designed so that capabilities can be expanded without turning the assistant into one large collection of hard-coded `if/else` commands.

---

# 🧠 AI Planning

Zyron uses **Ollama** as its local AI engine.

The current configuration uses:

```text
Model: phi4-mini
Endpoint: http://localhost:11434/api/generate
```

The AI layer is responsible for helping Zyron interpret user requests and determine which registered capability should be used.

The planner is designed to work with the capabilities made available by Zyron rather than inventing arbitrary tools.

---

# 🧭 Dynamic Capability Planning

One of the central ideas behind Zyron is the separation between:

```text
What the user wants
        ↓
Which capability can perform it
        ↓
Which arguments are required
        ↓
Whether those arguments are valid
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

This makes the assistant's execution flow more predictable and easier to extend.

---

# 🛡️ Argument Safety

A major design goal of Zyron is preventing the AI planner from silently inventing arguments.

For example:

```text
User:
Calculate 10 multiplied
```

If a capability requires:

```text
value
multiplier
```

Zyron should not silently assume:

```text
multiplier = 1
```

Instead, it should ask the user:

```text
I need 'multiplier' before I can continue.
Please provide it.
```

The argument is validated before the capability is executed.

This creates a clear separation between:

```text
AI Interpretation
       ↓
Validation
       ↓
Execution
```

---

# 💬 Multi-Argument Clarification

Zyron supports clarification when multiple required arguments are missing.

For example:

```text
User:
Perform the action for test@example.com
```

If the capability requires:

```text
recipient
subject
body
```

Zyron can identify the missing information and ask the user for it rather than inventing values.

The user can then provide the missing information across subsequent messages.

Only after the required arguments are available should the capability execute.

This behavior is covered by dedicated automated tests.

---

# 💾 Persistent Memory

Zyron includes a SQLite-backed conversation memory system.

The memory system distinguishes between normal conversation history and explicit memories.

### Conversation History

Recent conversation messages are retained according to the configured conversation limit.

### Explicit Memories

User-requested memories are stored separately and are not removed by the normal conversation-history limit.

Zyron supports memory operations such as:

```text
Remember
Forget
Forget by ID
Clear
```

The local memory database is stored inside the `data/` directory.

Runtime data is intentionally excluded from version control.

---

# 🎙️ Voice Interaction

Zyron includes a local voice pipeline for speech-based interaction.

## 🎤 Speech Recognition

**Faster-Whisper** is used for local speech-to-text processing.

The voice input system includes functionality for:

- microphone recording
- audio calibration
- speech detection
- silence handling
- audio validation
- transcription

## 🔊 Speech Synthesis

**Piper TTS** is used to generate spoken responses.

Local voice-model files are kept outside the Git repository.

> **Note:** Voice features may require system-level audio dependencies such as PortAudio or ffmpeg depending on the operating system.

---

# 🌐 Web Search

Zyron includes a web-search capability based on **DuckDuckGo search results**.

This allows Zyron to retrieve external information when a request requires current web data rather than relying entirely on the local AI model.

---

# 💻 System Capabilities

Zyron includes system-related capabilities for interacting with and inspecting the local computer.

Examples include:

- CPU information
- RAM information
- disk information
- battery information
- current time
- current date
- computer name
- system status

---

# 📂 File Management

Zyron includes a file-management layer for controlled filesystem operations.

Supported operations include:

```text
Create
Read
Write
Delete
Rename
```

File operations are designed with path-safety considerations so that capabilities do not blindly operate on arbitrary filesystem locations.

---

# 🖥️ Application Management

Zyron includes application-management functionality.

Applications are launched through a controlled allow-list rather than allowing arbitrary executable paths to be passed directly to the operating system.

This provides an additional layer of control over application execution.

---

# 🧪 Testing & Validation

Testing is an important part of Zyron's development.

The repository contains automated tests covering:

- Argument Safety
- Clarification Safety
- End-to-End Clarification
- Multi-Argument Clarification
- Required Argument Validation
- Router Regression
- Performance
- Regression scenarios

Current test structure:

```text
tests/
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

### Current Test Result

The latest full local test run completed successfully:

```text
27 passed
```

> No CI pipeline is currently configured.

---

# 🛠️ Technology Stack

| Category | Technologies |
|----------|--------------|
| Language | Python 3.13 |
| Local AI | Ollama |
| AI Model | phi4-mini |
| Speech Recognition | Faster-Whisper |
| Text-to-Speech | Piper TTS |
| Database | SQLite |
| HTTP / Web | Requests |
| System Information | psutil |
| Audio Input | SoundDevice |
| Testing | PyTest |
| Version Control | Git & GitHub |

---

# 📂 Repository Structure

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

# 🚀 Getting Started

Follow these steps to set up Zyron locally.

## 1. Clone the Repository

```bash
git clone https://github.com/Mustaq7892/Zyron.git
cd Zyron
```

## 2. Create the Python Environment

Zyron is currently developed with Python 3.13.

```bash
python -m venv .venv313
```

### Windows — PowerShell

```powershell
.\.venv313\Scripts\Activate.ps1
```

### macOS / Linux

```bash
source .venv313/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> Some voice features may also require system-level packages such as PortAudio or ffmpeg depending on your operating system.

## 4. Install and Run Ollama

Zyron currently uses:

```text
phi4-mini
```

The Ollama service must be running locally before using AI-powered functionality.

## 5. Run Zyron

```bash
python -m src.zyron.main
```

---

# 🧪 Running Tests

Run the complete test suite:

```bash
python -m pytest -v
```

Run the argument-safety tests:

```bash
python -m pytest tests/test_argument_safety.py -v
```

Run the multi-argument clarification tests:

```bash
python -m pytest tests/test_multi_argument_clarification.py -v
```

---

# ⚙️ Configuration

Configuration details for the Ollama host/port, model name, and memory database path have not yet been documented as a formal configuration interface.

This section will be expanded as the configuration system is finalized.

---

# 🔐 Design Philosophy

Zyron is being developed around several principles.

### 🏠 Local-First

AI inference is designed around a locally running Ollama engine rather than requiring every interaction to be sent to a remote AI service.

### 🧩 Explicit Capabilities

The agent can only execute capabilities registered with Zyron.

### 🎯 Grounded Arguments

Arguments should come from the user's request rather than being invented by the planner.

### 🛡️ Validate Before Execution

Tool arguments are validated before execution.

### 💬 Clarify Instead of Guessing

When required information is missing, Zyron asks the user rather than silently assuming a value.

### 🧪 Test Important Behavior

Safety-sensitive routing and clarification behavior is covered by automated tests.

---

# 🗺️ Roadmap

Zyron is an actively evolving project.

Potential future improvements include:

- Improved capability discovery
- Stronger tool planning
- Expanded voice interaction
- Improved memory management
- Additional safety validation
- Richer system capabilities
- Improved test coverage
- Better configuration management
- Improved documentation and developer tooling
- GitHub CI/CD integration

---

# 📌 Project Status

**Zyron is an actively developed personal AI assistant project.**

The architecture is evolving toward a more capable and reliable local-first assistant while maintaining a strong emphasis on:

- controlled capability execution
- argument safety
- user clarification
- extensibility
- local processing
- automated testing

---

# 🤝 Contributing

Contribution guidelines have not yet been formally defined.

As the project matures, this section will document:

- issue reporting
- development workflow
- branch and pull-request conventions
- coding standards
- testing requirements

---

# 📬 Contact / Support

For now, the primary project home is the GitHub repository:

https://github.com/Mustaq7892/Zyron

Additional support and community channels may be added as the project grows.

---

# 👨‍💻 About Me

Hi! I'm **Shaik Mustaq**, a **Software Developer** with over **2 years of professional experience** and a strong interest in **Data Engineering, Software Development, Python, SQL, and AI-assisted systems**.

I enjoy building practical projects that combine software engineering principles with data, automation, and intelligent systems.

Zyron represents my hands-on exploration of building a personal AI assistant from the ground up, including:

- AI planning
- capability-based architecture
- argument validation
- clarification workflows
- persistent memory
- voice interaction
- system integration
- automated testing

I'm continuously improving the project while strengthening my software engineering and data engineering skills through practical implementation.

## 🌐 Connect With Me

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/shaik-mustaq-915741254/)

---

# 📄 License

Zyron is intended to be released under the **MIT License**.

A root-level `LICENSE` file will be added before the project is formally published under that license.

---

⭐ If you find Zyron interesting, consider giving the repository a **Star**. It helps others discover the project and supports the continued development of the project.

# LYRN-AI Cognitive Architecture - v4.2.7

**LYRN (Live-reasoning & Structured Memory)** is a highly modular, professional-grade GUI for interacting with local Language Models. It is designed from the ground up for efficiency, accessibility, and genuine cognitive continuity. It features advanced job automation, live system monitoring, a dynamic prompt building system, and a robust, file-based architecture for memory and inter-process communication.

## Core Philosophy

LYRN is built on a philosophy that diverges significantly from mainstream LLM development. Instead of relying on ever-larger models and prompt injection, LYRN emphasizes **structured, live memory** to achieve genuine continuity, identity, and context. The core tenets are:

-   **Efficiency and Accessibility:** The primary goal is to create a powerful AI cognition framework that is lightweight enough to run on standard consumer hardware.
-   **Structured Memory over Prompt Injection:** All core context—personality, memory, goals—lives in structured text files and memory tables. The LLM reasons from this stable foundation rather than having it repeatedly injected into a limited context window.
-   **Simplicity and Robustness:** The architecture is inspired by the simplicity of 1990s text-based game parsers. The framework's job is to be a robust, simple system for moving data; the LLM's job is to do the heavy lifting of reasoning.

*For a deeper dive into the project's vision and architectural principles, see `AGENTS.md`.*

## Architectural Paradigm: A Comparison

It's helpful to understand how LYRN's design differs from a traditional software application. The following is a breakdown of the key contrasts:

1.  **State Management:**
    *   **LYRN Framework:** Manages state through plain text and JSON files on the filesystem. This is highly transparent, human-readable, and avoids external dependencies, making it very portable.
    *   **Traditional Approach:** Typically relies on databases (like PostgreSQL, MongoDB), in-memory caches (like Redis), or dedicated message brokers (like RabbitMQ) for state management. These systems are designed for performance, scalability, and safe concurrent access, but they add significant setup and operational complexity.

2.  **Error Handling:**
    *   **LYRN Framework:** Has intentionally minimal error handling. It operates like a simple Inter-Process Communication (IPC) layer, where its main job is to pass data. The responsibility for handling errors or unexpected states is implicitly pushed to the LLM.
    *   **Traditional Approach:** Considers robust error handling a top priority. Code is filled with try/except blocks, custom exception classes, structured logging, and well-defined failure modes to ensure the application is resilient and predictable.

3.  **Location of "Business Logic":**
    *   **LYRN Framework:** The Python code itself contains very little logic. It's a "dumb" parser and data shuttle. The core intelligence—the "business logic"—resides almost entirely within the LLM.
    *   **Traditional Approach:** The application's logic is the core of the codebase. It's explicitly written in Python (or another language) and organized into classes, functions, and modules that follow design patterns like MVC, Separation of Concerns, etc.

4.  **Architectural Goal:**
    *   **LYRN Framework:** The goal is to be a minimalist, lightweight "nervous system" for an AI. It's designed to be a component in a larger cognitive architecture, not a standalone application. Its primary virtue is its simplicity and low resource footprint.
    *   **Traditional Approach:** The goal is usually to build a self-contained, feature-rich application that is robust, scalable, and maintainable on its own terms.

In short, a traditional codebase is built to *be* the brain of the operation. This framework is built to *serve* a separate brain (the LLM). This is the most fundamental difference and it informs every other architectural choice.

## Major Features

✅ **Modern, Responsive UI**: Built with CustomTkinter for a professional look and feel. Asynchronous initialization ensures the UI loads instantly and never freezes during model operations.

✅ **Live System Monitoring**: Real-time gauges for CPU, RAM, Disk, and VRAM usage.

✅ **Advanced Theming Engine**: Includes a live, in-app Theme Builder to create, modify, and save custom color themes.

✅ **Dynamic System Prompt Builder**: A powerful two-panel UI gives you granular control over every component of the system prompt.
    - Dynamically create, edit, and delete prompt components.
    - Toggle components on or off.
    - Reorder components with arrow keys.
    - Customize block wrappers and content for ultimate flexibility.

✅ **Job & Tool Automation**: A powerful automation system with:
    - A **Job Manager** to create and run complex, multi-step jobs.
    - A **Scheduler** with a full calendar view to run jobs at specific dates and times.
    - A **Cycle Manager** to create and execute custom, multi-step cognitive cycles.
    - Support for the **`gpt-oss` "harmony" format** for defining tools, allowing the AI to be extended with new capabilities.

✅ **Structured, Long-Term Memory**:
    - **Episodic Memory**: Saves each chat interaction as a structured, searchable file.
    - **Topic Indexing**: A background process that identifies and indexes topics from conversations to build a personalized web of meaning over time.
    - **Quote System**: Right-click any text in the chat to "Quote to Context" for easy reference.

✅ **Chat Persistence & Control**:
    - Chat history is automatically saved and reloaded between sessions.
    - Fine-grained control over how much chat history and which memory "deltas" are injected into the context for each turn.

✅ **Full Model Control**:
    - Save and load model configuration presets for one-click setup.
    - In-app controls for all key generation parameters (`temperature`, `top_p`, `top_k`, etc.).
    - Stop generation at any time with a dedicated button.

## Screenshots

### Dashboard
![Dashboard](screenshots/dashboard.png)

### System Prompt Builder
![System Prompt Builder](screenshots/system_prompt_builder.png)

### Job Manager
![Job Manager](screenshots/jobs.png)

### Chat Settings
![Chat Settings](screenshots/chat_settings.png)

### Model Settings
![Model Settings](screenshots/model_settings.png)

### Performance Metrics
![Performance Metrics](screenshots/performance_metrics.png)

## Quick Start

1.  **Install Dependencies**:
    ```bash
    pip install -r dependencies/requirements.txt
    ```

2.  **Place Models**:
    -   Create a folder named `models` in the root directory.
    -   Place your GGUF-format model files inside the `models/` folder.

3.  **Run Application**:
    ```bash
    python lyrn_sad_v4.2.6.pyw
    ```

4.  **First Launch Setup**:
    -   On the first launch, the "Model Settings" window will appear.
    -   Select your model from the dropdown, adjust parameters if needed, and click "Load Model".
    -   The application auto-generates `settings.json` to store all configurations.

## Key Files

### Core Application
- `lyrn_sad_v4.2.6.pyw` - The main GUI application file.
- `settings.json` - Auto-generated configuration file for model settings, paths, and UI preferences.
- `automation/` - Contains all background watcher scripts and configurations for autonomous operation.
- `build_prompt/` - Contains all modular components for building the system prompt.
- `themes/` - Directory containing JSON theme files.
- `dependencies/requirements.txt` - A list of all required Python packages.

### Documentation
- `README.md` - This guide.
- `build_notes.md` - A detailed, version-by-version change log of all updates.
- `AGENTS.md` - Instructions and architectural rules for AI agent development on this codebase.

## Troubleshooting

### Common Issues
- **Application doesn't start**: Ensure all dependencies from `dependencies/requirements.txt` are installed.
- **Model won't load**: Check the console output. Ensure the model path is correct in the "Model Settings" popup and the file is not corrupt.
- **Missing folders**: Most required folders (like `models/`) are created automatically on startup. If you encounter issues, deleting `settings.json` will trigger the first-time setup again.
- **Automation not working**: Ensure the relevant watcher scripts are running. You can check your system's task manager for multiple python processes.

## License

This project is licensed under a custom source-available license. See the [LICENSE](LICENSE) file for details. The key points are:
- The software is provided "as-is".
- You are free to use, modify, and redistribute it for non-commercial purposes.
- Commercial use requires express written permission from the copyright holder (LYRN-AI).

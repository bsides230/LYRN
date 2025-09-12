# LYRN-AI Quick Start Guide

Welcome to LYRN-AI! This guide will help you get up and running quickly.

## 1. Installation

Getting LYRN-AI set up is straightforward.

### Step 1: Install Dependencies
First, you need to install the required Python packages. Open your terminal or command prompt and run the following command from the project's root directory:
```bash
pip install -r dependencies/requirements.txt
```

### Step 2: Add a Model
LYRN-AI works with local models in GGUF format.
1.  Create a folder named `models` in the root directory of the project.
2.  Download a GGUF model (e.g., from Hugging Face) and place the `.gguf` file inside the `models` folder.

## 2. First Launch

With the setup complete, you can now launch the application.

> **Note:** This application has been developed and tested primarily on **Windows**.

### Launching on Windows

There are two main ways to launch the application on a Windows system. The primary application file is `lyrn_sad_v4.2.7.pyw`.

#### Option 1: Standard Launch (No Console Window)

This is the recommended way to run the application for normal use. The `.pyw` extension tells Windows to run the script without opening a black console window in the background.

-   **Double-click** the `lyrn_sad_v4.2.7.pyw` file.

That's it! The main application window should appear.

#### Option 2: Launch with Console (for Debugging)

If you are a developer or need to see logs and error messages directly, you can run the script using the standard `python.exe` interpreter. This will open a console window alongside the GUI.

1.  Open a command prompt or PowerShell terminal in the project's root directory.
2.  Run the following command:
    ```bash
    python lyrn_sad_v4.2.7.pyw
    ```
    (You can also use `python lyrn_sad_v*.pyw` to auto-select the latest version).

### First-Time Setup

1.  The **Model Settings** window will appear automatically on the first launch.
2.  Your model file should be automatically selected in the **Model File** dropdown. If it isn't, please select it from the `models` folder you created.
3.  Adjust any parameters if you wish (the defaults are fine for most systems).
4.  Click **Load Model**. The application will load the model, which may take a few moments. The status light will turn green and say "Ready" when it's done.

## 3. A Tour of the Interface

The LYRN-AI interface is divided into three main columns.

### Left Sidebar: System & Controls

-   **System Status**: This section shows you the current status of the LLM (e.g., Ready, Thinking, Error) and allows you to load/offload the model.
-   **System Prompt**: Open the powerful **System Prompt Builder** to control exactly what the AI knows about itself and its task.
-   **Personality**: Open the **Personality Editor** to adjust the AI's core traits using simple sliders.
-   **Quick Controls**: Buttons to quickly clear the chat display, view logs, and open a terminal.

### Center Panel: The Chat

This is where you interact with the AI.
-   The main text view displays the conversation. You can right-click any text to **Quote it to Context**.
-   The input box at the bottom is where you type your messages. Use **Ctrl+Enter** to send.
-   The **Send**, **Copy**, and **Stop** buttons give you control over the conversation.

### Right Sidebar: Monitoring & Automation

-   **Date & Time**: Shows the current date and time. The **Gear Icon (⚙️)** opens the main **Settings** window.
-   **Performance Metrics**: Live graphs showing token usage, generation speed, and KV cache utilization.
-   **System Resources**: Live gauges for your computer's CPU, RAM, Disk, and VRAM usage.
-   **Job Automation**: This is the control center for LYRN's powerful automation features.
    -   **Job Manager**: Create, edit, and delete complex jobs.
    -   **OSS Tools**: Manage internal tools the AI can use.
    -   **Run Job/Tool**: Manually trigger a specific job or tool from the dropdowns.

## 4. What to Do Next

-   **Have a Conversation**: Start chatting with the model to see how it responds.
-   **Build a Prompt**: Open the **System Prompt Builder** (`📝 System Prompt` button) and explore the different components. Try disabling one to see how it affects the AI's responses.
-   **Explore Settings**: Click the **Gear Icon (⚙️)** to explore the settings, where you can change the theme, font size, and other application behaviors.

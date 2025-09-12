# LYRN GUI - Required Files and Folders

This document lists all the essential scripts, files, and folders required to run the LYRN GUI and its associated systems.

## Core Application Scripts

These are the essential Python scripts that make up the LYRN GUI application.

-   `lyrn_sad_v4.0.3.pyw` (Main application entry point)
-   `lyrn_sad_v4.0.6.pyw` (Main application entry point)
-   `affordance_manager.py`
-   `automation_controller.py`
-   `color_picker.py`
-   `confirmation_dialog.py`
-   `cycle_manager.py`
-   `delta_manager.py`
-   `episodic_memory_manager.py`
-   `file_lock.py`
-   `model_loader.py`
-   `system_checker.py`
-   `system_interaction_service.py`
-   `themed_popup.py`
-   `topic_index_popup.py`
-   `topic_manager.py`

## Automation System Scripts

These scripts are part of the automation framework and are executed as subprocesses.

-   `automation/cycle_watcher.py`
-   `automation/scheduler_manager.py`
-   `automation/scheduler_watcher.py`
-   `automation/task_goal_watcher.py`
-   `automation/topic_watcher.py`
-   `automation/chat_gpt_cc.py`

## Configuration and Data

These files and folders store the application's configuration, data, and assets.

-   **Files:**
    -   `settings.json`
    -   `personality.json`
    -   `hover_tooltip.json`
    -   `favicon.ico`
    -   `color_grid.json`
    -   `chat_review.txt`
    -   `quotes.txt`
-   **Folders:**
    -   `images/`
    -   `languages/`
    -   `themes/`
    -   `global_flags/`
    -   `dependencies/`

## Core Data and Memory Systems

These directories are critical for the application's data storage and memory functions.

-   **`build_prompt/`**: Contains all components for constructing the system's master prompt.
-   **`automation/`**: The core of the automation system. Includes jobs, queues, schedules, etc.
-   **`deltas/`**: Stores logs of changes to system configuration or personality.
-   **`active_chunk/`**: Holds the currently active chunk of text for processing.
-   **`topic_memory/`**: Contains the topic index files.
-   **`episodic_memory/`**: Stores detailed logs of user-AI interactions.

## Third-Party Dependencies

These external Python libraries must be installed. They are listed in `dependencies/requirements.txt`.

-   `customtkinter`
-   `llama-cpp-python`
-   `Pillow`
-   `psutil`
-   `pynvml`

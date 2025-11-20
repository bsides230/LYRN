## v4.3.0 - Verbatim Chat Format and Watcher Control (2025-09-13)

This update refines the Verbatim Episodic Memory system, introducing strict formatting for better parsing and giving users direct control over the archival process.

- **Verbatim Chat Formatting:**
    - The main GUI (`lyrn_sad_v4.3.0.py`) now wraps chat content in specific tags before writing to the temporary file.
    - **Input Format:** `###INPUT_START###\n[User Message]\n###_END###`
    - **Output Format:** `###OUTPUT_START###\n[AI Response]\n###_END###`
    - This ensures that the watcher script and any future tools can unambiguously identify the components of a chat turn.

- **Watcher Control & Toggle:**
    - The "Save Chat History" toggle in the Settings menu now controls the Verbatim Memory Watcher.
    - When enabled, the GUI signals the watcher to archive the current turn.
    - When disabled, the watcher remains idle, preventing the archival of sensitive or ephemeral conversations.
    - The `EpisodicMemoryManager` integration for saving chat history has been deprecated and removed in favor of this new, robust verbatim system.

- **Watcher Robustness:**
    - The `verbatim_memory_watcher.py` script has been updated to correctly handle the new tagged format.
    - It now appends output blocks with proper separation and includes safety checks to prevent data from being appended to the wrong file if a turn is interrupted or skipped.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v4.3.0.py`.
    - The previous version `lyrn_sad_v4.2.9.py` has been archived in `deprecated/Old/`.

### Logging
- Chat turns are now logged with explicit `###INPUT_START###` and `###OUTPUT_START###` tags in the Verbatim Memory history files.
# LYRN-AI Build Notes

## v4.2.9 - Verbatim Episodic Memory Layer (2025-09-12)

This update introduces the "Verbatim Episodic Memory Layer", a new system for archiving raw chat interactions into a structured file history, alongside the existing logging systems.

- **New Verbatim Memory Watcher:**
    - A new background script, `automation/verbatim_memory_watcher.py`, has been added.
    - It monitors a temporary file for chat updates and archives them into a structured `Chat_History` directory.
    - **Structure:**
        - `Chat_History/Session_[StartTimestamp]_[EndTimestamp]/`: One folder per session.
        - `Block_[Number]_[Timestamp]/`: Subfolders containing up to 50 chat pairs.
        - `[Timestamp].txt`: Individual files for each chat turn containing the verbatim input and output.

- **GUI Integration:**
    - The main GUI (`lyrn_sad_v4.2.9.py`) has been updated to write each chat turn (input and final output) to a `temp_chat_turn.txt` file.
    - State flags (`verbatim_state.txt`) are used to coordinate with the watcher script, ensuring data integrity.
    - The watcher is automatically launched on startup and handles session closing gracefully.

### Logging
- Chat turns are now redundantly logged to the new Verbatim Memory system in addition to the existing `chat/` logs and Episodic Memory database.

---

## v4.2.8 - Windows Quick Start Guide (2025-09-12)

This is a documentation update to clarify the launch process for new users on Windows.

- **Updated `QUICK_START.md`**:
  - The "First Launch" section has been rewritten to be Windows-specific, as this is the primary tested OS.
  - Added clear instructions for two launch methods:
    1.  **Standard Launch**: Double-clicking the `.pyw` file for a normal, console-free experience.
    2.  **Developer Launch**: Running the `.pyw` file with `python.exe` from a terminal to see console output for debugging.
  - Added a note clarifying that the project is primarily tested on Windows.

### Logging
- No changes to logging mechanisms were necessary for this update.

---

## v4.2.7 - Documentation and In-App Help (2025-09-12)

This is a major documentation and usability update focused on improving the user experience by providing comprehensive documentation and context-sensitive help directly within the application.

- **New In-App Help System:**
  - Implemented a new, context-sensitive help system.
  - A small question mark button (`?`) has been added to every major popup window and settings tab.
  - Clicking the button opens a popup with a detailed explanation of the features and controls in that specific section of the UI.
  - All help text is loaded from a new, easily editable `docs/en/help_content.json` file.

- **Documentation Overhaul:**
  - **Remade `README.md`**: The project's main README has been completely rewritten to be more comprehensive, up-to-date with the latest features, and to better explain the project's core philosophy.
  - **New `QUICK_START.md`**: A new quick start guide has been created to help new users get the application installed and running as quickly as possible.

- **Updated Hover Tooltips:**
  - All hover tooltips throughout the application have been reviewed and updated to be more descriptive, accurate, and helpful.
  - Tooltip text is now managed centrally in `hover_tooltip.json`.

### Logging
- No changes to logging mechanisms were necessary for this update.

---

## v4.2.6 - UI Refinements (2025-09-12)

This is a minor update to refine the UI for the System Prompt Builder and fix a theming bug with dynamically created elements.

- **Centralized Component Buttons:** The "Edit" and "Delete" buttons in the System Prompt Builder have been moved from being on every individual component to a single, centralized set of controls that operate on the selected component. This declutters the UI and provides a more standard user experience.
- **Dynamic Theming Fix:** Fixed a bug where new elements added in the "Component Builder" popup would not be correctly themed. The `apply_theme()` method is now called after an element is created, ensuring all new UI widgets receive the correct styling.

### Logging
- No changes to logging mechanisms were necessary for this update.

---

## v4.2.5 - Dynamic Prompt Component Builder (2025-09-12)

This update introduces a major new feature allowing users to dynamically create, edit, and delete components for the system prompt directly within the GUI.

### Key Features:
- **Component Builder Popup:** A new popup accessed via a '+' button in the System Prompt Builder allows for the creation of new prompt components.
- **Dynamic Elements:** Users can add elements like text boxes to their components, name them, and see them update in real-time.
- **Edit and Delete:** Existing components can be edited using the same builder interface, or deleted entirely.
- **Themed Confirmation:** A themed confirmation dialog has been implemented to prevent accidental deletion of components.
- **Modular by Default:** The default components (RWI, system instructions, etc.) can now be customized or even deleted for ultimate flexibility.

### Logging:
- All component creation, modification, and deletion events are logged to the console.
- The `components.json` file is updated to reflect the new component registry.
- New component directories and files are created under `build_prompt/`.

---

## v4.2.4 - Theming Overhaul (2025-09-12)

- **Theming Rework:**
  - Reworked all theme files (`lyrn_light.json`, `lyrn_dark.json`, `lyrn_black.json`) for consistency and to fix color mismatches.
  - Introduced new color properties (`secondary_button`, `secondary_border_color`, `secondary_accent`) to provide more granular control over UI elements.
  - Changed the "Settings" button to use the new `secondary_button` color for better visual distinction.
  - Applied a consistent border color to all text boxes across the application, including the main chat, popups, and viewers, using the new `secondary_border_color`.
  - Ensured that all UI elements correctly inherit and display colors from the selected theme.

### Logging
- No new logging was added in this version. The focus was on visual and theme-related improvements.

## v4.2.3 - UI Refinements and Persistence (2025-09-11)

This update introduces several user-requested UI improvements and adds chat persistence.

- **Performance Metrics Refactor:**
    - The performance metrics block has been reorganized for better readability.
    - A "Response Tokens" metric has been added.
    - "Generation Time" and "Tokenization Time" labels are now static to prevent framing issues when their values update.

- **UI Layout Changes:**
    - The "Automation" button has been renamed to "Job Manager".
    - The "OSS Tools" button has been moved to the right sidebar, below the "Job Manager" button.
    - A new combobox and "Run" button for OSS tools have been added below the job runner.
    - The "Settings" button has been moved to the right sidebar, next to the date and time display, and is now a square button with a gear icon.

- **Chat Persistence:**
    - The chat display content is now saved to `active_chat.txt` when the application is closed.
    - The chat content is reloaded from this file on startup.
    - Manually clearing the chat display now also clears the saved chat file.

### Logging
- No changes to logging mechanisms were necessary for this update.

## v4.2.1 - OSS Tooling & UI Overhaul (2025-09-11)

This is a major update that refactors the internal "Affordances" system to align with OpenAI's open-source tool format, overhauls several UI components for better usability, and fixes numerous bugs.

- **Affordance System Rebranded to OSS Tools:**
    - Researched and adopted the `gpt-oss` "harmony" format for tool definitions.
    - The `AffordancePopup` has been completely redesigned with a new text-based editor, replacing the old form. Users now define tools using a TypeScript-like syntax.
    - A new "Affordances" component has been added to the System Prompt Builder, which injects all defined tools into the context for the LLM, similar to how "Jobs" are handled.

- **Core GUI and UX Changes:**
    - **Backend Job Injection:** Running a job from the "Automation" popup now injects the trigger directly into the backend, rather than pasting it into the user's input box.
    - **Memory UI Cleanup:** The "Memory" button has been removed from the main UI. The chat history viewer is now accessed via a "View Chat History" button in the Chat Settings tab.
    - **Job Selection Removed:** The manual job selection dropdown has been removed from the main UI to streamline the interface.
    - **Brighter Metrics:** The color of the "Generation tok/s" label has been changed to a new, brighter theme color for better visibility.
    - **Settings Popup Resized:** The main settings window height has been increased to prevent buttons from being squished.

- **Bug Fixes and Minor Adjustments:**
    - **New Job Saving:** Fixed a bug where the "Save" button in the new job editor would fail to close the popup and refresh the job list due to a hardcoded path.
    - **Themed Preset Popup:** The input dialog for saving a model preset is now correctly themed.
    - **Total Tokens Metric:** The "Total Tokens" calculation in the performance metrics now correctly includes tokens from the KV cache.
    - **Tab Rename:** The "Reflection Cycle" tab in the Automation popup has been renamed to "Prompt Training" to be more descriptive.

### Logging
- No changes to logging mechanisms were necessary for this update.

## v4.2.1 - Merged Jobs Preview Hotfix (2025-09-11)

This is a minor hotfix to address a UI formatting issue in the System Prompt Builder.

- **Merged Jobs Separator:** Fixed a bug in the "View Merged Jobs" popup where all job instructions were concatenated into a single, unreadable block of text. A distinct visual separator (`================================================================================`) is now added between each job, making the preview clear and easy to read.

### Logging
- No changes to logging mechanisms were necessary for this update.

## v4.2.0 - Job Component for System Prompt (2025-09-11)

This update introduces a new "Jobs" component to the System Prompt Builder, designed to improve the performance of the automation system by pre-caching job instructions.

-   **New "Jobs" System Prompt Component:**
    -   A new "Jobs" component can be enabled in the System Prompt Builder. When active, it will inject the instructions for all available jobs directly into the system prompt.
    -   The goal is to load these instructions into the model's KV cache on startup, allowing automated jobs to be triggered with a simple, low-token trigger phrase without the need to re-send the full instructions each time.

-   **New Jobs Editor UI:**
    -   The editor panel for the "Jobs" component features a clickable list of all jobs defined in `automation/jobs/jobs.json`.
    -   A "Refresh" button allows the user to reload this list if they have added or removed jobs while the prompt builder is open.

-   **Job Viewing and Editing Workflow:**
    -   Clicking a job in the list opens a new popup (`JobInstructionViewerPopup`) that displays the full text of the job's instructions.
    -   This viewer popup contains an "Edit Job" button, which seamlessly opens the existing `JobBuilderPopup` for that specific job.
    -   This reuses the existing, robust job editing functionality and ensures that any changes saved in the editor are reflected in the viewer and the main job list.

### Logging
- No changes to logging mechanisms were necessary for this update.

## v4.1.9 Fixes #2 - UI and Logging Fixes (2025-09-07)

This update addresses user feedback regarding UI spacing and fixes a critical bug in the chat logging system to ensure logs are clean and correctly formatted for reinjection.

- **UI Spacing Refined:**
    - Reduced the vertical spacing in the chat display for a more compact and readable conversation flow.
    - Adjusted the newlines printed after the user's message and between the "Thinking" and "Assistant" sections of the response.

- **Chat Log Formatting Corrected:**
    - Fixed a major bug where chat logs were being written incorrectly, including raw model output with "thinking" steps and using the wrong headers.
    - Removed a redundant logging call that was saving the raw, unfiltered model output.
    - The `JournalLogger` now correctly saves only the final, clean assistant response.
    - Log files now begin with a `#Timestamp#` as requested.
    - Log file headers have been corrected from `#RESPONSE_START#` to `#ASSISTANT_START#`.

### Logging
- The chat logging system has been corrected to only log the final, user-facing messages, ensuring the logs are clean and suitable for being reinjected as chat history.

## v4.1.9 Fixes (2025-09-07)

This is a bugfix release to address two outstanding errors that were affecting model conversation history and UI stability.

- **Conversation Role Fix:** Resolved a critical bug that caused the `Conversation roles must alternate` error. The `ChatManager` now correctly treats all non-user roles (e.g., `assistant`, `model`, `thinking`) as the 'assistant' for the purpose of constructing chat history. This prevents consecutive 'user' messages from being sent to the model, which was the root cause of the error.
- **Metrics Display Fix:** Fixed an `AttributeError` in the `reset_metrics_display` function that occurred when reloading the model. The code was attempting to reference a non-existent UI widget (`speed_indicator`). The erroneous line has been removed, resolving the crash.

### Logging
- No changes to logging mechanisms were necessary for this update.

## v4.1.9 (2025-09-07)

This is a major feature update focused on improving model compatibility, user customization, and providing a clearer view of the AI's operations. The core changes revolve around a more flexible handling of model roles (e.g., `assistant`, `model`, `thinking`, `analysis`) to prevent conversation errors and give users more control over the GUI's appearance and behavior.

- **Dynamic Role Handling & History Fix:**
    - Refactored the core chat processing logic to dynamically handle various model output roles (e.g., `assistant`, `model`, `thinking`, `analysis`). This resolves the `Conversation roles must alternate` error that occurred with models not strictly using the `assistant` role.
    - The `ChatManager` now intelligently parses journal files to construct a valid, alternating `user`/`assistant` history for the LLM, while ignoring intermediate "thinking" steps for context, ensuring compatibility.

- **Separated Thinking/Analysis Display:**
    - All non-final model outputs (e.g., `thinking`, `analysis`, `smol_thought`) are now categorized as `thinking_process` and routed to a separate "Analysis" display box below the main chat window.
    - This visually separates the model's final response from its intermediate steps, reducing confusion.

- **New Chat Appearance Settings:**
    - Added a new "Chat Appearance" section to the "Chat" tab in Settings.
    - **Customizable Role Colors:** Users can now set custom colors for "User Text", "Assistant Text", "Thinking/Analysis Text", and "System Text".
    - **Toggle Thinking Display:** A new switch allows users to show or hide the "Analysis" display box, giving them control over GUI verbosity.

- **New Model Parameters:**
    - Added UI controls for `Temperature`, `Top P`, and `Top K` to the "Model Settings" popup, allowing users to fine-tune generation parameters.
    - Ensured these settings are correctly saved to and loaded from `settings.json` and model presets.

### Logging
- The `StructuredChatLogger` has been renamed to `JournalLogger` to better reflect its purpose.
- The Journal now logs all raw roles from the model stream (`USER`, `THINKING`, `RESPONSE`), creating a complete and auditable record of every interaction.

## v4.1.8 (2025-09-05)

This is a hotfix release to address a `SyntaxError` that was preventing the application from running.

- **SyntaxError Fix:** Corrected a `SyntaxError: expected 'except' or 'finally' block` in the `update_enhanced_metrics` function. The code was improperly structured, with several lines of code placed between the `try` and `except` blocks. These lines have been moved inside the `try` block, resolving the error.
- **Versioning:** The application version has been updated to `v4.1.8`.

### Logging
- No changes to logging mechanisms were necessary for this update.

## v4.1.7 (2025-09-05)

This update focuses on refining the prompt injection system, giving users more granular control over context, and improving UI compactness.

- **Performance Metrics Cleanup:** The Performance Metrics section in the UI has been made more compact. The "KV Caching Time" metric, which was non-functional, has been removed to save space and reduce clutter.

- **Delta and Chat History Injection Overhaul:**
    - **New Toggles:** The Chat Settings tab now includes dedicated on/off toggles for "Delta Injection" and "Chat History Injection", allowing users to control exactly what context is sent to the model.
    - **Corrected Injection Order:** The prompt building logic has been fixed to ensure that deltas and chat history are injected in the correct order: `master_prompt` -> `deltas` -> `chat_history` -> `user_input`.
    - **Decoupled Chat History:** The chat history mechanism is now fully decoupled from the long-term Episodic Memory. It now manages a rolling window of chat logs in the `chat/` directory, respecting the number of pairs set in the Chat Settings. A new `ChatManager` class handles this logic, ensuring only the desired amount of recent conversation is used for context.

### Logging
- No changes to logging mechanisms were necessary for this update.

## v4.1.6 (2025-09-05)

This update introduces several UI improvements and adds more detailed performance metrics.

- **"Episodic Memory" Tab Renamed:** The "Episodic Memory" tab in the Memory popup has been renamed to "Chat History" to be more intuitive for users.
- **Performance Metrics Enhanced:** The Performance Metrics section now includes timers for "Generation Time" and "Tokenization Time", displayed in minutes and seconds, giving users more insight into model performance.
- **Affordances Button Relocated:** The "Affordances" button has been moved from the right sidebar to the left sidebar, directly underneath the "Personality" button, for better grouping of related controls.
- **Ctrl+Enter Fix:** The Ctrl+Enter shortcut to send a message from the input textbox now works reliably and prevents the default action of inserting a newline.

### Logging
- No changes to logging mechanisms were necessary for this update.

## v4.1.5 (2025-09-05)

This update fixes two significant UI bugs related to the Theming and System Prompt Builder systems.

- **Prompt Builder Panel Fixed:** Resolved a critical bug where the right-side editor panel in the System Prompt Builder would not appear when a component was selected. This was caused by an incorrect layout manager configuration (`pack` and `grid` used in the same parent frame), which has been corrected to use `grid` consistently.
- **Theming System Refactored and Fixed:**
    - The Theme Builder is now fully functional. The "Open Theme Builder" button in the settings now correctly launches the builder instead of a "Coming Soon" popup.
    - The live preview in the Theme Builder has been fixed. It now correctly applies the preview theme to all open windows, not just the main application window, for a consistent and accurate preview.
    - Redundant theming code was removed from the `TabbedSettingsDialog` to centralize the theming logic in the `ThemedPopup` base class, improving maintainability.

### Logging
- No changes to logging mechanisms were necessary for this update.

## v4.1.4 (2025-09-05)

This update focuses on UI tweaks and performance improvements for the System Prompt Builder.

- **System Prompt Builder Arrow Relocation:** The up/down arrows used for reordering components in the System Prompt Builder have been moved from the right side of the component list to the far left of the popup. This provides a more intuitive layout and better visual grouping of controls.
- **System Prompt Builder Performance Enhancement:** The editor panel in the System Prompt Builder has been refactored to be significantly faster and more responsive. Instead of destroying and recreating the editor UI every time a new component is selected, all editor panels are now pre-loaded and cached when the popup is first opened. Switching between components now only toggles the visibility of these cached panels, eliminating the lag associated with UI reconstruction.

### Logging
- No changes to logging mechanisms were necessary for this update.

## v4.1.3 (2025-08-02)

This is a major refactoring of the System Prompt Builder UI to improve workflow and align with the system's modular design.

- **Complete UI Overhaul:** The System Prompt Builder has been completely redesigned, replacing the old tab-based interface with a more efficient two-panel layout.
- **Dynamic Component Editor:** The new UI features a draggable list of prompt components on the left. Selecting a component dynamically loads a dedicated editor for it on the right, providing a more intuitive and streamlined workflow.
- **New RWI (Relational Web Index) Editor:** A new "RWI" component has been added to the list. When selected, it provides a dedicated view for managing RWI-specific information, including the introductory text and a summary of all active components.
- **Unified Component Activation:** The activation of all prompt components, including Heartbeat, is now controlled by a single toggle switch in the main component list, removing redundant toggles from individual editor panels.
- **Decoupled RWI Instructions:** The old, centralized `rwi_instructions.txt` file has been deprecated. RWI information is now stored directly in the `config.json` file for each respective component, improving modularity.

## v4.1.2 (2025-08-28)

### Features
- **RWI Instruction Editor:** The info button ("?") on each component in the "Static RWI" tab has been replaced with an edit button ("✏️").
  - Clicking the edit button opens a new popup window (`RWIInstructionEditorPopup`) allowing the user to directly edit the instruction for that specific component.
  - Changes are saved back to the `rwi_instructions.txt` file, which is now dynamically parsed to populate the editor.
- **Full RWI Viewer/Editor:** A new "View/Edit Full RWI" button has been added to the "Static RWI" tab.
  - This opens a new popup (`FullRWIViewerPopup`) that displays the entire `rwi_instructions.txt` file in a large, editable textbox.
  - The popup includes a "Lock File" toggle switch. When enabled, it prevents the textbox and save button from being used, protecting the file from accidental edits. The lock state is saved in `build_prompt/rwi_lock.json`.

## v4.1.0 (2025-08-28)

### Features
- **Merged Memory/Task Popups:** The "Tasks/Goals" popup has been merged into the "Memory" popup. The functionality is now available under "Tasks" and "Goals" tabs in the unified Memory Manager, streamlining the UI.
- **Static RWI (Relational Web Index):** The "Prompt Build Order" tab in the System Prompt Builder has been renamed to "Static RWI" to better reflect its function based on the system's design documents.
  - The RWI section now injects an `rwi_instructions.txt` file at the beginning of the system prompt.
  - Each component in the RWI list now has an info button ("?") that opens a popup with a description of that component's purpose.
- **New Personality Popup:** The "Personality" editor has been removed from the Settings window and is now a standalone popup accessible from a new "Personality" button on the main UI, located under the System Prompt controls.
  - The sliders in the new Personality popup will now update the corresponding text box values in the System Prompt Builder in real-time if it is open.

### Refactoring
- **Moved Chat Controls:** The "Clear Chat Folder" and "Open Chat Folder" buttons have been moved from the main UI's quick controls into the "Chat" tab of the Settings window, grouping them with other chat-related settings.

## v4.0.9 (2025-08-28)

### Features
- **Chat Memory:** Implemented a chat history system. The LLM now receives the last `N` chat turns as context, enabling conversational memory.
- **Chat Settings:** Added a new "Chat" tab in the settings window.
  - Users can now enable or disable the saving of chat history via a toggle switch.
  - Users can control the number of conversation pairs (from 0 to 50) sent back to the LLM using a slider.
- **Memory Management UI:** Refactored the "Memory" popup. It now uses a tabbed interface to house the "Episodic Memory" viewer and the "Topic Index" manager in a single, consolidated window.

### Fixes
- **Missing Chat Saving:** The application now correctly calls the `EpisodicMemoryManager` to save conversations after they are completed. This was a missing piece of functionality.

### Refactoring
- Consolidated the `EpisodicMemoryPopup` and `TopicIndexPopup` classes into the `MemoryPopup` class to create the new tabbed interface, removing redundant code.

# LYRN-AI v4.0.8 Build Notes

## v4.0.8 - Dependency Updates (2025-08-26)

- Added `pyautogui` and `pygetwindow` to `dependencies/requirements.txt` to support system automation features.

### Logging
- No changes to logging mechanisms were necessary.


## v4.0.8 - Main UI Cleanup and Model Preset Fix (2025-08-24)

This update focuses on streamlining the main user interface by reorganizing and removing components, and addresses a bug in the model preset system.

- **Combined Load/Offload Button:** The "Load Model" and "Offload Model" buttons have been consolidated into a single toggle button. The button's text and color now dynamically update to reflect the current model state ("Load Model" when offloaded, "Offload Model" in an accent color when loaded), providing clearer state feedback and saving UI space.

- **New "Memory" Button:** The "Episodic Memory" and "Topic Index" buttons have been removed from the left sidebar. They are now accessible via a new "Memory" button on the right sidebar, which opens a new popup with a tabbed interface for each memory function. This groups related memory features together and declutters the main controls.

- **Removed Redundant Mode Controls:** The "Mode" selection dropdown and its associated "Refresh" button have been removed from the main UI. This functionality was previously moved to the "System Prompt Builder" popup, making these controls redundant.

- **Model Preset Loading Fixed:** Addressed an issue where selecting a model preset might not reliably update the model selection dropdown in the UI. An explicit UI update call has been added to ensure the dropdown's state is immediately synchronized after loading a preset.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v4.0.8.pyw`.
    - The previous version `lyrn_sad_v4.0.7.pyw` has been archived.

# LYRN-AI v4.0.8 Build Notes

## v4.0.8 - Prompt Builder UI Fixes (2025-08-23)

This update addresses several UI issues in the "System Prompt Builder" that were introduced during the recent overhaul.

- **Theming Fixed:** Fixed a major bug where the System Prompt Builder popup would appear un-themed. The popup's custom `apply_theme` method was conflicting with the one in its parent `ThemedPopup` class. The redundant method was removed, and the popup now correctly inherits the application's theme.

- **Personality Toggle Restored:** The on/off toggle for the "Personality" component, which was inadvertently removed, has been restored. It is now correctly located at the top of the "Personality" tab.

- **Redundant "Components" Tab Removed:** The "Components" tab has been removed from the prompt builder. With the personality toggle restored, all components now have their own on/off switch within their respective tabs, making the centralized "Components" tab unnecessary.

# LYRN-AI v4.0.7 Build Notes

## v4.0.7 - System Prompt Builder Overhaul (2025-08-23)

This is a major overhaul of the "System Prompt Builder" to provide granular control over every component of the prompt. The old system of simple text files has been replaced with a more robust JSON-based configuration for each component, and the UI has been completely redesigned to expose these new settings.

- **New Component-Based Architecture:**
    - Each prompt component (Personality, System Rules, etc.) is now defined by a `config.json` file in its respective directory.
    - This config file specifies the start/end brackets for the block and the name of the file containing the content, allowing for much greater flexibility.

- **Redesigned Prompt Builder UI:**
    - **New "System Instructions" Tab:** A completely new, fully-configurable prompt component has been added.
    - **Prompt Build Order First:** The "Prompt Build Order" tab has been moved to the first position for easier access and a "Save Order" button has been added.
    - **Bracket and Content Editors:** The "System Instructions", "User Preferences", "AI Preferences", and "System Rules" tabs now all feature dedicated text boxes for their start bracket, end bracket, and instruction content, with a save button for each.
    - **New Personality Editor:** The "Personality" tab has been completely redesigned to match the new format. It now has fields for start/end brackets and a dynamic list of traits. For each trait, there is a text box for its numerical value (0-1000) and a multi-line text box for its instructions.

- **New Toggle and Prompt Generation Logic:**
    - **Component Toggling:** A new "Components" tab replaces the old "System Rules & Toggles" tab. It contains a master list of all prompt components with on/off switches. Toggling a component off now removes it directly from the `prompt_order.json`, completely disabling it from the prompt build.
    - **Refactored Prompt Loader:** The `SnapshotLoader` has been rewritten to read the new `config.json` for each enabled component, dynamically assembling the `master_prompt.txt` with the correct custom brackets and content for each block.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v4.0.7.pyw`.
    - The previous version `lyrn_sad_v4.0.6.pyw` has been archived.

# LYRN-AI v4.0.6 Build Notes

## v4.0.6 - Startup Robustness and Error Handling (2025-08-22)

This update introduces a new system checker to improve application robustness on startup. It ensures that all necessary files and folders are present, and provides clear feedback to the user if any essential components are missing.

- **New System Checker Module:**
    - A new `system_checker.py` module has been created to house all startup verification logic.
    - This module is responsible for checking for the existence of essential files and directories.

- **Automatic Folder Creation:**
    - On every startup, the application now scans for all directories defined in `settings.json`.
    - If any of these directories are missing, they are automatically created. This prevents crashes due to accidental deletion of folders like `chat/` or `automation/`.

- **Missing File Detection and Alerting:**
    - The application now verifies the presence of all critical watcher and handler scripts on startup (e.g., `automation/scheduler_watcher.py`, `automation_controller.py`).
    - If any of these files are missing, a themed popup window appears, listing the missing files and warning the user that the application may not function correctly.

- **Integration:**
    - The system checks are integrated into the main application's startup sequence, running immediately after the settings are loaded.

# LYRN-AI v4.0.5 Build Notes

## v4.0.5 - Topic Indexing Engine (2025-08-22)

This update introduces the foundational layer of the Topic Indexing Engine, a new long-term memory system designed to build a personalized web of meaning from conversations.

- **New Topic Memory System:**
    - A new `topic_memory/` directory has been created to store all topic-related data. This includes indexes, templates, and active topic links.
    - A `topic_template.txt` file defines the structure for new topic indexes, including summaries, insights, linked topics, and chat references.

- **New Topic Manager Backend:**
    - A new `topic_manager.py` module has been created to handle all backend logic for the topic system.
    - The `TopicManager` class provides methods for creating, reading, saving, and searching topic indexes.

- **Automated Topic Discovery:**
    - A new background watcher script, `automation/topic_watcher.py`, has been added to the automation system.
    - It monitors chat logs for a `##TIS_START##...##TIS_END##` block containing a list of potential topics.
    - It logs all searched topics to `searched_topics.txt`.
    - If a topic is new, it is added to `new_topics.txt` to be fleshed out by the LLM in a future update.

- **New Topic Index GUI:**
    - A new "Topic Index" button has been added to the main UI, opening a comprehensive management popup.
    - Users can view all available topic indexes.
    - Users can select topics and add them to an `active_topics` folder for context injection.
    - A detailed, tabbed editor allows users to view and edit all sections of a topic index file directly from the GUI.
    - Controls have been added to configure which parts of a topic (Summary, Insights, Timeline) are injected into context by default, with settings saved to `settings.json`.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v4.0.5.pyw`.
    - The previous version `lyrn_sad_v4.0.4.pyw` has been archived.

# LYRN-AI v4.0.4 Build Notes

## v4.0.4 - Episodic Memory Manager (2025-08-20)

This update introduces a comprehensive new Episodic Memory system, moving away from a simple chat log to a structured, file-based memory architecture. This allows for more advanced searching, filtering, and context management.

- **New Episodic Memory Manager:**
    - A new `episodic_memory_manager.py` module has been created to handle all aspects of the new memory system.
    - It manages the creation and parsing of "Verbatim Chat Entry Pair" files, which store detailed information about each interaction.

- **Structured Chat Entries:**
    - Each chat interaction is now saved as a separate, structured text file in the `episodic_memory/` directory.
    - These files follow a detailed block format, including fields for ID, timestamp, mode, user input, model output, summaries, keywords, and topics.

- **New Episodic Memory Popup:**
    - A new "Episodic Memory" button has been added to the main UI, which opens a new popup window for managing memories.
    - The popup features a searchable and scrollable list of all past chat entries.
    - Each entry in the list displays a one-liner summary, timestamp, mode, and any associated tags.

- **Context Management:**
    - Users can select multiple entries from the list using checkboxes.
    - An "Add Selected to Context" button appends the full content of the selected entries to a `chat_review.txt` file, allowing them to be easily loaded into the model's context.

- **Quoting Feature:**
    - A new right-click context menu has been added to the main chat display.
    - Users can highlight any text in the chat, right-click, and select "Quote to Context".
    - This action appends the selected text to a `quotes.txt` file for easy reference and injection into the prompt.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v4.0.4.pyw`.


# LYRN-AI v4.0.3 Build Notes

## v4.0.3 - Heartbeat System Simplification (2025-08-20)

This update completely refactors the "Heartbeat" system, replacing a complex, job-based background process with a simple and direct system prompt injection, as per user request for simplification.

- **New Prompt-Based Heartbeat:**
    - The old system, which ran a separate job and was parsed by a `heartbeat_watcher.py` script, has been entirely removed.
    - The new system works by directly injecting a user-defined block of text into the system prompt.
    - This aligns with the project's philosophy of using the LLM for heavy lifting and keeping the application logic simple.

- **New Heartbeat Configuration:**
    - The old `config.txt` has been replaced with a new `build_prompt/heartbeat/heartbeat_config.json` file.
    - This JSON file stores the on/off state, begin/end brackets, instruction body, and a trigger phrase for user reference.

- **Redesigned GUI:**
    - The "Heartbeat" tab in the "System Prompt Builder" popup has been completely redesigned.
    - It now features a full editor for all the values in the new JSON config file, including a toggle switch and text boxes for the brackets, body, and trigger.
    - A "Save" button allows users to persist their changes directly from the UI.

- **Code Deprecation and Cleanup:**
    - The `heartbeat_watcher.py` script has been deleted.
    - The `heartbeat.py` module was rewritten to contain a single function that reads the new JSON config and returns the formatted prompt string.
    - All obsolete code for running the old heartbeat cycle, including the toggle switch on the main UI, has been removed from `lyrn_sad_v4.0.1.pyw`.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v4.0.3.pyw`.
    - The previous version `lyrn_sad_v4.0.2.pyw` will be archived upon completion.


# LYRN-AI v4.0.2 Build Notes

## v4.0.2 - Startup and Automation Refactor (2025-08-15)

This is a major stability and architectural update that resolves a critical application hang on startup and unifies the two separate automation systems into a single, more robust framework.

- **Asynchronous Initialization:**
    - Fixed a critical bug that caused the application to freeze ("Not Responding") after loading.
    - The entire application initialization sequence has been refactored to be non-blocking. All managers that perform file I/O (`CycleManager`, `AutomationController`, etc.) are now loaded in a background thread.
    - The UI now loads instantly and displays "Loading..." placeholders, which are populated with data once the background initialization is complete. This ensures the application is always responsive to the user.

- **Unified Automation System:**
    - The separate and redundant `JobWatcherManager` system has been completely removed.
    - Its functionality has been merged into the `CycleManager`. Simple text-parsing "Watcher Jobs" are now represented as a "parser" type of Cycle.
    - The `AutomationManagerPopup` (formerly `JobWatcherPopup`) has been refactored to provide a single, unified interface for managing all types of cycles.
    - The `automation/watcher_jobs.json` file is now obsolete and has been removed from the project.

- **Improved Stability:**
    - Fixed a critical race condition by implementing file locking (`SimpleFileLock`) in the `CycleManager`. This prevents data corruption when the main GUI and background watchers access the `automation/cycles.json` file concurrently.
    - Fixed multiple `AttributeError` crashes on startup related to `cycle_manager`, `resource_monitor`, and `current_font_size` that occurred during the refactoring process.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v4.0.2.pyw`.
    - The previous version `lyrn_sad_v4.0.1.pyw` has been archived.


# LYRN-AI v4.0.1 Build Notes

## v4.0.1 - Cycle Manager & Automated Cognitive Cycling (2025-08-15)

This update introduces the **Cycle Manager**, a powerful new automation feature that allows for the creation and execution of custom, multi-step cognitive cycles. This enables the AI to perform sequences of actions autonomously.

- **New Cycle Builder UI:**
    - A new "Cycle Builder" tab has been added to the "Automation" window (`JobWatcherPopup`).
    - This UI allows users to create multiple, named cycles.
    - For each cycle, users can add a sequence of named "triggers," which are custom prompts that will be executed in order.
    - A drag-and-drop list allows for easy reordering of triggers within a cycle.

- **New Backend Components:**
    - **`cycle_manager.py`**: A new manager class to handle saving and loading cycle definitions to and from `automation/cycles.json`.
    - **`automation/cycle_watcher.py`**: A new background watcher script that runs the active cycle. It monitors the LLM's status and injects the next trigger in the sequence only when the LLM is idle.

- **IPC and State Management:**
    - The watcher and the main GUI communicate using a system of flag files:
        - `global_flags/active_cycle.json`: Stores the currently active cycle and its progress (e.g., current step).
        - `global_flags/llm_status.txt`: Indicates whether the LLM is "busy" or "idle".
        - `ipc/cycle_trigger.txt`: Used by the watcher to send the next trigger prompt to the GUI for execution.

- **Main UI Integration:**
    - A new set of controls has been added to the right sidebar in the "Job Automation" section.
    - A dropdown menu allows the user to select one of the created cycles to be the "active" cycle.
    - A "Start/Stop" button allows the user to toggle the execution of the selected cycle.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v4.0.1.pyw`.
    - The previous version `lyrn_sad_v4.0.0.pyw` has been archived.

# LYRN-AI v4.0.0 Build Notes

## v4.0.0 - Prompt Builder Restructure (2025-08-15)

This major update modularizes the entire prompt building system for clarity, flexibility, and user control. The old system has been replaced with a new tabbed interface in a dedicated popup window.

- **New Modular Prompt Fragments:**
    - The prompt is no longer built from a single index file. Instead, it is constructed from modular fragments that are concatenated at runtime.
    - Each fragment is stored in its own file in a new directory structure under `build_prompt/`.
    - The new components are: Personality, Heartbeat, User Preferences, AI Preferences, and System Rules.

- **New System Prompt Builder UI:**
    - The old "System Prompt Builder" has been replaced with a new `SystemPromptBuilderPopup` window.
    - This new window features a tabbed interface with the following tabs:
        - **Personality:** Controls the LLM's personality settings and output tone.
        - **Heartbeat:** Manages when and how the heartbeat cycle is injected.
        - **Prompt Build Order:** A drag-and-drop list to control the order of prompt construction.
        - **User Preferences:** Fields for entering user preferences.
        - **AI Preferences:** Optional behaviors for the AI agent.
        - **System Rules & Toggles:** A GUI wrapper around system flags and hard constraints.

- **Toggle Logic and Configuration:**
    - Each prompt component can be toggled ON or OFF. If OFF, the component is skipped during the prompt build.
    - The toggle states are stored in a new `build_prompt/builder_config.json` file.
    - The order of the prompt components is defined in a new `build_prompt/prompt_order.json` file.

- **Refactored Prompt Loading Logic:**
    - The `SnapshotLoader` class has been refactored to use the new modular system.
    - It now reads the `builder_config.json` and `prompt_order.json` to build the `master_prompt.txt` file at runtime.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v4.0.0.pyw`.
    - The previous version `lyrn_sad_v3.9.6.pyw` has been archived.

# LYRN-AI v3.9.6 Build Notes

## v3.9.6 - Windows Environment Interaction System (2025-08-15)

This update introduces a powerful new "System Action" affordance type, allowing the AI to perform system-level actions on the Windows OS, similar to automation tools like AutoHotKey.

- **New 'system_action' Affordance Type:**
    - The core affordance system has been refactored to be type-based.
    - A new `system_action` type is now available, alongside the existing `text_parser` type.
    - This allows for greater flexibility and extensibility in creating new capabilities for the AI.

- **System Interaction Service:**
    - A new `system_interaction_service.py` module has been created to handle all OS-level interactions.
    - The `heartbeat_watcher.py` now dispatches `system_action` affordances to this new service.

- **Supported System Actions:**
    - **`open_app`**: Launch any application by its path.
    - **`send_keys`**: Send keystrokes to a specific application window.
    - **`click`**: Perform a mouse click at given coordinates.
    - **`move_mouse`**: Move the mouse cursor to a specific position on the screen.
    - **`window_focus`**: Bring a target window to the foreground.
    - **`window_resize`**: Resize and/or move a target window.

- **Dynamic Affordance Editor GUI:**
    - The "Affordance Editor" popup has been completely overhauled.
    - The UI now dynamically changes based on the selected affordance type (`text_parser` or `system_action`).
    - When creating a `system_action` affordance, the editor provides a nested, dynamic UI to select a specific action and configure its unique parameters.

- **Dependencies & Versioning:**
    - The following dependencies have been added to `dependencies/requirements.txt`: `pyautogui`, `pygetwindow`, `keyboard`, `pywin32`.
    - The main application file has been versioned to `lyrn_sad_v3.9.6.pyw`.
    - The previous version `lyrn_sad_v3.9.5.pyw` has been archived.

# LYRN-AI v3.9.5 Build Notes

## v3.9.5 - Granular Job Scheduler (2025-08-14)

This update introduces a new "Scheduler" tab in the Automation popup, allowing for granular, calendar-based job scheduling.

- **New Scheduler Tab:**
    - A new "Scheduler" tab has been added to the "Automation" window.
    - This tab features a full calendar view, with weeks starting on Sunday, allowing users to select a specific day to schedule jobs.
    - Days with scheduled jobs are highlighted in the calendar view.

- **Day-Specific Scheduling:**
    - Clicking on a day in the calendar opens a new popup window dedicated to that day's schedule.
    - Users can select a pre-existing job and schedule it to run at a precise time, with inputs for hour, minute, second, and millisecond.
    - The popup also lists all jobs already scheduled for that day.

- **New Backend Components:**
    - **`automation/scheduler_manager.py`**: A new manager class to handle saving and loading schedules to and from `automation/schedules.json`.
    - **`automation/scheduler_watcher.py`**: A new background watcher script that continuously checks for due schedules and adds them to the main job queue for execution.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v3.9.5.pyw`.
    - The previous version `lyrn_sad_v3.9.4.pyw` has been archived.

# LYRN-AI v3.9.4 Build Notes

## v3.9.4 - Task and Goal Management (2025-08-13)

This update introduces a new Task and Goal management system, allowing the AI to autonomously track and manage its objectives.

- **New Task/Goal Watcher:**
    - A new watcher script, `automation/task_goal_watcher.py`, runs in the background to monitor chat logs.
    - The watcher parses chat logs for specially formatted blocks (`###TASK_START###` and `###GOAL_START###`).
    - Extracted tasks and goals are saved as individual files in the `build_prompt/tasks/` and `build_prompt/goals/` directories, respectively.

- **New Tasks/Goals GUI:**
    - A new "Tasks/Goals" button has been added to the main UI.
    - This button opens a new popup window with a two-tab layout for managing tasks and goals.
    - The GUI allows users to view, add, edit, and delete tasks and goals, which correspond to files in the respective directories.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v3.9.4.pyw`.
    - The previous version `lyrn_sad_v3.9.3.pyw` has been archived.

# LYRN-AI v3.9.3 Build Notes

## v3.9.3 - Icon Loading Hotfix (2025-08-13)

This is a hotfix to address an issue with the application icon not displaying correctly on certain platforms.

- **Improved Icon Loading:**
    - Replaced the `wm_iconbitmap` method with the more robust `iconphoto` method for setting the application icon.
    - This change applies to both the main application window and all popup windows (via the `ThemedPopup` base class).
    - This ensures consistent and reliable icon display across different operating systems.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v3.9.3.pyw`.
    - The window title now correctly displays `v3.9.3`.
    - The previous version `lyrn_sad_v3.9.2.pyw` has been archived.

# LYRN-AI v3.9.2 Build Notes

## v3.9.2 - Feature Polish (2025-08-13)

This is a minor update to disable an unfinished feature and improve user feedback.

- **Disabled Theme Builder:**
    - The "Theme Builder" button, previously accessible from the Advanced tab in Settings, has been temporarily disabled.
    - Clicking the button now opens a popup informing the user that the feature is unfinished and will be coming in a future update.
    - This prevents users from accessing a non-functional part of the application.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v3.9.2.pyw`.
    - The window title now correctly displays `v3.9.2`.
    - The previous version `lyrn_sad_v3.9.1.pyw` has been archived.

# LYRN-AI v3.9.1 Build Notes

## v3.9.1 - Theming and Confirmation Dialogs (2025-08-13)

This update focuses on improving user experience by ensuring all popups are non-modal, fixing theme inconsistencies, and adding standardized confirmation dialogs for all destructive actions.

- **Standardized Confirmation Dialogs:**
    - Implemented a new, reusable `ConfirmationDialog` class for all actions that require user confirmation (e.g., deleting modes, themes, jobs, or clearing directories).
    - This dialog includes a "Don't ask me again" checkbox, which saves the user's preference to `settings.json` to prevent future prompts for that specific action.
    - Replaced all previous `CTkInputDialog` confirmation prompts with the new standardized dialog for a consistent look and feel.

- **Non-Modal Popups:**
    - All secondary windows (like the Theme Builder, Automation, and Affordance Editor) are now non-modal. They no longer block interaction with the main application window, allowing for a more flexible workflow.
    - This was achieved by removing the `grab_set()` call from the respective popup classes.

- **Theming Fixes:**
    - Addressed an issue where the "Model Settings" (preset picker) popup might not have been themed correctly after loading a preset. The theme is now explicitly reapplied to ensure visual consistency.
    - As part of the fix, the core `ThemedPopup` and `ThemeManager` classes were refactored into a separate `themed_popup.py` file to resolve a circular dependency and improve code organization.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v3.9.1.pyw`.
    - The window title now correctly displays `v3.9.1`.
    - The previous version `lyrn_sad_v3.9.pyw` has been archived.

# LYRN-AI v3.9 Build Notes

## v3.9 - Custom Color Picker and Theme Builder Enhancements (2025-08-12)

This update introduces a new custom color picker for the theme builder, allowing for more flexible and user-friendly theme customization.

- **New Custom Color Picker:**
    - Replaced the default `tkinter.colorchooser` with a custom color picker popup.
    - The new picker is implemented in a separate `color_picker.py` module for better organization.
- **Color Grid Display:**
    - The custom color picker displays a grid of colors loaded from `color_grid.json`, organized by section.
- **Custom Color Input and Saving:**
    - Users can now directly input a hex color code into the picker.
    - A "Save Custom" button allows users to save their custom colors, which are stored in `custom_colors.json` and displayed in a separate section within the picker.
- **Bug Fixes:**
    - Fixed a bug in `gui_designer.py` where it was attempting to load a non-existent GUI file (`lyrn_gui_v6.8.pyw`). It now correctly loads `lyrn_sad_v3.9.pyw`.
- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v3.9.pyw`.
    - The previous version `lyrn_sad_v3.8.pyw` has been archived.

# LYRN-AI v3.8 Build Notes

## v3.8 - Preset and Prompt Management Overhaul (2025-08-12)

This update introduces significant improvements to user workflow by adding model setting presets and enhanced control over the system prompt building process.

- **Model Settings Presets:**
    - The "Model Settings" popup now features a preset system.
    - Users can save the current model configuration (model path, context size, GPU layers, etc.) into one of five numbered preset slots.
    - Added a "Save" button and five preset buttons (1-5) to the popup.
    - Clicking a preset button instantly loads the saved configuration into the UI fields.
    - Presets are stored in `settings.json` under the `model_presets` key.

- **UI Reorganization:**
    - To improve contextual grouping, several controls have been relocated.
    - The "System Prompt" button has been moved from the "Quick Controls" section to the "System Status" section, directly under the "Mode" dropdown.
    - The "Heartbeat Cycle" switch and its associated "Open Logs" button have been moved from the right sidebar's "Job Automation" section to the same location under the "Mode" dropdown.

- **Prompt Builder Enhancements:**
    - **Remove from Index:** A "Remove File" button has been added to the "Prompt Builder" popup. This allows a user to select a file in the build list and remove it from the `build_prompt_index.json` without deleting the actual file.
    - **Index and Prompt Refresh Control:**
        - The button for re-scanning subfolders has been renamed to "Rebuild Master Index from Folders" for clarity.
        - A new "Refresh Prompt from Index" button has been added. This rebuilds the `master_prompt.txt` using only the files currently visible in the UI list, respecting any files that have been manually removed from the index. This allows for quick prompt updates without a full file system re-scan.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v3.8.pyw`.
    - The window title now correctly displays `v3.8`.
    - The previous version `lyrn_sad_v3.7.pyw` has been archived.

# LYRN-AI v3.7 Build Notes

## v3.7 - UI and Configuration Fixes (2025-08-12)

This update addresses several bugs and UI inconsistencies related to model configuration and window behavior.

- **Model Chat Format Configuration:**
    - Fixed a bug in the "Model Settings" popup where the `chat_format` could not be set to `None` (no format).
    - The UI now correctly saves an empty input as `None` in the settings, allowing a clear distinction between no format and an explicitly named format like `"none"`.
    - The model loader now correctly defaults to `None` if the `chat_format` setting is missing, improving initial setup.

- **"Keep on Top" Toggle Fix:**
    - Fixed a bug where the "Keep on Top" checkbox on popups (like the Log Viewer and Prompt Builder) had no effect.
    - The underlying window property (`transient`) that forced popups to always stay on top of the main window has been removed, allowing the toggle to function as expected.

- **Model Settings UI Enhancements:**
    - Renamed the "Change Model" button on the main UI to "Model Settings" for better clarity.
    - The corresponding popup window title has also been updated to "Model Settings".
    - A warning label has been added to the "Model Settings" popup to remind users that the model must be reloaded for changes to take effect.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v3.7.pyw`.
    - The window title now correctly displays `v3.7`.
    - The previous version `lyrn_sad_v3.6.pyw` has been archived.

# LYRN-AI v3.6 Build Notes

## v3.6 - Generation Control and Model Configuration (2025-08-12)

This update introduces critical user control features for model generation and enhances model configuration options.

- **Stop Generation Button:**
    - A "Stop" button has been added to the main chat interface next to the "Send" and "Copy" buttons.
    - This allows the user to immediately interrupt the model while it is generating a response, preventing runaway generation and provide more control.
    - The underlying logic uses a flag to gracefully exit the generation loop in the background thread.

- **Enhanced Model Settings:**
    - The "Change Model" popup has been updated with two new configuration fields:
        - **Chat Style:** A text input that allows the user to specify the `chat_format` for the model (e.g., `qwen`, `chatml`). It defaults to "none".
        - **Max Output Tokens:** A text input for the user to set the `max_tokens` parameter for the model's output.
    - These settings are now saved to and loaded from `settings.json`, allowing for persistent configuration.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v3.6.pyw`.
    - The window title now correctly displays `v3.6`.

# LYRN-AI v3.5 Build Notes

## v3.5 - Theming and Versioning Fixes (2025-08-12)

This update addresses several small but important UI and versioning issues to improve visual consistency and correctness.

- **Settings Border Theming:**
    - Fixed a bug where the borders around text boxes and entries in the Settings window were not using the correct color from the loaded theme. They now correctly apply the theme's `border_color`.

- **Icon Application:**
    - Changed the method for setting the application icon from `iconbitmap` to `wm_iconbitmap` to improve consistency across different window managers and platforms.

- **Title Bar Versioning:**
    - The main application window's title bar now correctly displays the current version, `v3.5`.

- **Versioning:**
    - Renamed `lyrn_sad_v3.4.pyw` to `lyrn_sad_v3.5.pyw`.
    - Archived the previous version in `deprecated/Old/`.

# LYRN-AI v3.4 Build Notes

## v3.4 - Popup Theming and Icon Consistency (2025-08-12)

This update focuses on improving the visual consistency of all popup windows by ensuring they use the application's theme and icon correctly.

- **Popup Icon Standardization:**
    - All popup windows now correctly display the main application icon (`favicon.ico`).
    - This was achieved by adding the icon-setting logic to the `ThemedPopup` base class, from which all other popups inherit.

- **Popup Theming and Title Bar Color:**
    - Fixed a major visual bug where most popups would appear with a jarring, un-themed (often white) title bar.
    - All popups are now correctly set as "transient" for the main window, which allows the operating system to manage them more closely and apply the correct title bar theme.
    - Fixed a bug where the "System Prompt Builder" popup was completely un-themed. Its broken, overriding `apply_theme` method was removed, allowing it to inherit the correct theming from its parent class.

- **Versioning:**
    - Renamed `lyrn_sad_v3.3.pyw` to `lyrn_sad_v3.4.pyw`.
    - Archived the previous version in `deprecated/Old/`.

# LYRN-AI v3.3 Build Notes

## v3.3 - UI Cleanup and Theming (2025-08-12)

This update addresses several UI issues, improves theming consistency for popups, and adds a convenience feature for accessing heartbeat logs.

- **Automation Popup Fixes:**
    - Corrected a major bug where the "Automation" popup's tabs ("Job Viewer", "Job Builder", "Reflection Cycle") were empty. The methods to create the tab content were incorrectly placed in the `AffordancePopup` class and have been moved to the correct `JobWatcherPopup` class.
    - Removed the "Open Affordance Editor" button from the "Automation" popup to streamline the UI, as it is already accessible from the main window.

- **Theming Engine for Popups:**
    - Created a new `ThemedPopup` base class to standardize theming across all popup windows.
    - All popups, including `JobWatcherPopup`, `AffordancePopup`, and `LogViewerPopup`, now inherit from this class and apply the application's current theme, ensuring a consistent look and feel.

- **Settings Window Modality:**
    - Fixed an issue where the "Settings" window would block interaction with all other application windows (modal behavior). The `grab_set()` call was removed, so it no longer blocks other windows from being closed.

- **Heartbeat Log Access:**
    - Added a new folder icon button next to the "Heartbeat Cycle" switch on the main UI.
    - Clicking this button opens the `automation/heartbeat_outputs` directory directly in the system's file explorer, providing quick access to the logs.

- **Versioning:**
    - Renamed `lyrn_sad_v3.2.pyw` to `lyrn_sad_v3.3.pyw`.
    - Archived the previous version in `deprecated/Old/`.

# LYRN-AI v3.2 Build Notes

## v3.2 - Heartbeat and Affordance GUI (2025-08-11)

This update focuses on fixing the heartbeat system to respect the global automation flag and implementing a full-featured GUI for managing internal affordances.

- **Heartbeat Watcher Fixes:**
    - The `heartbeat_watcher.py` script now correctly checks the `global_flags/automation.txt` file. The watcher will now only process heartbeat files when this flag is set to "on", preventing it from running when automation is disabled.
    - Cleaned up verbose logging from the watcher script to only show essential messages and errors.
    - Improved the parsing of the `CHAT_PAIR_ID` from heartbeat files to be more robust.

- **New Affordance Editor GUI:**
    - Implemented a new, full-featured "Affordance Editor" popup window.
    - The editor is accessible from the main UI via a new "Affordances" button in the "Job Automation" section, making it a first-class feature.
    - The popup has a two-tab layout:
        - **Viewer Tab:** Lists all saved affordances, with options to "Edit" or "Delete" them.
        - **Editor Tab:** A form for creating and editing affordances with fields for name, start/end triggers, an output filename, and a directory selector for the output path.
    - All changes made in the GUI are saved to `automation/affordances.json` via the existing `AffordanceManager`.

- **Versioning:**
    - Renamed `lyrn_sad_v3.1.pyw` to `lyrn_sad_v3.2.pyw` to reflect the updates.
    - The previous version has been archived in `deprecated/Old/`.

# LYRN-AI v3.1 Build Notes

## v3.1 - Heartbeat and Internal Affordances (2025-08-11)

This is a major update that introduces the "Heartbeat," a toggleable, autonomous cognitive loop for the AI, and a system for "Internal Affordances," which are internal-only jobs triggered by the AI's reasoning during a heartbeat.

- **New Heartbeat System:**
    - A "Heartbeat Cycle" switch has been added to the "Automation" section of the right sidebar, allowing the user to toggle the autonomous loop on or off. The state is saved in settings.
    - When enabled, after every chat response, the AI performs an internal "heartbeat" cycle. It analyzes the preceding conversation and generates a structured output containing summaries, keywords, insights, and potential actions.
    - This output is saved to `automation/heartbeat_outputs/` for processing.

- **Heartbeat Watcher Enhancements:**
    - The `heartbeat_watcher.py` script has been updated to be the central processor for the new Heartbeat system.
    - It now parses the full heartbeat output, creates memory deltas, and adds jobs to the queue as instructed by the AI.

- **New Internal Affordance System:**
    - Implemented a new class of internal-only jobs called "Affordances." These are simple, trigger-based parsers that the AI can activate to extract specific information from a conversation.
    - The `heartbeat_watcher.py` can now process `AFFORD|` commands from a heartbeat file, find the relevant chat log, and execute the affordance to save the extracted data.
    - A new `affordance_manager.py` module and `automation/affordances.json` file have been created to manage these new objects.

- **New Affordance Editor GUI:**
    - A new "Affordance Editor" popup has been created, accessible from the "Automation" window.
    - This editor, modeled on the Job Watcher, allows users to easily create, view, edit, and delete affordances through a user-friendly interface.

# LYRN-AI v3.0 Build Notes

## v3.0 - Reflection Cycle and Autonomous Refinement (2025-08-11)

This is a major update that introduces the "Reflection Cycle," a new system for evaluating and refining job outputs using LLM-based reflection. This feature allows for autonomous improvement of job prompts over time.

- **New "Reflection Cycle" Tab:**
    - A new tab has been added to the "Automation" window to configure the reflection process.
    - Users can provide custom instructions for the LLM on how to evaluate job outputs.
    - A "gold-standard" example output can be provided for comparison.
    - The number of reflection iterations can be set.

- **Automated Prompt Refinement:**
    - A checkbox allows the LLM to automatically rewrite a job's prompt based on its reflection of the outputs.
    - Updated prompts are saved with versioning (e.g., `jobname_v2.txt`) to the `automation/jobs/` directory.

- **Autonomous Job Continuation:**
    - A checkbox enables the job to automatically continue running with the newly refined prompt, creating a self-improving loop of execution → reflection → refinement.

- **Traceability and Logging:**
    - All reflection outputs, including scores, notes, and any generated prompts, are saved to a new `reflections/` directory.
    - Each reflection run is stored in a timestamped subfolder (e.g., `/reflections/jobname_timestamp/`).
    - A `reflection_changelog.txt` file tracks all prompt updates for full traceability.

- **Batch Reflection:**
    - Reflection can be configured to run automatically after a set number of job outputs are generated, allowing for batch analysis and refinement.

# LYRN-AI v2.9 Build Notes

## v2.9 - Versioning Cleanup and Deprecation (2025-08-11)

This update officially moves the project to a `v2.x` versioning scheme, dropping the legacy `v7` prefix which was a remnant from a previous development branch. This is a maintenance and cleanup release.

- **Version Renumbering:**
    - The main application file has been renamed from `lyrn_sad_v7.2.9.pyw` to `lyrn_sad_v2.9.pyw`.
    - The project's official version is now `v2.9`.

- **Deprecation of Multi-Agent Components:**
    - All files and folders related to the deprecated multi-agent dashboard have been moved into a `deprecated/` directory for future review. This includes the `Old/` and `ipc/` directories, and the `multi_model_manager.py` script.

- **Architectural Rules Update:**
    - The `AGENTS.md` file has been updated to reflect the new location for storing old GUI versions (`deprecated/Old/`).

# LYRN-AI v7 Cognition Upgrade Build Notes

## v7.2.9 - UI Polish and Combobox Fix (2025-08-11)

This update focuses on minor UI polishing and fixing a persistent issue with `CTkComboBox` widgets.

- **Combobox Default Text:**
    - Fixed a bug where several `CTkComboBox` widgets across the application would display the text "ctkcombobox" when they had no items to show.
    - All relevant comboboxes now correctly display an empty string ("") by default, providing a cleaner and more professional user experience.

- **UI Text Cleanup:**
    - The "Job Automation Watcher" button on the right sidebar has been renamed to simply "Automation" for a cleaner look.
    - The title of the corresponding popup window has also been updated to "Automation" for consistency.

## v7.2.8 - Job Automation Watcher (2025-08-11)

This update introduces a new "Job Automation Watcher" feature, providing a user-friendly interface to create, manage, and run simple parser jobs. These jobs can extract text from the main chat window based on user-defined start and end triggers and save the result to a specified file.

- **New Backend Module:**
    - A new `job_watcher_manager.py` file was created to handle the logic for these new parser jobs, keeping them separate from the existing prompt-based automation system.
    - It uses a new `automation/watcher_jobs.json` file to store job definitions.

- **Job Automation Watcher Popup:**
    - A new "Job Automation Watcher" button has been added to the right sidebar, launching a dedicated popup for this feature.
    - The popup has a two-tab interface:
        - **Job Viewer:** Displays a list of all saved parser jobs. Users can select a job to run, edit, or delete it. A confirmation dialog has been added for deletions.
        - **Job Builder:** A form for creating or editing jobs. It includes fields for a job name, start/end triggers, an output filename, and a directory selector for the output path.

- **Functionality:**
    - Users can now define simple, reusable parsing tasks directly within the GUI.
    - The "Run" function a job against the current content of the chat display, making it easy to extract information from conversations.

## v7.2.7 - UI Layout and Readability Enhancements (2025-08-11)

This update focuses on improving the main user interface layout for better balance and readability, based on user feedback.

- **Right Sidebar Reorganization:**
    - The "Job Automation" section has been moved from the left sidebar to the right sidebar, positioned below the "System Resources" block. This consolidates monitoring and action-oriented controls in one place.

- **Cleaner Performance Metrics:**
    - The layout of the "Performance Metrics" and "System Resources" sections has been updated for improved clarity.
    - All progress bars are now positioned directly underneath their corresponding labels, creating a cleaner, more organized, and easier-to-read vertical layout.
    - This change also helps ensure that the left and right sidebars can maintain a consistent width, contributing to a more balanced and visually appealing interface.

## v7.2.6 - Job Automation Logging (2025-08-11)

This update introduces a new structured logging system specifically for job automation. The goal is to create a detailed, machine-readable log of each interaction, which can be monitored by an external "watcher" script to trigger automated workflows.

- **Structured Chat Logger:**
    - A new `StructuredChatLogger` class has been added to handle the creation of timestamped log files.
    - For each user interaction, a new log file is created (e.g., `chat_20250811_102000_123456.txt`).

- **Tagged Log Content:**
    - The logger saves the interaction in three distinct, tagged sections within the same file:
        - The user's input is saved under `#USER_START#` and `#USER_END#`.
        - The's internal "thinking" process (text between `<thinking>` tags) is saved under `#THINKING_START#` and `#THINKING_END#`.
        - The final, complete response from the assistant is saved under `#RESPONSE_START#` and `#RESPONSE_END#`.
    - This structured format allows an external script to easily parse the different components of the conversation for automation purposes.

- **Integration:**
    - The new logger is integrated into the main chat workflow. It captures user input, thinking, and the final response, and logs them to the appropriate file.
    - The previous chat saving mechanism (`save_chat_message`) has been deprecated to avoid redundancy.

## v7.2.5 - Prompt Builder Overhaul (2025-08-11)

This update completely revamps the System Prompt Builder for a significantly improved user experience and adds powerful new features for managing prompt components.

- **Dedicated Prompt Builder Window:**
    - The "Prompt Manager" tab has been removed from the Settings window.
    - A new "Open System Prompt Maker" button has been added to the "Advanced" tab in Settings, which launches the prompt builder in a dedicated, non-modal popup window.
    - The popup includes a "Keep on Top" checkbox, allowing it to stay visible while interacting with the main application.

- **File Pinning:**
    - Users can now pin individual prompt files to the top of the build order.
    - Pinned files are visually distinct and will always be loaded first, regardless of other sorting.
    - The pinning status is saved and preserved when the prompt index is refreshed.

- **Enhanced Drag-and-Drop:**
    - The drag-and-drop functionality for reordering prompt files has been completely overhauled.
    - It now features a smooth dragging motion and a clear, visual drop indicator line, so users know exactly where a file will land.
    - The reordering logic now respects pinning, preventing un-pinned files from being dropped into the pinned section and vice-versa.

- **Underlying Data Structure:**
    - The `build_prompt_index.json` has been upgraded from a simple list of paths to a list of objects, allowing metadata like `pinned` status to be stored for each file.
    - A migration path has been added to automatically and seamlessly update the old file format for existing users.

## v7.2.4 - Settings Path Hotfix (2025-08-11)

This is a hotfix release to address a critical bug in the settings system.

- **Fixed Hardcoded Paths:** The `SettingsManager` was using a hardcoded absolute path (`D:\LYRN\chat`) for the chat directory, which would cause the application to fail for other users.
- **Improved First-Time Setup:** The system now correctly detects when `settings.json` is missing and generates a new, default settings file using relative paths (e.g., `./chat`), ensuring the application runs correctly on first launch without manual configuration.

## v7.2.3 - Settings Refactor & UI Cleanup (2025-08-11)

This update focuses on streamlining the settings window and improving user workflow based on feedback.

- **Settings Window Refactor:**
    - The "Model Config" tab has been removed from the settings window to reduce redundancy, as model selection is handled by the "Change Model" button on the main screen.
    - The "Theme Builder" tab has been removed. The theme builder is still accessible via a button in the "Advanced" tab.
    - The "Personality" editor, formerly a popup, has been moved into its own dedicated "Personality" tab within the settings window.
    - The "Reload Model (Full)" button has been removed from the "Advanced" tab to simplify the UI.

- **Prompt Manager Enhancements:**
    - The "Prompt Manager" tab in settings now includes a "Mode Management" section.
    - Users can now view all saved modes in a list.
    - A "Load Mode" button allows users to activate a saved mode, which updates the current prompt build order.
    - A "Delete Mode" button allows users to permanently remove a saved mode.

- **Chat History:**
    - Clarified that the chat history is saved as individual `.txt` files.
    - The save location is visible and configurable in the settings window under `Directory Paths -> Chat Directory`.

## v7.2.2 - UI Enhancements & Feature Additions (2025-08-11)

This update focuses on quality-of-life improvements, new features, and better project organization.

- **Terminal Popup:**
    - A new "Code Terminal" button has been added to the Quick Controls section.
    - This button opens a new native terminal window, allowing users to execute code or commands in a clean environment.
    - A "Terminal Start Path" setting was added to the "UI Settings" tab in the Settings window. This allows users to configure the default directory where the terminal opens. The default is the application's root directory.

- **Dependency Management:**
    - A new `dependencies` directory has been created to formalize project dependencies.
    - A `requirements.txt` file is now included in this directory, listing all required Python packages.
    - The `AGENTS.md` file has been updated to include a rule for maintaining this new dependency file, ensuring a smoother setup for future development.

- **Performance Metrics UI Overhaul:**
    - The status dot (●) next to the "generation tok/s" label has been removed, and the label is now centered for a cleaner look.
    - The "KV Cache" progress bar has been updated to accurately reflect the number of tokens used from the cache relative to the total context size (`n_ctx`), providing a more meaningful metric.
    - A new progress bar for "Total Tokens" has been added, which also shows the usage against the total context size, allowing for a quick comparison of token usage.

---

## Phase 1: Core Architecture (2025-08-09)

This initial phase implements the core architectural changes outlined in `cognition_upgrade_v1.2.md`.

- **New Modules:** Created `delta_manager.py`, `automation_controller.py`, `heartbeat.py`, `heartbeat_watcher.py`, and `file_lock.py`.
- **GUI Upgrade:** Upgraded `lyrn_gui` to v7, integrating the new components.
- **File-based IPC:** The architecture now uses the filesystem for inter-process communication. The GUI generates heartbeat files, which are processed by a separate `heartbeat_watcher` script. A shared `job_queue.json` is used for automation.
- **Locking:** A simple file-based lock (`SimpleFileLock`) has been implemented to prevent race conditions on shared resources like the job queue.
- **Features:** Implemented the new Personality Sliders UI, which uses the delta system for live updates.

---

## Phase 2: GUI v7.1 Refinement & Stability (2025-08-09)

This phase focuses on refining the v7 GUI, improving stability, and implementing key user-requested features.

- **External Model Process:** The most significant change is the offloading of the LLM into a separate process (`model_loader.py`). This prevents the GUI from freezing during model loading and generation, dramatically improving UI responsiveness. Communication is now handled via a file-based IPC system in the `ipc/` directory.
- **UI/UX Overhaul:**
    - The main layout was updated for better visual balance, moving the time/date display and increasing its size.
    - All major UI components now have a corner radius of 38 for a more modern aesthetic.
    - A "Change Model" button was added to the main interface for convenience.
- **Model Status Indicator:** The status light is now fully functional with a new, detailed color and animation key to provide clear feedback on the model's state (e.g., Ready, Thinking, Error).
- **Windowing Fixes:**
    - The "Personality" and "View Logs" popups are no longer modal, allowing them to be used simultaneously.
    - The "Personality" window now correctly remains open after applying changes, improving the workflow.
- **Documentation:** The project's `README.md` has been comprehensively updated to reflect all the new features and the v7.1 architecture.

---

## Design Philosophy Notes

### Heartbeat Parser Philosophy (verbatim from user, 2025-08-09)
> The heartbeat parser will just be a watcher for the folder that the heartbeat text goes into. This heartbeat is not just another job like i thought but does need to be a toggleable runtime. We are just injecting the trigger like a job though. So you need to think in terms of simple grab text from provided structured blocks and put them where its told to put them every time. no smart logic routing or handling. just dumb take this block of text between the brackets and place it where it needs to go. The entire system runs off of this logic and it will be simple to implement.

---

## Phase 3: Next Steps & Todos

- **Implement Delta Consumption**: The system currently *generates* deltas, but does not yet *consume* them. The next task is to implement the logic that, for each reasoning cycle, gathers all new delta files, reads their content, and injects the resulting block of strings into the LLM's context. This is a critical step for enabling the AI's self-monitoring capabilities. Refer to `AGENTS.md` for the specific injection point and architectural purpose.

---

## v7.2 - Multi-Agent Constellation (2025-08-10)

This major update introduces a multi-agent architecture, allowing users to load and interact with multiple language models simultaneously in a tabbed interface.

- **Multi-Agent GUI:**
    - The central chat window has been replaced with a custom tabbed interface.
    - Agent tabs are managed via a vertical set of buttons on the right side of the chat area, allowing for quick switching between conversations.
    - A new "+" button launches the "Add New Agent" popup to configure and load a new model into a new tab.

- **Dynamic Agent Loading:**
    - A new `AddNewAgentPopup` provides a comprehensive UI for loading new agents.
    - Users can name each agent tab, select a model file, and configure all model parameters (context size, GPU layers, etc.).
    - **Quick Picks:** The popup includes a preset system. Users can save a complete agent configuration as a named "Quick Pick" for one-click loading in the future. Presets are saved in `model_presets.json`.

- **Enhanced Process Management:**
    - Introduced `MultiModelManager`, a new class responsible for launching, tracking, and terminating multiple `model_loader.py` processes.
    - The file-based IPC system has been upgraded to support isolated communication channels for each agent, using unique subdirectories under the `ipc/` folder.
    - `model_loader.py` was updated to accept an `--ipc-id` to operate in its designated directory.

- **Startup Configuration:**
    - A new "Startup Agents" tab has been added to the main Settings window.
    - Users can select from their saved "Quick Picks" to create a list of agents that will be loaded automatically when the application starts.
    - This startup configuration is saved in `settings.json`. The application will now auto-load the user's preferred set of agents for a personalized experience.

---

## v7.2.1 - Revert to In-Process Model Loading (2025-08-10)

This update reverts the model loading mechanism to an in-process approach, removing the external `model_loader.py` and the associated file-based IPC. This change was made to simplify the architecture and resolve issues related to the IPC implementation, as the multi-agent control for which it was designed is no longer a project goal.

- **In-Process Model Loading:**
    - The `Llama` model is now instantiated directly within the main GUI process, as it was in v6.8 and earlier.
    - The `setup_model` function was updated to handle direct, in-process loading.
- **Removed External Process:**
    - The `model_loader.py` script is no longer used.
    - The `subprocess` calls and file-based trigger system (`chat_trigger.txt`) have been completely removed from the GUI.
- **Direct Response Generation:**
    - The `send_message` function now directly calls the `generate_response` method in a thread.
    - The `generate_response` method uses `self.llm.create_chat_completion` to stream the response directly to the GUI, eliminating the need for file tailing.
- **Code Simplification:** The removal of the IPC layer has simplified the codebase, making it easier to maintain and debug.
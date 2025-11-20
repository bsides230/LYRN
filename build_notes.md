## v4.3.1 - Job-Based Automation Loop and Session Control (2025-09-14)

This update transforms the chat system into a job-based automation loop and adds session management features.

- **Job-Based Automation Loop:**
    - The chat interaction is now governed by an automated job loop.
    - When a user sends a message, instead of generating a direct response, the system now triggers a sequence of jobs defined in `automation/job_sequence.txt`.
    - **Flow:**
        1.  **Input Capture:** The user's message is formatted with `#Active_Chat_Pair_Start#` and `#Active_Chat_Pair_End#` tags and saved to `temp_chat_turn.txt`.
        2.  **Sequence Execution:** The system iterates through the job triggers in `job_sequence.txt`.
        3.  **Job Responses:** Each job's output is appended to a `temp_job_responses.txt` file.
        4.  **Context Injection:** The LLM's context now includes the `temp_chat_turn.txt` (User Input) and `temp_job_responses.txt` (Intermediate Job Outputs), providing a "whiteboard" of recent activity.
        5.  **Final Output:** A `final_output` job is triggered at the end of the loop. Its response is appended to `temp_chat_turn.txt` (with tags) and displayed to the user.

- **Session Management:**
    - **Persistence:** The Verbatim Memory Watcher now checks for an existing, open session folder on startup and resumes it, preventing the creation of fragmented session logs after restarts.
    - **Manual New Session:** A "Start New Session" button has been added to the main GUI (left sidebar). This allows users to manually archive the current session and start a fresh one when desired.

- **GUI Changes:**
    - Added "Start New Session" button to the Quick Controls.
    - Updated the "Open Chat Folder" button in Settings to open the `Chat_History` directory (verbatim logs) instead of the old logs folder.

- **Versioning:**
    - The main application file has been versioned to `lyrn_sad_v4.3.1.py`.
    - The previous version `lyrn_sad_v4.3.0.py` has been archived in `deprecated/Old/`.

### Logging
- Chat interactions are now processed through an automation loop, with intermediate job outputs tracked in `temp_job_responses.txt` before the final response is logged.

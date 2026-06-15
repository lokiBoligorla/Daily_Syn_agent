# DailySync: AI Internship Daily Reporting Agent

DailySync is an automated, AI-powered assistant designed to streamline daily internship reporting workflows. By providing a single point of input, DailySync professionalizes your daily tasks, updates your Excel tracking sheet (preserving all cell styles and fonts), generates a formal daily update email, attaches the updated workbook, and mails it directly to your team leads.

## 🚀 Key Features

* **AI Task Expansion**: Translates informal task points into clear, action-oriented corporate descriptions.
* **Dynamic Excel Mapping**: Reads column headers dynamically without hardcoding. Maps and structures task data dynamically using the LLM.
* **Excel Formatting Preservation**: Copies cell formatting (fonts, borders, fills, alignment) from previous rows and auto-adjusts column widths.
* **Auto-Incrementing IDs**: Detects serial number / ID columns (like `S.No`, `ID`, `No.`) and increments them automatically.
* **Preview Workflow**: Review structured tasks, view Excel data changes (using a Pandas DataFrame view), and edit email drafts before dispatching.
* **SMTP Integration**: Delivers reports automatically with attachments to multiple team leads.
* **Offline Mock LLM Mode**: Fully test the application frontend and spreadsheet updating offline without an API key.

---

## 📁 Project Architecture

```text
├── app.py                     # Streamlit frontend with premium glassmorphic UI
├── requirements.txt           # Python library dependencies
├── .env                       # Environment credentials (API Keys & SMTP)
├── .env.example               # Template environment configuration
│
├── agent/                     # LangGraph workflow orchestration
│   ├── graph.py               # Workflow graph structure & conditional routing
│   ├── state.py               # Schema definitions for state management
│   ├── llm.py                 # LLM selection (Gemini, OpenAI, Nvidia, Mock)
│   ├── utils.py               # Shared utility functions
│   └── nodes/                 # Nodes processing state transitions
│       ├── task_processor.py  # Parse & expand raw tasks
│       ├── excel_updater.py   # Maps and appends to the Excel sheet
│       ├── email_generator.py # Formulates the update email draft
│       └── email_sender.py    # Dispatches email with attachment via SMTP
│
├── tools/                     # Helper tool interfaces
│   ├── excel_tool.py          # openpyxl styles copier & row appender
│   └── email_tool.py          # SMTP multipart email delivery
│
├── data/                      # Data files folder
│   └── internship_tracker.xlsx # Target tracking spreadsheet database
│
└── scratch/                   # Verification & simulation scripts
    ├── create_sample_excel.py # Generates base tracking template
    ├── test_agent.py          # Programmatic workflow dry-run script
    └── check_excel.py         # Style validation inspector
```

---

## 🛠️ Setup & Installation

### 1. Install Dependencies
Run the command below in your terminal to install the project dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to a new file named `.env` in the root directory:
```bash
cp .env.example .env
```
Open `.env` and fill in the values:
* **LLM_PROVIDER**: Choose `gemini` (default), `openai`, `nvidia`, or `mock`.
* **API Keys**: Add `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `NVIDIA_API_KEY` depending on your provider choice. (If set to `mock`, no API key is required).
* **SMTP Config**: Input your mail server settings (e.g. Gmail requires an **App Password**; standard SMTP port is `587` for TLS or `465` for SSL).
* **Team Leads**: Input recipient emails in `TEAM_LEAD_1` and `TEAM_LEAD_2`.

---

## 🚀 How to Run the App

### Launch the Streamlit Interface
Run the following command in the workspace directory:
```bash
streamlit run app.py
```
This opens the DailySync interface in your default web browser (usually at `http://localhost:8501`).

---

## 🧪 Verification & Simulation

You can test the entire workflow programmatically without opening the UI by running the dry-run simulation:

1. **Verify Agent Workflow (Dry Run)**:
   ```bash
   python scratch/test_agent.py
   ```
   This runs the agent up to the email generation node using the `MockLLM` fallback (if no keys are configured), updating the tracker and writing the email body.

2. **Inspect Spreadsheet Formatting**:
   ```bash
   python scratch/check_excel.py
   ```
   This prints the spreadsheet rows and verifies that styles (Segoe UI font, margins, color fills) are copied correctly.

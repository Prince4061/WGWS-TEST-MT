# 🎓 Student Assessment Tracker

A modern, web-based assessment tracking and diagnostic evaluation platform designed for schools. Built with **Flask**, **SQLAlchemy**, **Vanilla JS & CSS**, **ReportLab**, and **LangChain Deep Agents** (`deepagents`).

---

## 🌟 Key Features

### 1. Zero-Friction Student Assessment
- **Instant Join:** Students enter simply with **Name + Class** (no passwords, OTPs, or accounts required).
- **Server-Authoritative Timer:** Anti-tamper server countdown timer prevents client-side clock tampering and auto-submits on time expiration.
- **Auto-Save Engine:** Answers, dwell-time per question, and answer changes are saved seamlessly in the background via AJAX.
- **Interactive Question Palette:** Shows answered (green), unanswered (neutral), and marked-for-review (purple) questions with instant jumping.
- **Anti-Cheating Guard:** Monitors and logs browser tab-switching events (`visibilitychange`) for teacher review.

### 2. Teacher & School Administration
- **Teacher Dashboard:** Real-time visibility into active tests, total attempts, and class benchmarks.
- **CSV Test Builder:** Download standardized CSV question templates, upload question banks, and receive row-by-row validation with precise error reporting.
- **Live Monitor:** Real-time auto-updating view of students taking the test, elapsed time, current progress, and tab-switch alerts.
- **Class Results & CSV Export:** Class score distribution, top/lowest performers, and one-click export of complete student rosters to CSV.
- **School Branding:** Custom school name and logo uploader printed on all official student PDF report cards.

### 3. LangChain Deep Agent Diagnostic Evaluation
- **Multi-Agent Topology:** Powered by `deepagents` with 4 specialized sub-agents:
  - **Performance Analyst Sub-agent:** Evaluates topic-wise, question-type, and difficulty mastery.
  - **Time & Behavior Analyst Sub-agent:** Detects rush patterns (<12s with wrong answer), bottlenecks, and answer-switching habits.
  - **Mistake Diagnoser Sub-agent:** Classifies mistake root causes into *Concept Gap*, *Careless*, *Calculation Error*, or *Misread*.
  - **Study Coach Sub-agent:** Generates 3–5 concrete, grade-appropriate study tasks with estimated time and resource hints.
- **Deterministic Statistics Tools:** All percentages, averages, and counts are calculated with pure Python tools to eliminate hallucinations.
- **100% Reliable Fallback:** If the LLM is offline or unconfigured, a deterministic rule-based engine immediately generates an identical Pydantic-validated diagnostic schema so reports are never delayed.

### 4. Official PDF Report Cards
- Beautifully formatted, print-ready PDF generated via **ReportLab**:
  - School logo and header branding
  - Test & Student metadata
  - Score summary cards (Final Score, Percentage, Correct, Wrong, Skipped, Time taken)
  - AI Diagnostic Insights (Executive summary, strengths, weak areas with priority, action plan, coach note)
  - Topic-wise accuracy breakdown table
  - Itemized mistakes review with question text, student's choice, correct choice, and pedagogical explanation
  - Dynamic page numbering and generation timestamps

---

## 📁 Project Structure

```text
Student Assessment/
├── app/
│   ├── __init__.py               # Flask application factory
│   ├── models.py                 # SQLAlchemy DB models (SchoolSettings, Admin, Test, Question, Student, Attempt, Answer, Feedback, Report)
│   ├── blueprints/
│   │   ├── auth.py               # Admin login/logout
│   │   ├── admin.py              # Dashboard, test builder, CSV upload, live monitor, results
│   │   ├── student.py            # Student portal, live test engine, auto-save, instant scoring
│   │   └── report.py             # PDF report download & web report viewer
│   ├── services/
│   │   ├── csv_service.py        # CSV template generator & strict row-by-row validator
│   │   ├── test_engine.py        # Server timer, answer progress, and tab-switch logger
│   │   ├── scoring.py            # Deterministic scoring engine with negative marking
│   │   └── pdf_service.py        # Publication-quality PDF generator using ReportLab
│   ├── ai/
│   │   ├── agent.py              # create_deep_agent orchestrator with 4 sub-agents
│   │   ├── tools.py              # Pure Python mathematical calculation tools
│   │   ├── schemas.py            # Pydantic structured output schema
│   │   ├── fallback.py           # 100% reliable rule-based diagnostic engine
│   │   └── prompts.py            # Sub-agent and orchestrator system prompts
│   ├── templates/                # Jinja2 HTML templates (base.html, student/, admin/, report/)
│   └── static/
│       ├── css/style.css         # Modern, responsive design system
│       └── uploads/              # Uploaded school logos
├── sample_data/
│   └── sample_math_class10.csv  # 20-question ready-to-use Class 10 Math assessment
├── reports/                      # Generated student PDF reports
├── instance/                     # SQLite database
├── tests/
│   └── test_assessment.py        # Unit & integration test suite
├── seed_sample_test.py           # Seeds ready-to-test Class 10 assessment
├── config.py                     # Configuration settings
├── requirements.txt              # Project dependencies
├── .env.example                  # Environment variables guide
└── run.py                        # Server runner
```

---

## 🚀 Quickstart Guide

### 1. Setup Virtual Environment & Install Dependencies
```bash
uv venv
# Windows:
.venv\Scripts\activate
# Mac / Linux:
# source .venv/bin/activate

uv pip install -r requirements.txt
```

### 2. Seed Sample Assessment Data
Populates a sample 20-question Class 10 Mathematics assessment ready to test:
```bash
python seed_sample_test.py
```

### 3. Run Automated Tests
```bash
python -m unittest tests/test_assessment.py
```

### 4. Start the Application Server
```bash
python run.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser!

---

## 🔑 Default Credentials

- **Admin Login:** [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login)
  - **Username:** `prince`
  - **Password:** `tarunsirkijai`
- **Student Portal:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
  - Select **Class 10** to take the live seeded test.

---

## 📋 CSV Upload Format

Teachers can create tests by uploading CSV files with these headers:

| Column | Type | Allowed Values / Format | Description |
|---|---|---|---|
| `question_no` | Number | `1, 2, 3...` | Order index |
| `question` | Text | Any string | Question text (English/Hindi supported) |
| `option_a` | Text | Any string | Option A text |
| `option_b` | Text | Any string | Option B text |
| `option_c` | Text | Any string | Option C text |
| `option_d` | Text | Any string | Option D text |
| `correct_option`| Char | `A` / `B` / `C` / `D` | The correct answer |
| `topic` | Text | e.g. `Algebra` | Used for topic mastery analytics |
| `question_type` | Text | `conceptual`, `numerical`, `application`, `recall` | Diagnostic category |
| `difficulty` | Text | `easy`, `medium`, `hard` | Question difficulty level |
| `explanation` | Text | Optional string | Explanation printed on PDF mistake report |

---

## 🤖 Optional: Configuring Live LLM API Keys

The system works out of the box with the built-in deterministic fallback engine. To enable live LLM evaluation via LangChain Deep Agents:

Edit `.env`:
```ini
# For Groq (Recommended for lightning-fast inference)
GROQ_API_KEY=your_groq_api_key_here
DEFAULT_LLM_PROVIDER=groq
DEFAULT_MODEL=llama-3.3-70b-versatile

# OR for OpenAI
# OPENAI_API_KEY=your_openai_api_key_here
# DEFAULT_LLM_PROVIDER=openai
# DEFAULT_MODEL=gpt-4o-mini
```

---

## 🚀 Deploy to Render (One-Click Deploy)

This repository is pre-configured for Render with `render.yaml`, `Procfile`, and `gunicorn.conf.py`.

1. Go to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository (`Prince4061/WGWS-TEST-MT`).
4. Click **Apply**.
5. Render will automatically build and start the web service via Gunicorn.
   - **Default Admin:** `prince`
   - **Password:** `tarunsirkijai`


# GemmaNotepad1 — AI-Powered Study Notepad

A modern, fully offline Python desktop application for studying PDFs with local AI explanations and quiz generation.

## Quick Start

```bash
# 1. Create and activate a virtual environment

      # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python main.py
```

## Requirements

- Python 3.12+
- Ollama installed and running locally (for AI features — Phase 3+)
- Windows 10/11

## Development Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 — Desktop UI | ✅ Complete | Full GemmaNotepad1-themed UI shell |
| 2 — Documents  | 🔜 Next     | PDF rendering, text selection, image display |
| 3 — AI         | 🔜 Planned  | Ollama integration, AI popup, explanations |
| 4 — Quiz       | 🔜 Planned  | MCQ generation, scoring, history |
| 5 — Polish     | 🔜 Planned  | Packaging, transitions, persistence |

## Project Structure

```
study-notepad/
├── main.py                     Entry point
├── requirements.txt
├── app/
│   ├── core/                   Config, data models
│   ├── ui/                     All PySide6 widgets
│   ├── services/               Business logic (Phase 2+)
│   ├── workers/                QThread workers (Phase 3+)
│   └── storage/                SQLite repositories (Phase 2+)
└── assets/
    ├── icons/
    └── styles/                 QSS theme + color constants
```

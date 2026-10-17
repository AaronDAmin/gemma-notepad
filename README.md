# GemmaNotepad1

### Your intelligent workspace for focused learning.

**GemmaNotepad1** is a modern, lightweight, AI-powered desktop study application built with Python and PySide6. It combines document reading, intelligent explanations, note-taking, and interactive quizzes into a single distraction-free workspace.

Powered by **Ollama and local language models**, GemmaNotepad1 brings AI-assisted learning directly to your computer — without cloud dependencies, API keys, or internet access.

**Read. Understand. Practice. Repeat.**

---

## Application Demo

![GemmaNotepad1 Demo](assets/demo/gemmanotepad-demo.gif)

*Explore documents, highlight concepts, get instant AI explanations, and test your knowledge — all within one workspace.*

## Features

### Intelligent Document Workspace

- **Multi-tab interface** — Open and organize multiple study sessions.
- **PDF Reader** — Read PDFs with page navigation, zoom, and text selection.
- **Image Support** — Import and view images alongside your study materials.
- **Text Editor** — Create, edit, and save personal study notes.
- **Session Persistence** — Resume your documents and reading positions.

### Context-Aware AI Assistant

Select any passage from your study material and let the AI explain it using the surrounding document context.

- Instant explanations through contextual popups.
- Simplified or detailed explanations.
- Follow-up questions for deeper understanding.
- Document-aware responses.
- Local model selection through Ollama.
- Private, offline AI processing.

### Smart Quiz Generator

Turn your study materials into interactive multiple-choice quizzes.

- Generate quizzes directly from your documents.
- Choose specific chapters or pages.
- Customize difficulty and question count.
- Practice memorization, comprehension, and application.
- Receive automatic scoring and answer explanations.
- Review incorrect answers.
- Track quiz attempts and learning progress.

### Privacy by Design

Your documents stay on your computer.

GemmaNotepad1 uses locally hosted AI models through Ollama, so document analysis and quiz generation do not require external AI services.

No account. No API key. No cloud processing.

## Preview

### Application Interface

![GemmaNotepad1 Interface](assets/screenshots/main-window.png)

### AI-Powered Explanations

![Contextual AI Assistant](assets/screenshots/ai-assistant.png)

### Interactive Quizzes

![Quiz Interface](assets/screenshots/quiz.png)

---

## Tech Stack

| Component | Technology |
|---|---|
| Core Language | Python 3.12+ |
| Desktop Framework | PySide6 / Qt 6 |
| UI Styling | Qt Style Sheets (QSS) |
| PDF Processing | PyMuPDF |
| AI Runtime | Ollama |
| AI Models | Locally installed Ollama models |
| Local Database | SQLite |
| Background Processing | QThread / Qt Workers |
| Platform | Windows 10 / 11 |

## Installation

### Prerequisites

Ensure you have the following installed:

- Python 3.12 or later
- Ollama
- At least one Ollama-compatible local language model

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Prepare Ollama

Make sure Ollama is running locally.

```bash
ollama list
```

This command displays your installed models.

If Ollama is not already running, start it using:

```bash
ollama serve
```

### 5. Launch GemmaNotepad1

```bash
python main.py
```

Select your preferred installed AI model in the application's settings and start studying.

## How It Works

**1. Import your material**

Open a PDF, image, or text document using the Upload tool.

**2. Explore and understand**

Read your document, highlight an unfamiliar concept, and select **Explain with AI** to receive a contextual explanation.

**3. Practice what you learned**

Open Quiz mode, select the relevant material, and configure your quiz.

**4. Review your performance**

Answer questions, receive feedback, and revisit concepts that need improvement.

All within the same workspace.

## Project Architecture

```text
study-notepad/
│
├── main.py
├── requirements.txt
├── README.md
│
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── models.py
│   │
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── sidebar.py
│   │   ├── tab_bar.py
│   │   ├── workspace.py
│   │   ├── pdf_viewer.py
│   │   ├── image_viewer.py
│   │   ├── text_editor.py
│   │   ├── ai_popup.py
│   │   └── quiz_view.py
│   │
│   ├── services/
│   │   ├── document_service.py
│   │   ├── context_service.py
│   │   ├── ollama_service.py
│   │   └── quiz_service.py
│   │
│   ├── workers/
│   │   └── ai_worker.py
│   │
│   └── storage/
│       └── repositories.py
│
├── assets/
│   ├── icons/
│   ├── styles/
│   ├── screenshots/
│   └── demo/
│       └── gemmanotepad-demo.gif
│
└── tests/
```

## Design System

GemmaNotepad1 uses a custom **MUSTARD — Bold, Modern & Playful** design language.

| Color | Hex |
|---|---|
| Charcoal | `#282B28` |
| Mustard | `#D4A017` |
| Golden Yellow | `#F0C94C` |
| Soft Cream | `#F7E7B5` |
| Off-White | `#FFF0F5` |

The interface combines warm colors, clean typography, rounded components, and minimal navigation to create a comfortable learning environment.

## Performance & Offline Support

GemmaNotepad1 is designed to run locally on everyday desktop hardware.

- No cloud backend required.
- Lightweight native Qt interface.
- Background AI inference to keep the UI responsive.
- Local SQLite storage.
- Support for quantized language models.
- Efficient document rendering and page caching.

AI performance depends on the selected model and available system resources.

## Contributing

Contributions, feature suggestions, and bug reports are welcome.

To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Commit your changes.
5. Open a pull request.

Please keep contributions consistent with the project's lightweight, privacy-first architecture.

## License

License information will be provided in the repository's `LICENSE` file.

---

**GemmaNotepad1**

*Smarter studying. Powered by local AI.*

Built with Python, PySide6, and Ollama.
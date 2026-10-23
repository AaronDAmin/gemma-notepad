# NotepadLLM — UI/UX Implementation Specification

**Version:** 1.0  
**Platform:** Windows Desktop  
**Framework:** Python 3.12+ / PySide6 (Qt 6)  
**AI Runtime:** Existing local Ollama installation  
**Design System:** MUSTARD — Bold, Modern & Playful

## 1. Project Objective

Build a modern, lightweight desktop study application that combines PDF reading, image viewing, note-taking, contextual AI explanations, and quiz generation.

The provided design reference images define the intended visual appearance of the application.

**The primary objective is to faithfully reproduce these designs while implementing a functional, responsive and maintainable PySide6 application.**

Do not redesign the interface without a clear technical justification.

## 2. Core UI Architecture

The application must use one primary desktop window with a persistent navigation shell.

### Main Window

The layout consists of:

- Top application bar with application identity, search and window controls.
- Horizontal document tab bar.
- Left vertical navigation sidebar.
- Central content area.
- Optional contextual panels or modal dialogs.

Use `QMainWindow` as the root component.

Use `QStackedWidget` for switching between central views.

Use layouts such as `QHBoxLayout`, `QVBoxLayout` and `QGridLayout` rather than absolute positioning.

### Navigation Rules

The central workspace must support:

| View | Behavior |
|---|---|
| Home | Welcome screen and quick actions |
| PDF Reader | Display and interact with PDF documents |
| Image Viewer | Display imported images |
| Text Editor | Create and edit notes |
| Quiz | Configure, complete and review quizzes |
| Recent | Display recently accessed documents |
| Library | Organize imported documents |
| Search | Find documents and text passages |
| Settings | Configure the application |

The application must not open a new top-level window for each feature.

**Workspace & Tab Management is not a separate page.** Document organization happens directly through the top tab bar.

## 3. Sidebar Navigation

Use a compact vertical sidebar consistent with the reference images.

Primary actions:

- Select
- Upload
- Quiz
- Recent
- Library
- Settings
- Theme

Home may be accessible through the application logo or a Home tab.

Do not introduce additional navigation buttons without a functional reason.

Only the active navigation item should receive the primary mustard highlight.

### Upload Behavior

Clicking Upload must open a centered modal dialog.

The dialog allows users to:

1. Import a PDF.
2. Import an image.
3. Import a text file.
4. Create a new text note.

For the personal offline version, prioritize files from the local computer.

Do not implement Google Drive, OneDrive or cloud upload integrations.

## 4. Document Tabs

The top bar manages open documents and notes.

Each tab must support:

- Document title.
- Document type icon.
- Active/inactive state.
- Close action.
- Switching between documents.
- Restoration of its previous state.

The `+` button creates a new workspace tab.

Closing a tab must not delete the associated document.

Unsaved changes in text notes must trigger an appropriate confirmation.

## 5. Design System

### Colors

| Token | Color |
|---|---|
| Charcoal | #282B28 |
| Mustard | #D4A017 |
| Golden Yellow | #F0C94C |
| Soft Cream | #F7E7B5 |
| Off-White | #FFF0F5 |

Use centralized theme tokens rather than hardcoded colors throughout the application.

### Visual Guidelines

- Rounded corners: approximately 8–14 px.
- Consistent spacing based on 4 px increments.
- Clear typographic hierarchy.
- Subtle shadows and borders.
- Smooth hover and pressed states.
- Minimal visual clutter.
- Consistent iconography.
- Good text contrast.
- Responsive layouts for different window sizes.

Use reusable QSS styles.

Avoid excessive animation and decorative elements.

## 6. Required Screens

### 6.1 Home

Display a simple welcome workspace containing:

- Open Document.
- New Note.
- Generate Quiz.
- Recent Documents.

Do not overload the page with unnecessary dashboards.

### 6.2 PDF Reader

The PDF viewer must support:

- Original PDF page rendering.
- Page navigation.
- Zoom.
- Scrolling.
- Accurate text selection.
- Contextual AI actions.
- Reading-position restoration.

Use PyMuPDF for extraction and rendering where appropriate.

Investigate Qt PDF capabilities before selecting the final implementation.

Do not sacrifice text-selection accuracy for appearance.

### 6.3 Image Viewer

Support PNG, JPG and JPEG.

Provide basic zoom, scrolling and image fitting.

OCR is not required for the initial implementation.

### 6.4 Text Editor

Support:

- Writing notes.
- Editing.
- Copy/paste.
- Text selection.
- Saving and reopening.
- Contextual AI explanations.

Use a suitable native Qt text-editing widget.

### 6.5 Quiz Configuration

The user must be able to select:

- Source document.
- Page range or chapter.
- Number of questions.
- Difficulty.
- Learning objective.
- Optional time limit.

A primary Generate Quiz button starts generation.

### 6.6 Quiz Generation

Display a lightweight loading state while Ollama generates the quiz.

Include:

- Animated loading indicator.
- Current operation.
- Cancel button.

Do not display fabricated progress percentages. Use an indeterminate indicator when actual progress is unavailable.

### 6.7 Quiz Interface

Display one multiple-choice question at a time.

Include four answer choices, navigation buttons and a progress indicator.

Do not reveal the correct answer before submission.

### 6.8 Quiz Results

Display:

- Final score.
- Correct and incorrect answers.
- Review of individual questions.
- Explanation for each answer.
- Relevant source references.
- Retry Quiz action.
- Back to Document action.

### 6.9 Recent Documents

Show recently opened documents with:

- File name.
- Type.
- Last opened time.
- Open action.

An optional preview may appear when a document is selected.

### 6.10 Library

Provide a local document library with:

- Document listing.
- Basic folders or categories.
- Search.
- Open and remove actions.

Avoid complex cloud-storage functionality.

### 6.11 Search

Use the simplified search design.

Display:

- Search input.
- Matching document passages.
- Source document and page.
- Selected result preview.
- Open Page action.

AI explanation may be available as a secondary contextual action.

Avoid excessive filters, statistics and unrelated panels.

### 6.12 Settings

Group settings into:

- General.
- AI Model (Ollama).
- Documents & Notes.
- Quiz.
- Appearance.
- Advanced & Storage.

Keep all settings within the central workspace.

## 7. AI Components

### AI Explanation Popup

The user selects text and chooses Explain with AI.

The application must:

1. Capture the selected passage.
2. Identify the source document.
3. Retrieve nearby text.
4. Construct a contextual prompt.
5. Send it to the selected local model.
6. Display the explanation.

The popup must support simpler explanations, detailed explanations and follow-up questions.

Source references must be derived from the actual document, not invented by the model.

### Follow-up Conversation

Maintain the context of the selected passage or quiz question.

Display the conversation in a scrollable area.

Allow the user to ask additional questions without reopening the document.

### Ollama Integration

Ollama and at least one local model are already installed.

Do not reinstall Ollama or automatically download models.

Use the existing local API to:

- Check server availability.
- List installed models.
- Select the active model.
- Generate explanations.
- Generate structured quiz questions.

Use background workers for AI inference.

Never block the Qt main thread.

## 8. Modal Dialogs and Error States

Implement reusable modal components.

Required dialogs:

- Upload Document.
- AI Explanation.
- AI Follow-up.
- Unsupported File.
- Ollama Connection Error.
- Unsaved Changes confirmation.
- Delete confirmation.

Dialogs must support closing, keyboard navigation and appropriate focus behavior.

Do not use modal dialogs for ordinary navigation.

## 9. Local Persistence

Use SQLite for application metadata and saved study state.

Persist:

- Documents.
- Notes.
- Open tabs.
- Reading positions.
- Selected AI model.
- Quiz attempts.
- Scores.
- User preferences.

Store imported files locally.

Do not require an online account or cloud backend.

## 10. Reusable PySide6 Components

Create reusable components instead of duplicating UI code.

Recommended components:

- `MainWindow`
- `NavigationSidebar`
- `DocumentTabBar`
- `WorkspaceContainer`
- `DocumentCard`
- `PrimaryButton`
- `SecondaryButton`
- `SearchBar`
- `ModalDialog`
- `PDFViewer`
- `ImageViewer`
- `NoteEditor`
- `AIExplanationDialog`
- `QuizQuestionCard`
- `QuizProgressIndicator`
- `SettingsSection`
- `EmptyState`
- `ErrorState`

Use signals and slots to communicate between components.

Avoid direct coupling between unrelated widgets.

## 11. Suggested Architecture

```text
NotepadLLM/
├── main.py
├── requirements.txt
├── README.md
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── models.py
│   │   └── events.py
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── components/
│   │   ├── dialogs/
│   │   ├── pages/
│   │   └── themes/
│   ├── services/
│   │   ├── document_service.py
│   │   ├── pdf_service.py
│   │   ├── search_service.py
│   │   ├── ollama_service.py
│   │   └── quiz_service.py
│   ├── storage/
│   │   ├── database.py
│   │   └── repositories/
│   └── workers/
├── assets/
│   ├── icons/
│   └── references/
└── tests/
```

Adapt this structure to the existing repository rather than replacing working code unnecessarily.

## 12. Implementation Priorities

### Priority 1 — Visual Foundation

- Main window.
- Sidebar.
- Tabs.
- Central navigation.
- Theme.
- Reusable controls.
- Modal framework.

### Priority 2 — Documents

- PDF reading.
- Image viewing.
- Text editing.
- Local library.
- Recent documents.
- Search.

### Priority 3 — AI

- Existing Ollama connection.
- Installed model selection.
- Text selection and context extraction.
- Explanation popup.
- Follow-up conversation.

### Priority 4 — Quiz

- Configuration.
- Generation.
- Question interface.
- Results.
- History.

### Priority 5 — Finalization

- Persistence.
- Performance.
- Error handling.
- Accessibility.
- Packaging.
- Regression testing.

## 13. Testing Requirements

Test the application after every major change.

### Visual Testing

Launch the real PySide6 application and compare it with the reference image.

Verify:

- Layout proportions.
- Colors.
- Typography.
- Button placement.
- Padding and spacing.
- Dialog alignment.
- Tab behavior.
- Resizing.

Capture screenshots of the actual application.

Do not claim visual fidelity without inspecting the rendered interface.

### Functional Testing

Test:

- File imports.
- PDF navigation.
- Text selection.
- Note saving.
- Tab switching.
- Ollama connectivity.
- AI response handling.
- Quiz generation and scoring.
- Local persistence.
- Error recovery.

Use automated tests where practical and manual interaction testing for visual behavior.

## 14. Git Workflow

Work on the existing development branch unless a new branch is necessary.

Create dedicated branches for major features, for example:

- `feature/pdf-reader`
- `feature/ai-integration`
- `feature/quiz-engine`
- `feature/settings`

Make regular, meaningful commits after completed units of work.

Use descriptive commit messages.

Do not commit generated caches, virtual environments, local databases, private documents or AI model files.

Do not merge major changes without testing.

## 15. Agent Execution Instructions

Before implementing a screen:

1. Inspect the existing code.
2. Examine its corresponding reference image.
3. Identify the reusable components.
4. Explain any necessary technical deviations.
5. Implement the interface.
6. Launch the application.
7. Test its behavior.
8. Capture and inspect a screenshot.
9. Correct visible inconsistencies.
10. Commit the completed work.

**Do not implement all screens in one untested pass.**

Work incrementally and preserve functioning features.

## 16. Definition of Done

A screen is complete only when:

- It closely matches its approved reference.
- Its navigation works.
- Its controls perform real actions.
- Its layout resizes correctly.
- It does not block the application.
- Errors are handled appropriately.
- Relevant tests pass.
- Its implementation has been committed.

## Final Instruction

Use the reference images as the visual specification and this document as the functional specification.

Prioritize a clean, maintainable native desktop application over unnecessary features.

The final result should feel like a cohesive, polished study tool, not a collection of unrelated PySide6 windows.
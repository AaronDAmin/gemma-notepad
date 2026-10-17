# Transcription de la conversation

## Utilisateur

Tu es GitHub Copilot dans VSCode. Objectif : préparer le dépôt AaronDAmin/mustard-study-notepad pour les contributions. Fais les actions suivantes, en créant la branche, les fichiers, le commit et le PR. Si une action automatique n'est pas autorisée par permissions, génère les commandes git exactes et un patch/zip que je puisse exécuter localement.

1. Crée une branche nommée chore/contrib-ready à partir de la branche master.
2. Ajoute les fichiers suivants (chemin + contenu exact). Respecte l'encodage UTF-8.

- LICENSE (MIT) MIT License
Copyright (c) 2026 AaronDAmin

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

- CONTRIBUTING.md

# Contributing to Mustard Study Notepad
Merci de vouloir contribuer à ce projet.

## Comment contribuer

1. Ouvrez une issue pour discuter d'une fonctionnalité ou d'un correctif important.
2. Forkez le dépôt et créez une branche :
- `feature/nom-court`
- `fix/nom-court`
- `docs/nom-court`
3. Faites vos changements avec une documentation claire dans le code et les messages de commit.
4. Vérifiez le bon fonctionnement localement.
5. Ouvrez une Pull Request en décrivant le contexte, la solution et les validations.

## Installation locale
bash

```
python -m venv .venv
source .venv/bin/activate  # Windows : .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Vérifications de qualité
Avant de soumettre une PR, il est recommandé de lancer :

bash

```
black .
flake8
pytest -q
```

## Standards de code

- Utilisez un style Python lisible et cohérent.
- Ajoutez des tests pour les changements fonctionnels.
- Évitez les dépendances inutiles.
- Gardez les messages de commit clairs et concis.

## Convention de commits
Text

```
feat(ui): ajouter la gestion des marqueurs
fix(pdf): corriger le zoom sur certaines pages
docs(readme): ajouter la section contribution
```

## Pull Requests
Une PR doit inclure :

- une description du problème
- la solution proposée
- la ou les validations effectuées
- le lien vers l'issue associée si applicable

## Code de conduite
Nous appliquons un cadre de respect mutuel et de collaboration constructive. Les contributions doivent rester courtoises, utiles et respectueuses.

Merci pour votre aide !

- CODE_OF_CONDUCT.md

# Contributor Covenant Code of Conduct

## Our Pledge
We as members, contributors, and leaders pledge to make participation in our community a harassment-free experience for everyone, regardless of age, body size, visible or invisible disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming, diverse, inclusive, and healthy community.

## Our Standards
Examples of behavior that contributes to a positive environment include:

- Demonstrating empathy and kindness toward other people
- Being respectful of differing opinions, viewpoints, and experiences
- Giving and gracefully accepting constructive feedback
- Accepting responsibility and apologizing to those affected by our mistakes
- Focusing on what is best not just for us as individuals, but for the overall community
Examples of unacceptable behavior include:

- The use of sexualized language or imagery, and sexual attention or advances of any kind
- Trolling, insulting or derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without their explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

## Enforcement Responsibilities
Project maintainers are responsible for clarifying and enforcing our standards of acceptable behavior and will take appropriate and fair corrective action in response to any behavior they deem inappropriate, threatening, offensive, or harmful.

## Scope
This Code of Conduct applies within all project spaces, and also applies when an individual is officially representing the project in public spaces.

## Enforcement
Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the project maintainers at the email address configured for the project. All complaints will be reviewed and investigated promptly and fairly.

## Attribution
This Code of Conduct is adapted from the Contributor Covenant, version 2.1, available at [https://www.contributor-covenant.org/version/2/1/code_of_conduct.html](https://www.contributor-covenant.org/version/2/1/code_of_conduct.html)

- .github/ISSUE_TEMPLATE/bug_report.md

---

## name: Bug report about: Signaler un bug ou un comportement inattendu title: "" labels: bug assignees: ""

## Description du bug
Décrivez clairement le problème.

## Étapes pour reproduire

1.
2.
3.

## Comportement attendu
Décrivez le comportement attendu.

## Environnement

- OS :
- Version Python :
- Version du projet / commit :

## Logs / captures
Ajoutez ici les messages d'erreur, screenshot ou logs utiles.

- .github/ISSUE_TEMPLATE/feature_request.md

---

## name: Feature request about: Proposer une nouvelle fonctionnalité ou amélioration title: "" labels: enhancement assignees: ""

## Résumé
Décrivez la fonctionnalité ou l'amélioration souhaitée.

## Pourquoi c'est utile ?
Expliquez le besoin ou le problème qu'elle résout.

## Proposition
Décrivez votre idée ou le comportement attendu.

## Alternatives
Avez-vous envisagé une autre approche ?

- .github/PULL_REQUEST_TEMPLATE.md

## Description
Décrivez brièvement le changement et son objectif.

## Type de changement

- Bugfix
- Nouvelle fonctionnalité
- Documentation
- Refactor
- Autre

## Checklist

- J'ai lu le fichier `CONTRIBUTING.md`
- Les tests ont été ajoutés ou ajustés
- La validation locale a été effectuée (`black`, `flake8`, `pytest`)
- Le code est propre et compréhensible

## Liens
Fixes #<issue-number> (si applicable)

- .github/workflows/python-app.yml

name: CI
on: push: branches: [master] pull_request: branches: [master]

jobs: build: runs-on: ubuntu-latest

Code

```
steps:
  - name: Checkout repository
    uses: actions/checkout@v4

  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: '3.11'

  - name: Install dependencies
    run: |
      python -m pip install --upgrade pip
      pip install -r requirements.txt
      pip install black flake8 pytest

  - name: Check formatting with black
    run: black --check .

  - name: Lint with flake8
    run: flake8 .

  - name: Run tests
    run: pytest -q
```

- .github/dependabot.yml

version: 2
updates:

- package-ecosystem: "pip" directory: "/" schedule: interval: "weekly" open-pull-requests-limit: 10

- docs/CONVERSATION-COPILOT.md — crée un fichier texte contenant la transcription complète de cette conversation.

1. Staging & commit

- Commit message : "chore: prepare repo for contributions (CONTRIBUTING, CODE_OF_CONDUCT, LICENSE, templates, CI, dependabot)"
- Signale les changements créés et propose un diff/preview.

1. Tests et vérifications locales

- Exécute black --check ., flake8 . et pytest -q et rapporte les erreurs (noms des fichiers/ligne si échec).

1. Push & PR

- Pousse la branche chore/contrib-ready sur l'origine (origin).
- Ouvre une pull request depuis chore/contrib-ready vers master avec :
- Title: "chore: prepare repo for contributions"
- Body: bref résumé des fichiers ajoutés + instructions pour review (mentionne l'existence de tests, dépendabot, et checklist).
- Labels: chore, documentation
- Assignees: [laisser vide / propose le mainteneur]

1. En cas d'erreur de permission pour push or PR

- Génère un patch (git format-patch) ou un zip contenant tous les fichiers et les commandes git exactes à exécuter localement pour reproduire les étapes (création branche, ajout fichiers, commit, push, open PR via gh cli).
- Fournis aussi la commande gh pour créer la PR : gh pr create --title "chore: prepare repo for contributions" --body-file pr_body.md --base master --head yourfork:chore/contrib-ready

1. Termine en listant les fichiers créés, l'URL de la PR (si créée) ou le zip/patch à télécharger.
Important : avant de pousser, affiche un résumé des fichiers et demande confirmation explicite "Confirmer push et création de PR ? (oui/non)". Si l'utilisateur répond oui, push et crée la PR; si non, arrête

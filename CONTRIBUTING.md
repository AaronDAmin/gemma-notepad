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

```bash
python -m venv .venv
source .venv/bin/activate  # Windows : .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Vérifications de qualité

Avant de soumettre une PR, il est recommandé de lancer :

```bash
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

```text
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

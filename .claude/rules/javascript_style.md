# Conventions — JavaScript

## Philosophie

- JavaScript **minimal** : préférer CSS et HTML natifs quand c'est possible.
- Pas de framework JS. Vanilla JS uniquement.

## Style

- Indentation : **4 espaces**.
- Fonctions classiques (`function`) plutôt qu'arrow functions.
- Nommage `camelCase` pour les fonctions et variables.
- `var` utilisé historiquement ; préférer `const`/`let` pour le nouveau code.

## Inline vs fichier

- Scripts courts et spécifiques à une page : **inline** dans le template.
- Utilitaires réutilisables : dans `data/static/js/`.

## Interactions formulaires

- Auto-soumission via `onchange="this.form.submit()"` pour les selects.
- Event listeners pour les interactions DOM simples.

## Bibliothèques

- **Chart.js** pour les graphiques.
- Pas d'autres bibliothèques JS, le reste est géré côté serveur (Django, markdownx).

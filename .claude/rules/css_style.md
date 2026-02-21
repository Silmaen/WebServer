# Conventions — CSS

## Thème

- Thème **sombre** par défaut.
- Toutes les couleurs utilisent des **variables CSS** définies dans `:root`.

## Variables CSS (palette)

```css
:root {
    --bg-body: #181818;
    --bg-surface: #222222;
    --bg-elevated: #2a2a2a;
    --bg-header: #111111;
    --border: #383838;
    --separator: #333333;
    --text: #e0e0e0;
    --text-secondary: #999999;
    --blue: #5090C1;
    --blue-light: #7ab8eb;
    --blue-lighter: #9ac8fb;
    --blue-hover: #6aaad8;
    --bg-button: #303030;
    --bg-button-hover: #3a3a3a;
    --red: #c0392b;
    --red-hover: #e74c3c;
    --green: #27ae60;
    --yellow: #f39c12;
}
```

Toujours utiliser `var(--nom-variable)` au lieu de valeurs de couleur en dur.

## Nommage des classes

- Classes **sémantiques** et descriptives : `.site-header`, `.page-center`, `.inner-nav-item`.
- Composants article : `.Article`, `.ArticleHeader`, `.ArticleContent`, `.ArticleFooter` (PascalCase pour les composants principaux).
- Formulaires : `.form-group`, `.form-section`, `.form-section-title`, `.form-errors`.
- Enregistrement : `.reg-card`, `.reg-card-title`, `.reg-card-body`.
- Boutons : `.userbtn` (standard), `.userbtn-danger` (rouge, pour les suppressions).
- Messages : `.msg`, `.msg-success`, `.msg-error`, `.msg-warning`, `.msg-info`.
- Badges : `.admin-badge`.
- Impression : `.noprint`.

## Organisation du fichier CSS

1. Variables (`:root`)
2. Reset et styles globaux
3. Typographie
4. Conteneurs principaux (header, footer, contenu)
5. Navigation
6. Articles et contenu
7. Formulaires
8. Alertes et badges
9. Media queries responsives (en fin de fichier)

## Responsive

- Breakpoint principal : `max-width: 1000px`.
- Breakpoint mobile : `max-width: 768px`.
- Utilisation de `vw` pour le dimensionnement responsive.
- Layout en **flexbox**.

## Pas de styles inline

- **Jamais de `style="..."` dans les templates HTML** pour du style statique.
- Tout le style doit être dans les fichiers CSS.
- Seule exception tolérée : les **CSS custom properties dynamiques** passant des données serveur (`style="--projet-accent: {{ valeur }}"`).

## Transitions

- Transitions pour les éléments interactifs : `.2s` à `.3s`.

## Fichiers

- `default_www.css` — styles principaux du site.
- `default_profile.css` — styles de profil et inscription.
- Nommage : minuscules avec underscores.

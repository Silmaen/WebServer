# Conventions — CSS

## Thème

- Thème **sombre** par défaut.
- Toutes les couleurs utilisent des **variables CSS** définies dans `:root`.

## Variables CSS (palette)

La palette de référence est celle de `:root` dans `data/static/css/default_www.css` :

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
    --red: #e05555;
    --red-hover: #c94040;      /* aplat plus soutenu, sous du texte blanc */
    --green: #44cc44;
    --yellow: #d4a843;
    --white: #ffffff;          /* texte sur aplat saturé (bleu, rouge) */
    --text-on-accent: #101010; /* texte sur aplat clair (vert, jaune, bleu clair) */
    --blue-shadow: rgba(80, 144, 193, .4);
    --shadow: rgba(0, 0, 0, .4);
    --field-height: 2.55em;    /* hauteur d'un champ, pour aligner les boutons */
}
```

Toujours utiliser `var(--nom-variable)` au lieu de valeurs de couleur en dur.

`--green`, `--yellow`, `--red`, `--text`, `--text-secondary`, `--bg-surface` et `--border`
doivent rester des **hexadécimaux à 6 chiffres** : le script du tableau de bord de
supervision les lit via `getComputedStyle` et leur concatène un suffixe d'opacité.

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

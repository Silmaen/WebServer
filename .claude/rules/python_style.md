# Style Python

## Langue

- Docstrings, commentaires, noms de variables et de champs de modèles : **français** (sauf termes techniques Django/Python).
- Exemples : `titre`, `auteur`, `contenu`, `categorie`, `sous_categorie`.
- Les champs hérités de Django restent en anglais : `user`, `slug`, `active`.

## Conventions de nommage

| Élément | Convention | Exemples |
|---|---|---|
| Variables, fonctions | `snake_case` | `articles_per_page`, `get_articles()`, `news_page()` |
| Classes (modèles, formulaires, admin, tests) | `PascalCase` | `SiteArticle`, `ArticleCommentForm`, `SiteArticleAdmin` |
| Constantes module | `UPPER_CASE` | `ENREGISTRE`, `AUTORISE`, `AVANCE`, `ADMINISTRATEUR` |
| Noms d'URL | `snake_case` entre guillemets simples | `'accueil'`, `'archives_news'`, `'admin_users'` |
| Fichiers templates | minuscules, underscores | `a_propos_cv.html`, `admin_users.html` |
| Classes Admin | suffixe `Admin` | `SiteArticleAdmin`, `ArticleAdmin` |
| Classes Inline Admin | suffixe `Inline` | `UserProfileInline` |
| Formulaires | suffixe `Form` | `ArticleCommentForm`, `ProfileForm` |
| Classes de test | suffixe `Test` | `PagesAccessTest`, `ArchivesAccessTest` |

## Guillemets

- **Guillemets doubles** (`"`) par défaut pour les chaînes.
- **Guillemets simples** (`'`) pour les noms d'URL dans `path()` et `{% url %}`.
- **Triple guillemets doubles** (`"""`) pour les docstrings.

## Formatage de chaînes

- Préférer les **f-strings** pour les nouvelles interpolations.
- Pas de `str.format()` ni de `%`.

## Docstrings

Toujours en français, format Google-style :

```python
def accueil(request):
    """
    Page d'accueil du site.
     :param request : La requête du client.
     :return : La page rendue.
    """
```

- Présents sur toutes les fonctions de vue, méthodes de modèle, classes.

## Commentaires

- En **français**.
- Modérés : uniquement quand la logique n'est pas évidente.
- Style inline : `# commentaire ici`

## Type hints

- Non utilisés dans le projet existant. Ne pas en ajouter sauf demande explicite.

## Formatage

- Indentation : **4 espaces** (pas de tabulations).
- Longueur de ligne : **100 caractères** max (souple).
- **2 lignes vides** entre fonctions/classes au niveau module.
- **1 ligne vide** entre méthodes dans une classe.
- Lignes vides pour séparer les blocs logiques dans les fonctions.

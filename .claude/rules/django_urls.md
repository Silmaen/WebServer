# Conventions Django — URLs

## Structure

- `ROOT_URLCONF` : `multisite.urls`.
- Les patterns sont répartis entre apps via `include()`.
- Les routes de `www/` sont directement dans le urlconf racine (pas de préfixe).
- Les routes de `connector/` sont sous le préfixe `profile/`.

## Nommage

- Noms d'URL en `snake_case` entre **guillemets simples** : `name='accueil'`, `name='archives_news'`.
- Noms descriptifs en français : `'a_propos'`, `'mes_projets'`, `'bricolage'`.
- Préfixe par section pour les sous-pages : `'archives_news'`, `'archives_research'`.

## Chemins

- Chemins en français avec tirets : `"a-propos/"`, `"mes-projets/"`, `"archives/news/"`.
- Pas de slash de début, slash de fin : `"administration/utilisateurs/"`.
- Paramètres typés : `<int:article_id>`, `<int:n_page>`.

## Exemple

```python
urlpatterns = [
    path("", accueil, name='accueil'),
    path("a-propos/", a_propos, name='a_propos'),
    path("archives/article/<int:article_id>", detailed_news, name='detailed_news'),
]
```

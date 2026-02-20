# Conventions Django — Modèles

## Nommage des champs

- Noms de champs en **français** et `snake_case` : `titre`, `auteur`, `contenu`, `categorie`, `sous_categorie`, `nom`.
- Champs Django standards en anglais : `user`, `slug`, `active`, `date`.
- `verbose_name` en français : `verbose_name="Titre de l'article"`.

## Classe Meta

Toujours présente avec docstring :

```python
class Meta:
    """Meta data"""
    verbose_name = "article"
    verbose_name_plural = "articles"
    ordering = ['-date']
```

## Héritage de modèles

- Héritage multi-table : `Article(SiteArticle)` (les modèles de base sont dans `common/`).
- Les apps (`www`, `connector`) étendent les modèles de `common`.

## Related names

- Descriptifs, minuscules : `related_name="comments"`.

## Méthodes de modèle

- `__str__` sur chaque modèle.
- Méthodes utilitaires avec docstrings en français : `contenu_md()`, `nb_comments()`, `get_comments()`.

## Signaux

- Nommage descriptif avec préfixe d'action : `create_user_profile()`, `save_user_profile()`.
- Décorateur `@receiver(post_save, sender=Model)`.
- Auto-création de profils via signal `post_save` sur `User`.

## Visibilité des articles

Flags booléens hiérarchiques avec auto-sync dans `save()` :
- `staff` ou `developper` → active `private` et `superprivate`
- `superprivate` → active `private`

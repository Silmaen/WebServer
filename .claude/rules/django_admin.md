# Conventions Django — Admin

## Classes Admin

- Suffixe `Admin` : `SiteArticleAdmin`, `ArticleAdmin`.
- Inline : suffixe `Inline` : `UserProfileInline`.
- Hériter de la classe admin de base correspondante quand elle existe dans `common/`.

## Configuration standard

```python
class SiteArticleAdmin(admin.ModelAdmin):
    list_display = ('titre', 'auteur', 'date', 'content_overview', 'private', 'staff')
    list_filter = ('auteur', 'date')
    date_hierarchy = 'date'
    search_fields = ('titre', 'contenu')
    prepopulated_fields = {'slug': ('titre',)}
```

## Fieldsets

Organiser en groupes logiques avec titres en anglais ou français :

```python
fieldsets = (
    ('General', {
        'fields': ('titre', 'slug', 'auteur', 'date'),
    }),
    ('Acces', {
        'fields': ('private', 'superprivate', 'staff', 'developper',)
    }),
    ('Content of the article', {
        'fields': ('contenu',)
    }),
)
```

## Auto-attribution de l'auteur

Surcharger `save_model()` pour attribuer `request.user` comme auteur :

```python
def save_model(self, request, obj, form, change):
    if not change:
        obj.auteur = request.user
    super().save_model(request, obj, form, change)
```

## Actions personnalisées

```python
def approve_comments(self, request, queryset):
    queryset.update(active=True)
```

# Conventions Django — Vues

## Préférence : Vues fonctionnelles (FBV)

- Utiliser des **Function-Based Views** avec décorateurs.
- Les CBV sont réservées aux vues d'authentification Django (`LoginView`, `PasswordResetView`, etc.).

## Décorateurs de permissions

Utiliser les décorateurs personnalisés définis dans `www/views.py` :
- `@avance_required` — requiert login + niveau >= AVANCE (2)
- `@admin_required` — requiert login + niveau >= ADMINISTRATEUR (3)

Structure d'un décorateur :

```python
def avance_required(view_func):
    """Décorateur : login requis + niveau avancé minimum, sinon 403."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not user_is_avance(request.user):
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)
    return _wrapped
```

## Structure d'une vue

```python
def ma_vue(request):
    """
    Description de la vue.
     :param request : La requête du client.
     :return : La page rendue.
    """
    context = get_page_data(request.user, "nom_page")
    # logique métier
    return render(request, "www/template.html", context)
```

## Contexte de rendu

- Utiliser `get_page_data(user, page_name)` de `www/render_utils.py` pour le contexte de base.
- Ajouter les données spécifiques au dict de contexte via `context.update({...})` ou `context["clé"] = valeur`.

## Traitement POST

```python
if request.method == "POST":
    form = MonForm(data=request.POST)
    if form.is_valid():
        # traitement
else:
    form = MonForm()
```

## Gestion d'erreurs

- `get_object_or_404()` pour récupérer un objet ou 404.
- `HttpResponseForbidden()` pour les accès non autorisés.
- `redirect("nom_url")` pour les redirections.

# Conventions — Templates HTML

## Langue

- Tout le texte visible (UI, labels, boutons, messages) est en **français**.
- `<html lang="fr">`.

## Héritage de templates

- `common/common_base.html` → base générique minimale.
- `www/base.html` → base du site avec header, navigation, contenu, footer.
- `registration/base_registration.html` → base légère pour auth, hérite de `www/base.html`.
- Blocs principaux : `{% block content %}`, `{% block InnerContent %}`, `{% block mainsection %}`, `{% block title %}`, `{% block additionnalhead %}`.

## Tags Django

- Charger en haut du template : `{% load static template_extra %}`.
- URLs dynamiques : `{% url 'nom_vue' %}` ou `{% url 'nom_vue' param %}`. Jamais de chemins en dur.
- Fichiers statiques : `{% static 'css/default_www.css' %}`. Jamais de chemins en dur.
- Protection CSRF : `{% csrf_token %}` dans tous les formulaires POST.
- Contenu markdown : `{{ contenu|safe }}`.
- Valeurs par défaut : `{{ valeur|default:"-" }}`.

## Framework

- **Bootstrap 5.3** chargé depuis CDN (utilisé modérément, surtout le CSS custom).
- **Material Design Icons (MDI)** pour les icônes : `class="mdi mdi-login"`, `class="mdi mdi-account-circle"`.

## Formatage

- Indentation : **4 espaces**.
- Toutes les balises correctement fermées.
- Commentaires HTML pour les sections : `<!-- CSS -->`, `<!-- feuille de style -->`.

## Nommage des fichiers

- Minuscules avec underscores : `a_propos_cv.html`, `admin_users.html`.
- Noms en français : `accueil.html`, `bricolage.html`, `mes_projets.html`.
- Organisation par app : `www/`, `common/registration/`.

## Formulaires

- Rendu avec `{{ form.as_p }}` ou champ par champ avec `{{ field }}`.
- Labels personnalisés en français.
- Erreurs affichées dans des blocs `.alert-danger`.

## Boucles et conditions

```html
{% for article in articles %}
    <!-- contenu -->
{% empty %}
    <p>Aucun article disponible.</p>
{% endfor %}

{% if user.is_authenticated %}
    <!-- contenu authentifié -->
{% endif %}
```

# Imports Python

## Ordre des imports

1. Bibliothèque standard Python (`functools`, `datetime`, etc.)
2. Django core (`django.conf`, `django.db`, `django.utils`, `django.shortcuts`)
3. Django contrib (`django.contrib.auth`, `django.contrib.admin`)
4. Bibliothèques tierces (`markdownx`, `html5lib_truncation`)
5. Imports absolus depuis d'autres apps (`from common.models import SiteArticle`)
6. Imports relatifs dans la même app (`from .models import Article`, `from .forms import ArticleCommentForm`)

Séparer chaque groupe par une ligne vide.

## Style

- **Imports absolus** entre apps : `from common.user_utils import get_user_level`
- **Imports relatifs** dans la même app : `from .models import Article`
- Imports multi-lignes avec **parenthèses** (pas de backslash) :

```python
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordChangeView, PasswordChangeDoneView,
)
```

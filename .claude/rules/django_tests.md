# Conventions Django — Tests

## Organisation

- Tests dans `<app>/tests.py`.
- Classes de test avec suffixe `Test` : `PagesAccessTest`, `ArchivesAccessTest`.
- Héritent de `django.test.TestCase`.

## Patterns de test

### Accès aux pages publiques

```python
class PagesAccessTest(TestCase):
    def test_accueil(self):
        response = self.client.get(reverse('accueil'))
        self.assertEqual(response.status_code, 200)
```

### Contrôle d'accès

Tester les 3 cas :
1. **Anonyme** → 302 (redirection vers login)
2. **Utilisateur sans niveau suffisant** → 403 (Forbidden)
3. **Utilisateur avec niveau suffisant** → 200

```python
class ArchivesAccessTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        # configurer le user_level selon le test

    def test_anonymous_redirect(self):
        response = self.client.get(reverse('archives'))
        self.assertEqual(response.status_code, 302)

    def test_insufficient_level_forbidden(self):
        self.client.login(username='test', password='test')
        response = self.client.get(reverse('archives'))
        self.assertEqual(response.status_code, 403)
```

### Vérification des templates

```python
def test_template_used(self):
    response = self.client.get(reverse('accueil'))
    self.assertTemplateUsed(response, 'www/accueil.html')
```

### Protection superutilisateur

Tester que les superutilisateurs ne peuvent pas être rétrogradés.

## Exécution

```bash
python manage.py test www          # Tests d'une app
python manage.py test              # Tous les tests
```

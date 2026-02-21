"""Widgets personnalisés pour les formulaires www."""
from django.forms import widgets


MDI_ICONS_CURATED = [
    # Code & développement
    ("code-tags", "Code"),
    ("language-python", "Python"),
    ("language-javascript", "JavaScript"),
    ("language-c", "C"),
    ("language-cpp", "C++"),
    ("language-rust", "Rust"),
    ("language-go", "Go"),
    ("language-java", "Java"),
    ("language-html5", "HTML5"),
    ("language-css3", "CSS3"),
    ("git", "Git"),
    ("github", "GitHub"),
    ("console", "Console"),
    ("api", "API"),
    ("xml", "XML"),
    ("database", "Base de données"),
    ("docker", "Docker"),
    # Outils
    ("wrench", "Clé"),
    ("hammer-wrench", "Outils"),
    ("cog", "Engrenage"),
    ("cogs", "Engrenages"),
    ("tools", "Outils"),
    ("pickaxe", "Pioche"),
    ("screwdriver", "Tournevis"),
    # Hardware & électronique
    ("chip", "Puce"),
    ("circuit-board", "Circuit"),
    ("raspberry-pi", "Raspberry Pi"),
    ("server", "Serveur"),
    ("desktop-classic", "Ordinateur"),
    ("cellphone", "Mobile"),
    ("memory", "Mémoire"),
    ("usb", "USB"),
    ("led-on", "LED"),
    # Réseau & web
    ("web", "Web"),
    ("cloud", "Cloud"),
    ("wifi", "Wi-Fi"),
    ("earth", "Terre"),
    ("lan", "Réseau"),
    ("security", "Sécurité"),
    ("shield-lock", "Bouclier"),
    ("vpn", "VPN"),
    # Science & recherche
    ("flask", "Fiole"),
    ("atom", "Atome"),
    ("microscope", "Microscope"),
    ("telescope", "Télescope"),
    ("math-compass", "Compas"),
    ("calculator", "Calculatrice"),
    ("chart-line", "Graphique"),
    ("brain", "Cerveau"),
    # Jeux & loisirs
    ("gamepad-variant", "Manette"),
    ("controller", "Contrôleur"),
    ("dice-multiple", "Dés"),
    ("chess-knight", "Échecs"),
    ("cards-playing", "Cartes"),
    ("robot", "Robot"),
    ("creation", "Création"),
    # Art & design
    ("palette", "Palette"),
    ("brush", "Pinceau"),
    ("pencil", "Crayon"),
    ("image", "Image"),
    ("camera", "Caméra"),
    ("music", "Musique"),
    # Fichiers & documents
    ("file-document", "Document"),
    ("folder", "Dossier"),
    ("book-open-variant", "Livre"),
    ("notebook", "Carnet"),
    ("archive", "Archive"),
    # Général
    ("home", "Maison"),
    ("star", "Étoile"),
    ("heart", "Cœur"),
    ("bookmark", "Signet"),
    ("lightning-bolt", "Éclair"),
    ("rocket-launch", "Fusée"),
    ("puzzle", "Puzzle"),
    ("lightbulb", "Ampoule"),
    ("map-marker", "Marqueur"),
    ("compass", "Boussole"),
    ("leaf", "Feuille"),
    ("fire", "Feu"),
    ("cube-outline", "Cube"),
]


class ColorPickerWidget(widgets.Input):
    """Widget color picker avec swatch et champ texte hex synchronisés."""
    input_type = "color"
    template_name = "www/widgets/color_picker.html"


class MdiIconPickerWidget(widgets.HiddenInput):
    """Widget de sélection d'icône MDI avec grille, recherche et preview."""
    template_name = "www/widgets/mdi_icon_picker.html"

    def get_context(self, name, value, attrs):
        """Ajoute la liste d'icônes au contexte du widget."""
        context = super().get_context(name, value, attrs)
        context["icons"] = MDI_ICONS_CURATED
        return context

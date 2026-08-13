"""Les machines propres au lab, par opposition à ce qui traîne sur le réseau.

`devices.Device` est ce que le scanner a **observé** ; `Machine` est ce que le lab
**déclare** dans `_common/inventory.conf`. Les confondre perdrait la seule question
intéressante — la différence : un appareil vu et déclaré nulle part est un inconnu,
une machine déclarée et jamais vue est une machine qui n'est pas revenue.
"""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Machine(TimeStampedModel):
    """Une machine telle que déclarée dans `_common/inventory.conf`.

    Le fichier reste la source de vérité — il est lu par tous les outils du lab —
    donc ces lignes n'en sont qu'un miroir, réconcilié par
    `apps.fleet.inventory.sync()` et jamais l'endroit où l'on crée une machine.
    """

    name = models.CharField(max_length=64, unique=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    mac = models.CharField(max_length=17, blank=True)
    role = models.CharField(max_length=64, blank=True)
    os_family = models.CharField(max_length=16, blank=True, help_text="linux | openwrt | windows")
    ac_restores = models.CharField(
        max_length=16, blank=True, help_text="does it power itself back on?",
    )
    wol_known = models.CharField(
        max_length=16, blank=True, help_text="is Wake-on-LAN known to work?",
    )
    wake_order = models.PositiveIntegerField(default=0, help_text="0 = never woken automatically")
    ssh_user = models.CharField(max_length=32, blank=True)
    # Une machine retirée de inventory.conf garde sa ligne : ses rapports y renvoient
    # encore, et une machine qui disparaît en silence est exactement le genre
    # d'absence que cette console existe pour rendre visible.
    retired = models.BooleanField(default=False)
    # Quand la console a publié une approbation pour cette machine, et laquelle. Même
    # rôle que `Stack.deploy_requested_at` : une demande n'est pas un résultat, mais
    # entre le clic et le rapport qui suit il faut bien que la page puisse dire qu'il
    # se passe quelque chose. Un `upgrade` sur hecate a pris quatorze minutes, dont la
    # page ne montrait rien.
    action_requested_at = models.DateTimeField(
        null=True, blank=True,
        help_text="dernière approbation publiée par la console",
    )
    action_requested_verb = models.CharField(
        max_length=20, blank=True,
        help_text="verbe de cette approbation, pour l'afficher",
    )

    class Meta:
        """Meta data"""
        ordering = ["wake_order", "name"]

    def __str__(self):
        return self.name

    @property
    def latest_report(self):
        """Le rapport le plus récent de cette machine, ou None."""
        return self.reports.first()

    @property
    def action_en_cours(self):
        """Une approbation a-t-elle été publiée, sans rapport depuis ?

        Mêmes deux bornes que `Stack.deploiement_en_cours`, et la seconde compte
        davantage ici : un `upgrade` sur hecate a duré quatorze minutes (`pacman -Syu`),
        donc « en cours » doit tenir aussi longtemps qu'une action peut durer. La borne
        est l'heure que l'agent accorde au playbook ; au-delà, c'est terminé, réussi ou
        non.
        """
        if not self.action_requested_at:
            return False
        dernier = self.latest_report
        if dernier and dernier.received_at > self.action_requested_at:
            return False
        return timezone.now() - self.action_requested_at < timedelta(hours=1)


class Report(models.Model):
    """Un document `homelab-report`, tel que posté par la machine elle-même.

    Conservé en historique plutôt qu'écrasé : un disque qui se remplit ne se voit
    qu'en tendance. Pas un `TimeStampedModel`, dont la clé UUID serait le mauvais
    défaut pour une table qui grossit de dix lignes par heure ; `tasks.py` la purge.
    """

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="reports")
    # L'horodatage de la machine, pas le nôtre : c'est lui qui décide de la péremption
    # et il reste juste si la console était éteinte pendant que la machine rapportait.
    at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)
    schema = models.PositiveIntegerField(default=1)
    facts = models.JSONField(default=dict)
    drift_status = models.CharField(max_length=20, default="unknown")
    drift_count = models.PositiveIntegerField(default=0)
    drift_changes = models.JSONField(default=list)

    class Meta:
        """Meta data"""
        ordering = ["-at"]
        constraints = [
            # Reposter le même document devient idempotent, ce qui compte car
            # `homelab-report` est lancé à la fois par un timer et à la main.
            models.UniqueConstraint(fields=["machine", "at"], name="fleet_report_unique_at"),
        ]
        indexes = [models.Index(fields=["machine", "-at"])]

    def __str__(self):
        return f"{self.machine.name} @ {self.at:%Y-%m-%d %H:%M}"

    @property
    def age_seconds(self):
        """Âge du rapport en secondes."""
        return int((timezone.now() - self.at).total_seconds())

    @property
    def state(self):
        """`ok` ou `stale`. Le timer étant horaire, le seuil vaut deux passages ratés."""
        return "stale" if self.age_seconds > settings.FLEET_STALE_AFTER else "ok"

    @property
    def worst_disk(self):
        """Le système de fichiers le plus plein — le seul qui mérite une colonne.

        `disk` est un fait compacté (`/:46% /boot:14% ...`) ; le point de montage est
        pris par la droite, car il contient des slashs et pas de deux-points.
        """
        worst, where = 0, ""
        for item in (self.facts.get("disk") or "").split():
            mount, _, percent = item.rpartition(":")
            try:
                value = int(percent.rstrip("%"))
            except ValueError:
                continue
            if value > worst:
                worst, where = value, mount
        return worst, where


class Stack(TimeStampedModel):
    """Un projet compose déployé sur une machine, tel que Docker le rapporte.

    Rien ne les déclare : compose estampille ses conteneurs, donc `homelab-probe`
    en dérive la liste entière — ce qui donne enfin une trace aux stacks vivant dans
    leur propre dépôt. État courant et non une ligne par rapport, pour ne pas
    reproduire la croissance de `monitoring_checkresult`.
    """

    class Compose(models.TextChoices):
        """Suivi git du fichier compose de la stack."""
        TRACKED = "tracked", "Suivi par git"
        UNTRACKED = "untracked", "Jamais commité"
        MISSING = "missing", "Fichier disparu"
        NO_GIT = "no-git", "Hors dépôt git"
        UNKNOWN = "-", "Inconnu"

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="stacks")
    project = models.CharField(max_length=128)
    path = models.CharField(max_length=512)
    remote = models.CharField(max_length=256, blank=True)
    head = models.CharField(max_length=64, blank=True)
    worktree = models.CharField(max_length=16, blank=True, help_text="clean | dirty")
    behind = models.IntegerField(
        null=True, blank=True, help_text="commits behind the last known remote ref",
    )
    # `choices` n'est pas décoratif : c'est lui qui fait exister
    # `get_compose_display()`, la méthode que le gabarit appelle. Sans lui Django ne la
    # génère pas, le gabarit avale l'attribut manquant en silence, et la colonne
    # « Compose » de la page Stacks est restée vide depuis le premier jour -- alors que
    # l'encart d'alerte, qui compare la valeur brute, disait bien « le fichier compose a
    # disparu ». Le seul champ à choix de la console qui ne le déclarait pas.
    compose = models.CharField(
        max_length=16, choices=Compose.choices, default=Compose.UNKNOWN,
    )
    # Nom du script de déploiement trouvé par la sonde à côté du compose, vide sinon.
    # C'est lui qui autorise la console à proposer une mise à jour de la stack.
    deploy_script = models.CharField(
        max_length=128, blank=True,
        help_text="script de déploiement rapporté par homelab-probe",
    )
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)
    # La stack figurait-elle dans le dernier rapport de sa machine ? Une stack
    # déplacée ou supprimée cesse d'être rapportée sans que rien ne le dise : sa ligne
    # restait alors telle quelle, avec le `compose: missing` du dernier instant où la
    # sonde l'a vue à moitié démontée, et l'alerte rouge que cela déclenche n'avait
    # aucun moyen de s'éteindre. Ce drapeau est ce qui distingue « cassée » de
    # « plus là » -- la première mérite une alerte, la seconde une ligne grise et un
    # bouton pour l'oublier.
    present = models.BooleanField(
        default=True,
        help_text="présente dans le dernier rapport de la machine",
    )
    # L'état `compose` dont l'alerte a été acquittée, vide sinon -- « je sais ».
    #
    # Une valeur et non un booléen, et c'est tout l'intérêt : l'acquittement ne vaut
    # que pour le problème constaté. Il suffit de le comparer à `compose` pour qu'il se
    # réarme seul dès que l'état change, sans rien à remettre à zéro à l'ingestion --
    # même mécanique auto-nettoyante que `deploy_requested_at` comparé à `last_seen`.
    # Un booléen, lui, aurait fini par masquer un problème différent survenu depuis.
    #
    # Nécessaire parce que toutes les alertes ne se soignent pas ici : une stack qui
    # tourne, dont le dépôt est propre, et dont la sonde ne reconnaît pas le fichier
    # compose, se répare dans `home-server-stacks`. La console n'avait alors aucun
    # geste à offrir, et une alerte sans geste finit par ne plus être lue du tout.
    alert_ack = models.CharField(
        max_length=16, blank=True,
        help_text="état compose dont l'alerte a été acquittée",
    )
    # Quand la console a publié une demande de mise à jour pour cette stack. Une
    # demande, pas un résultat : la console n'exécute rien, elle publie un verbe, et
    # c'est la machine qui décide. Comparé à `last_seen`, ce champ permet de dire
    # « en cours » entre le clic et le rapport qui suit -- les soixante-dix secondes
    # pendant lesquelles la page semblait ne rien faire.
    deploy_requested_at = models.DateTimeField(
        null=True, blank=True,
        help_text="dernière demande de mise à jour publiée par la console",
    )

    class Meta:
        """Meta data"""
        ordering = ["machine__name", "project"]
        constraints = [
            models.UniqueConstraint(
                fields=["machine", "project", "path"], name="fleet_stack_unique_per_path",
            ),
        ]

    def __str__(self):
        return f"{self.machine.name}/{self.project}"

    @property
    def repo(self):
        """Le nom court du remote. L'URL complète est gardée ; un tableau veut le nom."""
        if not self.remote or self.remote == "-":
            return "-"
        return self.remote.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")

    @property
    def foreign(self):
        """Cette stack vient-elle d'un dépôt autre que home-server-stacks ?"""
        return self.repo not in ("home-server-stacks", "-")

    @property
    def severity(self):
        """À quel point la page doit signaler un problème.

        `missing` et `untracked` sont les deux états qu'aucun autre contrôle du lab
        ne voit : les conteneurs tournent, donc gatus et wud sont satisfaits.

        Une stack qui n'est plus rapportée ne relève de rien de tout cela : il n'y a
        plus de conteneurs, donc plus de compose à réparer. Elle ne pèse plus sur les
        alertes, sinon un déplacement de stack en laisserait une pour toujours.

        Un acquittement n'éteint que l'alerte du compose : un retard git ou un arbre sale
        restent signalés, car ce sont d'autres questions et personne ne les a acquittées.
        """
        if not self.present:
            return ""
        if self.compose_en_faute and not self.alerte_acquittee:
            return "danger"
        if (self.behind or 0) > 0 or self.worktree == "dirty":
            return "warning"
        return ""

    @property
    def compose_en_faute(self):
        """Le fichier compose est-il dans un état qu'aucun autre contrôle ne voit ?

        Les conteneurs tournent, donc gatus et wud sont satisfaits : ces deux états ne
        sont visibles que d'ici.
        """
        return self.compose in (self.Compose.MISSING, self.Compose.UNTRACKED)

    @property
    def alerte_acquittee(self):
        """Quelqu'un a-t-il dit « je sais » à propos de *cet* état du compose ?

        La comparaison est ce qui rend l'acquittement auto-nettoyant : dès que la sonde
        rapporte un autre état, il ne correspond plus et l'alerte revient d'elle-même.
        """
        return bool(self.alert_ack) and self.alert_ack == self.compose

    @property
    def alerte_acquittable(self):
        """La page doit-elle proposer d'acquitter (ou de réactiver) cette alerte ?

        Seulement sur une stack rapportée et en faute : ailleurs il n'y a rien à taire,
        et une stack disparue a son propre bouton, « Oublier ».
        """
        return self.present and self.compose_en_faute

    @property
    def deployable(self):
        """La console peut-elle demander une mise à jour de cette stack ?

        Un script disparu avec son compose ne peut pas être lancé : on ne propose
        rien plutôt que de publier une demande qui échouera sur la machine. Même
        raison pour une stack qui n'est plus rapportée — son répertoire n'est plus là.
        """
        return (
            self.present
            and bool(self.deploy_script)
            and self.compose != self.Compose.MISSING
        )

    @property
    def git_en_retard(self):
        """Le checkout est-il derrière son remote ? `None` quand la sonde ne sait pas."""
        return None if self.behind is None else self.behind > 0

    @property
    def deploiement_en_cours(self):
        """Une mise à jour a-t-elle été demandée, et rien rapporté depuis ?

        Deux bornes, parce qu'une demande n'est pas un résultat :

        * un rapport arrivé **après** la demande la solde, quoi qu'ait fait le script.
          C'est ce qui rend le champ auto-nettoyant : rien à remettre à zéro à
          l'ingestion, et un déploiement qui a échoué cesse d'être « en cours » dès que
          la machine reparle ;
        * au-delà d'une heure c'est fini de toute façon, réussi ou non -- c'est le
          `timeout` que l'agent applique au script. Sans cette borne, une machine
          éteinte juste après un clic garderait sa ligne « en cours » pour toujours.
        """
        if not self.deploy_requested_at:
            return False
        if self.last_seen > self.deploy_requested_at:
            return False
        return timezone.now() - self.deploy_requested_at < timedelta(hours=1)

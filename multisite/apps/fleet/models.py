"""The lab's own machines, as opposed to whatever is on the network.

This app absorbs `selene/console` from the home-server-stacks repository — the
Flask page that answered four questions nothing off the shelf answers together:
which machine still reports, what updates are pending, what has drifted from the
ansible recipe, and which running images have a newer tag. See
`_ops/docs/console-merge.md` there for the decision and the invariants.

The split that matters, and the reason `Machine` does not reuse `devices.Device`:

* `devices.Device` is what the scanner **observed** on the network;
* `Machine` is what the lab **declares** in `_common/inventory.conf`.

Conflating them would lose the only interesting question — the difference. A
device seen on the LAN and declared nowhere is a stranger; a machine declared and
never seen is a machine that did not come back.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class Machine(TimeStampedModel):
    """A machine as declared in `_common/inventory.conf`.

    The file stays the source of truth — it is parsed by busybox awk on the router
    and by every tool in that repository — so these rows are a mirror of it, never
    the place a machine is created. `apps.fleet.inventory.sync()` reconciles them.
    """

    name = models.CharField(max_length=64, unique=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    mac = models.CharField(max_length=17, blank=True)
    role = models.CharField(max_length=64, blank=True)
    os_family = models.CharField(max_length=16, blank=True, help_text="linux | openwrt | windows")
    ac_restores = models.CharField(max_length=16, blank=True, help_text="does it power itself back on?")
    wol_known = models.CharField(max_length=16, blank=True, help_text="is Wake-on-LAN known to work?")
    wake_order = models.PositiveIntegerField(default=0, help_text="0 = never woken automatically")
    ssh_user = models.CharField(max_length=32, blank=True)
    # A machine dropped from inventory.conf keeps its row: its reports still point
    # at it, and a machine that silently vanishes from the page is exactly the kind
    # of absence this console exists to make visible.
    retired = models.BooleanField(default=False)

    class Meta:
        ordering = ["wake_order", "name"]

    def __str__(self):
        return self.name

    @property
    def latest_report(self):
        return self.reports.first()


class Report(models.Model):
    """One `homelab-report` document, as posted by the machine itself.

    Not a `TimeStampedModel`: that gives a UUID primary key, which is the right
    default for a domain object and the wrong one for a table that grows by ten
    rows an hour for ever.

    Kept as history rather than overwritten, which is what the Flask console could
    not do — it held one JSON file per machine. A filesystem filling up is only
    visible as a trend, and the trend is what beszel was dropped for. `tasks.py`
    prunes it; an unbounded history table is the mistake this database already
    made once with `monitoring_checkresult`.
    """

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name="reports")
    # The machine's own timestamp, not ours: it is what decides staleness, and it
    # keeps working when the console was down while the machine kept reporting.
    at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)
    schema = models.PositiveIntegerField(default=1)
    facts = models.JSONField(default=dict)
    drift_status = models.CharField(max_length=20, default="unknown")
    drift_count = models.PositiveIntegerField(default=0)
    drift_changes = models.JSONField(default=list)

    class Meta:
        ordering = ["-at"]
        constraints = [
            # Re-posting the same document is then idempotent, which matters
            # because `homelab-report` is run both by a timer and by hand.
            models.UniqueConstraint(fields=["machine", "at"], name="fleet_report_unique_at"),
        ]
        indexes = [models.Index(fields=["machine", "-at"])]

    def __str__(self):
        return f"{self.machine.name} @ {self.at:%Y-%m-%d %H:%M}"

    @property
    def age_seconds(self):
        return int((timezone.now() - self.at).total_seconds())

    @property
    def state(self):
        """`ok` or `stale`. The timer runs hourly, so the threshold is two misses."""
        return "stale" if self.age_seconds > settings.FLEET_STALE_AFTER else "ok"

    @property
    def worst_disk(self):
        """The fullest filesystem — the only one worth a column.

        `disk` is a packed fact, `/:46% /boot:14% ...`; the mount point is taken
        with rpartition because it contains slashes and colons do not.
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
    """A compose project deployed on a machine, as the Docker daemon reports it.

    Nothing declares these. Compose stamps `com.docker.compose.project`,
    `.project.working_dir` and `.project.config_files` on every container it
    creates, so `homelab-probe` derives the whole list — which is what finally
    gives the stacks living in their own git repositories a trace, with no list to
    keep in sync.

    Current state, deliberately, not one row per report: this table would
    otherwise grow like `monitoring_checkresult` (1.9 M rows for a question nobody
    asks about the past). A stack that stops being deployed keeps its row with a
    stale `last_seen`, which is more useful than deleting it.
    """

    class Compose(models.TextChoices):
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
    behind = models.IntegerField(null=True, blank=True, help_text="commits behind the last known remote ref")
    compose = models.CharField(max_length=16, default=Compose.UNKNOWN)
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["machine__name", "project"]
        constraints = [
            models.UniqueConstraint(fields=["machine", "project", "path"], name="fleet_stack_unique_per_path"),
        ]

    def __str__(self):
        return f"{self.machine.name}/{self.project}"

    @property
    def repo(self):
        """The remote's short name. The full URL is kept; a table wants the name."""
        if not self.remote or self.remote == "-":
            return "-"
        return self.remote.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")

    @property
    def foreign(self):
        """Does this stack come from a repository other than home-server-stacks?"""
        return self.repo not in ("home-server-stacks", "-")

    @property
    def severity(self):
        """How loudly the page should say something is wrong.

        `missing` and `untracked` are the two states no other check in the lab can
        see: the containers are healthy, so gatus and wud are both satisfied.
        """
        if self.compose in (self.Compose.MISSING, self.Compose.UNTRACKED):
            return "danger"
        if (self.behind or 0) > 0 or self.worktree == "dirty":
            return "warning"
        return ""

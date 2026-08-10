"""The fleet page, and the one button that can affect a machine."""

from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from apps.core.mixins import StaffRequiredMixin, ViewerRequiredMixin

from . import ntfy
from .models import Stack
from .state import build_state


class FleetView(ViewerRequiredMixin, TemplateView):
    template_name = "fleet/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(build_state())
        ctx["verbs"] = ntfy.VERB_LABELS
        # The two stack states nothing else in the lab can see, hoisted out of the
        # per-machine rows so the page can lead with them: gatus sees healthy
        # containers and wud sees a fine image, so neither says a word.
        ctx["stack_alerts"] = [
            stack
            for row in ctx["machines"]
            for stack in row["stacks"]
            if stack.compose in (Stack.Compose.MISSING, Stack.Compose.UNTRACKED)
        ]
        return ctx


class ApproveView(StaffRequiredMixin, View):
    """Publish one approval for a machine.

    Reaching this endpoint gives no ability to run a command: it writes a message
    naming one of four verbs to an ntfy topic. See `apps/fleet/ntfy.py`.
    """

    def post(self, request, machine, verb):
        error = ntfy.publish(verb, machine)
        if error:
            messages.error(request, error)
        else:
            messages.success(request, f"« {verb} » publié pour {machine}")
        response = redirect("fleet:index")
        # 303, so refreshing the page the browser lands on does not repeat the POST.
        response.status_code = 303
        return response

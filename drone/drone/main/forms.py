"""main.forms"""
from django import forms

from markdownx.fields import MarkdownxFormField


class MdForm(forms.Form):
    """
    form to render markdown
    """
    content = MarkdownxFormField()

from interaktiv.alttextgenerator import _
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider


@provider(IFormFieldProvider)
class IAltTextSuggestionBehavior(model.Schema):
    alt_text_suggestion = schema.TextLine(
        title=_("alt_text_suggestion_label", default="Alt text suggestion"),
        description="",
        required=False,
        default="",
    )
    directives.omitted("alt_text_suggestion")


class IAltTextSuggestionMarker(Interface):
    """Marker interface for content that supports alt text suggestions."""


@implementer(IAltTextSuggestionBehavior)
class AltTextSuggestionAdapter:
    def __init__(self, context):
        self.context = context

    @property
    def alt_text_suggestion(self):
        return self.context.alt_text_suggestion

    @alt_text_suggestion.setter
    def alt_text_suggestion(self, value):
        self.context.alt_text_suggestion = value

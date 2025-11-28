from interaktiv.alttextgenerator import _
from plone.autoform import directives
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider


@provider(IFormFieldProvider)
class IAltTextMetadataBehavior(model.Schema):
    #
    # These values should not be edited by hand!
    #
    alt_text_ai_generated = schema.Bool(
        title=_("alt_text_ai_generated_label", default="The alt text is AI generated"),
        description=_(
            "alt_text_ai_generated_description",
            default="Is this alternative text AI generated?",
        ),
        required=True,
        default=False,
    )

    alt_text_model_used = schema.TextLine(
        title=_("alt_text_model_used_label", default="Model used"),
        description=_(
            "alt_text_model_used_description",
            default="The model used to generate the alt text.",
        ),
        required=False,
        default="",
    )
    directives.omitted("alt_text_model_used")

    alt_text_generation_time = schema.Datetime(
        title=_("alt_text_generation_time_label", default="Time of generation"),
        description=_(
            "alt_text_generation_time_description",
            default="The time at which the alt text was generated.",
        ),
        required=False,
    )
    directives.omitted("alt_text_generation_time")


class IAltTextMetadataMarker(Interface):
    """Marker interface for content that supports alt text metadata."""


@implementer(IAltTextMetadataBehavior)
class AltTextMetadataAdapter:
    def __init__(self, context):
        self.context = context

    @property
    def alt_text_model_used(self):
        return self.context.alt_text_model_used

    @alt_text_model_used.setter
    def alt_text_model_used(self, value):
        self.context.alt_text_model_used = value

    @property
    def alt_text_generation_time(self):
        return self.context.alt_text_generation_time

    @alt_text_generation_time.setter
    def alt_text_generation_time(self, value):
        self.context.alt_text_generation_time = value

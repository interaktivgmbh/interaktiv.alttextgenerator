from interaktiv.alttextgenerator import _
from plone import schema
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.restapi.controlpanels import RegistryConfigletPanel
from plone.z3cform import layout
from zope.component import adapter
from zope.interface import Interface


class IAltTextGeneratorSettings(Interface):
    system_prompt = schema.Text(
        title=_("System Prompt"),
        description=_("The system prompt used for alt text generation."),
        required=False,
    )

    user_prompt = schema.Text(
        title=_("User Prompt"),
        description=_(
            "The user prompt used for alt text generation. Use {language} to specify the target language."
        ),
        required=True,
    )

    target_language = schema.Choice(
        title=_("Target language"),
        description=_("The target language of alternative texts."),
        required=True,
        default="en",
        vocabulary="plone.app.vocabularies.AvailableContentLanguages",
    )

    whitelisted_image_types = schema.List(
        title=_("Whitelisted image types"),
        description=_(
            "The images types that are supported for generation of alt texts."
        ),
        required=True,
        default=["image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml"],
        missing_value=[],
        value_type=schema.Choice(
            vocabulary="interaktiv.alttextgenerator.image_mimetypes_vocabulary"
        ),
    )

    blacklisted_paths = schema.List(
        title=_("Blacklisted paths"),
        description=_(
            "Here you can add paths that should be excluded from generation."
        ),
        required=False,
        default=[],
        value_type=schema.TextLine(),
    )


class AltTextGeneratorForm(RegistryEditForm):
    schema = IAltTextGeneratorSettings
    schema_prefix = "interaktiv.alttextgenerator"
    label = _("Alt Text Generator Settings")


@adapter(Interface, Interface)
class AltTextGeneratorConfigletPanel(RegistryConfigletPanel):
    schema = IAltTextGeneratorSettings
    schema_prefix = "interaktiv.alttextgenerator"
    configlet_id = "alttextgenerator-controlpanel"
    configlet_category_id = "Products"
    title = "Alt Text Generator"
    group = "Products"


AltTextGeneratorView = layout.wrap_form(AltTextGeneratorForm, ControlPanelFormWrapper)

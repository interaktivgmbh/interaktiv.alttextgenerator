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
        required=True,
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

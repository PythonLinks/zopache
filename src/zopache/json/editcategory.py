from zopache.core.viewdecorators import *
from zopache.json.editjsonschema import EditJson
from zopache.core.interfaces import ITreeSecurity
from zopache.pages.interfaces import ICategory
from zopache.business.jsonschemavalidator import JSONSchemaValidator
from zopache.business.exists import DuplicateOrganization

@form_component
@name ('edit')
@context(ICategory)
@implementer(ITreeSecurity)
class EditFeaturedContent(EditJson):
    subTitle = 'Select Featured Articles and Videos.'


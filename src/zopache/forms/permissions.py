from zope.interface import Interface
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema._field import Choice
from zope.schema import Text, Set, List
from zopache.application.choices import fromList

class IPermissions(Interface): 
    permissions = Set(
        value_type =Choice(source = fromList(['Manage',
                                              'Party',
                                              'Develop',
                                              'Curate'])),
        title="Permissions",
        description= "What is this user allowed to do?",
        required = False)                

from zopache.core.viewdecorators import *
from zopache.ttw.interfaces import IInternalPrincipal
from zopache.crud.forms import EditForm

@form_component
@name ('permissions')
@context(IInternalPrincipal)
@permissions('Manage')
class EditPermissions (EditForm):
    title = 'Edit User Permissions'
    suTitle = 'What is each user allowed to do.'
    interface = IPermissions
    fields = Fields(IPermissions)
        
    def acquireTitle(self):
        return 'Edit Permissions'


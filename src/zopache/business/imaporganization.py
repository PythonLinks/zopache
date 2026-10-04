from zope import schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.interface import Interface
from zope.interface import directlyProvides
from zope.schema.interfaces import IContextSourceBinder
from zopache.business.interfaces import IMap

from zopache.application.choices import fromDict
from zopache.ttw.acquisition import ParentalAcquire
from zopache.ttw.treewidget import TreeField
from zopache.application.choices import fromList
from zopache.business.ifollow import IFollow
from zopache.pages.interfaces import IMap as IMapBase
from zopache.pages.interfaces  import (
                                       IPageBase,
                                       ILocationContainer,
                                       ILocationLeaf)
def possibleFocus (context):
    return fromDict(getDict(context))

def getDict(context):        
    choices = ParentalAcquire(context)['focusChoices']
    if ((choices != None) and
        (choices.__class__.__name__ == 'PythonScript')):
        return choices()
    return {}    

directlyProvides(possibleFocus, IContextSourceBinder)

class IMapOrganizationBase (IPageBase):
    title = schema.TextLine(
        title = 'Organization Name',
        description = u'What is this organization called?',
        required = True,
    )

    description= schema.Text(
        title = u'Description (200 Characters)',
        description = "A short description of this organization. ",
        required = False,
        max_length = 200,
        default = '',
    )

    address= schema.Text(
        title = u'Address',
        description = "Do you have an office location? (Optional) ",
        required = False,
        max_length = 200,
        default = '',
    )
    
    focus = schema.Choice(
        source = possibleFocus,
        title="Specialization",
        description= "What is this groups focus?",
        required = False)
    
    ballotStatus = schema.Choice(
        source = fromList(['On Ballot',
                           'Petitioning',
                           'Minor Party',
                           'Independent',
                           'Write-In',
                           'Unrecognized']),
        title="Ballot Status?",

        description= "One of six.",
        default = "On-Ballot",
        required = False,)
#    addTo=TreeField(
#           title="Where should this organization be?",
#           description= "To be approved, please place it in a leaf of the tree.?",
#           required = True,
#           )    
    #was url
    remoteURL = schema.URI(
        title = u'The Organization URL',
        description = """Please link to a web page, maybe twitter or gab.com 
. Include  'https://'""",
        required = False,
        missing_value ='',           
    )

    source= schema.Text(
        title = u'Longer Description',
        description = u'Please describe this organization further.',
        required = False,
        default = '',
    )    

    duesURL = schema.URI(
        title = u'Where to donate money URL',
        description = """Please support your party. Include  'https://'""",
        required = False,
        missing_value ='',           
    )

    registerURL = schema.URI(
        title = u'The URL to the register to vote page. ',
        description = """Where to register to vote. Include  'https://'""",
        required = False,
        missing_value ='',           
    )

    joinURL = schema.URI(
        title = u'The URL to join the party. . ',
        description = """The page to join the local party.  Include  'https://'""",
        required = False,
        missing_value ='',           
    )    



    lattitude = schema.Float(
        title = u'Latitude',
        description = u'Latitude',
        min=-90.,
        max=90.,
        default = 51.509865,
        required = True,
        )

    longitude = schema.Float(
        title = u'Longitude',
        description = u'Longitude ',
        min=-180.,
        max=180.,
        default = 0.,
        required = True,
    )

    zoomLevel = schema.Float(
        title = u'Google Maps Zoom Level',
        description = u'Google Maps Zoom Level',
        min=0.,
        max=22.,
        default = 5., 
        required = True,
    )
    
    showChildren = schema.Bool(
	    title = "Show Children?",
	    description = "Should it show the objects in the children?",    
	    required = False,
	    default = True)


from zopache.business.interfaces import  ISocialMedia,IOrganizationBase
    
class IMapOrganization(IOrganizationBase,
            IMapBase,ILocationContainer,
            IMapOrganizationBase,ISocialMedia):    
      pass

class IEndorsingOrganization(IMapOrganization,IMap):
       pass



    

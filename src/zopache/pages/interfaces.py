from zope.interface import Interface
from zope import schema
from dolmen.container import IBTreeContainer
from cromlech.container.interfaces import IOrderedContainer
from cromlech.browser.interfaces import IPublicationRoot

from zopache.crud.interfaces import IContainer , IZodbRoot
from zopache.ttw.interfaces import ISourceLeaf
from zopache.ttw.interfaces import IUntrustedHTML, IBranch, ICanonical
from zopache.python.interfaces import IDirectory
from zopache.ttw.interfaces import ISourceLeaf
from cromlech.file import FileField
from zopache.ttw.interfaces import IAceHTML
from zopache.core.interfaces import ICountable, ISiteRoot
from zopache.crud.interfaces import ILeaf
from zopache.ttw.interfaces import IJSON

class ICategoryBase(Interface):
    title = schema.TextLine(
        title = 'Category Name',
        description = 'Name this category..',
        required = True,
    )

    description= schema.Text(
        title = 'Description',
        description = "A brief description of this category",
        required = False,
        default = '',
    )

    #twitterIds = schema.TextLine(
    #    title = 'Twitter Ids',
    #    description = "Accounts to Notify",
    #    required = False,
    #    default = '',
    #)
    
    source= schema.Text(
        title = u'Content',
        description = u'This is the main content for this page',
        required = False,
        default = u'',
    )    
    

    tags = schema.TextLine(
        title = 'Tags',
        description = 'For this Cateogry.',
        required = False,
    )

class ILayoutView(Interface):
    pass

class IImaginary(ILayoutView):
   pass

class IImaginaryBTree(ILayoutView):
   pass

# A MARKER TO SHOW THAT THIS IS NEWS
class IRecent(Interface):
    pass

#THINGS THAT HAPPEN AT  A POINT IN TIME  
class ITime(Interface):
    pass

class IContent(ICanonical):
    pass

class IJSONInclude(Interface):
    pass
    

class IPageBase(ILayoutView,ICanonical,IContent):
    title = schema.TextLine(
        title = u'Page Name',
        description = u'Describe this page.',
        required = True,
    )
        
class ILinkBase(IPageBase,IBTreeContainer):
    pass

class ILinkTop(Interface):
    title = schema.TextLine(
        title = 'Remote Page Name',
        description = 'What is the title of this link?',
        required = True,
    )
    
    remoteURL= schema.URI(
        title = 'URL',
        description = """A URL That this page refers to. 
             Please include 'https://'""",
        required = False,
    )
    
class IAddLinkTop(ILinkTop):    
    imageURL= schema.URI(
        title = 'Image URL',
        description = """A URL That this highlights this link. 
             Please include 'https://
             The image will be automatically downloaded'""",
        missing_value = '',
        required = False,
    )
    
class IPageBottom(Interface):

    description= schema.Text(
        title = 'Description',
        description = """A brief introduction of this page.  
                        This is used by the search functions.""",
        required = False,
        default = u'',
    )

    
    source= schema.Text(
        title = u'Content',
        description = u'This is the main content for this page',
        required = False,
        default = u'',
    )
    
class IPage(IPageBase,IPageBottom,
            IContent, IOrderedContainer,
            IJSONInclude, IUntrustedHTML,IAceHTML):
    pass

class IProxyPage(IPage):
    pass

class IAddPage(IPage):
    imagegURL= schema.URI(
        title = 'Image URL',
        description = """A URL That this page refers to. 
             Please include 'https://
             The image will be automatically downloaded'""",
        required = False,
    )        
      
class ILink(IPage,ILinkTop,ILinkBase,ICountable):
    pass

class IAddLink(IPage, IAddLinkTop):
     pass
    
class IMarkdown (IAceHTML,ISourceLeaf):
    pass

from zopache.ttw.interfaces import IJSON
class INotebookBase(Interface):
    title = schema.TextLine(
        title = u'Notebook Title',
        description = u'What is the name of this notebook?.',
        required = True,
    )
    
    description= schema.Text(
        title = u'Description',
        description = """A brief introduction of this Notebook.  
                        This is used by the search functions.""",
        required = False,
        default = u'',
    )
    
from zopache.ttw.interfaces import IJSON
class INoteboko(INotebookBase,IJSON):
    source= schema.Text(
        title = u'Notebook Source:',
        description = u'This is the JSON  which defines the Notebook.',
        required = False,
        default = u'',
    )
    
class IAddNotebook(INotebookBase):    
    _v_source = FileField(
                    title=u'Upload a .pynib file',
                    required = True,
                      )    


class INotebook (ISourceLeaf,IDirectory):
    description= schema.Text(
        title = u'Description',
        description = """A brief introduction of this Notebook.  
                        This is used by the search functions.""",
        required = False,
        default = u'',
    )

class INews (IPage,IRecent):
    pass

#USED BY Green Maps
class IRootPage(ISiteRoot,
                IZodbRoot,
                IPage,
                IBranch):
    pass

class ISiteRootPage(ISiteRoot,IBranch,IPage,IBTreeContainer):
    description= schema.Text(
        title = 'Description',
        description = "A brief description of this web site.",
        required = False,
        default = '',
    )
    



class INotPage (Interface):
     pass

class ILatLng(Interface):
    latitude = schema.Float(
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

#This is the legacy Location,
#Used in pages.location.Location
#So it has to stay
class ILocation(ILatLng):
    pass

#For Politicians
class ILocationLeaf(ILocation):
    pass

#For State Party Organizations
class ILocationContainer(ILocation):
    pass

class IPin(ILocationLeaf,ILatLng):
    pass

class IMap(ILatLng):
    zoomLevel = schema.Float(
        title = u'Google Maps Zoom Level',
        description = u'Google Maps Zoom Level',
        min=0.,
        max=22.,
        default = 5., 
        required = True,
    )

class ISimpleMap(IPage,IMap):
    pass
    
from zopache.pages.address import Address
class IAddress(Interface):
    pass
    """"
    address= Address(
        title = u'Address (For the map)',
        description = u'Where is the main office for this company?',
        required = True,
        default = u'',
    )
    """
    
class IAddressMap(IMap,IAddress):
    pass

from zopache.ttw.interfaces import ICanonicalJSON
class ICategory(ICategoryBase,
                ICanonicalJSON,
                IPageBase):
    pass

class IGeographicalCategory(ICategory):
    """
    title = schema.TextLine(
        title = 'Geographical Category Name',
        description = u'Describe this page.',
        required = True,
    )

    description= schema.Text(
        title = 'Description',
        description = ""A brief introduction of this geographical category..  
                        This is used by the search functions."",
        required = False,
        default = '',
    )
    """
class ILocationCategory (IGeographicalCategory, ILatLng):
    pass

class IMapCategory(IGeographicalCategory,ILatLng):
    pass

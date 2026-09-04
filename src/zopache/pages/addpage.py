from dolmen.forms.base import Actions


from zopache.ttw.interfaces import ICanonical
from zopache.crud.actions import Cancel
from zopache.core.viewdecorators import *
from zopache.ttw.htmlviews import CkScripts
from zopache.ttw.htmlviews import AddCkHTMLBase
from zopache.crud.forms import AddByTitleForm, TreeSecurityAddForm
from zopache.crud.addbytitleactions import *
from dolmen.forms.base import Fields
from zopache.pages.interfaces import (
                                      ISimpleMap,
                                      ILocation,
                                      IPage,
                                      IPin,
                                      IPageBase,
                                      ISiteRootPage,
                                      IProxyPage,
                                      ILocationCategory,
                                      IMapCategory )
from zopache.pages.page import Page, Link, SiteRootPage
from zopache.pages.location import SimpleMap, Location, Pin
from zopache.core.interfaces import ITreeSecurity
from zopache.business.exists import Duplicate
from zopache.forms.urlvalidator import DuplicateURLValidator
from zopache.pages.htmlvalidator import HTMLValidator
from zopache.pages.proxypage import ProxyPage
from zopache.crud.getimage import getImage
from zopache.ttw.mail import Notify

class Base(object):
    count = 0 
    layoutName = "UserMenu"
    actions = Actions()
    dataValidators = [Duplicate, DuplicateURLValidator, HTMLValidator]
    
    @property
    def fields(self):
        return  Fields(self.interface)    
        
#This is for ones without tree security        
class BaseAdd(Base,AddCkHTMLBase,AddByTitleForm,Notify):
    def __init__(self,context,request):
        #First give it a context, then initialize Notify.
        AddCkHTMLBase.__init__(self)
        AddByTitleForm.__init__(self,context,request)
        Notify.__init__(self)

#This one is for ones with Tree Security
class AddAuthorizedPage(BaseAdd, AddCkHTMLBase,
                        TreeSecurityAddForm):
    actions = Actions()
    
    def __init__(self,context,request):
        #First give it a context, then initialize Notify.
        AddCkHTMLBase.__init__(self)
        TreeSecurityAddForm.__init__(self,context,request)
        Notify.__init__(self)
        
    def getSubTitle(self):
          return (
                "To a " +  
                self.context.webClass +
                u' called: ' +
                self.context.getTitle()
               )
    def addAuthorizedActions(self):           
        self.actions = Actions(
              AddByTitleAndView("Add and View", self.factory),
              AddByTitleAndAceEdit("Add and aceEdit", self.factory),
              AddByTitleAndCkEdit("Add and ckEdit", self.factory),
              AddByTitleAndManage("Add and Manage", self.factory),            
              Cancel("Cancel","Cancel"))
          
@view_component
@name('addPage')
@target(IView)
@context(IPageBase)
@implementer(ITreeSecurity)
class AddPage(AddAuthorizedPage):
    title = "Add a Web Page"
    subTitle = "It can have child pages."
    interface = IPage
    label=""
    factory = Page


    
from zopache.application.interfaces import IRootContainer
@view_component
@name('addSiteRootPage')
@target(IView)
@context(IRootContainer)
@implementer(ITreeSecurity)
class AddRootPage(AddAuthorizedPage):
    title = "Add a Root Page"
    subTitle = "This can be a whole new website.  Only at the top of the tree."
    dataValidators = []
    interface = ISiteRootPage
    label="Add a Root Wiki Page"
    factory = SiteRootPage
    
@view_component
@name('addProxyPage')
@target(IView)
@context(IPageBase)
@implementer(ITreeSecurity)
class AddProxyPage(AddAuthorizedPage):
    interface = IProxyPage
    title="Add a ProxyPage"
    subTitle = "This displays content from another page."
    factory = ProxyPage    
    
#LOCAION
@view_component
@name('addLocation')
@target(IView)
@context(IPageBase)
@implementer(ITreeSecurity)
class AddLocation(AddAuthorizedPage):
    interface = ILocation
    label="Add a Location"
    subTitle = 'These points show up on parent maps. '
    factory = Location

#LOCAION CATEGORY
from zopache.pages.interfaces import ILocationCategory
from zopache.pages.category import LocationCategory
@view_component
@name('addLocationCategory')
@target(IView)
@context(ICanonical)
@implementer(ITreeSecurity)
class AddLocationCategory(AddAuthorizedPage):
    interface = ILocationCategory
    label="Add a Location Category"
    subTitle = 'These points show up on parent maps. '
    factory = LocationCategory    

# PIN
@view_component
@name('addPin')
@target(IView)
@context(IPageBase)
@implementer(ITreeSecurity)
class AddPin(AddAuthorizedPage):
    interface = IPin
    label="Add a Pin"
    subTitle = 'These points show up on parent maps. '
    factory = Pin


@view_component
@name('addMap')
@target(IView)
@context(IPageBase)    
@implementer(ITreeSecurity)
class AddMap(AddAuthorizedPage):
    subTitle = 'Add a map'
    subTitile = 'Remember to enable map tokens.'
    interface = ISimpleMap
    label="Add a Map"
    factory = SimpleMap

    

from zopache.pages.category import Category
from zopache.pages.interfaces import ICategory,IPageBase

@view_component
@name('addCategory')
@target(IView)
@context(IPageBase)
@implementer(ITreeSecurity)
class AddCategory(AddAuthorizedPage):
     interface = ICategory
     title = "Add a Category"
     subTitle =""
     count = 0
     factory = Category
     layoutName = "UserMenu"
     dataValidators = [Duplicate]
        
#MAP CATEGORY
from zopache.pages.interfaces import IMapCategory
from zopache.pages.category import MapCategory
@view_component
@name('addMapCategory')
@target(IView)
@context(IPageBase)    
@implementer(ITreeSecurity)
class AddMapCategory(AddAuthorizedPage):
    title = 'Add a Map Category'
    subTitle = 'Both a map and a category.  Remember to enable map tokens.'
    interface = IMapCategory
    label="Add a Map Category"
    factory = MapCategory  

#REGION CATEGORY
from zopache.business.interfaces import IRegionalCategory
from zopache.business.regionalcategory import RegionalCategory
@view_component
@name('addRegionalCategory')
@target(IView)
@context(IPageBase)    
@implementer(ITreeSecurity)
class AddRegionCategory(AddAuthorizedPage):
    title = 'Add a Regional Category'
    subTitle = 'Both a region and a category.  '
    interface = IRegionalCategory
    factory = RegionalCategory  

#LOCATION CATEGORY
from zopache.pages.interfaces import ILocationCategory
from zopache.pages.category import LocationCategory
@view_component
@name('addLocationCategory')
@target(IView)
@context(IPageBase)    
@implementer(ITreeSecurity)
class AddLocationCategory(AddAuthorizedPage):
    title = 'Add a Location Category'
    subTitle = 'Both a location and a category.'
    interface = ILocationCategory
    factory = LocationCategory  

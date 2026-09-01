from slugify import slugify

from zopache.crud.addbyurl import  AddByURLForm
from zopache.crud.forms import AddByTitleForm
from zopache.core.interfaces import ITreeSecurity,IUserSecurity
from zopache.core.viewdecorators import *
from zopache.pages.interfaces import IPageBase, IPage
from zopache.remote.rss import  RSS, JustRSS
from zopache.remote.irss import IAddRSS,IRSS, IJustRSS 
from zopache.remote.rssarticle import  RSSArticle
from zopache.core.page import Page
from zopache.ttw.mail import Notify
from BTrees.OOBTree import OOBTree
from dolmen.container import IBTreeContainer
from zopache.business.exists import Duplicate
from zopache.pages.addanonymous import AddAnonymousPageByTitle

@view_component
@name ('addRSS')
@target(IView)
@context(IPage)
class AddRSS(AddAnonymousPageByTitle,Notify):
     interface = IAddRSS
     title = "Add an RSS Feed"
     subTitle ="Ask the admin to fetch the articles. "
     count = 0
     factory = RSS
     layoutName = "UserMenu"
     dataValidators = [Duplicate]
     
     def newURL(self,baseURL):
        return baseURL + '/manage'

     def dataModel(self):

        contextJsonDict =  self.template['rssSchema'].getAsDict()
        result = json.dumps(contextJsonDict)
        return result
   



@view_component
@name('addJustRSS')
@target(IView)
@context(IBTreeContainer)
@implementer(ITreeSecurity)
class AddJustRSS(AddByTitleForm,Notify):
     interface = IJustRSS
     title = "Just add an RSS Feed"
     subTitle =""
     count = 0
     factory = JustRSS
     layoutName = "UserMenu"
     dataValidators = [Duplicate]
     def newName(self,data):
         return self.context.name + "-rss-feed"
    
     def newURL(self,baseURL):
        return baseURL + '/manage'   

from zopache.core.baseform import Form
from zope.interface import Interface

""""
No longer used.  WAS USED FOR some strANge stuff. y

@view_component
@name('ckedit')
@target(IView)
@context(IRSS)
@implementer(ITreeSecurity)
class EditRSS(E):
    title = "Update an RSS Feed"
    subtitle = "All feeds will be fetched  again. "
    count = 0
    schemaName = "rssSchema"     
    def update(self):
        self.status='RSS Was updated'
        Form.update(self)
@form_component
@name ('aceedit')

@context(IJustRSS)
@implementer(IUserSecurity)
class EditRSS2(BaseEditForm):
    pass

"""

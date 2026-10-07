import time

from zope import schema
from zope.schema import Text

from cromlech.browser.exceptions import HTTPFound
from dolmen.forms.base import DISPLAY
from dolmen.forms.base.markers import FAILURE, SUCCESS

from zopache.core.viewdecorators import *
from zopache.pages.interfaces import ILinkBase
from zopache.forms.interfaces import IApprove

from dolmen.forms.base import Actions

from zopache.crud.forms import EditForm
from zopache.core.viewdecorators import *
from zopache.ttw.treewidget import TreeField
from zopache.core.interfaces import ITreeSecurity
from zopache.crud.update import Edit, Save,  SaveAndView,  Cancel
from zopache.core.breadcrumbs import Breadcrumbs    
from zopache.zmi.cutcopypaste import Cutter

class IApprove(Interface):
    title = schema.TextLine(
        title = u'Page Name',
        description = u'Describe this page.',
        required = True,
    )

    description= schema.Text(
        title = 'Description',
        description = """A brief introduction of this page.  
                        This is used by the search functions.""",
        required = False,
        default = u'',
    )        
    webApproved = schema.Bool(
        title = "Visible or not?",
        description = "Use this option to hide this article.",
        required = False,
        default = False)

    category=TreeField(
           title="Category Search",
           description= """Choose where to move the articcle. """,
           required = False,
            )
    
class Publish(Save):
    def __call__(self,form):
        result = Save.__call__(self,form)
        if result != FAILURE:
            self.publish()
            raise HTTPFound('/' + form.context.parent.name +'/manage')
        
        return result
    
    def publish(self):
        context = self.form.context
        context.webApproved = True
        form = self.form
        if getattr(context,'category',''):
            context.publicationApproved = True
            
            context.addImage()
            category = form.getSiteRoot()[context.category]
            if category!= context.__parent__:
                context.moveTo(category)

class AddCategory(Save):
    def __call__(self,form):
        result = Save.__call__(self,form)
        if result == FAILURE:
            return result            
        context = self.form.context
        context.webApproved = True
        context.publicationApproved = True
        category = getattr(context,'category',None)
        del context.category
        context.addImage()
        if category:
            Cutter(context).cut(form)
            raise HTTPFound('/' + category  +'/addCategory')
        return result        

class PublishAndToot(Publish):
    def __call__(self,form):
        result = Save.__call__(self,form)
        if result != FAILURE:
            self.publish()
            raise HTTPFound('/' + form.context.name + '/toot')
        return result
    
class Retract(Save):
    def __call__(self,form):
        result = Save.__call__(self,form)
        if result != FAILURE:
            self.retract()
            raise HTTPFound('/' + self.form.context.name)            
        return result              
        
    def retract(self):
        context = self.form.context
        context.publicationApproved = False
        rssFeed = context.rssFeed
        if rssFeed != context.__parent__:
           context.moveTo(rssFeed)

           

@form_component
@name ('approve')
@context(ILinkBase)
@permissions("Curate")
class Approve (EditForm,Breadcrumbs):
    title = 'Approve this Article?'
    subTitle = "The article will be moved to its new location. "
    interface = IApprove
    fields = Fields(IApprove)
    def newURL (self,baseURL):
           return baseURL

    def addAuthorizedActions(self):
        self.actions = Actions(
                    Edit("Save", "save"),        
                    Publish("Publish","publish"),
                    Retract("Retract","retract"),
                    PublishAndToot("Pubilsh And Toot","publishToot"),
                    AddCategory("Add Category", "addCategory"),
                    Cancel("Cancel","Cancel"))
        
    def postProcess(self, view = None):
        root = self.getSiteRoot() 
        aTime = int(time.time())

        if not hasattr(root,'movedArticles'):
           from BTrees.IOBTree import IOBTree            
           root.movedArticles = IOBTree()
        movedArticles = root.movedArticles
        movedArticles[- aTime] = self.context
        while len(movedArticles) > 30:
           maxKey = movedArticles.maxKey()
           del movedArticles [maxKey]
        self.context.postProcess(view = self)
        
           



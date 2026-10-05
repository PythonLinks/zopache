from zope.interface import Interface
from zope.schema import Text, TextLine, Bool

from cromlech.browser.exceptions import HTTPFound
from cromlech.webob.response import Response
from dolmen.view import View

from zopache.remote.vote import make_text_response
from zopache.core.viewdecorators import *
from zopache.crud.forms import EditForm
from zopache.pages.interfaces import IPageBase, ILinkBase
from zopache.forms.interfaces import IApprove
from zopache.core.interfaces import ITreeSecurity
from zopache.remote.rssarticle import IRSSArticle
from zopache.core.breadcrumbs import Breadcrumbs

@form_component
@name ('approve')
@context(IPageBase)
@implementer(ITreeSecurity)
class Approve (EditForm):
    title = 'Aprove this posting'
    subTitle = ''
    interface = IApprove
    fields = Fields(IApprove)

#@form_component
#@name ('approveLink')
#@context(ILinkBase)
#@implementer(ITreeSecurity)
#class ApproveLink (EditForm):
#    title = 'Approve this posting'
#    subTitle = ''
#    interface = IApprove
#    #fields = Fields(IApprove)    


@form_component
@name ('reject')
@context(IRSSArticle)
@implementer(ITreeSecurity)
class Reject (View,Breadcrumbs):
    responseFactory = Response
    make_response = make_text_response
    
    def render (self):
        return "Rejected"
    
    def update(self):
        context = self.context
        siteRoot = self.getSiteRoot()
        siteRoot.unIndexItem(context)
        self.context.webApproved = False
        siteRoot.indexItem(context)


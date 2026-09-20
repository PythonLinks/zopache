from cromlech.webob.response import Response
from dolmen.view import  make_view_response
from zopache.core import View
from zopache.core.breadcrumbs import Breadcrumbs
from dolmen.forms.base import Actions
from zopache.crud import actions as formactions, i18n as _
from zopache.crud import update as updateactions
from . import actions  as ttwactions
from zopache.core.interfaces import ITreeSecurity
from zopache.core.interfaces import ITreeSecurity
from chameleon import PageTemplate
from zope import interface
from zope import schema
from zope.schema.interfaces import IField
from zope.interface import Interface
from zopache.crud.forms import  BaseEditForm, EditDemoForm
from dolmen.forms.base import action, name, context, form_component
from crom import target, order
from cromlech.browser.directives import title
from zopache.ttw.acescripts import AceScripts
from dolmen.view import name, context, view_component
from zopache.ttw.interfaces import (ISource,
                                    IHTML,
                                    IAceHTML,
                                    ICkHTML,
                                    ISecureHTML,
                                    IHTMLClass,
                                    IAceHTMLClass,
                                    IUntrustedHTML,
                                    IIndexHTML,
                                    IAceHTMLPage)
from zopache.ttw.addeditforms import TreeSecurityAddForm, AceEditForm
from zopache.ttw.mixin import Mixin


from zopache.ttw.html import (HTML,
                              HTMLRecursionError,
                              AceHTML,
                              TrustedHTML,
                              UntrustedHTML,
                              HTMLPage,
                              SecureHTML)

from dolmen.container import IBTreeContainer, BTreeContainer
from zope.interface import implementer

class AceScripts(AceScripts):
      aceMode = 'html'

from zopache.ttw.acescripts import createEditorDiv
class CkScripts(object):
    def  headerScripts(self):
        result = """
<script src="https://cdn.ckeditor.com/4.4.4/standard/ckeditor.js"></script> 
        """ + TreeSecurityAddForm.headerScripts(self)
        return result
  
    def  footerScripts(self):
        return """
<script>
CKEDITOR.replace('form-field-source', {
    disableNativeSpellChecker: false,
    versionCheck: false
});
</script>
        """ 

from zopache.pages.htmlvalidator import HTMLValidator
class AddHTMLBase(object):
    interface = IHTML
    ignoreContent = True
    datavalidators = [HTMLValidator]

class AddCkHTMLBase(AddHTMLBase,CkScripts):
    subTitle="Add an HTML Object"
    factory=HTML

    def footerScripts(self):
        return CkScripts.footerScripts(self)

    def headerScripts(self):
          return CkScripts.headerScripts(self)


class AddCkHTMLWithActionsBase(AddCkHTMLBase):           
    def addAuthorizedActions(self):           
         self.actions = Actions(
              formactions.AddAndView(_("Add and View","Add -> View"), self.factory),
              ttwactions.AddAndCkEdit(_("Add and ckEdit","Add -> ckEdit"), self.factory),
              ttwactions.AddAndAceEdit(_("Add and AceEdit","Add -> AceEdit"), self.factory),
              formactions.Cancel(_("Cancel","Cancel")))


@form_component
@name ('addHTML')
@context(IBTreeContainer)
@implementer(ITreeSecurity)
class AddCkHTML(AddCkHTMLWithActionsBase,TreeSecurityAddForm):
    pass


class AddAceHTMLBase(AceScripts,AddHTMLBase,TreeSecurityAddForm):        
    subTitle="Add an Ace HTML Object"
    factory=AceHTML
    aceMode = "html"
    def addAuthorizedActions(self):           
         self.actions = Actions(
              formactions.AddAndView(_("Add and View","Add -> View"), self.factory),
              ttwactions.AddAndAceEdit(_("Add and AceEdit","Add -> AceEdit"), self.factory),
              formactions.Cancel(_("Cancel","Cancel")))


    
@form_component
@name (u'addAceHTML')
@context(IBTreeContainer)
@implementer(ITreeSecurity)
class AddAceHTML (AddAceHTMLBase):
    pass

@view_component
@name('index')
@context(IIndexHTML)
class Index(View,Breadcrumbs, Mixin):
    count=0
    responseFactory = Response
    make_response = make_view_response
    def setDisplayObject(self,item):
        self.zopacheTemplate=item

    def remoteHref(self,url,title):
            return F'<a href="{url}" > {title}</a>'

    def command(self,name):
        url =  self.context.__name__ + '/' + name
        return url

    def page(self,name):
        url =  name 
        return url        
    
    def render(self):
        #In the case of /index/index
        if not hasattr(self,'zopacheTemplate'):
               self.zopacheTemplate=self.context
               self.context=self.context.__parent__
        try:
               return self.zopacheTemplate(self)
        except HTMLRecursionError:
               return ('Your templates recursion exceeded 50 calls'+
                      self.zopacheTemplate.source)               

@view_component
@name('index')
@context(IAceHTMLClass)
class AceObjectIndex(Index):           
    def render(self):

        content = Index.render(self)
        zopacheTemplate = self.zopacheTemplate
        if not hasattr(zopacheTemplate,'layout'):
            return content
        layout = zopacheTemplate.layout
        if layout == "":
            return content
        template = self.layoutAcquire(layout)
        if template == None:
            return content  
        view = self
        return template.__call__(view,content=content)

from zopache.pages.interfaces import ILayoutView  
@view_component
@name('index')
@context(ILayoutView)
class PageIndex(AceObjectIndex):
    def update(self):
        self.zopacheTemplate = self.layoutAcquire('index')
        
class BaseHTMLEditForm(BaseEditForm):
    actions = Actions()
    dataValidators = [HTMLValidator]    

    def addAuthorizedActions(self):        
        action1=ttwactions.SaveAndAceEdit("Save","Save")
        action2=updateactions.SaveAndView("Save  and View","Save -> View")

        action3=ttwactions.SaveAndCkEdit(
                "Save and CkEdit","Save -> ckEdit")
        
        #action4=formactions.SaveAndTest(
        #        "Save and Test","Save -> Test")        

        action5=formactions.Cancel("Cancel","Cancel")
        if ICkHTML.providedBy(self.context):
                self.actions = Actions(action1,action2,action3,action5)
        else:
                self.actions = Actions(action1,action2,action5)                
        
class BaseAceEdit(AceScripts,BaseHTMLEditForm):
    __name__ = "aceedit"
    subTitle="Ace Edit this object" 
    aceMode = "html"
    
    def footerScripts(self):
        return AceScripts.footerScripts(self)

    def headerScripts(self):
          return AceScripts.headerScripts(self)    


class AceEdit(BaseAceEdit):
    pass            
        
#REGULAR ACE HTML FORM
@form_component
@context(IAceHTML)
@name("aceedit")
@implementer (ITreeSecurity)
class AceEditForm(AceEdit):
          pass

#ACE HTML FOR FOR THE ACE HTML CLASS. 
@form_component
@context(IAceHTML)
@name("aceedit")
@implementer (ITreeSecurity)
class AceEditForm(AceEdit):
    interface = IAceHTMLClass

#AND HERE IS THE DEMO ACE EDIT FORM
@form_component
@context(IAceHTML)
@name("acedemo")
class AceDemoHTML(BaseAceEdit):
    subTitle = "Saving is disabled in this demo."            
    @property
    def actions(self):
        return Actions()


class BaseCkEdit(CkScripts,BaseHTMLEditForm):
    __name__ = "ckedit"
    subTitle="CkEdit this object"        
    
    def footerScripts(self):
        return CkScripts.footerScripts(self)

    def headerScripts(self):
          return CkScripts.headerScripts(self)    


class CkEdit(BaseCkEdit):
    def addAuthorizedActions(self):
        self.actions = Actions(
              updateactions.SaveAndView(_("Save  and View","Save -> View")),
              ttwactions.SaveAndCkEdit(_("Save","Save")),
              ttwactions.SaveAndAceEdit(_("Save  and AceEdit","Save -> AceEdit")),
              #ttwactions.SaveAndTest(_("Save  and Test","Save -> Test")),
              formactions.Cancel(_("Cancel","Cancel")))


                
#HERE IS THE CKEDIT FORM
@form_component
@context(ICkHTML)
@name('ckedit')
class CkEditForm(CkEdit):
          pass


#AND HERE IS THE CkDemo Form
@form_component
@context(ICkHTML)
@name('ckdemo')
class CkDemoHTML(BaseCkEdit):
    subTitle = "Saving is disabled in this demo."    
    @property
    def actions(self):
        return Actions()

@view_component
@name('source')
@context(ISource)
class ViewSource(Index):
    def render(self):
            top="<html><head></head><body><code>"
            middle=self.context.source
            bottom="</code></body></html>"
            return top+middle+bottom

@view_component
@name('index')
@context(IUntrustedHTML)
class ViewSource2(Index):
    def render(self):
        return self.context.source



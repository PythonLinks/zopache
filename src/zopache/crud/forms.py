# -*- coding: utf-8 -*-

#This software is subject to the CV and Zope Public Licenses.
from zope.interface import Interface
from dolmen.forms.base import DISPLAY

from zopache.core.viewdecorators import *

from dolmen.container import BTreeContainer, IBTreeContainer
from dolmen.forms.base import Actions
from cromlech.security import Unauthorized

from .interfaces import IName, IContainer, ILeaf

from zopache.core.baseform import Form
from zopache.core.breadcrumbs import Breadcrumbs
from zopache.crud import actions as formactions, i18n as _
from zopache.crud import update as editActions
from zopache.crud.utils import getFactoryFields, getAllFields
from zopache.core.uniquename import UniqueName
from zopache.crud.actions import AddByName, AddByTitle
from zopache.ttw.mail import Notify
from zopache.core.interfaces import ITreeSecurity

class BasicForm(Form,Breadcrumbs,Notify):
    ignoreContent = True
    igrnoreRequest = False
    count = 0
    def __init__(self,context,request):
        Form.__init__(self,context,request)
        Notify.__init__(self)


class AddFormBase(Form, Breadcrumbs):    
    """The add form itself is not protected. The security is checked on
    'update'. It checks if the 'require' directive of the factored item
    is respected on the context.
    """
    error = ''
    submissionError = ''
    label= ''
    subTitle='Add an Object'
    
    def acquireTitle(self):
         return self.title
     
    @property
    def fields(self):
        return  Fields(self.interface)

#USING TRADITIONAL PERMISSIONS    
class AddForm(AddFormBase):
    @property
    def fields(self):
        return  Fields(IName,self.interface)

    actions = Actions()
    #def actions(self):
    #    return  Actions(
    #        formactions.Add(_("Add","Add"), self.factory),
    #        formactions.Cancel(_("Cancel","Cancel")))
    
class TreeSecurityAddForm(AddFormBase):
    @property
    def fields(self):
        return  Fields(IName,self.interface)
    actions = Actions()
    
    def update(self):
        if self.treeSecurity():
           self.addAuthorizedActions()
        else:
           self.addUnauthorizedActions()
           
    def addAuthorizedActions(self):
        self.actions = Actions()
        
    def addUnAuthorizedActions():
        self.actions = Actions()        
   
    
#THIS ONE IS LIKE ADD FORM, BUT BASED ON TREE SECURITY    
class AddByNameForm(TreeSecurityAddForm,UniqueName):
    def addAuthorizedActions(self):
            self.actions = Actions(
            formactions.AddByName(_("Add","Add"), self.factory),
            formactions.Cancel(_("Cancel","Cancel")))
    
class AddByTitleForm(TreeSecurityAddForm,Notify):
    @property
    def fields(self):
        return  Fields(self.interface)
    
    def __init__(self,context,request):
        TreeSecurityAddForm.__init__(self,context,request) 
        Notify.__init__(self)       
    
    def addAuthorizedActions(self):   
              self.actions = Actions(
              formactions.AddByTitle("Add", self.factory),
              formactions.Cancel("Cancel"))

class BaseEditForm(Form,Breadcrumbs):    
    actions = Actions()
    subTitle='Edit This Object'
    ignoreContent = False
    ignoreRequest = False
    count = 0
    @property
    def fields(self):
        return  Fields(self.interface)
    
    def update(self):
        if self.treeSecurity():
            self.addAuthorizedActions()
        else:
            self.addUnAuthorizedActions()

    def addUnAuthorizedActions(self):
        self.actions = Actions()

    def addAuthorizedActions(self):
        self.actions = Actions(editActions.Edit(_("Save","Save")),
                    editActions.SaveAndView(_("SaveAndView","Save And View")),
                    editActions.Cancel(_("Cancel","Cancel")))

    @property
    def label(self):
        return ''

    @property
    def fields(self):
        edited = self.getContentData().getContent()
        return getAllFields(edited, '__parent__', '__name__')

class EditDemoForm(BaseEditForm):
    pass

class EditForm(BaseEditForm):
    pass


#@form_component
#@name (u'display')
#@context(IDisplayable)
#@title("Display")
#@title("Display")
#@permissions('Manage')


class DisplayForm(Form):
    """
    """
    label =''
    subTitle='Display This Object'
    mode = DISPLAY
    ignoreRequest = True
    ignoreContent = False

    @property
    def label(self):
        return ''

    @property
    def fields(self):
        displayed = self.getContentData().getContent()
        return getAllFields(displayed, '__parent__', '__name__', 'title')

from zopache.pages.interfaces import IPageBase
from zopache.crud.delete import (DeleteLeaf,
                                 DeleteChildren,
                                 DeleteBranch)

@form_component
@name ('delete')
@context(IPageBase)
@implementer(ITreeSecurity)
class DeleteForm(Form):
    """A confirmation for to delete an object.
    """
    subTitle='Delete Something'
    description = """<p style = "clear:left;"><b>Are you really sure?</b><br><br>
    Delete Node only works if it is empty.<br>
    Delete Children, deletes the content, but leaves the logo or
    banner image. <BR>
    Deleted objects are first unindexed. <br><br>
    <b>So what would you like to delete?</b></p>
    
    """
    @property
    def actions(self):

        actionList = [ DeleteLeaf("Leaf","Leaf")]
        if self.isManager():
           actionList.append(DeleteChildren("Item + Children","Children"))
           #This one is too dangerous, so it is removed. 
           #DeleteBranch("Branch","Branch"),
        actionList.append(formactions.Cancel("Cancel","Cancel"))
        actions = Actions(*actionList)    
        return actions

# -*- coding: utf-8 -*-
#This software is subject to the CV and Zope Public Licenses.

from cromlech.webob.response import Response
import dolmen
from dolmen.template import TALTemplate
from dolmen.view import View, make_layout_response
from dolmen.forms.base import Form as BaseForm
from cromlech.location import get_absolute_url

from . import tal_template

from .scripts import Scripts

from dolmen.container import IBTreeContainer
from .breadcrumbs import Breadcrumbs

#FOR MONKEY PATCHING ACTION WIDGETS
def htmlClass(self):
    return getattr(self.component, 'htmlClass', 'action btn')
   
class Form(BaseForm,Scripts,Breadcrumbs):
    title=""
    subTitle=""
    status = ""
    responseFactory = Response
    make_response = make_layout_response
    template = tal_template('form.pt')
    allowAnonymous = False
    submissionError = ""
    def __init__(self, context, request, **kwargs):
        BaseForm.__init__(self, context, request, **kwargs)
        self.__parent__ = context
        self.submissionErrors = []

    def breadcrumbs(self):
        return self.breadcrumbsManage()
    
    @property
    def action_url(self):
        url = self.relativeURL()+ "/"  + getattr(self,'crom.name')        
        return url
    
    def before(self,widget):
        field = widget.component._field
        result = ""
        if hasattr(field,"text"):
            result = field.text
        return result
        
    def widgetDictionary(self):
        return {c.htmlId():c for c in self.bootstrapWidgets()}

    def fieldDictionary(self):
        return {c.__name__:c for c in self.fields}    

    def isBool(self,widget):
        return widget.component._field._type==type(True)

    def isCheckBoxList (self,widget):
        return  widget.__class__.__name__=='MultiChoiceFieldWidget'
    
    def isMultiChoiceFieldWidget (self,widget):
        return  widget.__class__.__name__=='MultiChoiceFieldWidget'
    
    def useFormControl(self,widget):
        if self.isCheckBoxList(widget):
            return False
        if self.isMultiChoiceFieldWidget(self):
            return False
        if self.isBool(widget):
            return False
        return True
    
    def bootstrap_widgets(self):
        return self.bootstrapWidgets()
    
    def bootstrapWidgets(self):
        """Adds the needed css classes for bootstrap styles.
        """
        result = []
        for widget in self.fieldWidgets:
            if not self.useFormControl(widget):
               if "form-control" in widget.defaultHtmlClass:
                   widget.defaultHtmlClass.remove ("form-control")
            else:
                if not ('form-control' in widget.defaultHtmlClass):                               widget.defaultHtmlClass.append('form-control')
            widget.defaultHtmlClass = widget.defaultHtmlClass.copy()
            result.append (widget)
        return result

    def bootstrapActionWidgets(self):
           """Adds the needed css classes for bootstrap styles.
           """
           dolmen.forms.base.widgets.ActionWidget.htmlClass = htmlClass
           result = []
           for widget in self.actionWidgets:
               result.append (widget)
           return result





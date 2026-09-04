#Subject to the Zope and CV Licesnse

# SO HERE WE HAVE A CUSTOM TRAVERSER.
# IT TRAVERSES TO THE OBJECT AND LOOKS UP THE VIEW
# IT ALSO HANDLES CASES WHERE THE TEMPLATE IS LOOKED UP IN THE PARENTS
# SO IT IS A LITTLE BIT TRICKY, BUT MINIMAL ADAPTATION
# MAKES IT EASIER TO UNSERSTAND
from zope.interface.interfaces import ComponentLookupError
from copy import copy 
from dolmen.container import IBTreeContainer
from zopache.ttw.interfaces import ITemplate
from zopache.ttw.interfaces import IWebClass
from zopache.ttw.acquisition import webClassAcquire
from zopache.python.interfaces import IDirectory

class Traverser(object):
    def __init__(self,view_lookup):
        self.view_lookup=view_lookup
        self.zopacheTemplate = None

    def __call__(self,context,request,name,publisher):
        #A HACK TO FIX AN IURL PROBLEM
        if name == 'root':
            return context, None
        #FIRST, IF YOU HAVE A TEMPLATE, CHECK FOR A VIEW
        if self.zopacheTemplate != None :
           zopacheTemplate = self.zopacheTemplate
           try:
              view = self.view_lookup(request, zopacheTemplate, name)
           except ComponentLookupError:
              #This allows us to pass arguments in the URL after
              # the template name
              view = self.view_lookup(request, zopacheTemplate, 'index')
           
           if view == None :
              view = self.view_lookup(request, context, "not-found")
              view.slug = name
              return context, view

           if hasattr(view, 'setDisplayObject'):
                view.setDisplayObject(zopacheTemplate)           
                view.context=context  
                return context, view
           else:
                 raise Exception (
                     "%s does not support method setZopacheTemplate",
                                   zopacheTemplate.__name__)

        #TRAVERSE THE CONTAINER
        if (IBTreeContainer.providedBy(context) or
           IDirectory.providedBy(context)):

            item = context.get(name,object)
            if item != object:
                publisher.newContext(item)
                return item, None
            
        #NOW GET IT FROM THE WEBCLASS
        if hasattr(context, "webClass"):
               item =webClassAcquire(context,name,marker = object)
               if item != object:
                  if ITemplate.providedBy(item):
                     self.zopacheTemplate = item
                     return context,None
                  else:
                     publisher.newContext(item)                      
                     return item, None
        try:
           view = self.view_lookup(request, context, name)
           if view is not None:
               return context, view           
        except ComponentLookupError as e:
           view = self.view_lookup(request, context, "not-found")
           view.slug = name
           return context, view

 


        

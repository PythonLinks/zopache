from zope.location.location import LocationIterator
from zope.interface import Interface
from dolmen.container import IBTreeContainer
from zopache.ttw.interfaces import IWebClass
from zopache.core.getroot import getProducts

#MAYBE THE WEBCLASS IS A STRING OR A POINTER
def webClassAcquire(context,name, marker = object):
    if IBTreeContainer.providedBy(context) and name in context:
          return context[name]
    if hasattr(context, "webClass"):
        webClass = context.webClass
        if IWebClass.providedBy(context):
            webClass = context 
        elif isinstance(webClass, str):
            products = getProducts(context)
            if not webClass in products:
                return marker
            webClass = products[webClass]
        else:
            raise Exception("Something is Wrong")
        item = webClass.getFromWebClass (name,object)
        if item != object:
            return item
    return marker


# JUST  PARENTAL (NO ZCLASS) ACQUISITION OF OBJECTS IN CONTAINERS
class ParentalAcquire (object):
  def __init__(self,context):
      self.context=context
      
  def __getitem__(self,name,default=object) :
     context=self.context
     _marker = default  

     #FIRST SEE IF THIS ITEM HAS THE VALUE
     if hasattr(context, '__getitem__'):
            result =context.get(name, _marker)
            if result!=_marker:
               return result

     #IF NOT CHECK THE PARENT CLASSES
     for item in LocationIterator(self.context):
       if hasattr(item, '__getitem__'):
         result =item.get(name, _marker)
         if result!=_marker:
            return result

class Acquire(ParentalAcquire):
    pass







import json
from zope.interface import implementer

from dolmen.forms.base.errors import Error, Errors

from zopache.core import Leaf
from zopache.pages.content import ContentWithChildContent
from zopache.json.interfaces import IMultilingual,IMultilingualLeaf
from zopache.core.ancestors import Ancestors

class Base(object):

    def getLanguages(self,view):
        if getattr(view,'languages', False):
           return view.languages 
        try:
          header = view.request.headers["Accept-Language"]
        except:
          header = ['en']
        #header is "en,fr;0.3,de;0.5,en-uk"  
        languages = header.split(',')
        languages = [language.split(';')[0][:2] for language in languages]
        #Default Language
        languages.append ('en')
        view.languages = languages
        return languages
        
    def getFieldFor(self,view,field):    
       languages = self.getLanguages(view)
       json = self.json
       for lang in languages:
           if (data:= json.get(lang,None)) != None:
               if (text:= data.get(field,None)) != None:
                   return text        
       return None

    def getTitleFor(self,view):
        if (text := self.getFieldFor(view,'title'))!=None:               
            return text
        else:
           return "Error: No title, not even an blank title,  is available."
       
    @property
    def title(self):
        json = self.json
        if 'en' in json:
          return json['en']['title']
        else:
          return "No English title available"

    @property
    def source(self):
        json = self.json
        if 'en' in json:
          return json['en']['content']
        else:
          return "No English content available"              
      
    def getTitleForDomain(self,view):
        return self.getTitleFor(view)

    def getDescriptionFor(self,view):
        if (text := self.getFieldFor(view,'description'))!=None:               
            return text
        else:
           return "Error: No description, not even a blank  description,  is available."
    
    def getHtmlFor(self,view):

        if (text := self.getFieldFor(view,'content'))!=None:               
            return text
        else:
           return "Error: No content is available."            
            
    def partialPostProcess(self, view=None):
        pass

@implementer(IMultilingualLeaf)
class MultilingualLeaf(Base,Leaf):
    def postAddProcess(self, view = None):
        pass

@implementer(IMultilingual)
class Multilingual(Base,ContentWithChildContent,Ancestors):
    webClass = "Multilingual"    
    
    @property
    def description(self):
        json = self.json
        if 'en' in json:
          return json['en']['description']
        else:
          return "No English Description available"
      

    def getDescriptionForDomain(self,view):
        return self.getDescriptionFor(view)            
            


from zopache.zmi.interfaces import IURLSegment
import crom
@crom.adapter
@crom.sources(IMultilingualLeaf)
@crom.target(IURLSegment)
class IMulilingualLeafAdaptor(object):
    def __init__(self,context):
        self.context=context
    def getSegment(self):
        return 'ckedit'

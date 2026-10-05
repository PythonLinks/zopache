import json
from bs4 import BeautifulSoup

from zope.interface import implementer

from dolmen.forms.base.errors import Error, Errors

from zopache.core.viewdecorators import *
from zopache.core.interfaces import ITreeSecurity

from zopache.pages.content import ContentWithChildContent
from zopache.pages.page import Link

from zopache.business.addbyurl import ProcessURL

from zopache.json.editjsonschema import EditJson
from zopache.json.jsonproperties import BasicProperties
from zopache.json.interfaces import INewsLetter

@implementer (INewsLetter)     
class NewsLetter(BasicProperties,Link,ProcessURL):
    webClass = "Newsletter"
    title = ""
    description = ""
    def __init__(self):
        self.json = {
        }
        Link.__init__(self)
        
    def postAddProcess(self, view = None):
        errors = Errors()
        errors, response = self.fetchURL(self.originalURL,errors)
        if errors:
            return errors, {}
        self.processContent(self.originalURL,errors, response)
        
    def processContent(self,remoteURL,errors, response):
        soup = BeautifulSoup(response.content, 'html.parser')
        content =  soup.find(class_="available-content")
        uls = content.find_all ("ul")
        
        jVideos= []
        videos = uls [0]
        for item in videos:
              embed = str(item.find("iframe"))
              embed = embed.strip()
              embed = embed [:-10]
              embed = embed + ' class = "YouTubeVideo"></iframe>'
              jVideos.append({
                  "title": str (item.p.a.contents[0]),
                  "url":str(item.p.a['href']),
                  "description": str(item.p.contents[-1:][0]),   
                  "embed": embed
              })
        self.json["videos"] = jVideos
    
    def getTitleFor(self,view):
        try:
          return self.json["content"]["title"]
        except:
           return "Error: Please define at least one language."
       
    def getDescriptionFor(self,view):
        try:
          return self.json[0]["description"]
        except:
           return "Error: Please define at least one language."

    def getHtmlFor(self,view):
       try:
          return self.json[0]["content"]
       except:
           return "Error: Please define at least one language."              
    
from zopache.zmi.interfaces import IURLSegment
import crom
@crom.adapter
@crom.sources(INewsLetter)
@crom.target(IURLSegment)
class INewsletterAdaptor(object):
    def __init__(self,context):
        self.context=context
    def getSegment(self):
        return 'ckedit'

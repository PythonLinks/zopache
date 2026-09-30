import time
from slugify import slugify

from zope.interface import Interface
from zope import schema
from zope.interface import implementer
from dolmen.container import OrderedBTreeContainer

from zopache.pages.interfaces import IPage, ICategory
from zopache.pages.page import Page
from zopache.core.viewdecorators import *
from webpreview import web_preview
from zopache.remote.rssdownload import fetch
from zopache.remote.irss import IRSSArticle
from zopache.core.relatives import parentsWhichImplement

from zopache.crud.getimage import getImage
from zopache.remote.voteable import Voteable
from zopache.pages.page import Page    
from zopache.remote.news.mixin import NewsMixIn
from zopache.remote.mastodon.tootable import Tootable

class BaseArticle(NewsMixIn,Page,Tootable):    

    _category = ""
    importTime = 0
    lastTootTime = 0
    isArticle = True
    imageURL = ""
    description = ""
    emailApproved = True
    publicationApproved = False
    tags = {}
    delay = 0
    def __init__(self):
         #Simpler to not call page initialization.
         #HOPE I DO NOT MISS ANYTHING
         OrderedBTreeContainer.__init__(self)
         self.modificationTime= time.time()
         self.importTime = int(self.modificationTime)

    def defaultToot(self,view):        
        return (self.tootTitlePlusDescription() +    
                  self.tootArticleURL() +
                  self.tootVia(view) +
                  self.tootReadMore() )
                  
    def tagsAsString(self):
               return" ".join (self.tagsAsArray())

    def tagsAsHTML(self):
         if (len(self.tagsAsArray()) < 5):
               return "<br>".join (self.tagsAsArray())
         else:
               return " ".join (self.tagsAsArray())
           
    def tagsAsArray(self):       
               terms = set()
               for tag in self.tags:
                   term = tag["term"]
                   term = "#" + slugify(term)
                   if term not in {"#news","#featured"}:
                       terms.add (term)
               return terms 
            
    def getCategory(self):
      return self._category

    def setImportTime(self,publishedAt,root):
        importTime = int(publishedAt)

        while (True):
           importTime -= 1            
           if not root.hasAnythingAt(importTime):
                break;
        self.importTime = importTime
            

    def setCategory(self,value):       
        self._category = value
       
    def getSrcSet(self):
        pass
    
    def getDefaultThumbNailURL(self):
        pass

    def getCreationTime(self):
        return self.publishedAt

    def setCreationTime (self, aTime):
        self.__dict__['creationTime'] = aTime
        
    creationTime = property(getCreationTime,setCreationTime)

    def creationDateForHumans(self):
         return time.strftime("%Y-%m-%d",time.localtime(self.importTime))

   
    def moveTo(self,category):
              name = self.__name__
              del self.__parent__[name]
              category [name] = self
              self.__name__ = name
  
    def preProcess(self,view):
       pass
    def postProcess(self,view):
       pass
    def postAddProcess(self,view):
       pass
    def preDeleteProcess(self,view):
       pass

    

@implementer (IRSSArticle)
class RSSArticle(BaseArticle):
    webClass = "RSSLink"

    def titlePlusDescription(self):
        result = self.title + " "
        if self.description != None:
           result += self.description + " "
        result += self.parent.title + " "
        try:
            result += self.rssFeed.title
        except:
            pass
                  
        return result

    
    def creationDateForHumans(self):
         return time.strftime("%Y-%m-%d",time.localtime(self.publishedAt))
         
    def getAuthor(self,view ):
        author = self.rssFeed
        authorName = author.title
        authorURL = author.remoteURL
        if 'Logo' in author:
            imageURL = view.secureShortURL(context = author) + "/Logo"
        else:    
            topic = self.parent
            imageURL = view.secureShortURL(context = self) + "/Logo"
        return authorName, authorURL, imageURL

    def preDeleteProcess(self,view):
        #Page.preDeleteProcess(self,view)
        self.removeAllToots()
        localArticles = self.rssFeed.localArticles
        if hasattr(self,'permaLink'):
            if self.permaLink in localArticles:
                 del localArticles [self.permaLink]
            else:
                raise Exception("That article was not listed in localArticles.")
            
            


    def postAddProcess (self, view = None,article = None):
        if "exclusive for subscribers" in self.title.lower():
           self.webApproved = False
        


import json
import time
import datetime
from operator import methodcaller
import arrow

from cromlech.container.contained import Contained    
from zopache.pages.interfaces import ITime, IPage, IPageBase, ISiteRootPage
from zopache.core.getroot import getZodbRoot
from zopache.ttw.html import UntrustedHTMLBase
from zopache.core.relatives import parentsUpTo
from zopache.core import AllObjects
from zopache.application.allblogobjects import ProcessTree
from zopache.core.interfaces import ICountable
from cromlech.security import unauthenticated_principal as Anonymous
from zopache.pages.used import Used
from zopache.ttw.acquisition import ParentalAcquire

class Content(Used,
              AllObjects,
              UntrustedHTMLBase,
              Contained,
              ProcessTree):
    private = False
    branchSize =1
    webApproved = True
#    emailApproved = False
#    basePath = "/"
    createdBy = None
    editedBy = None
    
    def __init__(self):
         self.creationTime=time.time()
         self.modificationTime=self.creationTime

    def getAltText(self):
        image = self.getDefaultImage()
        if  not image:
            return ""
        if result := image._altText:
            return result
        return image.title

    def setAltText(self,text):
        image = self.getDefaultImage()
        if  not image:
            return
        image._altText = text

    altText = property(getAltText,setAltText)
    
    def myDict(self,view):
                
        myDict = {
            "name" : self.name,
            "title" : self.title,
            "description" : self.description,
            "parentName" : self.parent.name,
            "parentTitle" : self.parent.title,
            
            "articleURL" : (getattr(self,'articleURL',False) or
                           getattr(self,'remoteURL',False) or
                           ""),
            
            "tagsAsString" : (self.tagsAsString() if
                             (self.className()=='RSSArticle') else ''),

            "parentalTags" : ( self.parentalTags()
                             if (self.className()=='RSSArticle')
                             else ''),
                            
            "myURL" : view.secureShortURL(context = self),
            "parentalURL" : view.secureShortURL(context = self.parent)
        }
            
        if hasattr(self,"rssFeed"):
            rssFeed = self.rssFeed
            if hasattr(rssFeed,"twitterId"):
               myDict["twitterId"] =rssFeed.twitterId
        return myDict

    def myJSON(self,view):
        return json.dumps(self.myDict(view))

    #NORMALLY THIS WOULD BE IN THE TEMPLATE
    #BUT IT WAS NOT WORKING, SO I MOVED IT TO PYTHON. 
    def getScript(self,view):
        result = "<script>    "
        result += "data = JSON.parse(" 
        result += self.myJSON(view) + ");"
        result += "register(data);"
        result += "</script>"
        return result
    
    def noDashName(self):
        return self.name.replace('-','')
    
    def countMe (self):
        if not self.webApproved:
            return False
        if (ICountable.providedBy(self) or
             len (self.source) > 5):
            return True
        return False

    def countLeaves(self):
        total=0
        if self.countMe():   
            total += 1        
        for item in self.realChildCategories():
            if IPage.providedBy(item):
                    total+=item.countLeaves()
        self.branchSize=total
        return total    
    
    def listFutureEvents(self):
        result = []
        for item in self.allBlogObjects():
            if (ITime.providedBy (item)):
                now = datetime.datetime.now()
                if now < item.time: 
                   result.append(item)
        return result

                              
    #USED TO DISPLAY CHILDREN, BUT NOT HTML OBJECTS
    def childCategories(self):
        result =[]
        for item in self.values():
            if (IPageBase.providedBy (item) and item.webApproved):
               result.append (item)
        return result
    
    def canView(self,view):
        return True
        
    def postProcessCore(self,view=None):
        return

    def preProcess(self,view=None):
        siteRoot = view.getSiteRoot()
        if self.webApproved:
            siteRoot.unIndexItem(self)
        
    def postProcess(self,view=None):
        siteRoot = view.getSiteRoot()
        siteRoot.indexItem(self)        
        self.modificationTime=time.time()        
        self.postProcessCore(view = view)
        principal = view.request.principal
        if principal != Anonymous:
           name = view.request.principal.__name__
           try:
              name = int(name)
           except:
              pass
           self.editedBy = name
            
    def postAddProcess(self,view=None):
        self.postProcessCore(view=view)        
        principal = view.request.principal
        if principal != Anonymous:
           name = view.request.principal.__name__
           try:
              name = int(name)
           except:
              pass
           self.createdBy = name
        
        if ((self.__parent__ != None) and
            self.__parent__.private):
            self.private = True
            
        if not view.treeSecurity():
           view.notifyAdminsNewPage()
        
    def getZodbRoot(self):
        return getZodbRoot (self)
     
    def blogParents(self):
         return parentsUpTo(self,ISiteRootPage)

    def isCategory (self):
        return False
    
    def isPage (self):
        return True    

    def wikiPageChildren(self):
        for item in self.values():
            if IPageBase.providedBy(item):
                yield item                   
                  
    def hasContent(self):
         if len(self.source)<2:
            return False
         else:
            return True
           
    def editDateForSiteMap(self):
         return time.strftime("%Y-%m-%d",time.localtime(self.modificationTime))

    def editDateForHumans(self):
         return self.creationTime

    def sortedByName(self):
           unsortedList=[]
           for item in self.values():
               if IPage.providedBy(item):
                  unsortedList.append(item)
           aKey=methodcaller('getName')
           return sorted(unsortedList, key=aKey)

    def getName(self):
         return self.__name__
     
    def allValues(self):
        return self.values()

    def asDict(self,classes = ['Category']):
        new = dict()
        new["key"] = self.name
        new["title"] = self.title
        if len (self) > 0:
           children = []
           new["children"] = children
           #new["folder"] = true           
           for item in self.values():
               if item.__class__.__name__ in classes:
                  children.append(item.asDict(classes = classes))
        return new
    
    def age(self):
       return arrow.get(self.creationTime).humanize()[:-3]

    def editDateForRSS(self):
        return time.strftime("%a, %d %b %Y %H:%M:%S %z",
                time.localtime(self.modificationTime))

    def humanCreationDate(self):
        if (self.publishedAt == 0):
            return '-'
        return time.strftime("%Y-%m-%d",time.localtime(self.publishedAt))
    
    def getDefaultImage(self):
        if 'SocialMediaImage' in self:
            return self['SocialMediaImage']

        if 'Banner' in self:
            return self['Banner']

        if 'Logo' in self:
            return self['Logo']

        if hasattr(self,'rssFeed') and 'Logo' in self.rssFeed:
            return self.rssFeed['Logo']

        image = ParentalAcquire(self) ['Logo']
        if image:
            return image

        return None

from dolmen.container import OrderedBTreeContainer
class ContentWithChildContent(Content,OrderedBTreeContainer):
    def __init__(self):
         Content.__init__(self)
         OrderedBTreeContainer.__init__(self)

    def __delitem__(self,key):
        siteRoot = self.getPublicationRoot()
        item = self[key]
        siteRoot.unIndexItem(item)
        OrderedBTreeContainer.__delitem__(self,key)
        
    def __setitem__(self,  key,item):
        OrderedBTreeContainer.__setitem__(self,key,item)
        siteRoot = self.getPublicationRoot()     
        siteRoot.addItem(item)

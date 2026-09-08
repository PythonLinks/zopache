import json
import itertools
import time
import os
import datetime
from itertools import islice 

from pydoc import locate
from operator import methodcaller
from dolmen.container import BTreeContainer
from BTrees.OOBTree import OOBTree
from zopache.pages.interfaces import (ITime,IContent,IPage ,IPageBase, 
                                      ISiteRootPage,
                                      IRootPage,
                                      INews,
                                      ICategory)

from zopache.core.getroot import getZodbRoot
from zopache.ttw.html import UntrustedHTMLBase
from dolmen.container import OrderedBTreeContainer
from cromlech.container.contained import Contained
from zope.interface import implementer
from zopache.ttw.interfaces import IBranch
from zopache.ttw.branch import Branch
from zopache.core.relatives import parentsUpTo
from zopache.core.ancestors import Ancestors
from zopache.pages.cache import cache, PageMixIn, RecentMixIn
from zopache.core import AllObjects
from zopache.application.allblogobjects import ProcessTree, AllBlogObjects
from collections import defaultdict
from zopache.core.interfaces import ICountable
from cromlech.security import unauthenticated_principal as Anonymous
from zopache.pages.interfaces import ILink
from zopache.ttw.branch import Branch
from zopache.core.relatives import parentsWhichImplement
from zopache.core.relatives import Parents
from zopache.pages.used import Used
from zopache.remote.news.mixin import NewsMixIn

class PageVeryBase(Used,AllObjects,OrderedBTreeContainer,UntrustedHTMLBase,Contained,ProcessTree):
    private = False
    branchSize =1
    webApproved = True
    emailApproved = False
    basePath = "/"
    createdBy = None
    editedBy = None
    def __init__(self):
         OrderedBTreeContainer.__init__(self)
         self.creationTime=time.time()
         self.modificationTime=self.creationTime

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
        self.partialPostProcess(view=view)
        cache.resetCache(self)

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
        
    def recalculateRootJSON(self):
         jsonRoot = self.getPublicationRoot()
         if jsonRoot:
            jsonRoot.setJson()
    
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

    def __delitem__(self,key):
        siteRoot = self.getPublicationRoot()
        item = self[key]
        siteRoot.unIndexItem(item)
        OrderedBTreeContainer.__delitem__(self,key)
        
    def __setitem__(self,  key,item):
        OrderedBTreeContainer.__setitem__(self,key,item)
        siteRoot = self.getPublicationRoot()     
        siteRoot.addItem(item)
                  
    def hasContent(self):
         if len(self.source)<2:
            return False
         else:
            return True
           
    def editDateForRSS(self):
         return time.strftime("%a, %d %b %Y %H:%M:%S %z",time.localtime(self.modificationTime))

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
    
    
    
class PageBase(PageVeryBase,PageMixIn,Ancestors):
    title = ''
    description = ''
    source = ''

    def sortedByTitle(self):
           unsortedList=[]
           for item in self.values():
               if IPage.providedBy(item):
                  unsortedList.append(item)
           aKey=methodcaller('getTitle')
           return sorted(unsortedList, key=aKey)

    
    def partialPostProcess(self, view=None):        
        self.description=self.description.replace ('"' , "&ldquo;", 1)
        self.description=self.description.replace ('"' , "&rdquo;", 1)
        self.description=self.description.replace ('"' , "&ldquo;")
        self.description=self.description.replace ('\n' , " ")
        self.description=self.description.replace ('\r' , " ")                

        self.title=self.title.replace ('"' , "&ldquo;", 1)
        self.title=self.title.replace ('"' , "&rdquo;", 1)
        self.title=self.title.replace ('"' , "&ldquo;")
        self.title=self.title.replace ('\n' , " ")
        self.title=self.title.replace ('\r' , " ")                

    
    def getAuthor(self,view):
        topic = self.parent
        topicName = topic.name
        topicName = "UncensoredNews.US" + "/" + topicName
        topicURL = view.secureShortURL(context = topic) 
        imageURL = topicURL + "/Logo"
        return topicName,topicURL, imageURL
    
    
@implementer (IPage)     
class Page(PageBase, PageMixIn):
    webClass='WikiPage'
    icon="ttwicons/WikiPage.png"
    
@implementer (ILink)     
class Link(NewsMixIn,PageBase, PageMixIn):
    webClass='Link'
    icon="ttwicons/WikiPage.png"
    tags = {}
    isArticle = True
    publicationApproved = True
    
    def preDeleteProcess(self,view):
        self.removeAllToots()

    def defaultToot(self,view):        
        return (self.tootTitlePlusDescription() +    
                  self.tootArticleURL() +
                  self.tootVia(view) +
                  self.tootReadMore() )

    def tootArticleURL(self):
            return self.remoteURL + "\n\n" 
    
    def getImportTime(self):
        return self.creationTime
    importTime = property (getImportTime)

    def tagsAsString(self):
        return ""
    
    def tagsAsHTML(self):
        return ""
    
from zopache.core.interfaces import ISiteRoot
from zopache.pages.cache import Cache
@implementer(ISiteRoot)
class SiteRoot(Branch,PageBase,PageMixIn):
    webClass = 'HomePage'
    appName = "A New Forest Wiki Application"
    homePage = ''
    googleClientId = ""
    localLogin = False
    mastodonLogin = True
    subscribeSlug = ""
    twitterId = ""

    def preProcess(self,view=None):
        pass
        
    def __init__(self):
       Branch.__init__(self)
       PageBase.__init__(self)
       cache = Cache()

    def setJson(self):
         #self.json=self.jsonTree(0)
         pass

#USED ON GREEN MAPS         
@implementer(IRootPage)
class RootPage(SiteRoot):
    twitterId = ""
    mqttServer = ""
    def getSiteRootFor(self,hostName):
        return self

    def delAttribute(self, name):
        if name in self.__dict__:
            del self.__dict__[name]
            self._p_changed = True


#FOR MULTIPLE SITES
@implementer(ISiteRootPage)         
class SiteRootPage(SiteRoot):
    twitterId = ""
    mqttServer = ""
    mapBoxKey =""
    
    def __init__(self):
       from zopache.ttw.principalfolder import PrincipalFolder
       Page.__init__(self)
       Branch.__init__(self)
       self ["person"] = PrincipalFolder()

    def getSiteRootFor(self,hostName):
        return self    


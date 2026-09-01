#FOR INDEXING THIS USES pylons/hypatia.
#Not that well documented.  You may want to read
#https://github.com/repoze/repoze.catalog/blob/master/docs/usage.rst

import time
import random
import sys
from zope import schema
from zope import interface

from hypatia.catalog import Catalog
from hypatia.field import FieldIndex
from hypatia.text import TextIndex
from hypatia.keyword import KeywordIndex

from hypatia.text.htmlsplitter import HTMLWordSplitter

from hypatia.text.lexicon import (
    CaseNormalizer,
    Lexicon,
    Splitter,
    StopWordRemover,
    )

lexicon = Lexicon(
                  HTMLWordSplitter(),
                  Splitter(),
                  CaseNormalizer(),
                  StopWordRemover())

from zope.interface import Interface
from zope.schema.interfaces import IField
from zope.interface import implementer
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree

from cromlech.browser.interfaces import IPublicationRoot
from dolmen.container import BTreeContainer, OrderedBTreeContainer
from dolmen.container import IBTreeContainer

from zopache.pages.interfaces import IPage, IPageBase, ILocation
from zopache.ttw.interfaces import ICanonical
from zopache.ttw.interfaces import (IBranch,
                                    IWebClass,
                                     IProducts,
                                     IInternalPrincipal)

from zopache.remote.ivideo import IVideo
from zopache.ttw.interfaces import  ICanonical
from zopache.pages.interfaces import ICategory, IImaginary
from zopache.business.interfaces import IOrganization, IOnlineOrganization
from zopache.pages.interfaces import ILocationContainer
from zopache.core.relatives import parentsWhichImplement

#THIS ONE SUBCLASSES OFF OF BTREE CONTAINER
@implementer(IBranch)
class SimpleBranch(object):
    branchSize = 0
    def __init__(self):
       self.valuesByToken = OOBTree()
       
    def addItem(self,item):
        self.indexItem(item,itemType = ICanonical)
        
    def deleteItem(self,item):
       self.unIndexItem(item)

    def indexTree(self):
        self.valuesByToken=OOBTree()
        self.indexBranch(self,self)

    def __contains__(self, key):
        return (key in self._data  or 
                key in self.valuesByToken)

    def __delitem__(self, key):
        self.unIndexItem(key)
        BTreeContainer.__delitem__(self,key)
        if key in self.valuesByToken:
                self.valuesByToken.__delitem__(key)
    
    def __getitem__(self, name):
        result = self._data.get(name)
        if result != None:
            return result
        result = self.valuesByToken.get(name)
        if result != None:
            return result
        if name == self.name:
            return self
        return None
    
    def get(self,name,default=None):
      if name in self:
         return self[name]

      if name in self.valuesByToken:
          return self.valuesByToken[name]

      if "." in name:
          words = name.split(".")
          if words[0] in self.valuesByToken:
             context = self
             length = len(words)
             context = self.get(words[0],default = object)
             for index in range(1,length):

                 shortName = words[index]
                 context = context.getImaginary(shortName,default = default)
                 if context == default:
                     return default
             return context
      
      # IF ALL ELSE FAILS
      return default

#THIS ONE SUBCLASSES OFF OF ORDERED CONTAINER  
@implementer (IBranch)
class Branch(SimpleBranch):

    def __init__(self):
        SimpleBranch.__init__(self)
        self.reInit()

    def mostRecentlyCuratedRSSArticle(self):
        for item in self.contentByTime.values():
            if item.__class__.__name__ == 'RSSArticle':
               if item.publicationApproved:
                   return item
        return None

    def mostRecentlyAddedLink(self):
        for item in self.contentByTime.values():
            if item.__class__.__name__ == 'Link':
               if item.publicationApproved:
                   return item
        return None    
    
    def reInit(self):
        self.rssFeeds = OOBTree() 
        self.valuesByToken=OOBTree()
        self.remoteURLs = OOBTree()
        self.pagesByTwitterId = OOBTree()
        self.globalArticles = OOBTree()
        self.contentByTime = IOBTree()        
        self.tootedArticles = IOBTree()
        
        contentCatalog = Catalog()
        contentCatalog['importTime'] = FieldIndex('importTime')
        contentCatalog['isVideo']=FieldIndex('isVideo')
        contentCatalog['recommended']=FieldIndex('recommended')
        contentCatalog['titlePlusDescription']=TextIndex(
                                  'titlePlusDescription',
                                 lexicon = lexicon)

        contentCatalog['ancestorNames']=KeywordIndex('ancestorNames')
        self.contentCatalog = contentCatalog
        
        categoryCatalog = Catalog()
        categoryCatalog['titlePlusDescription']=TextIndex(
                               'titlePlusDescription')
        self.categoryCatalog = categoryCatalog

    @property    
    def nextImportTime(self):    
        lastImportTime = - int  (self.contentByTime.minKey()) 
        currentTime = int(time.time())
        return max (currentTime,lastImportTime + 1)

    def __delitem__(self, key):
        item = self[key]
        self.unIndexItem(item)
        OrderedBTreeContainer.__delitem__(self,key)
                
    def urlOnly(self,link):
       if link.startswith('http://'):
          link = link[7:]
       elif link.startswith('https://'):
           link = link[8:]
       return link
   

    def existsRemoteURL(self,link):
       if link == "":
           return False
       link = self.urlOnly(link)
       return self.remoteURLs.get(link,False)
   
    def addRemoteURL(self,anObject,remoteURL):
       if anObject.__class__.__name__  == "RemoteAccount":               
           return
       link = self.urlOnly(remoteURL)
       if link == "":
           return
       if link in self.remoteURLs:
          print(link) 
          print ("DUPLICATE URLs", anObject.name,
                 self.existsRemoteURL(remoteURL).name)
          
          pass
       else:
          self.remoteURLs[link] = anObject 
           
    def deleteRemoteURL(self,link):
        if link == "":
            return
        link = self.urlOnly(link)
        
        #Temporary RemoteAccountFix, best to remove. 
        if not link in self.remoteURLs:
            return
        del self.remoteURLs[link]

            
    def getUniqueNumberString(self):
        anInteger = random.randint (1,sys.maxsize)        
        while (True):
            if anInteger == sys.maxsize:
                anInteger = 10000
            anInteger += 1
            newName = str(anInteger)
            if not newName in self:
                return newName
            
       
    #def test(self,item):
    #    if IBTreeContainer.providedBy(item):
    #       return True
    #    return False

    def indexTree(self):
        self.reInit()
        self.indexBranch(self,self)
        
    def indexBranch(self,tree,branch,itemType=ICanonical, ancestorNames = tuple()):
        ancestorNames = ancestorNames + (branch.name,)
        
        if IImaginary.providedBy(branch):
            return

        for item in branch.values():

            if itemType.providedBy(item):
                self.indexItem(item,
                               itemType = itemType,
                               ancestorNames = ancestorNames,
                               indexingBranch = True)
                if IBTreeContainer.providedBy(item):
                        self.indexBranch(tree,
                                         item,
                                         ancestorNames = ancestorNames)

    def addTootedArticle(self,article):
        if len(article.toots) > 0:
            self.tootedArticles[int(article.importTime)] = article
            
    def indexItem(self,item,
                  itemType=ICanonical,
                  ancestorNames = [],
                  indexingBranch = False):
            
        if not ICanonical.providedBy(item):
            return

        self.valuesByToken[item.__name__] = item
        
        #Unless WebApproved, return.
        if not getattr(item,'webApproved',True):
                   return

        if getattr(item,'remoteURL',None):
            self.addRemoteURL(item,item.remoteURL)
            
        if getattr(item,'articleURL',None):
            self.addRemoteURL(item,item.articleURL)
            
        if ancestorNames == []:
           if item.parent:
               ancestorNames = item.parent.ancestorNames 

        if ILocationContainer.providedBy(item):
           if indexingBranch:
               item.mapPoints =  OOBTree()
                                                                     
        match item.__class__.__name__:
            case "Category":
               item.reInit()

            case "RegionalCategory":
               item.reInit()           

            case "RSS":
               self.indexRSS(item)
           
            case "JustRSS" :
               self.indexRSS(item)           

            case "JSONMarkdown":
                importTime = int(item.creationTime)
                self.contentByTime[importTime] = item
                proxy = MarkdownProxy(item)
                self.contentCatalog.index_doc(importTime,proxy)
            
            case "RSSArticle":
                importTime = int(item.importTime)
                self.addTootedArticle(item)
                self.contentByTime[importTime] = item
                self.catalogContent(item,ancestorNames)
                self.globalArticles [item.permaLink] = item

            case "Article":
                self.addTootedArticle(item)
                self.contentByTime[item.importTime] = item
                self.catalogContent(item,ancestorNames)
                    
            case 'Link':
                importTime = int(item.importTime)
                self.addTootedArticle(item)
                self.contentByTime[importTime] = item
                self.catalogContent(item,ancestorNames)
                
            case _ if IVideo.providedBy(item):
               self.contentByTime[ int(item.importTime)] = item
               self.catalogContent(item,ancestorNames)
               
            case _ if ILocation.providedBy(item):
                if item.__class__.__name__ =='Politician':
                   if not (hasattr(item, 'candidateInfo') or
                            hasattr(item, 'electedOfficial')):
                            return
                for organization in (
                    parentsWhichImplement(
                    item,ILocationContainer)):
                    #This is a hack.  For some unknown reason
                    #IlocationContainer is providedBy CountryPostalCodes. 
                    if (organization.__class__.__name__ !=
                        "CountryPostalCode"):
                        organization.mapPoints[item.name] = item
 
    def indexRSS(self,item):        
       self.rssFeeds[item.name] = item 
       for category in parentsWhichImplement(item,ICategory):
           category.childFeeds += 1
        #self.categoryCatalog.index_doc(
        #        self.recordCategory(item),
        #        item)               

                   
    def catalogContent(self,item,ancestorNames):
        proxy = Proxy(item,ancestorNames)
        self.contentCatalog.index_doc(int(item.importTime),proxy)

    def unCatalogContent(self,item):
        self.contentCatalog.unindex_doc(int(item.importTime))

    def hasAnythingAt(self,importTime):
        result = self.contentCatalog['importTime'].apply((-importTime,-importTime))
        return len(result) 
    
    def unIndexItem(self,item, itemType=IPage):
        if not IPageBase.providedBy(item):
            return
        
        if not item.__name__ in self.valuesByToken: 
           return

        del self.valuesByToken[item.__name__]
       
        if not getattr(item,'webApproved',True): 
                   return

        if getattr(item,'remoteURL',None):
            self.deleteRemoteURL(item.remoteURL)

        if getattr(item,'articleURL',None):
            self.deleteRemoteURL(item.articleURL)

        match item.__class__.__name__:
            # Category, RegionalCategory, RSS
            # Do nothing
            
            case "RSS":
               self.unindexRSS(item)

            case "JustRSS":
               self.unindexRSS(item)           
           
            case "JSONMarkdown":
                importTime = int(item.creationTime)
                if importTime in self.contentByTime:
                   del self.contentByTime[importTime]
                self.unCatalogContent(item)
            
            case "RSSArticle":
                globalArticles = self.globalArticles
                importTime = int(item.importTime)             
                if importTime in self.tootedArticles:
                   del self.tootedArticles[importTime]                         
                if importTime in self.contentByTime:
                   del self.contentByTime[importTime]
                if item.permaLink in globalArticles:
                    del globalArticles [item.permaLink]
                self.unCatalogContent(item)

            case "Article":
                importTime = item.importTime
                if importTime in self.tootedArticles:
                   del self.tootedArticles[importTime]                         
                if importTime in self.contentByTime:
                   del self.contentByTime[importTime]
                self.unCatalogContent(item)            
           
            case 'Link':
                importTime = int(item.importTime)
                if importTime in self.tootedArticles:
                   del self.tootedArticles[importTime]             
                del self.contentByTime[int(item.importTime)]
                self.unCatalogContent(item)
            case _ if IVideo.providedBy(item):
                del self.contentByTime[int(item.importTime)]
                self.unCatalogContent(item)

            case _ if IOrganization.providedBy(item):
                if item.__class__.__name__=='Politician':
                  if not (hasattr(item, 'candidateInfo') or
                     hasattr(item, 'electedOfficial')):
                     return
             
                if (item.__class__.__name__ != 'OnlineOrganization'):
                   for organization in (
                        parentsWhichImplement(
                            item,ILocationContainer)):
                        # A Hack, described above. 
                        if (organization.__class__.__name__ !=
                            "CountryPostalCode"):
                            del organization.mapPoints[item.name]

    def unindexRSS(self,item): 
           del self.rssFeeds[item.name]
           for category in parentsWhichImplement(item,ICategory):
               category.childFeeds -= 1
           #self.categoryCatalog.unindex_doc(item.importTime)           
           #ERROR

                       
    def checkName(self, name, object):
        """See zope.container.interfaces.INameChooser
        """
        if not name:
            raise ValueError(
                _("An empty name was provided. Names cannot be empty.")
                )

        if name[:1] in '+@' or '/' in name:
            raise ValueError(
                _("Names cannot begin with '+' or '@' or contain '/'")
                )

        if name in self:
            raise KeyError(
                _("The given name is already being used")
                )

        return True


    def chooseName(self, name, object):
        """See zope.container.interfaces.INameChooser
        """

        container = self

        # convert to unicode and remove characters that checkName does not allow

        name = name.replace('/', '-').lstrip('+@')

        if not name:
            name = unicode(object.__class__.__name__)

        # for an existing name, append a number.
        # We should keep client's os.path.extsep (not ours), we assume it's '.'
        dot = name.rfind('.')
        if dot >= 0:
            suffix = name[dot:]
            name = name[:dot]
        else:
            suffix = ''

        nm = name + suffix
        i = 0
        while nm in container:
            i += 1
            nm = name + u'-' + str(i) + suffix

        # Make sure the name is valid.  We may have started with something bad.
        self.checkName(nm, object)

        return nm

#USED TO NOT RECALCULATE ancestorNames EACH TIME.    

from zopache.remote.ivideo import IVideo
class Proxy(object):
    def __init__(self,target,ancestorNames):
        self.target = target
        self.ancestorNames = ancestorNames
    
    @property
    def isArticle(self):
       return self.target.__class__.__name__ in [ "RSSArticle",
                                                  "Link",
                                                  'Article']
    @property
    def importTime(self):
        importTime = self.target.importTime
        return - int(importTime)        

    @property
    def isVideo(self):
       return IVideo.providedBy(self.target)
   
    @property
    def recommended(self):
        return (IVideo.providedBy(self.target) or
                getattr(self.target,'publicationApproved', False))
    
    @property            
    def titlePlusDescription(self):
        result =self.target.titlePlusDescription()
        if getattr(self.target,'toots',[]):
           result += 'Via: ' + self.target.getVia()
        return result

class MarkdownProxy(object):
    isArticle = False
    isVideo = False
    recommended = True
    
    def __init__(self,target):
        self.target = target

    @property
    def importTime(self):
        creationTime = self.target.creationTime
        return - int(creationTime)        
        
    @property            
    def titlePlusDescription(self):
        result = self.target.titlePlusDescription()
        result += ""
        result += self.target.source
        return result

@implementer(IPublicationRoot)       
class Root (Branch):
   pass

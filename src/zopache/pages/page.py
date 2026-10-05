from operator import methodcaller
from zopache.pages.interfaces import IPage, ISiteRootPage, IRootPage, ILink
from zope.interface import implementer
from zopache.ttw.branch import Branch
from zopache.core.ancestors import Ancestors
from zopache.remote.mastodon.tootable import Tootable
from zopache.remote.news.mixin import NewsMixIn
from zopache.pages.content import ContentWithChildContent

class PageBase(ContentWithChildContent,Ancestors):
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
class Page(PageBase):
    webClass='WikiPage'
    icon="ttwicons/WikiPage.png"
    
@implementer (ILink)     
class Link(NewsMixIn,PageBase,  Tootable):
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
                  self.tootReadMore(view) )

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
@implementer(ISiteRoot)
class SiteRoot(Branch,PageBase):
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

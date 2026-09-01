import time
import asyncio
import feedparser

from dolmen.forms.base.markers import FAILURE, SUCCESS

from zopache.remote.irss import  IRSSBase
from zopache.core.interfaces import ITreeSecurity
from zopache.core.viewdecorators import *
from zopache.core.baseform import Form
from zopache.remote.rssdownload import fetchAll
from zopache.pages.interfaces import ISiteRootPage, IPageBase
from zopache.crud.getimage import createImageInFrom
from zopache.core.interfaces import ITreeSecurity
from zopache.remote.rssarticle import IRSSArticle, RSSArticle
from itertools import islice
from cromlech.browser.exceptions import HTTPFound


@form_component
@context(IPageBase)
@crom.target(IView)
@name("getrssxyz")
#@permissions('Manage')
#@implementer(ITreeSecurity)
class GetRSS(Form):
    title = "Download the RSS Feeds"
    subTitle = "To get the newest news."

    def __init__(self, context, request, **kwargs):
        Form.__init__(self, context, request, **kwargs)
        self.time = self.getSiteRoot().nextImportTime
        self.lock = None

    async def getTime(self):
        lock = asyncio.Lock()
        async with lock:
            self.time += 1
            return self.time
        
    def update(self):
        leaves = self.getSiteRoot().rssFeeds.values()        
        self.updateCore(leaves)
        
    def updateCore(self,leaves):    
        feeds = []
        print ("Leaves = ",(leaves))
        for item in leaves:
               if IRSSBase.providedBy(item):
                  if item.rssApproved:   
                      feeds.append(item)
        self.fetchArticles(feeds)
        root = self.getSiteRoot()
        root.lastRSSFetchTime = time.time() 
        #if hasattr(root,'lastFetchTime'):
        #    del root.lastFetchTime
            
        Form.update(self)
        #raise HTTPFound('/categories/newest')

    #COPY OF THIS HERE AND IN RSS.PY
    #This one has no view argument, just uses self
    def fetchArticles(self, feeds):

        result = fetchAll(feeds,self)
        for item in result:
              if item[0] ==  FAILURE:  
                 self.submissionErrors.append( "ERROR:" + str(item [1:]))
        self.status='RSS Feeds were downloaded.'

@form_component
@context(IPageBase)
@crom.target(IView)
@name("fetch")
@permissions('Manage')
@implementer(ITreeSecurity)
class GetJustOneRSSFeed(GetRSS):
    def update(self):
        leaves = [self.context]
        self.updateCore(leaves)

 
from cromlech.browser.interfaces import IPublicationRoot
          
@form_component
@context(ISiteRootPage)
@crom.target(IView)
@name("getImages")
@permissions('Manage')
@implementer(ITreeSecurity)
class SiteRootGetImages(Form):
    title = "Download the Article Images"
    subTitle = "To get the newest pictures."
            
    def update(self):
        callTwice(self)
        callTwice(self)
        self.status='Images were downloaded.'
        Form.update(self)


@form_component
@context(IRSSBase)
@crom.target(IView)
@name("getImages")
@permissions('Manage')
@implementer(ITreeSecurity)
class GetImages(Form):
    title = "Download the Article Images"
    subTitle = "To get the newest pictures."
            
    def update(self):
        articles = list(self.context.values())
        callTwiceCore(self,articles)
        callTwiceCore(self,articles)
        self.status='Images were downloaded.'
        Form.update(self)
        

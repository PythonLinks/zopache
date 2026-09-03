import time
from html import unescape

from slugify import slugify
import feedparser

from zope import schema
from zope.interface import Interface

from dolmen.forms.base.markers import FAILURE, SUCCESS

from zopache.pages.page import Link
from zopache.core.viewdecorators import *
from zopache.crud.interfaces import IContainer
from zopache.core.uniquename import UniqueName
from BTrees.OOBTree import OOBTree
from zopache.pages.interfaces import ILink
from zopache.remote.rssarticle import RSSArticle
from bs4 import BeautifulSoup
from zopache.remote.irss import IRSS, IJustRSS
from zopache.remote.rssdownload import fetchAll
from zopache.crud.getimage import getImage

class RSSBase(object):
    
    def parseHTML(self,html,maxLength = 300):
        soup = BeautifulSoup(html, 'html.parser')
        try:
           text = soup.text
           length = len(text)
           if length <= maxLength:
              return text
           else:
              for i in range(maxLength,length):
                  if text[i]==' ':
                     result = text [0:i-1] +  '...'
                     return result
        except:
           return ""
          
   
    def postAddProcess(self,view = None):
        Link.postAddProcess(self,view = view)
        if self.logoURL:
            getImage(self,self.logoURL)
        self.fetchArticles([self],view)

    #COPY OF THIS HERE AND IN RSSFetch.PY
    #AND IN mastodon/fetch.py
    #That one has no view argument.
    def fetchArticles(self,feeds,view):    
        result = fetchAll(feeds,view)
        for item in result:
            if item[0] ==  FAILURE:  
               view.submissionErrors.append( "ERROR:" + str(item))
        self.status='RSS Feeds were downloaded.'
        
@implementer (IRSS)     
class RSS(Link,UniqueName,RSSBase):
    webClass = "RSS"
    htmlSummary = True
    title = ""
    twitterId = ''
    mastodonId = ''
    rssApproved = True
    keepAllArticles = False

    # FOR A NEW RSS FEED       
    def createOneArticle(self,article,view,currentTime):
       new = RSSArticle()
       new.articleURL = article.link
       if hasattr(article, 'tags'):
           new.tags = article.tags
       unescaped = unescape (article.title)
       result  = self.parseHTML(unescaped)
       new.title = result

       if hasattr(article,'summary'):
           unescaped = unescape( article.summary)
           result  = self.parseHTML(unescaped)
           new.description = result or unescaped or ''
       
       if hasattr(article, 'updated_parsed'):
          new.updated = article.updated_parsed

       if 'image' in article:      
           new.image = article.image

       if 'links' in article:
           new.links = article.links
           
       theId = article['id']
       new.permaLink = theId
       if hasattr(article,"published_parsed"):
          new.publishedAt = min(
                            time.mktime( article["published_parsed"]),
                            currentTime)
       else:
          new.publishedAt = currentTime
          
       #WHEN CREATING A NEW FEED ARTICLES GO AT THEIR PROPER TIME
       #PREVENTS BUNCHING THEM UP.
       new.setImportTime(new.publishedAt,view.getSiteRoot())
       new.__parent__ = self
       new.rssFeed = self          
       newName = slugify (new.title)
       newName = self.uniqueBothName (self,newName)
       self[newName] = new

       #LocalList
       self.localArticles[theId] = new

       new.postAddProcess(view = view ,article = article)
       return new
    
    def __init__(self):
         self.localArticles = OOBTree()
         Link.__init__(self)

    def removeOldArticles(self):
           articles = []
           if self.keepAllArticles:
               return
           for value in self.values():
               if value.__class__.__name__ == "RSSArticle":               
                   articles.append(value)

           for article in articles[0:-4]:    
               article.preDeleteProcess(self)
               del article.parent [article.name]
               
    """
    REMOVES ARTICLES LISTED IN localArticles, but which has no parent. 
    should be an empty set.

    Has not yet been tested, so commented out. 
    def clearOrphans(self):           
           orphans = []    
           for articlein self.localArticles.values():
               if article.parent == None:
                   orphans.append(article.permalink)
           for key in orphans:
               p rint (key)
               del context.localArticles [key]
    """
         
    async def createArticles(self,entries,view):
       currentTime = int(time.time()) 
       root =  self.getPublicationRoot()
       globalArticles= root.globalArticles
       articles = []
       for article in entries[:20]:
           theId = article['id']
           if theId in globalArticles:
               continue
           if root.existsRemoteURL(article.link):
               continue
           new = self.createOneArticle(article,view,currentTime)
           articles.append(new)
       return SUCCESS, articles, len(entries)
   
    def postProcess(self,view = None):
        Link.postProcess(self, view = view)

    async def processResponse(self, session, response,view):
          html  =  await response.text()
          feed = feedparser.parse(html)
          entries = feed['entries']
          return await self.createArticles(entries,view)
          
@implementer(IJustRSS)
class JustRSS(RSS):
    interface = IJustRSS
    
    def postProcess(self,view = None):
        return

    def postAddProcess(self,view = None):
        return
    
    @property
    def title(self):
        return self.parent.title + " RSS Feed"
    
    @property
    def description(self):
        return "This is the RSS feed for " + self.parent.title


    @property
    def remoteURL(self):
        return self.parent.remoteURL
    
import crom
from zopache.zmi.interfaces import IURLSegment
@crom.adapter
@crom.sources(IRSS)
@crom.target(IURLSegment)
class IRSSAdaptor(object):
    def __init__(self,context):
        self.context=context   

    def getSegment(self):
        return 'manage'


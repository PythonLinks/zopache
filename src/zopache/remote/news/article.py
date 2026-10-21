import re
from urllib.parse import urljoin, urlparse
from slugify import slugify
from inspect import currentframe, getframeinfo
from bs4 import BeautifulSoup
from webpreview import web_preview
from zope.interface import implementer

from dolmen.forms.base.markers import FAILURE, SUCCESS

from zopache.pages.page import Link
from zopache.remote.rssdownload import fetch, HTML_ACCEPT
from zopache.crud.getimage import createImageInFrom
from zopache.remote.news.interfaces import IArticle
from zopache.remote.mastodon.tootable import Tootable

REGEXP = re.compile(r"^\s*project\s+website\s*$", re.IGNORECASE)

@implementer(IArticle)
class Article (Link, Tootable):
    webClass = "RSSLink"
    toots = None
    importTime = 0
    description = ''
    title = ''
    __name__ = ''

    #This has to be here, otherwise link version overrides it. 
    def tootArticleURL(self):
        return self.articleURL + "\n\n"
                
    
    def __init__(self, toot, url, account, mastodonArticles,root):
        Link.__init__(self)
        self.toots = []
        if 'red' in toot.tags:
            self.red = True
        if 'yellow' in toot.tags:
            self.yellow = True

        self.articleURL = url

        hostName = urlparse(url).hostname
        domainName = account.domainName
        if domainName and (domainName in hostName):
           self.webApproved = False
        self.parent = root.get(
           account.defaultCategory,
           mastodonArticles)
    
    def titlePlusDescription(self):
        return (self.title + ' ' +
                self.description)
        
    def preDeleteProcess(self,view):
        if hasattr(self,'toots'):
            for toot in self.toots:
                toot.removeArticle(self)
                self.toots = []
    
    async def processResponse(self, session, response,view):
        try:
            contentType = response.headers.get('content-type').lower()
        except:
           return FAILURE, self, "ContentType was not defined." 

        if 'text'in contentType:
           return await self.processTextResponse(
              session, response,view)
        elif 'image' in contentType:
           result =   await self.processImageResponse(session,
                                                      response,
                                                      view)
           return result
        else:
          frameinfo = getframeinfo(currentframe())
          return (FAILURE,
                  (frameinfo.filename + ' ' +
                  str(frameinfo.lineno) + ' ' +
                  contentType),
                  self)

    async def processImageResponse(self,session, response, view):
        try:
            content =  await response.content.read()
            contentType = response.headers['content-type']
            createImageInFrom(self,content, contentType, 'Logo')
            print ("*",end = "")
            return SUCCESS, self
        except Exception as e:
          return (FAILURE,
                  ("Error processing Image response in Article " +
                   str(e)),
                   self)

    def extractProjectURL(self,html):
        soup = BeautifulSoup(html, "html.parser")
        self.articleURL = None
        for anchor in soup.find_all("a", href=True):
            text = anchor.get_text().strip()
            if REGEXP.match(text):
                self.articleURL = anchor["href"]
                #Last one wins, unlikely bug.
                
    async def processTextResponse(self, session, response,view):
        try:
            html  =  await response.text()
        except Exception as e:
            return  (FAILURE,
                     f"Failed to fetch {self.articleURL}" +
                     " " + str(e))
          
        if urlparse(self.articleURL).hostname == "certification.oshwa.org":
             self.extractProjectURL(html)
             if not self.articleURL:
                 return (FAILURE,
                       "The OSHWA page did not have a project url ")

             try:
                 async with session.get(self.articleURL,
                     headers={"Accept": HTML_ACCEPT}) as response:
                     if response.status != 200:
                         return (FAILURE,
                             f"OSHWA project page returned "
                             f"{response.status} {self.articleURL}")
                     html = await response.text()
             except Exception as e:
                return  (FAILURE,
                       f"Failed to fetch OSHWA Project {self.articleURL}" +
                       " " + str(e))

        # The following line could be earlier, but easier to read this way   
        if view.siteRoot.existsRemoteURL(self.articleURL) != False:
           return FAILURE, "URL Already Exists"

        #This is a link to a Mastodon server, quit
        if (
           "To use the Mastodon web application, please enable JavaScript."
           in html):
             return  FAILURE, f"This is a mastodon server {self.articleURL}"
        
        try:
            title, description, image  = web_preview(self.articleURL, content = html )
        except Exception as e:
            return  FAILURE, f"Web Preview failed to parse  {self.articleURL} {e}"

        
        if description == None:
            description = ""
        if title == None:
            title = ""
        if not title.strip():
            return FAILURE, "NO TITLE GIVEN", self
        self.title = title
        if image:
            self.imageURL = urljoin(self.articleURL, image)
       
        if len(description) > 100:
           description = description[:100]
           description = description.rsplit(' ', 1)[0]
           description = description + "..."
           
        self.description = description
        parent = self.parent
        newName = slugify (self.title)
        newName = view.uniqueBothName (parent,newName)
        parent[newName] = self
        print (".",end = "")
        self.postAddProcess(view )
        if image:
           return await fetch(session,self,view)
        else:
           return SUCCESS, self.name + "but no image"
       
    def postAddProcess(self,view):
        pass
    
    def defaultToot(self,view):        
        return (self.tootTitlePlusDescription() +    
                  self.tootArticleURL() +
                  self.tootVia(view) +
                  self.tootReadMore(view) )
               


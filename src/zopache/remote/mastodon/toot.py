import sys
import time
import re

from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urlparse

from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

from slugify import slugify

from webpreview import web_preview

from zope.interface import implementer

from dolmen.forms.base.markers import FAILURE, SUCCESS
from zopache.remote.mastodon.interfaces import IToot

from zopache.core import Leaf

hostNamesToIgnore = {"uncensorednews.us",
                     "takvera.blogspot.com",
                     "twitter.com",
                     "www.twitter.com",
                     "climatejustice.social",
                     "c.im"}


@implementer(IToot)
class Toot(Leaf):
    webClass = "Toot"
    webApproved = False
    publicationApproved = False
    description = ""
    content = ""
    source = ""
    recommended = False
    numberOfBoosts = 0
    numberOfFavorites = 0
    count = 0
    title = ""
    
    def __init__(self):
        Leaf.__init__(self)
        self.articles = []
        self.articleURLs = []

    def addArticle(self,article):
        self.articles.append(article)
        url = (getattr(article, 'articleURL', False) or
                   article.remoteURL)
        try:
           self.articleURLs.remove (url)
        except ValueError as e:
           if url.startswith("https://"):
              url = "http://" + url[8:]
              self.articleURLs.remove (url)
           elif url.startswith("http://"):
              url = "https://" + url[7:]
              self.articleURLs.remove (url)              
           else:
              raise ValueError("In toot.py") 
        self._p_changed = True        
        
    def removeArticle(self,article):
        self.articles.remove(article)
        url = (getattr(article, 'articleURL', False) or
                   article.remoteURL)        
        self.articleURLs.append(url)
        self._p_changed = True
        
    def hasWords(self, toot, account):
        for word in account.wordsToAvoid.split("\r\n"):
               if word == '':
                   continue
               if word in toot.content:
                  return True
        return False
        
    def createToot(self,toot,account):
        if toot.reblog:
            return 'Reblog/Boosted', self
        
        if toot.visibility in ['private','direct']:
           return 'Visibility', self

        if self.hasWords(toot,account):
          return "Forbidden Words", self
       
        tootId = str(toot.id)
        if oldToot :=  account.get(tootId,None):
            oldToot.updateValue(
                                'numberOfBoosts',
                                toot.reblogs_count)
            oldToot.updateValue(
                                'numberOfFavorites',
                                toot.favourites_count)
            return "Existing Toot", oldToot
        
        self.source =  toot.content
        soup = BeautifulSoup(toot.content, 'html.parser')
 
        text = soup.get_text()
        self.title = text [0:20]        
        if not soup.text.strip():
            return 'No Content', self
        try:
            language = detect(text)
        except LangDetectException as e:
            return 'Language Error', self
        if language not in ('en', 'de'):
            return 'Not English or German', self

        soup, textTags = self.removeHashTags(soup)
        soup, articleURLs = self.processURLs (soup)
        self.articleURLs = articleURLs
        if len(articleURLs) == 0:
            return 'No article URLS', self
        soup.smooth()
        text = soup.get_text()
        soup = self.removeEmptyParagraphs(soup)
        if len (text) > 500:
            return "Text is too long", self
            
        #NOW CREATE THE TOOT   
        self.content = str(soup)
        self.tags = ' '.join(textTags)
        self.parent =  account
        tootId = str(toot.id)
        self.name = tootId
        self.hasMedia =  True if toot.media_attachments else False
        self.userId = toot.account.acct
        self.numberOfBoosts = toot.reblogs_count
        self.numberOfFavorites = toot.favourites_count
        self.description = ""
        self.tootId = tootId
        self.tootURL = toot.url
        if self.name == None:
           return "Error: new.name == None", self
        try:
            account[self.name] = self
        except:
            return "ERROR: account[new.name] = new", self
        
        return 'SUCCESS', self

    @property
    def asText(self):
        soup = BeautifulSoup(self.source, 'html.parser')
        text = soup.get_text()
        return text
        
    def processURLs(self,soup):    
        urls  = soup.find_all('a')
        articleURLs = []
        for item in urls:
            #Ignore Mentions     
            text = item.get_text() 
            if not text:
                continue
            if text and text[0]=='@':
               continue
           
            url = item["href"]
            item.replace_with('')            
            if not url:
                continue
            hostName = urlparse(url).hostname
            if not hostName:
               continue                
            if hostName.lower() in hostNamesToIgnore:
               continue
            articleURLs.append(url)
            
        return soup, articleURLs
    
    def preDeleteProcess(self,view):
        for article in self.articles.copy():
            self.removeArticle(article)
            article.removeToot(self)
            
    def tagsAsHTML(self):
        return self.tags
    
    def updateValue(self,name,newValue):
        if getattr(self,name,None) != newValue:
            setattr(self,name,newValue)
            
    #Iterate through destroying all but the last hash tag. 
    def removeHashTags(self,soup):
        hashTags =  []
        textTags = []                        
        
        previousTag = None
        lastWasHashTag = False
        contents = soup.contents
        for paragraph in contents:
            if isinstance(paragraph, NavigableString):
                continue
            for tag in paragraph:
                #skip spaces
                if not tag.text.strip():
                    continue
                if self.isHashTag(tag):
                    if not lastWasHashTag:
                        hashTags.append([])
                    hashTags [-1].append(tag)
                    lastWasHashTag = True
                else:
                    lastWasHashTag = False 

        for sequence in hashTags:

            if len (sequence) > 1:
               for tag in sequence:
                       textTags.append(tag.text)
                       tag.replace_with('')
            else:
               for tag in sequence:
                   text = tag.text
                   textTags.append(text)
                   result= re.findall('[A-Z]*[^A-Z]*', text[1:])
                   result.remove('')
                   #print ("SPLIT= ", result)
                   text = ' '.join(result)
                   tag.replace_with(text)
                                             
        return soup, textTags
        
    def isHashTag(self,tag):
       try:
           if tag.name == 'a':
              if tag.text[0] == '#':
                  return True
       except:
           pass
       return False    

    def removeEmptyParagraphs(self,soup):
        for item in soup:
            if not item.text.strip():
               item.replace_with('')
        return soup       

   

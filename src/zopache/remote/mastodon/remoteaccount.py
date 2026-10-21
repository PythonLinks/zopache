import os
import time
import logging
import transaction

from mastodon import MastodonAPIError

from dolmen.forms.base.markers import FAILURE
from zopache.core.viewdecorators import *
from zopache.remote.mastodon.toot import Toot
from zopache.remote.mastodon.interfaces import IRemoteAccount, IHashTag
from dolmen.container import BTreeContainer
from zopache.core.uniquename import UniqueName
from zopache.core.ancestors import Ancestors
from zopache.remote.rssdownload import fetchAll
from zopache.crud.getimage import getImage
from zopache.remote.news.article import Article
from zopache.core.transactionnote import TransactionNote
from zopache.pages.content import Content

secondsInaDay = 3600 *24

os.makedirs('/app/data/logs', exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(
    logging.FileHandler('/app/data/logs/crawl.log', mode = "a"))

fetch_logger = logging.getLogger('fetchMastodon')
fetch_logger.setLevel(logging.DEBUG)
fetch_logger.addHandler(
    logging.FileHandler('/app/data/logs/fetchMastodon', mode = "a"))

class Base (Content, BTreeContainer, UniqueName, Ancestors, TransactionNote) :
    webClass = "RemoteAccount"
    lastImported = 0
    htmlSummary = True
    webApproved = True
    title = ""
    mastodonId = ''
    keepAllArticles = False
    wordsToAvoid = ""
    description = ""
    defaultCategory = ""
    domainName = ""
    maxId = None
    mostRecentTootId = None
    crawledToStart = False
    def childCategories(self):
        return []

    def __init__(self):
        Content.__init__(self)
        BTreeContainer.__init__(self)
        self.reset()

    def previousImportTime(self,indexTime,view):
            while True:
                indexTime -= 1
                if - indexTime not in view.contentByTime:
                    return indexTime


    def crawl(self,view):
        proxy = view.proxy
        accountName = self.mastodonId
        user = proxy.account_search(accountName)[0]
        logger.info ("\n---------------------------\n")
        if self.crawledToStart == False: #first import
               return self.crawlingToStart(view,proxy,user)
        else:
               return self.crawlingMostRecent(view,proxy,user)


    def crawlingToStart (self,view,proxy,item):
        pageOfToots = [None]
        pageCount = 0
        totalNewArticles = 0
        logger.info("Crawling To Start " + self.mastodonId)
        while pageOfToots and (proxy.ratelimit_remaining > 3):
                pageOfToots = self.fetchToots(
                       view, proxy, item, 'crawlingToStart',
                       self.maxId,limit=1000)
                if len(pageOfToots) == 0:
                    self.crawledToStart = True
                    logger.info ("Crawled To Start" +  self.mastodonId)
                    break
                else:
                    #set the resume cursor before processing the page,
                    #so it commits atomically with this page's data
                    lastToot = pageOfToots [-1]
                    self.maxId = self.setMaxId(self.maxId,lastToot.id)
                    existingToots, newArticles = (
                      self.processPage(pageOfToots,view))
                    totalNewArticles += newArticles
                    pageCount += 1
        return totalNewArticles, pageCount

    def crawlingMostRecent(self,view,proxy,item):
        maxId = None
        startTime = int(view .startTime)
        logger.info("Crawling Recent Toots " +  self.mastodonId)
        pageOfToots = self.fetchToots(
                              view,proxy,item,
                              'crawlingMostRecent-initial',maxId)
        # No Toots
        if not pageOfToots:
           logger.info("No Toots " + self.mastodonId)
           return 0,0

        #No new Toots
        mostRecentTootId = pageOfToots [0].id
        if mostRecentTootId == self.mostRecentTootId:
           logger.info("No New Toots " + self.mastodonId)
           return 0, 0

        #anchor: walk back to where the last successful crawl left
        #off, or to the newest toot already stored if there's no
        #recorded boundary (fresh HashTag, or just after reset20).
        previousMostRecentTootId = self.mostRecentTootId
        if previousMostRecentTootId is not None:
            anchorId = int(previousMostRecentTootId)
        else:
            anchorId = self.largestStoredId()

        self.mostRecentTootId = mostRecentTootId
        self.lastImported = startTime
        self.modificationTime = startTime

        totalNewArticles, pageCount, oldestTootAge = self.crawlPages(
                              view,proxy,item,pageOfToots,anchorId)
        logger.info ("oldestToot Age " + str(int(oldestTootAge)))
        return totalNewArticles, pageCount

    def crawlPages(self,view,proxy,item,pageOfToots,anchorId):
        totalNewArticles = 0
        oldestTootAge = 0
        pageCount = 0
        maxId = None
        while (pageOfToots and
                (proxy.ratelimit_remaining > 3) ):

              existingToots, newArticles = (
                      self.processPage(pageOfToots,view))
              totalNewArticles += newArticles
              print ("TOTAL NEW ARTICLES + ", totalNewArticles)
              pageCount += 1
              lastToot = pageOfToots [-1]
              maxId = self.setMaxId(maxId,lastToot.id)
              oldestTootAge = self.tootAge(lastToot,view)
              print ("Age = ", oldestTootAge," days", end = "")

              if anchorId is not None and int(lastToot.id) <= anchorId:
                  logger.debug("Break: reached last known toot " +
                                 self.mastodonId)
                  break

              pageOfToots = self.fetchToots(
                              view, proxy, item, 'crawlPages', maxId)

        return totalNewArticles, pageCount, oldestTootAge


    def fetchToots(self,view,proxy,item,method,maxId,**kwargs):
        user = item
        try:
            result = proxy.account_statuses(user.id, max_id=maxId, **kwargs)
            self.logFetchSuccess(
                "account_statuses", method, user.id, maxId, kwargs, proxy)
            return result
        except MastodonAPIError as error:
            self.logFetchFailure(
                "account_statuses", error, method, user.id, maxId, kwargs,
                proxy)
            raise

    def logFetchSuccess(self, apiName, method, itemId, maxId, kwargs, proxy):
        fetch_logger.debug(
            "%s OK method=%s account=%s userId=%s "
            "maxId=%s kwargs=%s ratelimit_remaining=%s",
            apiName, method, self.mastodonId, itemId, maxId, kwargs,
            getattr(proxy,'ratelimit_remaining',None))

    def logFetchFailure(self, apiName, error, method, itemId, maxId, kwargs,
                         proxy):
        status_code = error.args[1] if len(error.args) > 1 else None
        reason = error.args[2] if len(error.args) > 2 else None
        error_msg = error.args[3] if len(error.args) > 3 else None
        fetch_logger.error(
            "%s FAILED method=%s account=%s userId=%s "
            "maxId=%s kwargs=%s ratelimit_remaining=%s "
            "status=%s reason=%s error_msg=%s",
            apiName, method, self.mastodonId, itemId, maxId, kwargs,
            getattr(proxy,'ratelimit_remaining',None),
            status_code, reason, error_msg)

    def setMaxId(self, maxId,tootId):
        if maxId == None:
            return  tootId

        elif int(tootId) <= int(maxId):
            return  tootId

        else:
            raise Exception("Something strange with the Mastodon Ids. ")
         

    def processPage(self,pageOfToots,view):
        view.allToots=allToots = set()
        view.newArticles = newArticles = {}
        view.oldArticles = oldArticles = set() 
        loopStart = time.time()
        existingToots = self.processToots(pageOfToots,view)
        numberOfNewArticles = self.postProcessPage(view)
        loopEnd = time.time()
        loopTime = int(loopEnd - loopStart)
        print("\nLoopTime = ", loopTime, " seconds")
        logger.info("Number of New Articles = " +
                    str(numberOfNewArticles ))
        if existingToots:
           logger.info("ExistingToots")
        return existingToots,  numberOfNewArticles
    
    def tootAge(self,toot,view):
        currentTime = view.startTime
        age = currentTime - self.getPublicationTime(toot,view)
        tootAge = int(age/(secondsInaDay))
        return tootAge
    
    def postProcessPage(self,view):
           allToots = view.allToots
           newArticles = view.newArticles
           oldArticles = view.oldArticles
           #Until you successfull fetch the article, 
           #and add it to the
           #Parent, it will not be in contentByTime. 
           for item in newArticles.values():
                  del view.contentByTime[-item.importTime]
           allArticles = set(newArticles.values()) | oldArticles
           self.fetchArticles (allArticles,view)
           for toot in allToots:
               for url in toot.articleURLs:
                   article = view.root.existsRemoteURL(url)
                   if article != False:
                      toot.addArticle(article) 
                      article.addToot(toot)
                      
           #Since the created articles did not know about
           #the relevant toots.
           root = view.root
           numberOfNewArticles = 0
           for article in newArticles.values():
               if article.name:
                   numberOfNewArticles += 1
                   root.unIndexItem(article)
                   root.indexItem(article)
           self.describeTransactionWithText(
                "Fetching from: " + self.mastodonId
           )                   
           transaction.manager.commit()
           return numberOfNewArticles

    #COPY OF THIS HERE AND IN RSS.PY    

    def fetchArticles(self,articles,view):
        result = fetchAll(articles,view, allowedTime = 20)
        for item in result:
            if item[0] ==  FAILURE:  
               view.submissionErrors.append("ERROR: " + str(item[1:]))
               # ' status = ' must match the text returned by fetch() in
               # remote/rssdownload.py:88, which already logged the failure.
               if not ' status = ' in str(item[1:]):
                  if not "TIME OUT" in str(item): 
                     try:
                         logger.warning ("\n" +  str(item))
                     except:
                         logger.warning ("\n" + str( type(item)))
                         
        view.status='RSS Feeds were downloaded.'

        
    def processToots(self,pageOfToots,view):
        root = view.root
        allToots = view.allToots
        newArticles = view.newArticles
        oldArticles = view.oldArticles
        contentByTime = root.contentByTime
        existingToots = False
        for toot in pageOfToots:
           account = self
           message, new  = Toot().createToot(toot,account)
           #DEBUG: temporary, remove once the missing-articles bug is found
           logger.debug("createToot result: " + message +
                         " tootId=" + str(toot.id))
           if message == "Existing Toot":
              existingToots = True
           if message != "SUCCESS":
               continue
           allToots.add(new)           
           for url in new.articleURLs:
               article = root.existsRemoteURL(url)
               if article == False:
                 if url not in newArticles:
                     anArticle = Article(toot,
                                       url,
                                       account,
                                       view.mastodonArticles,
                                       root)
                     importTime = self.getPublicationTime(toot,view)
                     importTime = self.previousImportTime(importTime,view)
                     anArticle.importTime = importTime
                     newArticles[url] = anArticle
                     contentByTime[-importTime] = anArticle
                     print(".", end = "") 
               else:                    
                   if not article.publicationApproved:
                       article.publicationApproved = True
                       oldArticles.add (article)
        return existingToots
    
    def getPublicationTime(self,toot,view):           
        try:
            publicationTime = time.mktime(toot.created_at.timetuple())
        except:    
            publicationTime = view.startTime
        return int (publicationTime)

         
    def valuesAsList(self):
        result = []
        for item in self.values():
               result.append (item)
        return result

    def largestStoredId(self):
        ids = []
        for name in self.keys():
            try:
                ids.append(int(name))
            except ValueError:
                continue
        return max(ids, default=None)

    def mostRecentStored(self, count):
        byId = {}
        for name, item in self.items():
            try:
                byId[int(name)] = item
            except ValueError:
                continue
        return [byId[tootId] for tootId in sorted(byId)[-count:]]

    def reset(self):
         #self.crawledToStart = False
         self.maxId = None
         self.mostRecentTootId = None
         
    def postAddProcess(self,view = None):
        if self.logoURL:
            getImage(self,self.logoURL)

@implementer (IRemoteAccount)
class RemoteAccount( Base):
    
    @property
    def remoteURL(self):
        blank,user, server = self.parts()
        return 'https://' + server + '/@' + user

    def getLink(self):
        return f'<a href ="{self.remoteURL}">{self.userName()}</a>'
        
    def parts(self):
        id = self.mastodonId
        if id[0]!='@':
            id = '@' + id
        return id.split('@')

    def userName(self):
        return "@" + self.parts()[1]
    
            
@implementer (IHashTag)
class HashTag(Base):
    #This crawl looks like the inherited crawl,
    #But soon it will not require a logged in user.
    #So it is staying separate.
    def crawl(self,view):
        proxy = view.proxy
        hashTag = self.mastodonId.lstrip("#")
        logger.info ("\n---------------------------\n")
        if self.crawledToStart == False: #first import
               return self.crawlingToStart(view,proxy,hashTag)
        else:
               return self.crawlingMostRecent(view,proxy,hashTag)

    def fetchToots(self,view,proxy,item,method,maxId,**kwargs):
        hashTag = item
        try:
            result = proxy.timeline_hashtag(hashTag, max_id=maxId, **kwargs)
            self.logFetchSuccess(
                "hash tag", method, hashTag, maxId, kwargs, proxy)
            return result
        except MastodonAPIError as error:
            self.logFetchFailure(
                "hash tag", error, method, hashTag, maxId, kwargs, proxy)
            raise

import crom
from zopache.zmi.interfaces import IURLSegment
@crom.adapter
@crom.sources(IRemoteAccount)
@crom.target(IURLSegment)
class IRemoteAccountAdaptor(object):
    def __init__(self,context):
        self.context=context   

    def getSegment(self):
        return 'manage'

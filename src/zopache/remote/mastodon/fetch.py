import logging
import re
import time

from mastodon import MastodonError

from zopache.core.viewdecorators import *
from zopache.remote.mastodon.basebot import MastodonBot
from zopache.remote.mastodon.interfaces import IRemoteAccount
from zopache.remote.rss import RSSBase
from zopache.remote.news.mastodonarticles import MastodonArticles
from zopache.remote.mastodon.remoteaccount import RemoteAccount
from zopache.core.baseform import Form

regexp = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')

@view_component
@context(IRemoteAccount)
@target(IView)
@name("reset")
@permissions('Manage')
class Reset(Form):
    title = "Reset this mastodon Account"
    subtitle = "So you can crawl it again"
    
    def update(self):
        context = self.context
        context.reset()
        self.status='Account was reset.'
        #logging.info ("Reset account ", context.mastodonId)


@view_component
@context(IRemoteAccount)
@target(IView)
@name("reset20")
@permissions('Manage')
class Reset20(Form):
    title = "Reset the most recent toot id. "
    subtitle = "So you can crawl it again"
    
    def update(self):
        context = self.context
        context.mostRecentTootId = None
        context.lastLongImportTime = time.time() - (3600 * 24 * 8)
        all = context.valuesAsList()
        all = all [-20:]
        for item in all:
            del context [item.name]
        self.status='Account was reset.'
        #logging.info ("Reset account ", context.mastodonId)

@view_component
@context(IRemoteAccount)
@target(IView)
@name("fetch")
@permissions('Manage')
class FetchTimeLine(Form,MastodonBot,RSSBase):

    #First the title
    @property
    def title(self):
        title = "Download the toots for "
        title += self.context.mastodonId
        return  title


    def getAccountName(self,toot):
        accountName = toot.account.acct
        if not '@' in accountName:
            accountName =  accountName + "@mastodon.social"
        if not accountName.startswith("@"):
            accountName = "@" + accountName
        return accountName
    
    def getAccount(self,toot):
        root = self.root
        feeds = root['mastodon-accounts']
        accountName = self.getAccountName(toot)
        account = feeds.get(accountName,None)
        if account == None:
           account = RemoteAccount()
           account.title = toot.account.username
           account.mastodonId = accountName
           feeds [accountName] = account
        return account    
        
    def update(self):
        self.startTime = time.time()
        self.root = self.getSiteRoot()
        #self.siteRoot is Needed elsewhere. 
        self.siteRoot = self.root
        self.proxy =  self.getUserProxy()
        account = self.context
        self.contentByTime = self.getSiteRoot().contentByTime
        self.mastodonArticles = self.root.get('mastodon-articles',None)
        if self.mastodonArticles == None:
            logging.debug('Creating Category "mastodond-articles".')
            logging.debug('You may want to move it.')
            self.mastodonArticles = MastodonArticles()
            self.root['mastodon-articles'] = self.mastodonArticles

        try:
            totalNewArticles, pageCount = account.crawl(self)
        except MastodonError as error:
            self.submissionErrors.append(
                "MASTODON ERROR: " + str(error))
            totalNewArticles, pageCount = 0, 0
        logging.debug("Pages,Articles" + account.mastodonId +
                      str(pageCount) + " " + str ( totalNewArticles))
        self.totalNewArticles = totalNewArticles
        if totalNewArticles:
            self.getSiteRoot().lastMastodonFetchTime = time.time()        
        self.pageCount = pageCount
        Form.update(self)
        
    def render(self):
        self.duration = (self.startTime - time.time())/60
        logging.info ("Duration = " +  str(self.duration))
        errors = "<br>".join(self.submissionErrors)
        return (
            "Account was crawled. Details in /app/data/logs/crawl <br>" +
            "Duration =  " + str(self.duration) +
            " minutes" +
            "<br> New Articles = " + str(self.totalNewArticles) +
                "<Br> Page Count " + str(self.pageCount) +
    "<Br> Total Toots " + str(len(self.context)) +
    "<Br> Errors: <br>" + errors )
               

    """
    def debug(self,pageOfToots):
        from bs4 import BeautifulSoup
        for item in pageOfToots:
       yes
    if not item.reblog:
                soup = BeautifulSoup(item.content, 'html.parser')
                print()
                print( item.created_at.ctime())
                print (soup.get_text())

                
    """
    """
    def fixTime(self,toot):
            root = self.siteRoot
            account = self.context
            contentByTime = self.contentByTime        
            if tootedArticle := account.localArticles.get(toot.id,None):
               publicationTime = None 
               try:
                   publicationTime = self.getPublicationTime(toot)
               except:
                   pass
               if publicationTime:
                  root.unIndexItem(tootedArticle)
                  importTime = self.previousImportTime(publicationTime)
                  tootedArticle.importTime = importTime
                  root.indexItem(tootedArticle) 
    """

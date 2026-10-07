import logging
import time

from mastodon import MastodonError

from zopache.core.view import View
from zopache.core.viewdecorators import *
from zopache.core.baseform import Form
from zopache.remote.mastodon.basebot import MastodonBot
from zopache.remote.mastodon.interfaces import IRemoteAccount
from zopache.remote.rss import RSSBase
from zopache.remote.news.mastodonarticles import MastodonArticles
from zopache.remote.mastodon.remoteaccount import RemoteAccount
from dolmen.container import IBTreeContainer

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
        self.crawldeToStart = False        
        self.status='Account was reset.'

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
        context.reset()
        for item in context.mostRecentStored(20):
            del context [item.name]
        self.status='Account was reset.'
        #logging.info ("Reset account ", context.mastodonId)


class Base(MastodonBot,View):
    def update(self):
        View.update(self)
        self.message = ""
        self.submissionErrors = []
        self.startTime = time.time()
        self.root = self.getSiteRoot()
        self.siteRoot = self.root
        self.proxy =  self.getUserProxy()
        self.contentByTime = self.getSiteRoot().contentByTime
        self.mastodonArticles = self.root.get('mastodon-articles',None)
        if self.mastodonArticles == None:
            logging.debug('Creating Category "mastodond-articles".')
            logging.debug('You may want to move it.')
            self.mastodonArticles = MastodonArticles()
            self.root['mastodon-articles'] = self.mastodonArticles

        
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


    def crawlAccount(self,account):
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
        self.message  += (f"{account.mastodonId} crawled,"
                           f" {pageCount}  pages, "
                           f"{totalNewArticles} articles"
                           + "".join("<br>" + e for e in self.submissionErrors)
                           + "<hr>")

    def render(self):
        self.duration = (self.startTime - time.time())/60
        logging.info ("Duration = " +  str(self.duration))
        return (
            "Crawl details in /app/data/logs/crawl.log <br>" +
            "Duration =  " + str(self.duration) +
            " minutes" + self.message )

        
    
@view_component
@context(IRemoteAccount)
@target(IView)
@name("fetch")
@permissions('Manage')
class FetchOne(Base):

    #First the title
    @property
    def title(self):
        title = "Download the toots for "
        title += self.context.mastodonId
        return  title
        
    def update(self):
        Base.update(self)
        account = self.context
        self.crawlAccount(account)

    def render(self):
        return (Base.render(self) +
                "<Br> Total Toots " + str(len(self.context)))
        
                           

@view_component
@context(IBTreeContainer)
@target(IView)
@name("crawl")
@permissions('Manage')
class CrawlMany(Base):                    
    title = "Crawl Multiple Mastodon Acconts"
    subtitle = "So easy. "
    
    def update(self):
        Base.update(self)
        context = self.context
        self.status='Account were crawled.'
        feeds = []
        for account in context.values():
            if IRemoteAccount.providedBy (account):
                feeds.append(account)
        feeds.sort(key=lambda feed: feed.lastImported)
        for account in feeds:
               self.crawlAccount(account)
               self.submissionErrors = []
               
    def render(self):
        return Base.render(self) 

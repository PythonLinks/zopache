from zopache.core.view import View
from zopache.core.viewdecorators import *
from dolmen.container import IBTreeContainer

@view_component
@context(IBTreeContainer)
@target(IView)
@name("crawl")
@permissions('Manage')
class CrawlMastodon(View):
    title = "Crawl Multiple Mastodon Acconts"
    subtitle = "So easy. "
    
    def update(self):
        context = self.context
        self.status='Account were crawled.'
        feeds = []
        for account in context.values():
            if account.className == ("RemoteAccount"):
                feeds.append(account)
        feeds.sort()
        
        feeds.sort(key=lambda feed: feed.lastImported)
        result = ""
        for item in feeds:
            result += Fetch(self.context,self.request)().render()

        self.status = result    
            
            

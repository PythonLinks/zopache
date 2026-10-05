from zopache.core.viewdecorators import *
from zopache.remote.news.interfaces import IMastodonArticles
from zopache.crud.getimage import getImage
from zopache.core.ancestors import Ancestors
from zopache.core.uniquename import UniqueName
from zopache.pages.content import ContentWithChildContent

#all imports are used

@implementer (IMastodonArticles)
class MastodonArticles(ContentWithChildContent, UniqueName, Ancestors):
    #webClass = "MastodonArticles"
    webClass = "RSS"
    webApproved = True
    remoteURL = ""
    description = "Articles mentioned on Mastodon."
    htmlSummary = True
    title = ""
    keepAllArticles = True

import crom
from zopache.zmi.interfaces import IURLSegment
@crom.adapter
@crom.sources(IMastodonArticles)
@crom.target(IURLSegment)
class IMastodnoArticlesAdaptor(object):
    def __init__(self,context):
        self.context=context   

    def getSegment(self):
        return 'manage'

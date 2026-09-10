from BTrees.OOBTree import OOBTree

from zopache.core.viewdecorators import *
from zopache.remote.news.interfaces import IMastodonArticles
from zopache.crud.getimage import getImage
from zopache.core.ancestors import Ancestors
from zopache.application.source import Source

#all imports are used

@implementer (IMastodonArticles)
class MastodonArticles(Source):
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


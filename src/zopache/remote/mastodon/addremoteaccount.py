from slugify import slugify

from zopache.crud.forms import AddByTitleForm, TreeSecurityAddForm
from zopache.core.interfaces import ITreeSecurity
from zopache.core.viewdecorators import *
from zopache.pages.interfaces import IPageBase
from zopache.remote.mastodon.interfaces import IAddRemoteAccount
from zopache.remote.mastodon.remoteaccount import RemoteAccount
from zopache.ttw.mail import Notify
from zopache.business.exists import Duplicate
from zopache.ttw.htmlviews import AddCkHTMLBase
from zopache.pages.addpage import AddByTitleForm

@view_component
@name ('addTimeline')
@target(IView)
@context(IPageBase)
class AddRemoteAccount(AddByTitleForm):
     interface = IAddRemoteAccount
     title = "Add a Timeline"
     subTitle ="Ask the admin to fetch the content"
     count = 0
     factory = RemoteAccount
     layoutName = "UserMenu"
     dataValidators = [Duplicate]
     def newName(self,data):
         return data['mastodonId'].strip()
     
     def newURL(self,baseURL):
        return baseURL 





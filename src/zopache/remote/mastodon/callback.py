import logging

from zopache.core.viewdecorators import *
from zopache.core.baseform import Form
from zopache.ttw.interfaces import IPrincipalFolder
from zopache.remote.mastodon.actions import MastodonCallBackAction
from zopache.remote.mastodon.actions import GithubCallBackAction
from zopache.remote.mastodon.basebot import MastodonBot
from zopache.ttw.mail import Notify

@form_component
@context(IPrincipalFolder)
@target(IView)
@name("callback")
class CallBack(Form, MastodonBot,Notify):
    title = "Respond to the Oauth Callback "
    subTitle = """If you see this, it means the Mastodon server
    is overloaded, please try again. """

    def __init__(self,context,request):
        Form.__init__(self,context,request)
        Notify.__init__(self)

    def update(self):
        if self.getOauthServer() == "github.com":
           GithubCallBackAction("Redirect","redirect")(self)
        else:
           MastodonCallBackAction("Redirect","redirect")(self)


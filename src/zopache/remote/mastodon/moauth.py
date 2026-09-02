import os
import logging
import uuid
from pathlib import Path

from mastodon import Mastodon

from requests.models import urlencode

from cromlech.browser import getSession
from cromlech.browser.exceptions import HTTPFound

from zopache.core.viewdecorators import *
from zopache.core.baseform import Form
from zopache.ttw.interfaces import IPrincipalFolder
from zopache.remote.mastodon.basebot import MastodonBot, TIMEOUT

logger = logging.getLogger("oauth")

@form_component
@context(IPrincipalFolder)
@target(IView)
@name("moauth")
class MastodonOauth(Form, MastodonBot):
    title = "Authenticate with Mastodon.Social"
    subTitle = """Should you see this, it means their server is overloaded,
    plese try logging in again.. """
    #actions = Actions()

    def update(self):
        oauthServer = self.getOauthServer()
        if oauthServer == "github.com":
            self.githubOauth()
        else:
            self.mastodonOauth()


    def githubOauth(self):
        # credential file missing -> show error, re-render this page
        try:
            params = self.getGithubParams()
        except FileNotFoundError:
            self.submissionErrors.append(
                "Github oauth credential file does not exist.")
            return

        params['redirect_uri'] = self.callbackURL()
        params['scope'] = ["read:user", "user:email"]
        oauthState = uuid.uuid4().hex
        getSession()['oauthState'] = oauthState
        params['state'] = oauthState

        endPoint = "https://github.com/login/oauth/authorize?"
        url = endPoint + urlencode(params)
        raise HTTPFound(url)

    
    def mastodonOauth(self):
        mastodonDomain = self.getOauthServer()
        errorURL = "/person/oauth?form.field.domain=" + mastodonDomain
        secretFile = self.getSecretFile(mastodonDomain)
        
        if not os.path.exists(secretFile):
            appName = (self.getSiteRoot().appName or
                       (self.getDomain() + " Oauth")).strip()
            try:
                logger.info("Trying to create secret for %s", mastodonDomain)
                app = Mastodon.create_app(
                    appName,
                    api_base_url = mastodonDomain,
                    redirect_uris = self.callbackURL(),
                    scopes = self.SCOPES,
                    request_timeout = TIMEOUT,
                    to_file = str(secretFile)
                    )
                # Is this really necessary
                if not os.path.exists(secretFile):
                    raise Exception ("Secret File Failed to be crated")
            except Exception as e:
                logger.info("Failed to create secret for %s", mastodonDomain)                
                message = ("Failed to register app for " +
                           mastodonDomain + ' ' +
                           str(e))
                self.sendMessage(message, type = "Error")
                raise HTTPFound(errorURL)

        # No error, all is good.
        try:
           logger.info("Trying to create a request url for %s", mastodonDomain)            
           app= self.createOauthApp()
           url = app.auth_request_url(
                 redirect_uris = self.callbackURL(),
                 scopes = self.SCOPES,
                 force_login=False)
        except Exception as e:
            logger.info("Failedto create the request URL for %s", mastodonDomain)
            message = str(e)
            self.sendMessage(message, type = "Error")
            raise HTTPFound(errorURL)
        # No error, all is good - redirect outside the try so this
        # HTTPFound (itself an Exception, used for control flow) is
        # not caught by the except block above.
        oauthState = uuid.uuid4().hex
        getSession()['oauthState'] = oauthState
        url = url + "&" + urlencode({"state": oauthState})
        logger.info("Redirecting to %s", url)
        raise HTTPFound(url)

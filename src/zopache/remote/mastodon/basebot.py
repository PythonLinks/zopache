import os
import logging
from mastodon import Mastodon

from dolmen.forms.base.markers import FAILURE, SUCCESS
from cromlech.security import unauthenticated_principal as anonymous
from cromlech.browser.exceptions import HTTPFound

LOGIN_TIMEOUT = 7
FETCH_TIMEOUT = 60

logger = logging.getLogger("oauth")

class MastodonBot (object):
    SCOPES = ['read:accounts','read:statuses','write:media','write:statuses']

    def getOauthServer(self):
        path = self.request.url.split('?')[0]
        return path.rstrip('/').split('/')[-1].lower()
        
    def callbackURL(self):
        domain = self.getDomain().lower()
        oauthServer = self.getOauthServer()
        result = ("https://"+
                  domain +
                  '/person/callback/'+
                  oauthServer
                  )
        return result

    def getSecretFile(self,mastodonDomain):    
        wikiDomain = self.getDomain().lower()
        secretDirectory = ( "/app/data/oauth/" + wikiDomain + '/')
        os.makedirs(secretDirectory, exist_ok=True)
        secretFile = secretDirectory + mastodonDomain + '.secret'
        return secretFile

    def createOauthApp(self):
        oauthServer = self.getOauthServer()
        app = Mastodon(client_id = self.getSecretFile(oauthServer),
                       request_timeout = LOGIN_TIMEOUT)
        return app

    def getAccessToken(self,code):
        app  = self.createOauthApp()
        try: 
            accessToken = app.log_in( code = code ,
                    scopes = self.SCOPES,
                    redirect_uri= self.callbackURL())
            if accessToken is None:
                raise ValueError("Access Token is None.")
            if not isinstance(accessToken, str):
                raise ValueError("Access Token is not a string.")
            if len(accessToken) < 5:
                raise ValueError("Access Token is too short.")
        except Exception as error:
            msg = "while trying to get the Access Token "
            msg +=  "there was a problem. "
            msg += str(error)
            self.sendMessage(msg, type ="Error")
            self.submissionError += msg
            logger.debug(msg)
            return '',FAILURE            
        return  accessToken, SUCCESS

    def oauth(self):
        url = "/person/oauth"
        raise HTTPFound( url)

    #Only to be used in ./mauth
    def getNewUserName(self,accessToken):
        oauthServer = self.getOauthServer()        
        proxy =  Mastodon (request_timeout = LOGIN_TIMEOUT,
                         api_base_url = "https://" + oauthServer,
                         access_token = accessToken)
        try:
            userInfo = proxy.me()
            userName = userInfo["username"]
            if userName is None:
                raise ValueError("User name is None.")
            if not isinstance(userName, str):
                raise ValueError("User name is not a string.")
            if len(userName) < 2:
                raise ValueError("User name is too short.")
            return  userName, SUCCESS
        except Exception as error:
            msg = "while trying to get the User Info"
            msg +=  "was a problem. "
            msg += str(error)
            self.sendMessage(msg, type ="Error")
            self.submissionError += msg
            logger.debug(msg)
            return '',FAILURE


    
    def getUserProxy(self):
        principal = self.request.principal
        if principal == anonymous:
            self.oauth()
        accessToken = principal.accessToken
        if not accessToken:
            self.oauth()
        proxy =  Mastodon (request_timeout = FETCH_TIMEOUT,
                         api_base_url=principal.mastodonServerURL,
                         access_token = accessToken)
        return proxy
    
    def getGithubParams(self):
        fileName =  ("/app/data/oauth/" +
                    self.getDomain().lower() +
                    "/" +
                    self.getOauthServer() +
                    ".secret")
        with open(fileName) as secretFile:
            clientID = secretFile.readline().rstrip()
            clientSecret = secretFile.readline().rstrip()
        params = dict()
        params['client_id'] = clientID
        params['client_secret'] = clientSecret
        return params
    
    

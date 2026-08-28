from mastodon import Mastodon
from cromlech.security import unauthenticated_principal as anonymous

TIMEOUT = 7

class BaseBot (object):

    def proxyForUser(self):
        principal = self.request.principal
        if principal == anonymous:
            self.oauth()
        proxy = getattr (principal,'accountProxy',None)
        if proxy == None:
            self.oauth()
        return proxy

    def getOauthServer(self):
        path = self.request.url.split('?')[0]
        return path.rstrip('/').split('/')[-1].lower()

    def redirectURL(self):
         return self.callbackURL()
     
    def callbackURL(self):
        domain = self.getDomain().lower()
        oauthServer = self.getOauthServer()
        result = ("https://"+
                  domain +
                  '/person/callback/'+
                  oauthServer
                  )
        return result


    # This is only called once moauth has create the secret file. 
    def createMastodon(self, timeout):
        context = self.context
        fileName =  ("/app/data/oauth/" +
                    self.getDomain().lower() +
                    "/" +
                    self.getOauthServer() +
                    ".secret")
        mastodon = Mastodon(client_id = fileName, request_timeout = timeout)
        return mastodon

    def getParams(self):
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
    
class MastodonBot(BaseBot):
    SCOPES = ['read:accounts','write:media','write:statuses']

    def userLoginProxy(self,code):
        context = self.context
        mastodon  = self.createMastodon(TIMEOUT)
        result = mastodon.log_in( code = code ,
                               #scopes = self.SCOPES,
                               redirect_uri= self.callbackURL())
        return mastodon
    


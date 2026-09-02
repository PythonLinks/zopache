# What this does is first is first get the oauth code
# Then it creates a userLogin proxy
# Then it creates a user proxy
# Then it gets the user info.
# Then it logs the person in, or creates the account and logs them in. 
# Then redirects them to gdpr or to home.
# All a bit tricky.

# -*- coding: utf-8 -*-

import sys
import logging
import hmac
import requests
from requests.models import urlencode
from urllib.parse import parse_qs

from mastodon import Mastodon

from cromlech.browser import IURL, getSession
from dolmen.forms.base import Action, SuccessMarker
from dolmen.forms.base.markers import FAILURE, SUCCESS
from dolmen.forms.base.utils import set_fields_data, apply_data_event
from cromlech.browser.exceptions import HTTPFound

from zopache.core.getroot import getPrincipalFolder
from zopache.pages.interfaces import IPage
#from zopache.remote.mastodon.basebot import MastodonBot, GithubBot
from zopache.core.breadcrumbs import Breadcrumbs
from zopache.ttw.principalfolder import InternalPrincipal

logger = logging.getLogger("oauth")

class BaseAction(Action):
    def __call__(self, form):
        self.form = form
        self.verifyOauthState()
        # popped now, before the network calls below can raise --
        # single-use, so it must not survive an exception either.
        gdpr = getSession().pop("gdprPermission", None)

        authorizationCode, result = self.getOauthCode()
        if result == FAILURE:
            return FAILURE
        
        userName, accessToken, result = self.getUserInfo(authorizationCode)
        if result == FAILURE:
            return FAILURE
        
        principalFolder = form.getPrincipalFolder()

        email = userName + '@' + self.form.getOauthServer()
        handle = "@" + email
        if email in principalFolder.idByEmail:
            personId = principalFolder.idByEmail[email]
            person = principalFolder.getPrincipalById(personId)
            person.accessToken = accessToken
            principalFolder.loginUser(person,form)
            newURL = '/' + self.form.getSiteRoot().homePage 
            logger.debug("Logged in: %s", person.email)
            raise HTTPFound(newURL)
        else:
            if not (gdpr== "True"):
                form.sendMessage("GDPR Permission is required.",type = "Error")
                newURL = "/person/oauth?domain= " + form.getDomain()
                raise HTTPFound(newURL)                
            person = principalFolder.newPerson(self.form)
            self.form.new = person
            person.email = email
            person.handle = handle
            person.accessToken = accessToken    
            principalFolder [person.__name__] = person
            principalFolder.loginUser(person,form)            
            person.postAddProcess(view = form)
            newURL = (form.getSecureLongURL (
                   context = form.getPrincipal())
                  + '/address')
            logger.debug("Created %s", person.email)
            raise HTTPFound(newURL)

    def verifyOauthState(self):
        form = self.form
        # popped immediately -- single-use, must not survive either a
        # failed check or an exception raised later in this request.
        expectedState = getSession().pop("oauthState", None)
        returnedState = form.request.form.get("state")
        valid = (expectedState is not None
                 and returnedState is not None
                 and hmac.compare_digest(expectedState, returnedState))
        if not valid:
            logger.debug("Oauth state mismatch")
            form.sendMessage("OAuth state mismatch.", type = "Error")
            newURL = "/person/oauth?domain= " + form.getDomain()
            raise HTTPFound(newURL)

    def getOauthCode(self):
        code = self.form.request.form['code']
        try:
           if len(code) == 0:
               raise Exception("Empty access token returned by Masotdon")
        except Exception as error:
            msg = "while trying to get the access code "
            msg +=  "an empty access token was returned. "
            msg += str(error)
            logger.debug(msg)
            self.form.sendMessage (msg, type = "Error")
            return '', FAILURE
        return code, SUCCESS

class MastodonCallBackAction(BaseAction):
    def getUserInfo(self,authorizationCode):
        accessToken , result = self.getAccessToken(authorizationCode)
        if result == FAILURE:
            return '','', FAILURE
        userName, result = self.form.getNewUserName(accessToken)
        if result == FAILURE:
            return '','', FAILURE
        return  userName, accessToken, SUCCESS

    
    def getAccessToken(self,code):
        return self.form.getAccessToken(code)
    
        
class GithubCallBackAction(BaseAction):
    def getUserInfo(self,authorizationCode):
        accessToken, result = self.getAccessToken(authorizationCode)
        if result == FAILURE:
            return '','', FAILURE
        userName, result = self.getUserName(accessToken)
        if result == FAILURE:
            return '','', FAILURE
        return  userName, accessToken, SUCCESS

    def getAccessToken(self,code):
        tokenDict, result = self.getUserLoginProxy(code)
        if result == FAILURE:
            return '', FAILURE
        accessToken = tokenDict['access_token'][0]
        return accessToken, SUCCESS

    def getUserLoginProxy(self,code):
        url = "https://github.com/login/oauth/access_token"
        params = self.form.getGithubParams()
        params['code'] = code
        response = requests.post(url,data=params)

        status = response.status_code
        if status == 200:
            parsedValue = parse_qs(response.text)
            if not 'access_token' in parsedValue:
               return {}, FAILURE

            return parsedValue, SUCCESS
        else:
            msg = "while trying to get the access code "
            msg +=  "there was a problem. "
            form = self.form
            form.submissionError += msg
            form.submissionErrors.append(msg)
            return {}, FAILURE

    def getUserName(self,accessToken):
        endPoint = "https://api.github.com/user"
        if not accessToken:
            return '', FAILURE

        headers = {'Authorization': 'token ' + accessToken}
        response = requests.get(endPoint, headers=headers)
        status = response.status_code
        if status == 200:
            result = response.json()
            return  result['login'], SUCCESS
        else:
            msg = "while trying to get the user info "
            msg +=  "there was a problem. "
            form = self.form
            form.submissionError += msg
            form.submissionErrors.append(msg)
            return '', FAILURE


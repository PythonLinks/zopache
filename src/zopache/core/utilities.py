import urllib
import json
import arrow
import random

from pydoc import locate
import hashlib
from html import escape, unescape

from cromlech.security import Unauthorized
from dolmen.message import SessionSource, MessageReceiver

from zopache.core.getroot import getSiteRoot
from zopache.application.everyobject import EveryObject

def sortFunction(item):
  return item.__name__

class Utilities (object):

    def randomIndex(self):
        return  ('/index/' + str(random.randint(0,2**32 -1))) 
  
    def urlEscape(self,text):
        return urllib.parse.quote(text)

    def getOption(self,value,title,selected):
        result = f'<option value= "{value}"'
        if selected:
          result += " selected "
        result += f'> {title} </option>'
        return result
      
    def ago (self,time):
        return arrow.get(time).humanize()
      
    def sendMessage(self,message, type = None):
        source = SessionSource()
        source.send(message, type = type)
        try:
            len1 = len(source)
            if len1 > 2:
              messages = list(source)
              for msg in messages[2:]:
                 source.remove(msg)
        except UnboundLocalError:
            pass

    def receiveMessage(self,type = None):
        result = ""
        receiver = MessageReceiver (SessionSource())
        result += "<ul>"
        for item in receiver.receive(type = type):
            result += "<li>"
            result += item["body"]
            result += "</li>"
        result += "</ul>"                        
        return result
      
    @property
    def accessToken(self):
        if not hasattr(self,'_accessToken'):
           self._accessToken = getattr(self.getPrincipal(),
                                       'accessToken',
                                       False)
        return self._accessToken
 
    def parentalMenu(self):
        parentalMenu = self.parentalAcquire("ParentalMenu")
        if parentalMenu != None:
           return parentalMenu(self)
        return ""

    def webClassMenu(self):
        webClassMenu = self.webClassAcquire("WebClassMenu")
        if webClassMenu != None:
           return webClassMenu(self)
        return ""      
      
    def htmlEscape(self,text):
        return escape(text)

    def htmlUnEscape(self,text):
        return unescape(text)      
    
    def everyObject(self):
        return EveryObject(self.context)
      
    def sortByName(self,aList):
        return aList.sort(key=sortFunction)
    

    def createdBy(self,*args):
        item = self.context if len(args)==0 else args [0]        
        siteRoot = self.getSiteRoot()
        createdBy = item.createdBy
        if createdBy == None:
            return "Anonymous"
        elif type (createdBy) == int:
            item = siteRoot[str(createdBy)]
            return item.handle
        else:
            return createdBy
        
    def editedBy(self,*args):
        item = self.context if len(args)==0 else args [0]        
        siteRoot = self.getSiteRoot()
        editedBy = item.editedBy
        if editedBy == None:
            return "Anonymous"
        elif type (editedBy) == int:
            item = siteRoot[str(editedBy)]
            return item.handle
        else:
            return editedBy
        
    def shouldDisplay(self):
        if self.context.private == False:
           return
        if self.context.private == True:
           if self.treeSecurity():
              return
        self.raiseUnauthorized()
        
    def shortenURL(self,url):        
        return url
    
    def rename(self,item,newName):
        parent = item.__parent__
        del parent[item.__name__]
        parent[newName] = item
        item.__parent__ = parent
        item.__name__ = newName

    def className(self,*args):
        item = self.context if len(args)==0 else args [0]
        return item.__class__.__name__


    def contextClassName(self):
        return self.context.__class__.__name__    

    #def message(self,message):
    #    return self.sendMessage(message)
      
    def raiseUnauthorized(self):
        raise Unauthorized
    
    def getNavBar(self):
         navbar = self.getLayout()['navbar.py']
         if navbar != object:
           return navbar(self)
         else:
           return ""
  
    def getDefaultImage(self):
        context = self.context
        return context.getDefaultImage()

    def getSiteName(self):
        siteRoot = self.getSiteRoot()
        if hasattr(siteRoot, 'siteName'):
            return siteRoot['siteName']
        return None    
    
    def widgetJsonURL(self):
        siteRoot = self.getSiteRoot()
        categoryName = siteRoot.categoryName
        uri = "/" + categoryName + "/json"
        return uri
    
    def parameters(self):
        parameters = {}
        parameters["webPageName"] = self.context.__name__
        context = self.context
        title = context.title if hasattr(context,'title') else ''
        parameters["webPageTitle"] = title
        parameters ["parents"] =list(map(lambda x: x.__name__,
                                         self.parentsUpToSiteRoot()))
        parameters ["banner"] = (self.parentalAcquire("Banner.png")
                                     != None)
        parameters ["logo"] = (self.parentalAcquire("Logo") != None)
        parameters ["homePage"]= getSiteRoot(self.context,self).homePage
        
        if self.isAuthenticated():
            parameters["isAuthenticated"] = True
            principal = self.request.principal
            parameters["handle"]= principal.handle
            parameters["email"]= principal.email
            parameters["userId"] = principal.__name__
            parameters["permissions"]= list(principal.permissions)
        else:
            parameters["isAuthenticated"] = False            
            parameters["handle"]= 'Guest'
            parameters["email"]= ''
            parameters["userId"] = ''            
            parameters["permissions"]= []
        result = json.dumps(parameters)
        return result
    
    
    def safeMethod(self,attribute):
       result = getattr(self, attribute,None)
       if result:
          return result()
       result = getattr(self.context, attribute,None)
       if result:
          return result()        
       return None 


    def debug(self,*args):
        import pdb;pdb.set_trace()
        if args:
          fred = args
          item = args [0]
          pass
        
    def hash(self,value):
         h = hashlib.sha256() 
         h.update(value.encode('utf-8')) # Update the hash using a bytes object
         return h.hexdigest()

    def longestName(self,context,*args):
        if (len (args)==0):
           pass
         
    lorumIpsum = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""

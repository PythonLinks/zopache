#MAYBE TWO PEPOLE CAN HAVE THE SAME SLUGIFIED HANDLE
#M

# Copyright (c) 2004 Zope Foundation and Contributors.
#Copyright Chrisotpher Lozinski 2018
# All Rights Reserved.

# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).


# THIS File WAS EXTRACTED FROM zope.pluggableauth
# AND SIMPLIFIED
import time
import json

from slugify import slugify
import time
from jinja2.sandbox import SecurityError
from BTrees.OOBTree import OOBTree
from zope.schema import ValidationError
from zope.interface import implementer, Interface

from dolmen.container import BTreeContainer
from cromlech.browser import getSession, setSession
from cromlech.security import unauthenticated_principal as anonymous

from zopache.core import Container
from zopache.crud.interfaces import IImutable, IContainer
from zopache.ttw.interfaces import IPrincipalFolder, IInternalPrincipal
from zopache.core.getroot import (getPrincipalFolder,
                                  getPrincipalFolderNoView,
                                  getPublicationRoot,
                                  getProducts)
from zopache.ttw.file import FileBase

class DuplicateIDError(ValidationError):
    pass

from zopache.pages.page import Page


@implementer(IInternalPrincipal)
class InternalPrincipal(FileBase,Page):
    _handle  = ''
    _email = ''
    branchSize = 1    
    chatPermission = False
    contentType = "text/plain"
    description = ""
    lastAuthenticationTime = 0
    lastNotificationTime = 0
    newsPermission = False
    permissions = ['Vote']
    postalCode =""
    source = ""
    talkURL =""
    title = "Your Profile"
    voter = None
    webClass = 'Person'
    gdprPermission = False
    
    def secureParent(self):
        raise SecurityError('''You are not allowed to access attribute "secureParent" on %r %r ''' % (self.name,self.__class__.__name__))
    
    secureParent = property(secureParent)

    def isPage(self):
        return False

    def getCategory(self):
        return json.dumps(self.groups)

    def setCategory(self,value):
        self._grups = set(json.load(value))
        
    category = property (getCategory,setCategory)
    
    def getGroups(self):
         if not hasattr(self,'_groups'):
            self._groups =  set()
         return self._groups

    groups = property (getGroups)
    
    def addGroup(self,name):
        self.groups.add(name)
        self._p_changed
        
    def removeGroup(self,name):
        self.groups.remove(name)
        self._p_changed
    
    def __init__(self):
        self.creationTime=time.time()
        self.modificationTime=time.time()
        Page.__init__(self)
        FileBase.__init__(self)
        
    def postProcessCore(self,view=None):
        pass
    
    def logout(self,session=None, view = None):
        if session is None:
            session = getSession()
            
        if 'user' in session:
            session.clear()
        
    """ Pricipals which are stored in the ZODB Principal Folder"""
    def upVote(self,item):
        self.possiblyCreateVoteCounts()
        key = item.__name__
        if key in self._downVotes:
            del self._downVotes[key]
        if key in self._upVotes:
            del self._upVotes[key]            
            return
        self._upVotes[key] = time.time()
        self._p_changed = True
   
    def downVote(self,item):
        self.possiblyCreateVoteCounts()
        key = item.__name__
        if key in self._upVotes:
            del self._upVotes[key]
        if key in self._downVotes:
           del self._downVotes[key]            
           return
        self._downVotes[key] = time.time()           
        self._p_changed = True
        
            
    def possiblyCreateVoteCounts(self):    
        if not hasattr(self,"_upVotes"):
           self._upVotes = {}
        if not hasattr(self,"_downVotes"):
           self._downVotes = {}

    def slugifiedHandle(self):
        return slugify(self.handle)
                 
    def getTitle(self):
        return self._handle 
        
    def getId(self):
        return self._email    
    
    def getEmail(self):
        return self._email

    def getHandle(self):
        return self._handle
        
    def setEmail(self, email):
        oldEmail = self._email
        if email == oldEmail:
           return
        self._email = email
        if self.__parent__ is not None:
            try:
                getPrincipalFolderNoView(self).notifyEmailChanged(oldEmail,   self)
            except ValueError:
                self._email = oldEmail
                raise


    def setHandle(self, handle):
        oldHandle = self._handle
        if handle == oldHandle:
            return
        self._handle = handle
        if self.__parent__ is not None:
            try:
                getPrincipalFolderNoView(self).notifyHandleChanged(oldHandle,  self)
            except ValueError:
                self._handle = oldHandle
                raise
    def updateAccount(self,accountProxy,userAccount):
        # Mastodon: accountProxy is a live client -- store just its access
        # token, never the client object itself, so ZODB never pickles a
        # requests.Session or version-specific internals.
        # Github: accountProxy is a plain dict -- getattr() can't read dict
        # keys, so it must be extracted with .get(), not getattr().
        # userAccount (Mastodon's AttribAccessDict, Github's plain dict) is
        # not stored at all -- the account identity is already in email/
        # handle, and nothing in this codebase reads it back.
        if isinstance(accountProxy, dict):
            self.accountProxy = accountProxy.get('access_token', accountProxy)
        else:
            self.accountProxy = getattr(accountProxy, 'access_token', accountProxy)

    def postAddProcess (self, view =None):
        #view.notifyUserNewUser()
        view.notifyAdminsNewUser()
        #self.editors = {self.__name__}
        # Before Googel Login, the first user would get permissions
        #if len(self.__parent__)==1:
        #   self.permissions = ['AddContent','EditContent',
        #                       'Manage','Vote','Edit','Add','Python']

            
    title = property(getTitle)
    email = property(getEmail, setEmail)
    id = property(getId)
    handle = property(getHandle, setHandle)    
    @property
    def mastodonId(self):
        return self.handle

    @property

    def mastodonURL (self):
        handle = self.handle.lstrip('@')
        try:
            username, domain = handle.split('@', 1)
        except ValueError:
            raise ValueError(
                f"Invalid Mastodon ID format: {self.handle!r}. "
                "Expected '@username@domain' or 'username@domain'."
            )
        
        return f"https://{domain}/@{username}"




def key(item):
    return item._p_mtime

@implementer(IPrincipalFolder)
class PrincipalFolder(Container):
    """ A Container of Principals.
    """
    ancestorNames = []
    title = "Principal Folder"
    description = "The user objects are stored here. "
    branchSize = 1
    def html (self) :
        return ""
    icon="ttwicons/Container.svg"
    webClass = "PrincipalFolder"
    def __init__(self):
        super(PrincipalFolder, self).__init__()
        self.idByEmail = OOBTree()
        self.idBySlugifiedHandle = OOBTree()

    def getEveryone(self):
       siteRoot = self.__parent__
       people = [siteRoot.get(id) for id in self.idByEmail.values()]
       return people

    def newPerson(self,view):
        newPerson = InternalPrincipal()
        newPerson.__parent__ = self

        #You have to set the name before setting the email.
        #Because it updates the email->name index.        
        root = view.getSiteRoot()
        newName = root.getUniqueNumberString()
        newPerson.__name__= newName
        root.addItem(newPerson)
        return newPerson
        
    def getTitleForDomain(self,view):
        return self.title
    
    def getTitleFor(self,view):
        return self.title    

    def getDescriptionForDomain(self,view):
        return self.description

    def getDescriptionFor(self,view):
        return self.description

    def setJson(self):
        pass

    def values(self):
        all = []
        for item in Container.values(self):
            all.append(item)
        all.sort(key=key, reverse = True)
        return all
    
    def indexTree(self):
        self.idByEmail = OOBTree()
        self.idBySlugifiedHandle = OOBTree()                
        for item in self.values():
           if IInternalPrincipal.providedBy(item):  
              try:
                  self.idByEmail[item.email] = item.__name__
                  slug = item.slugifiedHandle()
                  self.idBySlugifiedHandle[slug] = item.__name__
              except Exception as error:
                  raise Exception (str(error))
          
    def getPrincipalByUserName(self,userName, default = anonymous):
            id = self.getIdByEmail(userName)
            if id == None:
                id = self.getIdByHandle(userName)
            if id != None:    
               principal = self.getPrincipalById(id)
               if principal != None:   
                  return principal
            return default
        
    def getPrincipalById(self,id):
        root = getPublicationRoot(self)
        return root.get(id)

    
    def notifyEmailChanged(self, oldEmail,  principal):
        """Notify the Container about changed email or handle of a user.
        We need this, so that our two other trees can be kept up-to-date.
        """
        # A user with the new login already exists
        if principal._email in self.idByEmail:
            raise ValueError('That Email Address already taken!')
        if oldEmail in self.idByEmail:
            del self.idByEmail[oldEmail]
        self.idByEmail[principal.email] = principal.__name__

    def notifyHandleChanged(self,  oldHandle, principal):
        """Notify the Container about changed email or handle of a user.
        We need this, so that our two other trees can be kept up-to-date.
        """
        # A user with the new login already exists
        if slugify(principal._handle) in self.idBySlugifiedHandle:
            raise ValueError('That Handle is already taken!')        

        oldHandle = slugify (oldHandle)
        if oldHandle in self.idBySlugifiedHandle:
           del self.idBySlugifiedHandle[oldHandle]
           
        handle = principal.slugifiedHandle()
        self.idBySlugifiedHandle[handle] = principal.__name__  

    def __setitem__(self,key,principal):
        if IInternalPrincipal.providedBy(principal):        
           self.idByEmail[principal.email] = principal.__name__
           slug = principal.slugifiedHandle()
           self.idBySlugifiedHandle[slug] = principal.__name__        
        root = getPublicationRoot(self)
        root.addItem(principal)
        BTreeContainer.__setitem__(self,key,principal)


    def unindexPrincipal(self,principal):
        del self.idByEmail[principal.email]
        del self.idBySlugifiedHandle[principal.slugifiedHandle()]

    #REALLY THIS IS DELETE USER    
    def __delitem__(self,name):
        principal = self[name]
        if IInternalPrincipal.providedBy(principal):
            self.unindexPrincipal(principal)
        root = getPublicationRoot(self)
        root.deleteItem(principal)
        BTreeContainer.__delitem__(self,name)        

    def removeItem(self,principal):
        BTreeContainer.__delitem__(self,principal.__name__)

    def loginUser(self,user,form):
        session = getSession()
        session['user'] =getattr(user,'email')
        form.request.principal = user
        
    def getIdByEmail(self, email):
        return self.idByEmail.get (email,None)

    def getIdByHandle(self, handle):
        aSlug = slugify(handle) 
        return self.idBySlugifiedHandle.get(aSlug,None)

    #USED BY REGISTER VALIDATORS
    def existsHandle(self,handle):           
        aSlug = slugify(handle) 
        return aSlug in self.idBySlugifiedHandle            

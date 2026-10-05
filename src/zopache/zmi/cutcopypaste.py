##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Copy, Paste and Move support for content components
"""
__docformat__ = 'restructuredtext'

import transaction
import crom
from slugify import slugify, SLUG_OK
from zope.interface import implementer, Invalid
from dolmen.container.interfaces import IBTreeContainer#, IOrderedContainer
from zope.interface import implementer
from zope.interface import Interface

from zopache.core.transactionnote import TransactionNote
from zopache.copy import copy
from zopache.crud.interfaces import IRenameable,IDeletable,ICopyable
from zopache.crud.interfaces import IMoveable 
from zopache.core.uniquename import UniqueName
from zopache.zmi.interfaces import IObjectCutter
from zopache.zmi.interfaces import IObjectDeleter
from zopache.zmi.interfaces import IObjectCopier
from zopache.zmi.interfaces import IObjectRenamer
from zopache.zmi.interfaces import IObjectPaster
from .cutfolder import cutFolder
from zopache.core.getroot import getSiteRoot

class BaseClass(TransactionNote,UniqueName):
    def __init__(self, object):
        self.context = object
        self.__parent__ = object # TODO: see if we can automate this


    def moveFrom(self,firstFolder,firstName, secondFolder, secondName):

        obj=firstFolder[firstName]
        del firstFolder [firstName]
        secondFolder[secondName] = obj

@crom.adapter
@crom.sources(Interface)
@crom.target(IObjectRenamer)
class Renamer(BaseClass):
    def __init__(self, object):
        self.context = object.__parent__
        self.__parent__ = object.__parent__ # TODO: see if we can automate this
        
    def renameItem(self, oldName, newName,view):
        container=self.context
        obj = container.get(oldName)
        if obj is None:
               view.error += oldName + "WAS NOT FOUND <br>"
        if not self.allowed(obj):
                     return
        newName=self.uniqueContainerName(container,newName)
        newName = slugify(newName,ok=SLUG_OK+'.', lower= False)
        if hasattr(obj,'preMoveProcess'):
            obj.preMoveProcess(view)
        self.moveFrom(container,oldName, container, newName)
        if hasattr(obj,'postMoveProcess'):
            obj.postMoveProcess(view)        
        
    def allowed(self,obj):
        if  IRenameable.providedBy(obj):
                return True
        return False

@crom.adapter
@crom.sources(Interface)
@crom.target(IObjectCutter)
class Cutter(BaseClass):
    """Adapter for moving objects between containers
    """

    def cut(self,view):
        self.view = view        
        """ Move the object to the pastefolder"""
        obj=self.context
        if not self.allowed(obj):
                self.view.error += self.context.__name__  + """" 
                     IS NOT ALLOWED TO BE CUT <br>"""
                return

        oldName=obj.__name__
        toFolder=cutFolder(view)

        newName=self.uniqueContainerName(toFolder,oldName)
        container = obj.__parent__
        if hasattr(obj,'preMoveProcess'):
            obj.preMoveProcess(view)        
        self.moveFrom(container, oldName, toFolder, newName)
        self.describeTransaction(" Cut ", obj)

    def allowed(self,item):
        if  IMoveable.providedBy(item):
                return True 
        return False

@crom.adapter
@crom.sources(Interface)
@crom.target(IObjectCopier)
class Copier(BaseClass):
    def copy(self,view):
        self.view = view        
        """ Move the object to the pastefolder"""
        obj=self.context
        if not self.allowed(obj):
                self.view.error +=self.context.__name__+ " IS  NOT ALLOWED TO BE COPIED <br>"
                return
        toFolder=cutFolder(view)
        oldName=obj.__name__
        newName=self.uniqueContainerName(toFolder,oldName)
        parent = obj.__parent__
        obj.__parent__ = None
        toFolder[newName]= copy(obj)
        obj.__parent__ = parent
        self.describeTransaction(" Copy ", obj)
         
    def allowed(self,item):
        if hasattr(item,'canCopy'):
           return item.canCopy()        
        if  ICopyable.providedBy(item):
                return True
        return False


@crom.adapter
@crom.sources(Interface)
@crom.target(IObjectPaster)
class Paster(BaseClass):
                           
    def paste(self,view):
        self.view = view        
        """Copy this object to the `target` given.
        """
        toContainer = self.context
        fromFolder=cutFolder(view)
        
        #Modifying a BTree while iterating over it does not work. 
        items=[]
        for item in fromFolder.values():                   
            items.append(item)
        for item in items:    
           orig_name = item.__name__
           new_name=self.uniqueContainerName(toContainer,orig_name)
           if not self.allowed(item):
               self.view.error +=orig_name + " WAS NOT PASTED <br>"
               continue 
           self.moveFrom(fromFolder, orig_name, toContainer, new_name)
           if hasattr(item,'postMoveProcess'):
               item.postMoveProcess(view)

           self.describeTransaction(" Paste ", toContainer[new_name])
           
    def allowed(self,obj):
        if hasattr(obj,'canCopy'):
           return obj.canCopy()                
        return True


#THIS IS THE GENERIC DELETER
# JUST DELETE THE OBJECT
@crom.adapter
@crom.sources(Interface)
@crom.target(IObjectDeleter)
class Deleter(BaseClass):
    def deleteItem(self,view):
        self.view = view
        obj=self.context
        container=obj.__parent__
        name=obj.__name__
        if not self.allowed(obj):
            self.view.error +=  name + " was not deleted. <br>"
            return
        
        # HAVE TO DESCRIE BEFORE DELETING OTHERWISE NO NAME AVAILABLE
        if hasattr(obj,'preDeleteProcess'):
            obj.preDeleteProcess(view)                
        del container[name]
        if view.request.principal == obj:
           obj.logout()

        
    def allowed(self,item):
        if hasattr(item,'canDelete'):
           return item.canDelete()
        if IDeletable.providedBy(item):
                return True
        return False

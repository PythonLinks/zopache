import crom
from zopache.crud.interfaces import IRenameable,IDeletable,ICopyable
from zopache.zmi.cutcopypaste import Cutter, Copier, Deleter
from zopache.zmi.cutcopypaste import Paster, Renamer
from zopache.pages.interfaces import IPageBase
from zopache.pages.uniquename import UniquePageName

from zopache.zmi.interfaces import IObjectDeleter
from zopache.zmi.cutfolder import cutFolder


from zopache.zmi.interfaces import IObjectCutter
from zopache.zmi.interfaces import IObjectDeleter
from zopache.zmi.interfaces import IObjectCopier
from zopache.zmi.interfaces import IObjectRenamer
from zopache.zmi.interfaces import IObjectPaster
from zopache.core.transactionnote import TransactionNote
from zopache.core.getroot import getPublicationRoot


            
@crom.adapter
@crom.sources(IPageBase)
@crom.target(IObjectCopier)
class CategoryCopier(Copier):
    # YOU NEVER WANT TO COPY CATEGORIES
    #REALLY WANT PROXY OBJECTS
    def allowed(self,item):
        return False

@crom.adapter
@crom.sources(IPageBase)
@crom.target(IObjectCutter)
class PageCutter(Cutter):
    """Adapter for moving objects between containers
    """
    #IF IT IS A CATEOGRY DELETE FROM VALUESByTOKEN
    def cut(self,view):
        super().cut(view)
        
@crom.adapter
@crom.sources(IPageBase)
@crom.target(IObjectPaster)
class PagePaster(Paster,UniquePageName):
                           
    def paste(self,view):
        self.view = view        
        """Copy this object to the `target` given.
        """
        toContainer = self.context
        fromFolder=cutFolder(view)
        #Modifying a BTree while iterating over it does not work. 
        items=[]
        items = list( fromFolder.values())
        siteRoot = view.getSiteRoot()
        for item in items:
            if not self.allowed(item):
                 self.view.error = "Not Pasted"
                 continue
            orig_name = item.__name__
            new_name=self.uniqueName(toContainer,orig_name,"Copy")
            self.moveFrom(fromFolder, orig_name, toContainer, new_name)

            
class ItemNotFoundError(Exception):
    pass
@crom.adapter
@crom.sources(IPageBase)
@crom.target(IObjectRenamer)
class PageRenamer(Renamer,UniquePageName):
    def renameItem(self, oldName, newName,view):
        self.view = view
        item = self.context[oldName]
        if not self.allowed(item):
             self.view.error += oldName + " Not Allowed "
             return
        container=self.context
        obj = container.get(oldName)
        if obj is None:
            raise ItemNotFoundError(self.container, oldName)
        newName=self.uniqueName(container,newName)
        siteRoot = obj.getPublicationRoot()
        #siteRoot.unIndexItem(obj)
        self.moveFrom(container,oldName, container, newName)

        
#FOR DELETING CATEGORIES
#IF VIDEO DELETE LINK FROM CONFERENCE
#IF NOT EMPTY DO NOT DELETE.
#DELTE ROOT.INDEX
@crom.adapter
@crom.sources(IPageBase)
@crom.target(IObjectDeleter)
class PageDeleter(Deleter):
    def deleteItem(self,view):
        self.view = view
        contained=self.context
        name=contained.__name__
        if not self.allowed(contained):
            self.view.error +=   name + " was not deleted. <br>"   
            self.view.error += " Maybe it still contains something"
            return
        # DELETE THE OBJECT
        container=contained.__parent__
        # So even though root is not used till later, 
        #we have to do this before deleting the __parent__ Pointer.
        if IPageBase.providedBy (container):
           root = getPublicationRoot(contained)
        if hasattr(contained,'preDeleteProcess'):
             contained.preDeleteProcess(view)
        del container[name]
        
        # IF IT IS A VIDEO DELETE IT FROM THE CONFERENCE
        if contained.isVideo():
           self.describeTransactionWithText("It was a Video")
           if hasattr(contained,'conference'):
               del contained.conference.talks[name]
           
        # UNLESS IT IS THE ROOT CATEGORY, RECALCULATE THE JSON   
        # THIS SHOULD ALWAYS BE TRUE
        if IPageBase.providedBy (container):
           root.recalculateRootJSON()

           
    def allowed(self,item):
         if len(item) > 1:
             return False
         if 'Logo' in item:
             return True
         return True    

from zopache.zmi.interfaces import IURLSegment
from zopache.pages.interfaces import INotebook     
@crom.adapter
@crom.sources(INotebook)
@crom.target(IURLSegment)
class IPNotebookAdaptor(object):
    def __init__(self,context):
        self.context=context
    def getSegment(self):
        return 'source'

    
from zopache.pages.interfaces import IMarkdown
@crom.adapter
@crom.sources(IMarkdown)
@crom.target(IURLSegment)
class IPNotebookAdaptor(object):
    def __init__(self,context):
        self.context=context
    def getSegment(self):
        return 'aceedit'        

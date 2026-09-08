from dolmen.forms.base import Action, SuccessMarker
from zopache.core.transactionnote import TransactionNote
from dolmen.forms.base.markers import FAILURE, SUCCESS
from dolmen.container.interfaces import IBTreeContainer

from cromlech.browser import IURL
from zopache.core.getroot import getPublicationRoot
from zope.location import ILocation

class Base(object):
  def deleteOne(self,child,view):          
      if hasattr(child,'preDeleteProcess'):
                child.preDeleteProcess(view)
      del child.parent[child.name]
        
  def deleteRoot(self,view):
        container = view.context.parent
        url = str(IURL(container, view.request))
        url = url + '/manage'
        context = view.context       
        self.deleteOne(context,view)
        view.sendMessage(self.successMessage)           
        return SuccessMarker('Deleted', True, url=url)

class DeleteBranch(Action, Base):
    """Delete action for any locatable context.
    """
    successMessage = ("This branch  has been deleted.")
    failureMessage = ("This branch could not be deleted.")
    
    def __call__(self, form):
        view = form                
        context = view.context
        self.deleteDescendents(context,view)
        return self.deleteRoot(view)



    def deleteDescendents(self,parent,view):
        all = []
        for child in parent.values():
            all.append(child)
            if IBTreeContainer.providedBy(child):
                self.deleteDescendents(child,view)

        for child in all:
            self.deleteOne(child,view)
            

class DeleteLeaf(Action,Base):
    successMessage = "The node has been deleted."
    failureMessage = """"This node  could not be deleted,
                     it contains something other than an image"""
    
    def __call__(self, form):
        view = form               
        context = view.context    
        if (len(context)==0):
            return self.deleteRoot(view)
           
        elif ((len(context) == 1)  and 
              (IImageBase.providedBy(next(context.values())))):
            return self.deleteRoot(view)               
               
        else:
            form.status = self.failureMessage
            return FAILURE

from zopache.ttw.interfaces import IImageBase               
class DeleteChildren(Base,Action):
    successMessage = "Children were deleted"
    failureMessage = "There are no children."
               
    def __call__(self, form):
        all = []
        view = form         
        context = view.context
        for child in context.values():
            if not IImageBase.providedBy(child):    
                all.append(child)
        
        if len (all) == 0:
            form.submissionErrors.append( self.failureMessage)
            return FAILURE
               
        for child in all:
            if child.parent != None:
               self.deleteOne(child,view)
            else:
              print (child.title, child.articleURL)
              pass
        form.status = self.successMessage
        return SUCCESS        

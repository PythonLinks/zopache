import crom
from zopache.zmi.cutcopypaste import Renamer, Deleter , Copier
from zopache.ttw.interfaces import IInternalPrincipal 

from zopache.zmi.cutfolder import cutFolder

from zopache.zmi.interfaces import IObjectCopier
from zopache.zmi.interfaces import IObjectDeleter
from zopache.zmi.interfaces import IObjectRenamer
from zopache.core.transactionnote import TransactionNote

@crom.adapter
@crom.sources(IInternalPrincipal)
@crom.target(IObjectCopier)
class PrincipalCopier(Copier):
    # YOU NEVER WANT TO COPY Principals
    def allowed(self,item):
        return False

@crom.adapter
@crom.sources(IInternalPrincipal)
@crom.target(IObjectRenamer)
class PrincipalRenamer(Renamer):
    # YOU NEVER WANT TO RENMAE Principals
    def allowed(self,item):
        return False

@crom.adapter
@crom.sources(IInternalPrincipal)
@crom.target(IObjectDeleter)
class PrincipalDeleter(Deleter):
    def deleteItem(self,view):
        self.view = view
        contained=self.context
        container=contained.__parent__
        name=contained.__name__
        self.describeTransaction("Deleted a principal",contained)
        del container[name]

    def allowed(self,item):
         return True    
     

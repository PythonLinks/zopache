from slugify import slugify, SLUG_OK

from dolmen.forms.base import Action, SuccessMarker
from dolmen.forms.base.markers import FAILURE

from .interfaces import IObjectCutter, IObjectCopier, IObjectRenamer
from .interfaces import IObjectPaster, IObjectDeleter
from .interfaces import IObjectRetitler, IObjectRenamer
from zopache.crud.utilities import title_or_name
from zopache.core.transactionnote import TransactionNote

class BaseAction(Action):
    def getValues(self,form,message,which='ids_list'):
        request = form.request
        if not hasattr(request, 'POST'):
            return []
        POST = request.POST
        ids = POST.getall(which)
        if not ids or len(ids)==0:
            form.error += message
            return []
        return ids

    def reTitle(self,form):    
        """Given a sequence of tuples of old, new ids we rename"""
        ids = self.getValues(form,
               "You did not specify any object to reTitle")
        newTitles = self.getValues(form,
                            "You did not specify any new Titles",
                            which = 'newTitleValue_list')
        if (len (ids) != len (newTitles)):
            form.error += "Lengs of Ids and Titles do not match. "
            return
        for id , newTitle in zip (ids, newTitles):        
            item = form.context[id]
            reTitler = IObjectRetitler(item)
            reTitler.retitleItem(item,newTitle,form)   
        return SuccessMarker('Retitled', True)
    
class ReName(BaseAction):
    def __call__(self,form):
        ids = self.getValues(form,
               "You did not specify any object to rename")
        newIds = self.getValues(form,
                            "You did not specify any new names",
                            which = 'newNameValue_list')
        if (len (ids) != len (newIds)):
            form.error += "Lengths of Ids and Names  do not match. "
            return

        for oldId , newId in zip (ids, newIds):
            item = form.context[oldId]
            newId = newId
            if newId != oldId:
                renamer = IObjectRenamer(item)
                renamer.renameItem(oldId, newId,form)
        return SuccessMarker('Renamed', True)
    
class ReTitle(BaseAction):                
    def __call__(self,form):
        return self.reTitle(form)
    

class ReBoth(BaseAction):
    def __call__(self,form):

        result = self.reTitle(form)
        if not hasattr(form.context, "valuesAsList"):
            return result

        ids = self.getValues(form,
               "You did not specify any object to reTitle")
        newTitles = self.getValues(form,
                            "You did not specify any new Titles",
                            which = 'newTitleValue_list')
        if (len (ids) != len (newTitles)):
            form.error += "Lengs of Ids and Titles do not match. "
            return
        for id , newTitle in zip (ids, newTitles):        
            item = form.context[id]
            newId = slugify(newTitle,ok=SLUG_OK+'.', lower= True)
            if newId != item.__name__:
                renamer = IObjectRenamer(item)
                renamer.renameItem(item.__name__, newId,form)       
        return SuccessMarker('Retitled', True)        
        return SuccessMarker('Renamed', True)
    

    
class CopyObjects(BaseAction):
    def __call__(self,form):
        """Copy objects specified in a list of object ids"""
        ids = self.getValues(form,
             "You didn't specify any ids to copy.")
        for id in ids:
            item = form.context[id]
            copier = IObjectCopier(item)
            if not copier.allowed(item):
                form.error += "Object "+ id + " cannot be copied"
                return
            copier.copy(form)
        return SuccessMarker('Copied', True)
    
class CutObjects(BaseAction):
    def __call__(self,form): 
        """Cut objects specified in a list of object ids"""
        ids = self.getValues(form,"You didn't specify any ids to cut.")
        for id in ids:
            item = form.context[id]
            cutter = IObjectCutter(item)
            if not cutter.allowed(item):
                title = title_or_name(item)
                form.error += ("Object " +
                               id + ' ' + title + 
                               " Cannot be Cut")
                return
            cutter.cut(form)
        return SuccessMarker('Cut', True)
    
class PasteObjects(BaseAction):            
    def __call__(self,form):
        target = form.context
        paster = IObjectPaster(target)
        paster.paste(form)
        return SuccessMarker('Pasted', True)
    
class DeleteObjects(BaseAction):        
    def __call__(self,form):
        """Remove objects specified in a list of object ids"""
        ids = self.getValues(form,
                    "You did not select any objects to delete")
        container = form.context

        note = f"Deleting {len(ids)} Objects From: "
        note += form.context.__name__ + "<Br>"
        note += '<br>'.join(ids)
        note = note[0:100]        
        TransactionNote().describeTransactionWithText(note)

        for id in ids:
            item= container [id]
            deleter = IObjectDeleter(item)
            deleter.deleteItem(form)
            
        return SuccessMarker('Deleted', True)
            

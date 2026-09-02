from time import time
from datetime import datetime, timedelta


from cromlech.security import unauthenticated_principal as anonymous
from cromlech.browser.exceptions import HTTPFound
from dolmen.forms.base import Action,Actions
from dolmen.forms.base import Actions


from zope.interface import Interface
from zope.schema import Text, Float

from zopache.core.viewdecorators import *
from zopache.crud.forms import EditForm
from zopache.pages.interfaces import IPageBase
from zopache.remote.irss import IRSSArticle
from zopache.crud.update import Cancel, Edit
from zopache.crud.update import Edit
from zopache.remote.mastodon.basebot import MastodonBot


class Toot(Edit):
    def __call__(self, form):
        Edit.__call__(self,form)
        form.nowToot()
        
class TootAndView(Toot):
    def __call__(self, form):
        Edit.__call__(self,form)
        form.nowToot()
        if getattr(form.context, 'tootURL',None):
             raise HTTPFound(form.context.tootURL)


class OnlyToot(Edit):
    def __call__(self, form):
        form.nowToot()
        
class OnlyTootAndView(Toot):
    def __call__(self, form):
        url = form.nowToot()
        if url != '':
           raise HTTPFound(url)
         
class Reset(Action):
    def __call__(self, form):
        context = form.context
        context._toot = context.defaultToot(view = form)

class OnlyReset(Action):
    def __call__(self, form):
        raise HTTPFound(".")

class Delete(Action):
    def __call__(self, form):
        #Delete Image not supported.
        tootId = getattr(form.context,'tootId',None)
        if not tootId:
            form.submissionError += "No Toot to Delete"            
        try:
            result = form.getUserProxy().status_delete(tootId)
            del form.context.tootURL 
            del form.context.tootId 
        except Exception as error:
            form.report(error)
            form.submissionError += """
                 <br><br> Maybe that means that there is no such toot."""
            
    #2021 Looks like the Mastodon API does not support this
    """
    def deleteImage(self):
        
        image = self.getDefaultImage()
        mediaId = getattr(image,'mediaId',None)        
        if mediaId == None:
            form.submissionError += "No Image to Delete"
            return 
        try:
            result = form.getUserProxy().status_delete(tootId)
            del form.context.tootURL 
            del form.context.tootId 
        except Exception as error:
            form.report(error)
            form.submissionError += '''
                 <br><br> Maybe that means that there is no such toot.'''
         """  
        
class IClass(Interface):

    toot= Text(
        title = 'Toot',
        description = 'Say something!',
        required = False,
        default = '',
    )

    spoilerText = Text(
        title = 'SpoilerText',
        description = 'If empty, not displayed',
        required = False,
        default = '',
    )    
    
    delay= Float(
        title = 'Delay',
        description = 'Hours until posted',
        required = False,
        default = 0.,
    )         

    
@form_component
@name ('toot')
@context(IPageBase)
class TootForm (EditForm,MastodonBot):
    title = 'Toot'
    subTitle = 'Limit 500 characters'
    interface = IClass
    fields = Fields(IClass)
    tootURL = ""
    layoutName = "UserMenu"
    twitterId = ''
    link = ''
    imageURL = ""
    scheduledAt = 0
    tempScheduledAt = 0

    
    def getDefaultImage(self):
        context = self.context
        
        if 'Banner' in context:
            return context['Banner']
        
        if 'Logo' in context:
            return context['Logo']        

        if (hasattr(context,'rssFeed') and
          'Logo' in context.rssFeed):
            return context.rssFeed['Logo']           
     
        image =  self.parentalAcquire('Logo', context = context)
        if image:
            return image
        
        raise Exception("This toot  needs an image!")

        
    def update(self):
        if self.request.principal == anonymous:
            self.oauth()
            
        self.tootURL =  getattr(self.context,'tootURL','')
        self.tempTootURL =  getattr(self,'tootURL','')
        
        image = self.getDefaultImage()
        if image:
          self.imageURL = getattr(image, 'mastodonURL','')
 
        if hasattr(self.context,'rssFeed'): 
           rssFeed = self.context.rssFeed
           if hasattr(rssFeed,'twitterId'):
              self.twitterId = twitterId = rssFeed.twitterId
              self.link = ("https://twitter.com/" + twitterId) if twitterId else ''
        self.canToot =  self.request.principal.accessToken
        
        self.template = self.getTemplates()['toot']
        #if self._toot == "":
        #   context = form.context
        #   context._toot = context.defaultToot(view = form)            
        self.updateLocalActions()
        EditForm.update(self)
    
    def nowToot(self):
         context = self.context
         tootText = self.request.form["form.field.toot"]
         if tootText== "":
            self.submissionError += """You submitted an empty toot,
                               so nothing 
                               was posted."""
            return ''
         mediaList = self.mediaIdAsList()
         spoilerText = context.spoilerText
         minDelay = 0.03 #(hours)
         delay = self.context.delay
         if delay == None:
             delay = 0
         if delay < minDelay:
             delay = self.delay = 0
             scheduledAt = None
         else:    
             scheduledAt = datetime.now() + timedelta( hours=delay + 1 )
         inReplyToId = (context.tootId
                        if self.className(context)=='Toot'
                        else None)
         try:
            tootDict = self.getUserProxy().status_post(
                                            tootText,
                                            in_reply_to_id=inReplyToId,
                                            spoiler_text = spoilerText,
                                            media_ids=mediaList,
                                            scheduled_at = scheduledAt
        )
                                 
            if self.isManager():
                target = self.context
            else:
                target = self
                
            tootTime = time()
            #Only need to do this if
            #There is a future message
            if delay >0:
                tootTime += (delay * 3600)
                at= tootDict["scheduled_at"]
                if at:
                   self.sendMessage("Your Toot will show up at: " +
                                 str(at), type = "Error")
                self.sendMessage("local Server Time: " +
                                 str(datetime.now()), type = "Error")
                            
            if tootDict.get('url',False):
                target.tootURL = tootDict.url

            if self.treeSecurity():
               self.context.getEmbed(self)
               
            if tootDict.get('id',False):
                target.tootId = tootDict['id']

            if tootDict.get('schedule_at',False):
                target.scheduledAt = tootDict['scheduledAt']
                
            target.lastTootTime = tootTime
                
            #Otherwise the delete action does not show up. 
            self.updateLocalActions()
            if 'url' in tootDict:                            
                return tootDict ["url"]
            return ""
        
         except Exception as error:
            self.report(error)
            self.submissionError += """ <br><br> 
               Sorry about that. 
               Try reducing the number of charactrs by 5. 
               <br><br>"""
            return False
        
    def report (self,error):
        self.submissionError += (error.args[3] if len(error.args) > 3
                                        else str(error))
        
    def updateLocalActions(self):
        if self.treeSecurity():
            self.addAuthorizedActions()
        else:
            self.addUnAuthorizedActions()
            
    def addAuthorizedActions(self):
        actionList = [Edit("Save",'save'),
                      Toot("Toot","toot"),
                      TootAndView("Toot And View","tootView"),
                      Reset("Reset",'reset')
                      ]
        if hasattr(self.context,'tootURL'):
              actionList.append(Delete("Delete Toot","deleteToot"))
        actionList.append(Cancel("Cancel","Cancel"))
        actionList = tuple(actionList)                  
        self.actions = Actions(*actionList)

    def addUnAuthorizedActions(self):
        actionList = [OnlyToot("Toot","toot"),
                      OnlyTootAndView("Toot And View","tootView"),
                      Cancel("Cancel","Cancel")                      
                      ]
        actionList = tuple(actionList)                  
        self.actions = Actions(*actionList)        

        
    def acquireTitle(self):
        return 'Toot about: '
    
    @property
    def subTitle(self):
       return  self.context.title 

    def postrocess(self):
        pass
    
    
    def mediaIdAsList(self):
        #if self.className() == "EmbedVideo":
        #    return None
        image = self.getDefaultImage()
        mediaId = getattr(image,'mediaId',None)
        if mediaId != None:
           return [mediaId]
        data , mimeType, title = image.mastodonImage()
        
        try: 
           mediaDict =   self.getUserProxy().media_post(media_file = data,
                                          mime_type = mimeType,
                                          description = title,
                                          focus = None)
           image.mastodonURL = mediaDict['url']
           image.mastodonId = mediaDict['id']           
           return [image.mastodonId]
        except Exception as error:
            self.report (error)
            return [] 



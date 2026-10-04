# -*- coding: utf-8 -*-
#This software is subject to the CV and Zope Public Licenses.
from slugify import slugify, SLUG_OK

from webpreview import web_preview

from zope.event import notify
from zope.location import ILocation
from zope.lifecycleevent import ObjectCreatedEvent
#https://github.com/ludbek/webpreview
from webpreview import web_preview
import requests
from html_to_etree import parse_html_bytes
#https://github.com/fluquid/extract-social-media
from extract_social_media import matches_string, find_links_tree
from dolmen.forms.base import Actions
from cromlech.browser import IURL
from dolmen.forms.base import Action, SuccessMarker
from dolmen.forms.base.markers import FAILURE
from dolmen.forms.base.utils import set_fields_data, apply_data_event
from cromlech.browser.exceptions import HTTPFound
from dolmen.forms.base.errors import Error, Errors
from zopache.core.getroot import getSiteRoot
from zopache.crud import i18n as _
from zopache.core.uniquename import UniqueName
from zopache.core.transactionnote import TransactionNote
from zopache.crud.getimage import getImage

class Add(Action, UniqueName, TransactionNote):
    """Add action for an IAdding context.
    """
    def appendName(self,url,name):
        return url + "/" + name
    
    def __init__(self, title, factory):
        Action.__init__(self,title)
        self.factory = factory

    def __call__(self, form):
        self.form=form
        obj= form.factory()
        self.new=form.new=obj
        data, errors = self.form.extractData()
        if errors:
            form.submissionError = errors
            return FAILURE
        self.data = data
        errors = self.setFields()
        if errors:
            form.submissionError = errors
            return FAILURE

        return self.callInner(obj,data,form)
    
    def baseURL(self):
        return self.form.absoluteURL (self.new)

    #THERE CAN BE ERRORS IN CALL INNER,
    #PARTICULARLY WITH COMPINLING THE TEMPLATE
    #SO THIS SHOULD ALSO BE WRAPPED IN ERROR
    #CATCHING AND REPORTING
    def callInner(self,obj,data,form):     
        notify(ObjectCreatedEvent(obj))
        self.actuallyAdd(obj,data)
        #form.sendMessage("Content created")
        baseURL = self.baseURL()
        self.describeWithView(obj,form)

        #NOW DO Form Specific newURLs. 
        if hasattr(form, 'newURL'):
           url=self.form.newURL(baseURL)
        else:
           url=self.newURL(baseURL)
        #Form Specific postAddProcessing
        if hasattr(form,'postAddProcess'):
               form.postAddProcess()
        elif hasattr(form.new,'postAddProcess'):
               form.new.postAddProcess(view=form)

        #Now do form specific returns
        #DISCORD USES THIS, DOES NOT REDIRECT
        if hasattr(form,'getReturn'):
            return form.getReturn(url)
        else:
           return SuccessMarker('Added', True, url=url,code=307)
    
    def setFields(self):
            set_fields_data(self.form.fields, self.new, self.data)
            return Errors()

    def getName(self,data):
        if hasattr(self.form, 'newName'):
           newName = self.form.newName(data)
        else:   
           newName = self.newName(data)
        return newName
    
    def actuallyAdd(self,item,data):
        newName = self.getName(data)
        context = self.form.context
        context[newName]=item

    def newURL(self,baseURL):
        if hasattr(self.form, 'newURL'):
            return self.form.newURL(baseURL)
        else:
            return baseURL

    def newName(self,data):
        name =  data['__name__']        
        return self.uniqueContainerName(self.form.context,name)

class AddAction(Add):
    pass
    
class AddByName(Add):
    pass

class AddByTitle (Add):
    def actuallyAdd(self,item,data):
        if hasattr(self.form,'newName'):
            newName = self.form.newName(data)
        else:    
            newName = self.newName(data)        
        context = self.getContext(data)
        context[newName]=item

        if hasattr(self.new,'imageURL'):
            getImage (self.new,self.new.imageURL)
            del self.new.imageURL
            
    def baseURL(self):
        result = "/" + self.form.urlEncode(self.new.__name__)
        return result
    
    def getContext(self,data):
        return self.form.context
    
    def newName(self,data):    
        newName =  data['title']
        return self.uniqueBothName(self.form.context,newName)

class AddByJSON(AddByTitle):
    def newName(self,data):
        newName =  self.form.newName(data)
        return self.uniqueBothName(self.form.context,newName)
    
    def setFields(self):
        errors = self.form.applyData(self.data)
        return errors

class AddByJsonAndEdit(AddByJSON):
    def newURL(self,baseURL):
        return baseURL + '/editPolitician'
    
class AddByTitleAndCkEdit(AddByTitle):    
    def newURL(self,baseURL):
        return baseURL + '/ckedit'
    

class AddByTitleToTreeAndView(AddByTitle):

    def getContext(self,data):
        if not 'categoryName' in data:
            return self.form.context
        siteRoot = self.form.getSiteRoot()
        categoryName = data ['categoryName']
        category = siteRoot [categoryName]
        return category
    
    def setFields(self):
            set_fields_data(self.form.fields, self.new, self.data)
            return Errors()
    
class AddAndView(AddByName):
    def newURL(self,baseURL):
        return baseURL + '/index'        

        
from zopache.business.interfaces import IOrganization
from bs4 import BeautifulSoup
class AddByCrawl(Add):
    fields = IOrganization
    def __call__(self, form):
        self.form = form
        self.data = form.request['form.field.data']

        soup = BeautifulSoup(self.data, 'html.parser')
        divs = soup.findAll("div", {"class": "views-rows"})
        for item in divs:
            new = form.factory
            new.imageURL = item.img.src
            title = item.find("div",{"class":"views-field-title"})
            title = title.h2.a.content
#views-field-field-website
# .a .urlind_all('a'):

        
    def setFields(self):
            set_fields_data(self.fields, self.new, self.data)
            
    def createItem(self):
        errors = Errors()
        new = self.new=self.form.factory()
        remoteURL = new.remoteURL
        try:
            result = web_preview(remoteURL, parser="html.parser")
            new.title = result[0]
            new.description = result[1]
            new.imageURL = result[2]
        except:

            error = Error("Failed to Fetch and Parse URL")
            errors.append(error)
        if hasattr(new,'imageURL'):
           getImage(new,new.imageURL) 
        return errors

class Cancel(Action):
    """Cancel the current form and return on the default content view.
    """

    def __call__(self, form):
        content = form.getContentData().getContent()
        url = str(IURL(content, form.request))
        return SuccessMarker('Aborted', True, url=url)

class View(Action):
    """ View the object.
    """

    def __call__(self, form):
        content = form.getContentData().getContent()
        url = str(IURL(content, form.request))
        return SuccessMarker('Aborted', True, url=url)    

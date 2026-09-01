import json
from dolmen.container import IBTreeContainer

from dolmen.view import View
#from dolmen.view import name, context, view_component
from cromlech.webob.response import Response

from zopache.core.viewdecorators import *
from zopache.pages.interfaces import ICategory
from zopache.json.interfaces import  IMultilingual

def make_json_response(view, result, *args, **kwargs):
        response = view.responseFactory()
        response.write(result or u'')
        response.content_type=u'application/json'
        return response    

#GETS ALL THE ARTICLES
@view_component
@name('articles.json')
@target(IView)
@context(ICategory)
class Articles(View):
    responseFactory = Response
    make_response = make_json_response
    def render(self):
        if self.context.__name__ not in ['categories']:
           return 'JSON is not available for that object.'
        asDict = self.context.asDict(classes =['Category','RSS','RSSArticle'])
        return json.dumps(asDict, indent = 2)


#GET ALL THE MULTILIGUAL
@view_component
@name('json')
@target(IView)
@context(IMultilingual)
class Multilingual(View):
    responseFactory = Response
    make_response = make_json_response
    def render(self):
        if self.context.__name__ not in ['syllabus']:
           return 'JSON is not available for that object.'
        asDict = self.context.asDict(classes =['Multilingual'])
        return json.dumps(asDict, indent = 2)


#THIS ONE JUST GETS THE TREE OF CATEGORIES
@view_component
@name('categories.json')
@target(IView)
@context(ICategory)
class Categories(View):
    responseFactory = Response
    make_response = make_json_response
    def render(self):
        if self.context.__name__ not in ['all-news','climate-change']:
           return 'JSON is not available for that object.'
        asDict =  self.context.asDict()
        return json.dumps(asDict,  indent = 2)               

from zope.interface import Interface
#ALL THE PARTIES
@view_component
@name('parties.json')
@target(IView)
@context(Interface)
class Parties(View):
    responseFactory = Response
    make_response = make_json_response
    def render(self):
        if self.context.__name__ not in ['usa']:
           return 'JSON is not available for that object.'
        asDict =  self.context.asDict()
        return json.dumps(asDict,  indent = 2)               




 

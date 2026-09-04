import re
from dolmen.forms.base.errors import Error,Errors
from zope.schema import ValidationError
from slugify import slugify
import json

#Needed to add a missing args method to Dolmen.Forms.Base.Errors.
class ArgsError(Error):
     @property
     def args(self):
          return [self.title,self.identifier]

#From Zope.schema.DottedName
# An identifier is a letter or underscore, followed by
# any number of letters, underscores, and digits.
_identifier_pattern = r'[a-zA-Z_]+\w*'

_isDotted = re.compile(
    # The start of the line, followed by an identifier,
    '^' + _identifier_pattern
    # optionally followed by .identifier any number of times
    + r"([.]" + _identifier_pattern + r")*"
    # followed by the end of the line.
    + r"$").match

     
class VirtualHostValidator(object):

    def __init__(self, fields, form):
        self.form = form
        
    def getDict(self, data):
        form = self.form
        siteRoot = self.form.context
        theJson = data ['source']
        theJson = json.loads (theJson)
        return theJson
   
    def validate(self, data):        
        errors = Errors()
        theDict = self.getDict(data)

        #MAKE SUE THE DOMAINS ARE DOTTED NAQMES
        for key in theDict.keys():
           if not _isDotted(key):
                msg = key + " is not a Valide domain name."
                error =ArgsError(title=msg, identifier= key)
                errors.append(error)


        #NOW CHECK THAT THE VALUES EXITS   
        context = self.form.context           
        for value in theDict.values():
           path = value.split("/")
           for item in path:
               if item not in context:
                    msg = ""
                    msg = value + " does not exist in this directory."
                    error =ArgsError(title=msg, identifier= key)
                    errors.append(error)
                    break
        return errors        


   

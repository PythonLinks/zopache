from zope.interface import Interface
from zope import schema
from dolmen.container import IBTreeContainer

from zopache.core.viewdecorators import *
from zopache.crud.forms import EditForm
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary
from zope.interface import directlyProvides
from zopache.core.getroot import getPrincipalFolderNoView
from zopache.core.interfaces import ITreeSecurity
from zopache.forms import tal_template

def possibleEditors(context):
    people = getPrincipalFolderNoView(context).getEveryone()
    terms = []
    term = SimpleVocabulary.createTerm('None','None','None')
    terms.append(term)    
    for principal in  people:
        title =  principal.title
        key = principal.__name__
        term = SimpleVocabulary.createTerm(key, key, title)
        terms.append(term)
    return SimpleVocabulary(terms)

directlyProvides(possibleEditors, IContextSourceBinder)


#THIS ONE WORKS, BUT BOY IS IT UGLY.

class IEditors(Interface):
     editors = schema.Set(
         title=u"Editor",
        value_type=schema.Choice(source=possibleEditors),
        required=False,
    )

    
@form_component
@name (u'editors')
@context(IBTreeContainer)
@implementer(ITreeSecurity)
class EditEditors(EditForm):
    title = 'Assign Editors'
    interface = IEditors
    fields = Fields(IEditors)
    ignoreContent = False
    template = tal_template('editors.pt')    
  
    def update(self):
        EditForm.update(self)  
        people = self.getPrincipalFolder().getEveryone()
        self.people = sorted(people, key =  lambda x: x.title.lower())
        parents = self.parents()[:-1]
        inheritedEditors = set()
        for ancestor in parents:
           if hasattr(ancestor,'editors'):
               for editor in ancestor.editors:
                    inheritedEditors.add(editor)
        self.inheritedEditors = inheritedEditors
        
    def checked(self,person):
        context = self.context
        if hasattr(context,'editors'):
          if person.name in context.editors:
              return  "checked"
        return ""
    
    def showValue(self,person):
       return 'value ="' + person.name +'"'
    
    def labelHtml(self, person):
        text = person.title
        if person.name in self.inheritedEditors:
            text += ' (Inherited Editor)'
        isEffectiveEditor = (self.checked(person) == "checked"
                              or person.name in self.inheritedEditors)
        if isEffectiveEditor:
            return '<strong>' + text + '</strong>'
        return text
    

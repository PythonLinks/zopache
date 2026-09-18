from zopache.core.viewdecorators import *
from zopache.core.baseform import Form
from zopache.ttw.interfaces import IBranch
from zopache.ttw.interfaces import IWebClass, IProducts
from BTrees.OOBTree import OOBTree

@form_component
@context(IBranch)
@crom.target(IView)
@crom.name("reIndex")
@permissions('Manage')
class ReIndex(Form):
    label = 'ReIndex'
    def update(self):
           people = self.getPrincipalFolder()
           people.initIndexes()

           root = self.getSiteRoot ()
           root.indexTree()
           
           products = self.getProducts ()
           products.indexTree()
           
           self.status='The tree of pages was indexed'
           Form.update(self)


@form_component
@context(IProducts)
@crom.target(IView)
@crom.name("reIndex")
@permissions('Manage')
class ReIndexProducts(Form):
    label = 'ReIndex'
    def update(self):
        products = self.context
        products.valuesByToken = OOBTree()        
        products.indexTree()
        self.status='The tree of products were indexed'
        Form.update(self)

           

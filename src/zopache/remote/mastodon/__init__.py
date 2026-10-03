#THIS IS ALSO PART OF THE PACKAGE
from os import path
from dolmen.template import TALTemplate

TEMPLATE_DIR = path.join(path.dirname(__file__), 'templates')
def tal_template(name):
    return TALTemplate(path.join(TEMPLATE_DIR, name))

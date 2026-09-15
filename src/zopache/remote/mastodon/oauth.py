"""
This form just checks if the user entered a valid domain name,
and if so, redirects them to /person/moauth/<mastodon_server>
which does the real work of the mastodon oauth process flow.
"""

import os
import logging

from zope.interface import Interface
from zope.schema import DottedName

from cromlech.browser import getSession

from zopache.core.viewdecorators import *
from zopache.core.baseform import Form
from zopache.ttw.interfaces import IPrincipalFolder
from dolmen.forms.base import Actions, Action, SuccessMarker
from dolmen.forms.base.markers import FAILURE

logger = logging.getLogger("oauth")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    os.makedirs('/app/data/logs', exist_ok=True)
    logger.addHandler(logging.FileHandler('/app/data/logs/oauth.log', mode="a"))


class IDomain(Interface):

    domain = DottedName(
        title = u'Domain Name',
        description = ("the domain name of your "
                       " Mastodon/Fediverse oauth "
                       "server which you wish to use to login here."),
        required = True,
    )

    gdprPermission = schema.Bool(
        title = ("To run this web site, including cookie-based "
                 "authentication."),
        required = True,
        default = False)

    gdprPermission.text = """
    <p> I give permission 
to process my personal information for the following  
purposes:</p>"""
    
class CreateAndUse(Action):

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            form.submissionError = errors
            return FAILURE

        domain = data['domain']
        newURL = "/person/moauth/" + domain
        getSession()['gdprPermission'] = str(data["gdprPermission"])
        logger.info("Logging in using  %s ", domain)
        return SuccessMarker('Logging In', True, url=newURL)


@form_component
@name ('oauth')
@context(IPrincipalFolder)
class ChooseServer (Form):
    title = "Mastodon or Fediverse Oauth Login"
    subTitle = 'Please enter the domain name of your home server.'
    allowAnonymous = True
    interface = IDomain
    fields = Fields(IDomain)
    actions = Actions(CreateAndUse("Login"))
    fields["domain"].htmlAttributes = {"placeholder":
               "e.g. example.social or https://example.social"}
    def acquireTitle(self):
        return "Oauth Login"

    def footerScripts(self):
        result = Form.footerScripts(self)
        result += """
<script>
document.addEventListener('DOMContentLoaded', function () {
  const domainField = document.getElementById('form-field-domain');
  if (!domainField) return;

  const form = domainField.closest('form');

  function stripToDottedName() {
    if (!domainField.value.trim()) return;

    let value = domainField.value.trim().toLowerCase();

    const hasScheme = /^https?:\\/\\//i.test(value);
    const toParse = hasScheme ? value : `https://${value}`;

    let host;
    try {
      host = new URL(toParse).hostname;
    } catch {
      host = value
        .replace(/^https?:\\/\\//i, '')
        .split(/[/?#]/)[0]
        .split('@').pop()
        .split(':')[0];
    }

    domainField.value = host.replace(/\\.$/, '');
  }

  // Clean on blur, so the user sees the normalized value before submitting
  domainField.addEventListener('blur', stripToDottedName);

  // Also clean on submit, in case blur never fired (e.g. autofill + Enter key)
  if (form) {
    form.addEventListener('submit', stripToDottedName);
  }
});
</script>
"""
        return result

    

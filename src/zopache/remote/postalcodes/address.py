# -*- coding: utf-8 -*-

from slugify import slugify

from cromlech.security import Unauthorized
from cromlech.browser.exceptions import HTTPFound
from dolmen.forms.base import Actions
from dolmen.forms.base import Fields
from dolmen.forms.base import action, name, context, form_component
from dolmen.forms.base.markers import HIDDEN
from cromlech.browser.exceptions import HTTPBadRequest

from zopache.crud import update as editActions
from zopache.crud.actions import Cancel
from zopache.crud.forms import BaseEditForm
from zopache.crud.utils import getFactoryFields, getAllFields
from zopache.remote.postalcodes.interfaces import IAddressForm
from zopache.remote.postalcodes.countrypostalcode import CountryPostalCode
from zopache.ttw.interfaces import IInternalPrincipal
from zopache.business.region  import Region
from dolmen.forms.ztk import InvariantsValidation


@form_component
@name ('address')
@context(IInternalPrincipal)
class EditAddress(BaseEditForm):
    dataValidators = [InvariantsValidation]
    layoutName = "UserMenu"
    fields = Fields(IAddressForm)
    fields["countryCode"].mode = HIDDEN
    fields["city"].mode = HIDDEN
    fields["region"].mode = HIDDEN
    fields["latitude"].mode = HIDDEN
    fields["longitude"].mode = HIDDEN
    subTitle = ""
    allowAnonymous = False

    def update(self):
        #if not (self.request.principal == self.context):
        #    raise Unauthorized ("People can only update their own data.")
        BaseEditForm.update(self)
        
    def acquireTitle(self):
       return 'GDPR Permissions'

    def newURL(self,new):
        root = self.getSiteRoot()
        newURL =   root.homePage #+ self.randomIndex() 
        raise HTTPFound(newURL)
    
    def addUnAuthorizedActions(self):
        self.addAuthorizedActions()

    def addAuthorizedActions(self):
        self.actions = Actions(editActions.Edit("Save","Save"),
                    editActions.Cancel("Cancel","Cancel"))
        
    def renderMenuBar(self,layout):
        return ""

    def headerScripts(self):
        result = BaseEditForm.headerScripts(self)
        accessToken = self.getSiteRoot().mapBoxKey
        result += f"""
<script src="https://api.mapbox.com/search-js/v1.6.0/web.js"></script>
<script>
var mapboxAccessToken = "{accessToken}";
var postalCodeDebounceTimer;

function createCountrySearchBox(fieldName) {{
    var countryField = document.getElementById(fieldName);
    countryField.style.display = 'none';
    var searchBox = new mapboxsearch.MapboxSearchBox();
    searchBox.accessToken = mapboxAccessToken;
    searchBox.options = {{types: 'country'}};
    searchBox.addEventListener('retrieve', onCountrySelected);
    searchBox.addEventListener('clear', onCountryCleared);
    countryField.after(searchBox);
    searchBox.value = countryField.value;
}}

function onCountrySelected(event) {{
    var country = event.detail.features[0].properties.context.country;
    document.getElementById('form-field-countryName').value = country.name;
    document.getElementById('form-field-countryCode').value = country.country_code;
    lookupPostalCode();
}}

function onCountryCleared() {{
    document.getElementById('form-field-countryName').value = '';
    document.getElementById('form-field-countryCode').value = '';
    document.getElementById('form-field-postalCode').value = '';
    clearPostalCodeError();
}}

function clearPostalCodeError() {{
    var oldError = document.getElementById('postalcode-error');
    if (oldError) {{ oldError.remove(); }}
}}

function showPostalCodeError(message) {{
    clearPostalCodeError();
    var postalField = document.getElementById('form-field-postalCode');
    var errorSpan = document.createElement('span');
    errorSpan.id = 'postalcode-error';
    errorSpan.className = 'text-danger';
    errorSpan.textContent = message;
    postalField.after(errorSpan);
}}

function lookupPostalCode() {{
    var postalCode = document.getElementById('form-field-postalCode').value;
    var countryCode = document.getElementById('form-field-countryCode').value;
    if (!postalCode) {{
        clearPostalCodeError();
        if (countryCode) {{
            document.getElementById('form-field-countryCode').value = '';
            document.getElementById('form-field-countryName').value = '';
        }}
        return;
    }}
    if (!countryCode) {{
        clearPostalCodeError();
        return;
    }}
    var url = "https://api.mapbox.com/search/geocode/v6/forward"
        + "?postcode=" + encodeURIComponent(postalCode)
        + "&country=" + countryCode
        + "&autocomplete=false"
        + "&access_token=" + mapboxAccessToken;
    fetch(url)
        .then(function(response) {{ return response.json(); }})
        .then(function(data) {{
            var feature = data.features && data.features[0];
            var matchedContext = feature ? feature.properties.context : null;
            var postcodeReturned = matchedContext && matchedContext.postcode;
            var countryReturned = matchedContext && matchedContext.country
                && matchedContext.country.country_code === countryCode;
            if (!postcodeReturned || !countryReturned) {{
                showPostalCodeError("Please enter a valid country name and postal "
                    + "code pair.  It is also okay to leave both blank, "
                    + "then your fediverse account will not be displayed.");
                return;
            }}
            clearPostalCodeError();
            var coordinates = feature.geometry.coordinates;
            document.getElementById('form-field-longitude').value = coordinates[0];
            document.getElementById('form-field-latitude').value = coordinates[1];
            document.getElementById('form-field-city').value = matchedContext.place ? matchedContext.place.name : '';
            document.getElementById('form-field-region').value = matchedContext.region ? matchedContext.region.name : '';
        }})
        .catch(function() {{
            showPostalCodeError("Could not reach the postal code lookup service.");
        }});
}}

function checkSubmittable(event) {{
    var postalCode = document.getElementById('form-field-postalCode').value;
    var countryCode = document.getElementById('form-field-countryCode').value;
    var bothBlank = !postalCode && !countryCode;
    var bothSet = postalCode && countryCode;
    if (bothBlank) {{
        return;
    }}
    if (bothSet && !document.getElementById('postalcode-error')) {{
        return;
    }}
    event.preventDefault();
    if (!bothSet) {{
        if (!countryCode) {{
            showPostalCodeError("Please select a country to validate this postal "
                + "code, or clear it to skip location sharing.");
        }} else {{
            showPostalCodeError("Please enter a postal code, or clear the selected "
                + "country to skip location sharing.");
        }}
    }}
}}
</script>
"""
        return result

    def footerScripts(self):
        result = BaseEditForm.footerScripts(self)
        result += """
<script>
createCountrySearchBox('form-field-countryName');
document.getElementById('form-field-postalCode').addEventListener('blur', lookupPostalCode);
document.getElementById('form-field-postalCode').addEventListener('input', function() {
    clearTimeout(postalCodeDebounceTimer);
    postalCodeDebounceTimer = setTimeout(lookupPostalCode, 400);
});
document.getElementById('form-action-Save').form.addEventListener('submit', checkSubmittable);
</script>
"""
        return result

    def getPostalContainer(self, root, countryCode,
                           postalCode, city, region,
                           countryName, latitude, longitude):
        postalContainerName = countryCode + "_" + postalCode
        postalContainerName = slugify (postalContainerName)
        postalContainer = root.get(postalContainerName,None)
        if not postalContainer:
            mapName = "world"
            if (self.getDomain().lower()=="greenmaps.us"):
               mapName = "usa" 
            directory = root[mapName]
            if directory == None:
               directory = Region()                
               root[mapName] = directory
            postalContainer = CountryPostalCode(countryCode, postalCode,
                                                city,
                                                region,
                                                countryName,
                                                latitude,
                                                longitude)
            directory [postalContainer.__name__]= postalContainer
        return postalContainer
       
    def postProcess(self, view = None):
        principal = self.context
        postalCode = principal.postalCode
        countryCode = principal.countryCode
        countryName  = principal.countryName
        root = self.getSiteRoot()
        principalFolder = self.getPrincipalFolder()

        #No Data - principal belongs in /root/person
        if ((countryName == "") and (postalCode == "")):
           if principal.__parent__ is not principalFolder:
               name = principal.__name__
               del principal.__parent__[name]
               principalFolder[name] = principal
           view.submissionError += "You did not provide location information and "
           view.submissionError += "therefore are not listed. "
           return

        #Only 1 data
        if (countryCode == "") != (postalCode == ""):
            raise HTTPBadRequest(self.request.url)


        # Data looks good, get or create the postal container.
        postalContainer = self.getPostalContainer(root,
                                                  principal.countryCode,
                                                  principal.postalCode,
                                                  principal.city,
                                                  principal.region,
                                                  principal.countryName, 
                                                  principal.latitude,
                                                  principal.longitude)

        # Move the principal itself into the postal container.
        if principal.__parent__ is not postalContainer:
            name = principal.__name__
            if principal.__parent__ is principalFolder:
                principalFolder.removeItem(principal)
            else:
                del principal.__parent__[name]
            postalContainer[name] = principal

        del principal.latitude
        del principal.longitude
        newURL = "/world"
        raise HTTPFound(newURL)

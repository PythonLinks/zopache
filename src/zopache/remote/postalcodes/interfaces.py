from zope import schema
from zope.interface import Interface, invariant, Invalid
from zopache.pages.interfaces import (ILocation,
                                      IPage,
                                      IPageBase)

from zopache.crud.interfaces import IMoveable

from zopache.json.interfaces import IClass

class IAddressForm(Interface):
        
    countryName  = schema.TextLine(
        title='Your country', required=False)

    postalCode  = schema.TextLine(
        title='Your Postal code', required=False,
        default = "")

    countryCode  = schema.TextLine(
        title='Your country code', required=False,
        default = "")

    city  = schema.TextLine(
        title='Your city', required=False,
        default = "")

    region  = schema.TextLine(
        title='Your state or province', required=False,
        default = "")        

    @invariant
    def checkForBothCountryAndCountryPostalCodeOrNeither(data):
        if bool(data.countryCode) != bool(data.postalCode):
            message = ("Please enter a valid country name and postal "
                       "code pair.  It is also okay to leave both blank, "
                       "then your fediverse account will not be displayed.")
            raise Invalid(message)

    latitude = schema.Float(
        title = u'Latitude',
        description = u'Latitude',
        min=-90.,
        max=90.,
        default = 51.509865,
        required = True,
        )

    longitude = schema.Float(
        title = u'Longitude',
        description = u'Longitude ',
        min=-180.,
        max=180.,
        default = 0.,
        required = True,
    )

class ICountryPostalCode(ILocation, IPage, IMoveable):
    pass

    

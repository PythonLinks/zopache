from zope.interface import Interface
from zope import schema
from zopache.pages.interfaces import  ILinkBase
from zopache.crud.interfaces import ILeaf, IDeletable


class IRemoteAccount(ILinkBase):    
    
    title=schema.TextLine(
        title = "Mastodon Account Name",
        description ="What is the account  called?",
        required = True,
        )
    
    description= schema.Text(
        title = 'Description',
        description = """The Mastodon Account BIo.  """,
        required = False,
        default = '',
    )    

    mastodonId=schema.TextLine(
        title = "Mastodon Id",
        description ="""@User@Domain or #hashtag """,
        required = False,
        )    

    defaultCategory = schema.TextLine(
        title = "Whereto place their recommended links",
        description ="This is the /slug where you can see their recommendedlinks.",
        required = False,
        )
    
    rssApproved=schema.Bool(
        title = "Is this feed approved for downloading",
        description ="We can block some feeds without deleting them.",
        required = False,
        default = True,
        )
    
    keepAllArticles=schema.Bool(
        title = "Keep all of their articles?",
        description ="Or clear out the old ones to save space?",
        required = False,
        default = True,
    )    
        
    domainName = schema.DottedName(
        title = 'Their Domain Name',
        description = 'Articles in this domain are listed, not approved.',
        required = False,
        missing_value = "",
    )
    
    wordsToAvoid = schema.Text(
        title = 'Words To Avoid',
        description = """These words will get the item rejected.  """,
        required = False,
        default = '',
    )
    
class IHashTag(IRemoteAccount):
    title=schema.TextLine(
        title = "Hash Tag Title",
        description ="What is the hash tag about?",
        required = True,
        )
    
    mastodonId=schema.TextLine(
        title = "Hash Tag",
        description ="""#hashtag """,
        required = False,
        )        

class ILogo (Interface):
    logoURL=schema.URI(
        title = "Logo URL ",
        description ="An image is important",
        required = False,
        missing_value = '',
        )
    
class IAddRemoteAccount(IRemoteAccount,ILogo):
    pass

class IAddHashTag(IHashTag, ILogo):
     pass

class IToot(ILeaf,IDeletable):
    description= schema.Text(
        title = u'Description',
        description = """A brief introduction of this page.  
                        This is used by the search functions.""",
        required = False,
        default = u'',
    )

    source= schema.Text(
        title = 'Content',
        description = 'This is the main content for this page',
        required = False,
        default = '',
    )

  



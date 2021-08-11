class OAIException(Exception):
    """ A Python exception that handles errors defined in the OAI spec
    :attr msg: The message that will be returned from the user
    :attr code: A machine readable code, defined by the OAI spec
    """
    msg = None
    code = None


class OAIBadVerb(OAIException):
    msg = "Illegal OAI verb."
    code = "badVerb"


class OAINoRecordsMatch(OAIException):
    msg = "No records found for the request."
    code = "noRecordsMatch"


class OAIDoesNotExist(OAIException):
    msg = ("The value of the identifier argument is unknown or illegal"
           " in this repository.")
    code = "idDoesNotExist"


class OAIUnsupportedMetadataFormat(OAIException):
    msg = ("The metadata format identified by the value given for the"
           " metadataPrefix argument is not supported by the item or by"
           "the repository.")
    code = "cannotDisseminateFormat"


class OAIBadToken(OAIException):
    msg = "The value of the resumptionToken argument is invalid or expired."
    code = "badResumptionToken"


class OAIBadArgument(OAIException):
    msg = ("The request includes illegal arguments, is missing required"
           " arguments, includes a repeated argument, or values for arguments"
           "have an illegal syntax.")
    code = "badArgument"

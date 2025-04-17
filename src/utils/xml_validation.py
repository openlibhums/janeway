from lxml import etree


class NetworkResolver(etree.Resolver):
    """
    Custom resolver to allow loading external DTDs and entities over the network.
    """
    def resolve(self, url, pubid, context):
        return self.resolve_filename(url, context)


def validate_jats_with_remote_dtd(xml_string):
    """
    Validate a JATS XML string that includes a remote DTD declaration.
    This function allows fetching the DTD and entities over the network.
    """
    try:
        parser = etree.XMLParser(
            dtd_validation=True,
            load_dtd=True,
            no_network=False,
            resolve_entities=True,
        )
        parser.resolvers.add(NetworkResolver())

        doc = etree.fromstring(xml_string.encode("utf-8"), parser)
        return True, "Validation successful"
    except etree.XMLSyntaxError as e:
        return False, str(e)
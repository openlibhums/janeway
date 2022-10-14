#from urllib.parse import unquote_plus
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode

from freezegun import freeze_time

from utils.testing import helpers
from repository import models as repo_models
import datetime
import pytz

REPO_DOMAIN = 'repo.domain.com'

class TestPreprintOAIViews(TestCase):

    @classmethod
    @freeze_time("2022-08-31")
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.repo, cls.subject = helpers.create_repository(cls.press, [], [])

        cls.author = helpers.create_user("preprintauthor@test.edu")
        cls.author.first_name = "Preprint"
        cls.author.last_name = "Author"
        cls.author.save()

        cls.preprint = helpers.create_preprint(cls.repo, cls.author, cls.subject)
        cls.preprint.stage = repo_models.STAGE_PREPRINT_PUBLISHED
        cls.preprint.date_published = datetime.datetime(2022, 8, 31, tzinfo=pytz.UTC) 
        cls.preprint.make_new_version(cls.preprint.submission_file)
        cls.preprint.save()

        cls.unpublished_preprint = helpers.create_preprint(cls.repo, cls.author, cls.subject, title="Unpublished Preprint")

        cls.older_preprint = helpers.create_preprint(cls.repo, cls.author, cls.subject, title="Older Test Preprint")
        cls.older_preprint.stage = repo_models.STAGE_PREPRINT_PUBLISHED
        cls.older_preprint.date_published = datetime.datetime(2022, 8, 29, tzinfo=pytz.UTC)
        cls.older_preprint.make_new_version(cls.older_preprint.submission_file)
        cls.older_preprint.save()

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2022-09-01")
    def test_list_records_dc(self):
        expected = LIST_RECORDS_DATA_DC
        response = self.client.get(reverse('OAI_list_records'), SERVER_NAME=REPO_DOMAIN)
        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2022-09-01")
    def test_list_records_jats(self):
        expected = LIST_RECORDS_DATA_JATS
        path = reverse('OAI_list_records')
        query_params = dict(
            verb="ListRecords",
            metadataPrefix="jats",
        )
        query_string = urlencode(query_params)
        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME=REPO_DOMAIN
        )
        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2022-09-01")
    def test_list_sets(self):
        expected = LIST_SETS_DATA_DC

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="ListSets",
            metadataPrefix="oai_dc",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME=REPO_DOMAIN
        )

        self.assertEqual(str(response.rendered_content).split(), expected.split())


    @override_settings(URL_CONFIG="domain")
    @freeze_time("2022-09-01")
    def test_get_record_dc(self):
        expected = GET_RECORD_DATA_DC

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="GetRecord",
            metadataPrefix="oai_dc",
            identifier="oai:testrepo:id:1",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="repo.domain.com"
        )

        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2022-09-01")
    def test_get_record_jats(self):
        expected = GET_RECORD_DATA_JATS

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="GetRecord",
            metadataPrefix="jats",
            identifier="oai:testrepo:id:1",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="repo.domain.com"
        )

        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2022-09-01")
    def test_list_identifiers_jats(self):
        expected = LIST_IDENTIFIERS_JATS

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="ListIdentifiers",
            metadataPrefix="jats",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="repo.domain.com"
        )

        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2022-09-01")
    def test_identify_dc(self):
        expected = IDENTIFY_DATA_DC

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="Identify",
            metadataPrefix="oai_dc",
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="repo.domain.com"
        )
        self.assertEqual(str(response.rendered_content).split(), expected.split())

    @override_settings(URL_CONFIG="domain")
    @freeze_time("2022-09-01")
    def test_get_records_until(self):
        expected = GET_RECORD_DATA_UNTIL

        path = reverse('OAI_list_records')
        query_params = dict(
            verb="ListRecords",
            metadataPrefix="oai_dc",
            until=str(datetime.datetime(2022, 8, 30, tzinfo=pytz.UTC)),
        )
        query_string = urlencode(query_params)

        response = self.client.get(
            f'{path}?{query_string}',
            SERVER_NAME="repo.domain.com"
        )

        self.assertEqual(str(response.rendered_content).split(), expected.split())

LIST_RECORDS_DATA_DC = """
    <?xml version="1.0" encoding="UTF-8"?>
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
            http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2022-09-01T00:00:00Z</responseDate>
    <request verb="ListRecords" metadataPrefix="oai_dc">http://repo.domain.com/api/oai/</request>
    <ListRecords>
        <record>
            <header>
                <identifier>oai:testrepo:id:3</identifier>
                <datestamp>2022-08-29T00:00:00Z</datestamp>
            </header>
            <metadata>
                <oai_dc:dc
                    xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                    xmlns:dc="http://purl.org/dc/elements/1.1/"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/
                    http://www.openarchives.org/OAI/2.0/oai_dc.xsd">

                    <dc:title>Older Test Preprint</dc:title>
                    <dc:creator>Author, Preprint</dc:creator>
                    <dc:description>This is a fake abstract.</dc:description>
                    <dc:date>2022-08-29T00:00:00Z</dc:date>
                    <dc:date>2022-08-31T00:00:00Z</dc:date>
                    <dc:type>PREPRINTS</dc:type>
                    <dc:publisher>Press</dc:publisher>
                    <dc:identifier>http://repo.domain.com/repository/manager/3/download/3/</dc:identifier>
                    <dc:identifier>3</dc:identifier>
                    <dc:source>Test Repository</dc:source>
                    <dc:subject>Repo Subject</dc:subject>
                </oai_dc:dc>
            </metadata>
        </record>
        <record>
            <header>
                <identifier>oai:testrepo:id:1</identifier>
                <datestamp>2022-08-31T00:00:00Z</datestamp>
            </header>
            <metadata>
                <oai_dc:dc
                    xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                    xmlns:dc="http://purl.org/dc/elements/1.1/"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/
                    http://www.openarchives.org/OAI/2.0/oai_dc.xsd">

                    <dc:title>This is a Test Preprint</dc:title>
                    <dc:creator>Author, Preprint</dc:creator>
                    <dc:description>This is a fake abstract.</dc:description>
                    <dc:date>2022-08-31T00:00:00Z</dc:date>
                    <dc:date>2022-08-31T00:00:00Z</dc:date>
                    <dc:type>PREPRINTS</dc:type>
                    <dc:publisher>Press</dc:publisher>
                    <dc:identifier>http://repo.domain.com/repository/manager/1/download/1/</dc:identifier>
                    <dc:identifier>1</dc:identifier>
                    <dc:source>Test Repository</dc:source>
                    <dc:subject>Repo Subject</dc:subject>
                </oai_dc:dc>
            </metadata>
        </record>
    </ListRecords>
</OAI-PMH>
"""


LIST_RECORDS_DATA_JATS = """
    <?xml version="1.0" encoding="UTF-8"?>
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
            http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
        <responseDate>2022-09-01T00:00:00Z</responseDate>
        <request verb="ListRecords" metadataPrefix="jats">http://repo.domain.com/api/oai/</request>
        <ListRecords>
            <record>
                <header>
                    <identifier>oai:testrepo:id:3</identifier>
                    <datestamp>2022-08-29T00:00:00Z</datestamp>
                </header>
                <metadata>
                    <article
                        article-type="research-article"
                        dtd-version="1.0" xml:lang="en"
                        xmlns="https://jats.nlm.nih.gov/publishing/1.2/"
                        xmlns:mml="http://www.w3.org/1998/Math/MathML"
                        xmlns:xlink="http://www.w3.org/1999/xlink"
                        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        <front>
                            <journal-meta>
                                <journal-id journal-id-type="publisher">testrepo</journal-id>
                                <journal-title-group>
                                    <journal-title>Test Repository</journal-title>
                                </journal-title-group>
                                <publisher>
                                    <publisher-name>Press</publisher-name>
                                </publisher>
                            </journal-meta>
                            <article-meta>
                                <article-id pub-id-type="publisher-id">3</article-id>
                                <article-version vocab="JAV" vocab-identifier="http://www.niso.org/publications/rp/RP-8-2008.pdf" article-version-type="AO" vocab-term="Author's Original">preprint</article-version>
                                <article-version article-version-type="publisher-id">1</article-version>
                                <article-categories>
                                    <subj-group>
                                        <subject>Repo Subject</subject>
                                    </subj-group>
                                </article-categories>
                                <title-group>
                                    <article-title>Older Test Preprint</article-title>
                                </title-group>
                                <contrib-group>
                                    <contrib contrib-type="author">
                                        <name>
                                            <surname>Author</surname>
                                            <given-names>Preprint</given-names>
                                        </name>
                                        <email>preprintauthor@test.edu</email>
                                        <xref ref-type="aff" rid="aff-1"/>
                                    </contrib>
                                </contrib-group>
                                <aff id="aff-1">Made Up University</aff>
                                <pub-date date-type="pub" iso-8601-date="2022-08-29" publication-format="electronic">
                                    <day>29</day>
                                    <month>08</month>
                                    <year>2022</year>
                                </pub-date>
                                <self-uri content-type="text/html" xlink:href="http://repo.domain.com/repository/view/3/"/>
                                <self-uri content-type="pdf" xlink:href="http://repo.domain.com/repository/manager/3/download/3/"/>
                                <abstract>This is a fake abstract.</abstract>
                                <pub-history>
                                    <event event-type="pub">
                                        <event-desc>Version of Record published:
                                            <string-date iso-8601-date="2022-08-31">
                                                <day>31</day>
                                                <month>08</month>
                                                <year>2022</year>
                                            </string-date>
                                            (version 1)
                                            <self-uri content-type="application/pdf" xlink:href="http://repo.domain.com/repository/manager/3/download/3/"/>
                                        </event-desc>
                                    </event>
                                </pub-history>
                            </article-meta>
                        </front>
                    </article>
                </metadata>
            </record>
            <record>
                <header>
                    <identifier>oai:testrepo:id:1</identifier>
                    <datestamp>2022-08-31T00:00:00Z</datestamp>
                </header>
                <metadata>
                    <article
                        article-type="research-article"
                        dtd-version="1.0" xml:lang="en"
                        xmlns="https://jats.nlm.nih.gov/publishing/1.2/"
                        xmlns:mml="http://www.w3.org/1998/Math/MathML"
                        xmlns:xlink="http://www.w3.org/1999/xlink"
                        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        <front>
                            <journal-meta>
                                <journal-id journal-id-type="publisher">testrepo</journal-id>
                                <journal-title-group>
                                    <journal-title>Test Repository</journal-title>
                                </journal-title-group>
                                <publisher>
                                    <publisher-name>Press</publisher-name>
                                </publisher>
                            </journal-meta>
                            <article-meta>
                                <article-id pub-id-type="publisher-id">1</article-id>
                                <article-version vocab="JAV" vocab-identifier="http://www.niso.org/publications/rp/RP-8-2008.pdf" article-version-type="AO" vocab-term="Author's Original">preprint</article-version>
                                <article-version article-version-type="publisher-id">1</article-version>
                                <article-categories>
                                    <subj-group>
                                        <subject>Repo Subject</subject>
                                    </subj-group>
                                </article-categories>
                                <title-group>
                                    <article-title>This is a Test Preprint</article-title>
                                </title-group>
                                <contrib-group>
                                    <contrib contrib-type="author">
                                        <name>
                                            <surname>Author</surname>
                                            <given-names>Preprint</given-names>
                                        </name>
                                        <email>preprintauthor@test.edu</email>
                                        <xref ref-type="aff" rid="aff-1"/>
                                    </contrib>
                                </contrib-group>
                                <aff id="aff-1">Made Up University</aff>
                                <pub-date date-type="pub" iso-8601-date="2022-08-31" publication-format="electronic">
                                    <day>31</day>
                                    <month>08</month>
                                    <year>2022</year>
                                </pub-date>
                                <self-uri content-type="text/html" xlink:href="http://repo.domain.com/repository/view/1/"/>
                                <self-uri content-type="pdf" xlink:href="http://repo.domain.com/repository/manager/1/download/1/"/>
                                <abstract>This is a fake abstract.</abstract>
                                <pub-history>
                                    <event event-type="pub">
                                        <event-desc>Version of Record published:
                                            <string-date iso-8601-date="2022-08-31">
                                                <day>31</day>
                                                <month>08</month>
                                                <year>2022</year>
                                            </string-date>
                                            (version 1)
                                            <self-uri content-type="application/pdf" xlink:href="http://repo.domain.com/repository/manager/1/download/1/"/>
                                        </event-desc>
                                    </event>
                                </pub-history>
                            </article-meta>
                        </front>
                    </article>
                </metadata>
            </record>
        </ListRecords>
    </OAI-PMH>
"""


GET_RECORD_DATA_DC = """
    <?xml version="1.0" encoding="UTF-8"?>
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2022-09-01T00:00:00Z</responseDate>
    <request verb="GetRecord" metadataPrefix="oai_dc">http://repo.domain.com/api/oai/</request>
    <GetRecord>
        <record>
            <header>
                <identifier>oai:testrepo:id:1</identifier>
                <datestamp>2022-08-31T00:00:00Z</datestamp>
            </header>
            <metadata>
                <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                            xmlns:dc="http://purl.org/dc/elements/1.1/"
                            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                            xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/
                            http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
                    <dc:title>This is a Test Preprint</dc:title>
                    <dc:creator>Author, Preprint</dc:creator>
                    <dc:description>This is a fake abstract.</dc:description>
                    <dc:date>2022-08-31T00:00:00Z</dc:date>
                    <dc:date>2022-08-31T00:00:00Z</dc:date>
                    <dc:type>PREPRINTS</dc:type>
                    <dc:publisher>Press</dc:publisher>
                    <dc:identifier>http://repo.domain.com/repository/manager/1/download/1/</dc:identifier>
                    <dc:identifier>1</dc:identifier>
                    <dc:source>Test Repository</dc:source>
                    <dc:subject>Repo Subject</dc:subject>
                </oai_dc:dc>
            </metadata>
        </record>
    </GetRecord>
</OAI-PMH>
"""

GET_RECORD_DATA_UNTIL = """
<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2022-09-01T00:00:00Z</responseDate>
    <request verb="ListRecords" metadataPrefix="oai_dc">http://repo.domain.com/api/oai/</request>
    <ListRecords>
        <record>
            <header>
                <identifier>oai:testrepo:id:3</identifier>
                <datestamp>2022-08-29T00:00:00Z</datestamp>
            </header>
            <metadata>
                <oai_dc:dc
                    xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                    xmlns:dc="http://purl.org/dc/elements/1.1/"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/
                    http://www.openarchives.org/OAI/2.0/oai_dc.xsd">

                    <dc:title>Older Test Preprint</dc:title>
                    <dc:creator>Author, Preprint</dc:creator>
                    <dc:description>This is a fake abstract.</dc:description>
                    <dc:date>2022-08-29T00:00:00Z</dc:date>
                    <dc:date>2022-08-31T00:00:00Z</dc:date>
                    <dc:type>PREPRINTS</dc:type>
                    <dc:publisher>Press</dc:publisher>
                    <dc:identifier>http://repo.domain.com/repository/manager/3/download/3/</dc:identifier>
                    <dc:identifier>3</dc:identifier>
                    <dc:source>Test Repository</dc:source>
                    <dc:subject>Repo Subject</dc:subject>
                </oai_dc:dc>
            </metadata>
        </record>
    </ListRecords>
</OAI-PMH>
"""


GET_RECORD_DATA_JATS = """
<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2022-09-01T00:00:00Z</responseDate>
    <request verb="GetRecord" metadataPrefix="jats">http://repo.domain.com/api/oai/</request>
    <GetRecord>
        <record>
            <header>
                <identifier>oai:testrepo:id:1</identifier>
                <datestamp>2022-08-31T00:00:00Z</datestamp>
            </header>
            <metadata>
                <article
                    article-type="research-article"
                    dtd-version="1.0" xml:lang="en"
                    xmlns="https://jats.nlm.nih.gov/publishing/1.2/"
                    xmlns:mml="http://www.w3.org/1998/Math/MathML"
                    xmlns:xlink="http://www.w3.org/1999/xlink"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <front>
                        <journal-meta>
                            <journal-id journal-id-type="publisher">testrepo</journal-id>
                            <journal-title-group>
                                <journal-title>Test Repository</journal-title>
                            </journal-title-group>
                            <publisher>
                                <publisher-name>Press</publisher-name>
                            </publisher>
                        </journal-meta>
                        <article-meta>
                            <article-id pub-id-type="publisher-id">1</article-id>
                            <article-version vocab="JAV" vocab-identifier="http://www.niso.org/publications/rp/RP-8-2008.pdf" article-version-type="AO" vocab-term="Author's Original">preprint</article-version>
                            <article-version article-version-type="publisher-id">1</article-version>
                            <article-categories>
                                <subj-group>
                                    <subject>Repo Subject</subject>
                                </subj-group>
                            </article-categories>
                            <title-group>
                                <article-title>This is a Test Preprint</article-title>
                            </title-group>
                            <contrib-group>
                                <contrib contrib-type="author">
                                    <name>
                                        <surname>Author</surname>
                                        <given-names>Preprint</given-names>
                                    </name>
                                    <email>preprintauthor@test.edu</email>
                                    <xref ref-type="aff" rid="aff-1"/>
                                </contrib>
                            </contrib-group>
                            <aff id="aff-1">Made Up University</aff>
                            <pub-date date-type="pub" iso-8601-date="2022-08-31" publication-format="electronic">
                                <day>31</day>
                                <month>08</month>
                                <year>2022</year>
                            </pub-date>
                            <self-uri content-type="text/html" xlink:href="http://repo.domain.com/repository/view/1/"/>
                            <self-uri content-type="pdf" xlink:href="http://repo.domain.com/repository/manager/1/download/1/"/>
                            <abstract>This is a fake abstract.</abstract>
                            <pub-history>
                                <event event-type="pub">
                                    <event-desc>Version of Record published:
                                        <string-date iso-8601-date="2022-08-31">
                                            <day>31</day>
                                            <month>08</month>
                                            <year>2022</year>
                                        </string-date>
                                        (version 1)
                                        <self-uri content-type="application/pdf" xlink:href="http://repo.domain.com/repository/manager/1/download/1/"/>
                                    </event-desc>
                                </event>
                            </pub-history>
                        </article-meta>
                    </front>
                </article>
            </metadata>
        </record>
    </GetRecord>
</OAI-PMH>
"""

LIST_IDENTIFIERS_JATS = """
<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2022-09-01T00:00:00Z</responseDate>
    <request verb="ListIdentifiers" metadataPrefix="jats">http://repo.domain.com/api/oai/</request>
    <ListIdentifiers>
        <header>
            <identifier>oai:testrepo:id:3</identifier>
            <datestamp>2022-08-29T00:00:00Z</datestamp>
        </header>
        <header>
            <identifier>oai:testrepo:id:1</identifier>
            <datestamp>2022-08-31T00:00:00Z</datestamp>
        </header>
    </ListIdentifiers>
</OAI-PMH>
"""

IDENTIFY_DATA_DC = """
<?xml version="1.0" encoding="UTF-8"?>
 <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2022-09-01T00:00:00Z</responseDate>
    <request verb="Identify" metadataPrefix="oai_dc">http://repo.domain.com/api/oai/</request>
    <Identify>
        <repositoryName>Test Repository</repositoryName>
        <baseURL>http://repo.domain.com/api/oai/</baseURL>
        <protocolVersion>2.0</protocolVersion>
        <adminEmail>a@b.com</adminEmail>
        <earliestDatestamp>2022-08-29T00:00:00Z</earliestDatestamp>
        <deletedRecord>no</deletedRecord>
        <granularity>YYYY-MM-DDThh:mm:ssZ</granularity>
        <description>
            <toolkit
                    xmlns="http://oai.dlib.vt.edu/OAI/metadata/toolkit"
                    xsi:schemaLocation="http://oai.dlib.vt.edu/OAI/metadata/toolkit
                                        http://oai.dlib.vt.edu/OAI/metadata/toolkit.xsd">
                <title>Janeway</title>
                <author>
                    <name>Birkbeck, University of London</name>
                    <email>olh-tech@bbk.ac.uk</email>
                </author>
                <version></version>
                <URL>http://janeway.systems/</URL>
            </toolkit>
        </description>
    </Identify>
</OAI-PMH>
"""

LIST_SETS_DATA_DC = """
<?xml version="1.0" encoding="UTF-8"?>
    <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
    <responseDate>2022-09-01T00:00:00Z</responseDate>
    <request verb="ListSets" metadataPrefix="oai_dc">http://repo.domain.com/api/oai/</request>

        <ListSets>

        </ListSets>

    </OAI-PMH>
"""

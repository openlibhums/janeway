__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from bs4 import BeautifulSoup
from urllib.parse import urlparse
import uuid
import os
from dateutil import parser as dateparser
from itertools import chain
import warnings
from iso639 import Lang

from django.apps import apps
from django.urls import reverse
from django.db import (
    connection,
    DEFAULT_DB_ALIAS,
    models,
)
from django.db.models.query import RawQuerySet
from django.db.models.sql.query import get_order_dir
from django.conf import settings
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    SearchVectorField,
)
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.template import Context, Template
from django.template.loader import render_to_string
from django.db.models.signals import pre_delete, m2m_changed
from django.dispatch import receiver
from django.core import exceptions
from django.utils.functional import cached_property
from django.utils.html import mark_safe
import swapper

from core.file_system import JanewayFileSystemStorage
from core.model_utils import (
    AbstractLastModifiedModel,
    DynamicChoiceField,
    BaseSearchManagerMixin,
    JanewayBleachField,
    JanewayBleachCharField,
    M2MOrderedThroughField,
    DateTimePickerModelField,
)
from core import workflow, model_utils, files, models as core_models
from core.templatetags.truncate import truncatesmart
from identifiers import logic as id_logic
from identifiers import models as identifier_models
from metrics.logic import ArticleMetrics
from review import models as review_models
from repository import models as repository_models
from utils.function_cache import cache
from utils.logger import get_logger
from utils.orcid import validate_orcid, COMPILED_ORCID_REGEX
from utils.forms import plain_text_validator
from journal import models as journal_models
from review.const import (
    ReviewerDecisions as RD,
)
from transform import utils as transform_utils

logger = get_logger(__name__)

fs = JanewayFileSystemStorage()


def article_media_upload(instance, filename):
    try:
        filename = str(uuid.uuid4()) + "." + str(filename.split(".")[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "articles/{0}/".format(instance.pk)
    return os.path.join(path, filename)


CREDIT_ROLE_CHOICES = [
    ("conceptualization", "Conceptualization"),
    ("data-curation", "Data Curation"),
    ("formal-analysis", "Formal Analysis"),
    ("funding-acquisition", "Funding Acquisition"),
    ("investigation", "Investigation"),
    ("methodology", "Methodology"),
    ("project-administration", "Project Administration"),
    ("resources", "Resources"),
    ("software", "Software"),
    ("supervision", "Supervision"),
    ("validation", "Validation"),
    ("visualization", "Visualization"),
    ("writing-original-draft", "Writing - Original Draft"),
    ("writing-review-editing", "Writing - Review & Editing"),
]


# This language set is ISO 639-2/T
LANGUAGE_CHOICES = (
    ("eng", "English"),
    ("abk", "Abkhazian"),
    ("ace", "Achinese"),
    ("ach", "Acoli"),
    ("ada", "Adangme"),
    ("ady", "Adyghe; Adygei"),
    ("aar", "Afar"),
    ("afh", "Afrihili"),
    ("afr", "Afrikaans"),
    ("afa", "Afro-Asiatic languages"),
    ("ain", "Ainu"),
    ("aka", "Akan"),
    ("akk", "Akkadian"),
    ("sqi", "Albanian"),
    ("ale", "Aleut"),
    ("alg", "Algonquian languages"),
    ("tut", "Altaic languages"),
    ("amh", "Amharic"),
    ("anp", "Angika"),
    ("apa", "Apache languages"),
    ("ara", "Arabic"),
    ("arg", "Aragonese"),
    ("arp", "Arapaho"),
    ("arw", "Arawak"),
    ("hye", "Armenian"),
    ("rup", "Aromanian; Arumanian; Macedo-Romanian"),
    ("art", "Artificial languages"),
    ("asm", "Assamese"),
    ("ast", "Asturian; Bable; Leonese; Asturleonese"),
    ("ath", "Athapascan languages"),
    ("aus", "Australian languages"),
    ("map", "Austronesian languages"),
    ("ava", "Avaric"),
    ("ave", "Avestan"),
    ("awa", "Awadhi"),
    ("aym", "Aymara"),
    ("aze", "Azerbaijani"),
    ("ban", "Balinese"),
    ("bat", "Baltic languages"),
    ("bal", "Baluchi"),
    ("bam", "Bambara"),
    ("bai", "Bamileke languages"),
    ("bad", "Banda languages"),
    ("bnt", "Bantu languages"),
    ("bas", "Basa"),
    ("bak", "Bashkir"),
    ("eus", "Basque"),
    ("btk", "Batak languages"),
    ("bej", "Beja; Bedawiyet"),
    ("bel", "Belarusian"),
    ("bem", "Bemba"),
    ("ben", "Bengali"),
    ("ber", "Berber languages"),
    ("bho", "Bhojpuri"),
    ("bih", "Bihari languages"),
    ("bik", "Bikol"),
    ("bin", "Bini; Edo"),
    ("bis", "Bislama"),
    ("byn", "Blin; Bilin"),
    ("zbl", "Blissymbols; Blissymbolics; Bliss"),
    ("nob", "Bokm\xe5l, Norwegian; Norwegian Bokm\xe5l"),
    ("bos", "Bosnian"),
    ("bra", "Braj"),
    ("bre", "Breton"),
    ("bug", "Buginese"),
    ("bul", "Bulgarian"),
    ("bua", "Buriat"),
    ("mya", "Burmese"),
    ("cad", "Caddo"),
    ("cat", "Catalan; Valencian"),
    ("cau", "Caucasian languages"),
    ("ceb", "Cebuano"),
    ("cel", "Celtic languages"),
    ("cai", "Central American Indian languages"),
    ("khm", "Central Khmer"),
    ("chg", "Chagatai"),
    ("cmc", "Chamic languages"),
    ("cha", "Chamorro"),
    ("che", "Chechen"),
    ("chr", "Cherokee"),
    ("chy", "Cheyenne"),
    ("chb", "Chibcha"),
    ("nya", "Chichewa; Chewa; Nyanja"),
    ("zho", "Chinese"),
    ("chn", "Chinook jargon"),
    ("chp", "Chipewyan; Dene Suline"),
    ("cho", "Choctaw"),
    (
        "chu",
        "Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic",
    ),
    ("chk", "Chuukese"),
    ("chv", "Chuvash"),
    ("nwc", "Classical Newari; Old Newari; Classical Nepal Bhasa"),
    ("syc", "Classical Syriac"),
    ("cop", "Coptic"),
    ("cor", "Cornish"),
    ("cos", "Corsican"),
    ("cre", "Cree"),
    ("mus", "Creek"),
    ("crp", "Creoles and pidgins"),
    ("cpe", "Creoles and pidgins, English based"),
    ("cpf", "Creoles and pidgins, French-based"),
    ("cpp", "Creoles and pidgins, Portuguese-based"),
    ("crh", "Crimean Tatar; Crimean Turkish"),
    ("hrv", "Croatian"),
    ("cus", "Cushitic languages"),
    ("ces", "Czech"),
    ("dak", "Dakota"),
    ("dan", "Danish"),
    ("dar", "Dargwa"),
    ("del", "Delaware"),
    ("din", "Dinka"),
    ("div", "Divehi; Dhivehi; Maldivian"),
    ("doi", "Dogri"),
    ("dgr", "Dogrib"),
    ("dra", "Dravidian languages"),
    ("dua", "Duala"),
    ("dum", "Dutch, Middle (ca. 1050-1350)"),
    ("nld", "Dutch; Flemish"),
    ("dyu", "Dyula"),
    ("dzo", "Dzongkha"),
    ("frs", "Eastern Frisian"),
    ("efi", "Efik"),
    ("egy", "Egyptian (Ancient)"),
    ("eka", "Ekajuk"),
    ("elx", "Elamite"),
    ("enm", "English, Middle (1100-1500)"),
    ("ang", "English, Old (ca. 450-1100)"),
    ("myv", "Erzya"),
    ("epo", "Esperanto"),
    ("est", "Estonian"),
    ("ewe", "Ewe"),
    ("ewo", "Ewondo"),
    ("fan", "Fang"),
    ("fat", "Fanti"),
    ("fao", "Faroese"),
    ("fij", "Fijian"),
    ("fil", "Filipino; Pilipino"),
    ("fin", "Finnish"),
    ("fiu", "Finno-Ugrian languages"),
    ("fon", "Fon"),
    ("fra", "French"),
    ("frm", "French, Middle (ca. 1400-1600)"),
    ("fro", "French, Old (842-ca. 1400)"),
    ("fur", "Friulian"),
    ("ful", "Fulah"),
    ("gaa", "Ga"),
    ("gla", "Gaelic; Scottish Gaelic"),
    ("car", "Galibi Carib"),
    ("glg", "Galician"),
    ("lug", "Ganda"),
    ("gay", "Gayo"),
    ("gba", "Gbaya"),
    ("gez", "Geez"),
    ("kat", "Georgian"),
    ("deu", "German"),
    ("gmh", "German, Middle High (ca. 1050-1500)"),
    ("goh", "German, Old High (ca. 750-1050)"),
    ("gem", "Germanic languages"),
    ("gil", "Gilbertese"),
    ("gon", "Gondi"),
    ("gor", "Gorontalo"),
    ("got", "Gothic"),
    ("grb", "Grebo"),
    ("grc", "Greek, Ancient (to 1453)"),
    ("ell", "Greek, Modern (1453-)"),
    ("grn", "Guarani"),
    ("guj", "Gujarati"),
    ("gwi", "Gwich'in"),
    ("hai", "Haida"),
    ("hat", "Haitian; Haitian Creole"),
    ("hau", "Hausa"),
    ("haw", "Hawaiian"),
    ("heb", "Hebrew"),
    ("her", "Herero"),
    ("hil", "Hiligaynon"),
    ("him", "Himachali languages; Western Pahari languages"),
    ("hin", "Hindi"),
    ("hmo", "Hiri Motu"),
    ("hit", "Hittite"),
    ("hmn", "Hmong; Mong"),
    ("hun", "Hungarian"),
    ("hup", "Hupa"),
    ("iba", "Iban"),
    ("isl", "Icelandic"),
    ("ido", "Ido"),
    ("ibo", "Igbo"),
    ("ijo", "Ijo languages"),
    ("ilo", "Iloko"),
    ("smn", "Inari Sami"),
    ("inc", "Indic languages"),
    ("ine", "Indo-European languages"),
    ("ind", "Indonesian"),
    ("inh", "Ingush"),
    ("ina", "Interlingua (International Auxiliary Language Association)"),
    ("ile", "Interlingue; Occidental"),
    ("iku", "Inuktitut"),
    ("ipk", "Inupiaq"),
    ("ira", "Iranian languages"),
    ("gle", "Irish"),
    ("mga", "Irish, Middle (900-1200)"),
    ("sga", "Irish, Old (to 900)"),
    ("iro", "Iroquoian languages"),
    ("ita", "Italian"),
    ("jpn", "Japanese"),
    ("jav", "Javanese"),
    ("jrb", "Judeo-Arabic"),
    ("jpr", "Judeo-Persian"),
    ("kbd", "Kabardian"),
    ("kab", "Kabyle"),
    ("kac", "Kachin; Jingpho"),
    ("kal", "Kalaallisut; Greenlandic"),
    ("xal", "Kalmyk; Oirat"),
    ("kam", "Kamba"),
    ("kan", "Kannada"),
    ("kau", "Kanuri"),
    ("kaa", "Kara-Kalpak"),
    ("krc", "Karachay-Balkar"),
    ("krl", "Karelian"),
    ("kar", "Karen languages"),
    ("kas", "Kashmiri"),
    ("csb", "Kashubian"),
    ("kaw", "Kawi"),
    ("kaz", "Kazakh"),
    ("kha", "Khasi"),
    ("khi", "Khoisan languages"),
    ("kho", "Khotanese;Sakan"),
    ("kik", "Kikuyu; Gikuyu"),
    ("kmb", "Kimbundu"),
    ("kin", "Kinyarwanda"),
    ("kir", "Kirghiz; Kyrgyz"),
    ("tlh", "Klingon; tlhIngan-Hol"),
    ("kom", "Komi"),
    ("kon", "Kongo"),
    ("kok", "Konkani"),
    ("kor", "Korean"),
    ("kos", "Kosraean"),
    ("kpe", "Kpelle"),
    ("kro", "Kru languages"),
    ("kua", "Kuanyama; Kwanyama"),
    ("kum", "Kumyk"),
    ("kur", "Kurdish"),
    ("kru", "Kurukh"),
    ("kut", "Kutenai"),
    ("lad", "Ladino"),
    ("lah", "Lahnda"),
    ("lam", "Lamba"),
    ("day", "Land Dayak languages"),
    ("lao", "Lao"),
    ("lat", "Latin"),
    ("lav", "Latvian"),
    ("lez", "Lezghian"),
    ("lim", "Limburgan; Limburger; Limburgish"),
    ("lin", "Lingala"),
    ("lit", "Lithuanian"),
    ("jbo", "Lojban"),
    ("nds", "Low German; Low Saxon; German, Low; Saxon, Low"),
    ("dsb", "Lower Sorbian"),
    ("loz", "Lozi"),
    ("lub", "Luba-Katanga"),
    ("lua", "Luba-Lulua"),
    ("lui", "Luiseno"),
    ("smj", "Lule Sami"),
    ("lun", "Lunda"),
    ("luo", "Luo (Kenya and Tanzania)"),
    ("lus", "Lushai"),
    ("ltz", "Luxembourgish; Letzeburgesch"),
    ("mkd", "Macedonian"),
    ("mad", "Madurese"),
    ("mag", "Magahi"),
    ("mai", "Maithili"),
    ("mak", "Makasar"),
    ("mlg", "Malagasy"),
    ("msa", "Malay"),
    ("mal", "Malayalam"),
    ("mlt", "Maltese"),
    ("mnc", "Manchu"),
    ("mdr", "Mandar"),
    ("man", "Mandingo"),
    ("mni", "Manipuri"),
    ("mno", "Manobo languages"),
    ("glv", "Manx"),
    ("mri", "Maori"),
    ("arn", "Mapudungun; Mapuche"),
    ("mar", "Marathi"),
    ("chm", "Mari"),
    ("mah", "Marshallese"),
    ("mwr", "Marwari"),
    ("mas", "Masai"),
    ("myn", "Mayan languages"),
    ("men", "Mende"),
    ("mic", "Mi'kmaq; Micmac"),
    ("min", "Minangkabau"),
    ("mwl", "Mirandese"),
    ("moh", "Mohawk"),
    ("mdf", "Moksha"),
    ("mol", "Moldavian; Moldovan"),
    ("mkh", "Mon-Khmer languages"),
    ("lol", "Mongo"),
    ("mon", "Mongolian"),
    ("mos", "Mossi"),
    ("mul", "Multiple languages"),
    ("mun", "Munda languages"),
    ("nqo", "N'Ko"),
    ("nah", "Nahuatl languages"),
    ("nau", "Nauru"),
    ("nav", "Navajo; Navaho"),
    ("nde", "Ndebele, North; North Ndebele"),
    ("nbl", "Ndebele, South; South Ndebele"),
    ("ndo", "Ndonga"),
    ("nap", "Neapolitan"),
    ("new", "Nepal Bhasa; Newari"),
    ("nep", "Nepali"),
    ("nia", "Nias"),
    ("nic", "Niger-Kordofanian languages"),
    ("ssa", "Nilo-Saharan languages"),
    ("niu", "Niuean"),
    ("zxx", "No linguistic content; Not applicable"),
    ("nog", "Nogai"),
    ("non", "Norse, Old"),
    ("nai", "North American Indian languages"),
    ("frr", "Northern Frisian"),
    ("sme", "Northern Sami"),
    ("nor", "Norwegian"),
    ("nno", "Norwegian Nynorsk; Nynorsk, Norwegian"),
    ("nub", "Nubian languages"),
    ("nym", "Nyamwezi"),
    ("nyn", "Nyankole"),
    ("nyo", "Nyoro"),
    ("nzi", "Nzima"),
    ("oci", "Occitan (post 1500)"),
    ("arc", "Official Aramaic (700-300 BCE); Imperial Aramaic (700-300 BCE)"),
    ("oji", "Ojibwa"),
    ("ori", "Oriya"),
    ("orm", "Oromo"),
    ("osa", "Osage"),
    ("oss", "Ossetian; Ossetic"),
    ("oto", "Otomian languages"),
    ("pal", "Pahlavi"),
    ("pau", "Palauan"),
    ("pli", "Pali"),
    ("pam", "Pampanga; Kapampangan"),
    ("pag", "Pangasinan"),
    ("pan", "Panjabi; Punjabi"),
    ("pap", "Papiamento"),
    ("paa", "Papuan languages"),
    ("nso", "Pedi; Sepedi; Northern Sotho"),
    ("fas", "Persian"),
    ("peo", "Persian, Old (ca. 600-400 B.C.)"),
    ("phi", "Philippine languages"),
    ("phn", "Phoenician"),
    ("pon", "Pohnpeian"),
    ("pol", "Polish"),
    ("por", "Portuguese"),
    ("pra", "Prakrit languages"),
    ("pro", "Proven\xe7al, Old (to 1500); Occitan, Old (to 1500)"),
    ("pus", "Pushto; Pashto"),
    ("que", "Quechua"),
    ("raj", "Rajasthani"),
    ("rap", "Rapanui"),
    ("rar", "Rarotongan; Cook Islands Maori"),
    ("qaa-qtz", "Reserved for local use"),
    ("roa", "Romance languages"),
    ("ron", "Romanian"),
    ("roh", "Romansh"),
    ("rom", "Romany"),
    ("run", "Rundi"),
    ("rus", "Russian"),
    ("sal", "Salishan languages"),
    ("sam", "Samaritan Aramaic"),
    ("smi", "Sami languages"),
    ("smo", "Samoan"),
    ("sad", "Sandawe"),
    ("sag", "Sango"),
    ("san", "Sanskrit"),
    ("sat", "Santali"),
    ("srd", "Sardinian"),
    ("sas", "Sasak"),
    ("sco", "Scots"),
    ("sel", "Selkup"),
    ("sem", "Semitic languages"),
    ("srp", "Serbian"),
    ("srr", "Serer"),
    ("shn", "Shan"),
    ("sna", "Shona"),
    ("iii", "Sichuan Yi; Nuosu"),
    ("scn", "Sicilian"),
    ("sid", "Sidamo"),
    ("sgn", "Sign Languages"),
    ("bla", "Siksika"),
    ("snd", "Sindhi"),
    ("sin", "Sinhala; Sinhalese"),
    ("sit", "Sino-Tibetan languages"),
    ("sio", "Siouan languages"),
    ("sms", "Skolt Sami"),
    ("den", "Slave (Athapascan)"),
    ("sla", "Slavic languages"),
    ("slk", "Slovak"),
    ("slv", "Slovenian"),
    ("sog", "Sogdian"),
    ("som", "Somali"),
    ("son", "Songhai languages"),
    ("snk", "Soninke"),
    ("wen", "Sorbian languages"),
    ("sot", "Sotho, Southern"),
    ("sai", "South American Indian languages"),
    ("alt", "Southern Altai"),
    ("sma", "Southern Sami"),
    ("spa", "Spanish; Castilian"),
    ("srn", "Sranan Tongo"),
    ("zgh", "Standard Moroccan Tamazight"),
    ("suk", "Sukuma"),
    ("sux", "Sumerian"),
    ("sun", "Sundanese"),
    ("sus", "Susu"),
    ("swa", "Swahili"),
    ("ssw", "Swati"),
    ("swe", "Swedish"),
    ("gsw", "Swiss German; Alemannic; Alsatian"),
    ("syr", "Syriac"),
    ("tgl", "Tagalog"),
    ("tah", "Tahitian"),
    ("tai", "Tai languages"),
    ("tgk", "Tajik"),
    ("tmh", "Tamashek"),
    ("tam", "Tamil"),
    ("tat", "Tatar"),
    ("tel", "Telugu"),
    ("ter", "Tereno"),
    ("tet", "Tetum"),
    ("tha", "Thai"),
    ("bod", "Tibetan"),
    ("tig", "Tigre"),
    ("tir", "Tigrinya"),
    ("tem", "Timne"),
    ("tiv", "Tiv"),
    ("tli", "Tlingit"),
    ("tpi", "Tok Pisin"),
    ("tkl", "Tokelau"),
    ("tog", "Tonga (Nyasa)"),
    ("ton", "Tonga (Tonga Islands)"),
    ("tsi", "Tsimshian"),
    ("tso", "Tsonga"),
    ("tsn", "Tswana"),
    ("tum", "Tumbuka"),
    ("tup", "Tupi languages"),
    ("tur", "Turkish"),
    ("ota", "Turkish, Ottoman (1500-1928)"),
    ("tuk", "Turkmen"),
    ("tvl", "Tuvalu"),
    ("tyv", "Tuvinian"),
    ("twi", "Twi"),
    ("udm", "Udmurt"),
    ("uga", "Ugaritic"),
    ("uig", "Uighur; Uyghur"),
    ("ukr", "Ukrainian"),
    ("umb", "Umbundu"),
    ("mis", "Uncoded languages"),
    ("und", "Undetermined"),
    ("hsb", "Upper Sorbian"),
    ("urd", "Urdu"),
    ("uzb", "Uzbek"),
    ("vai", "Vai"),
    ("ven", "Venda"),
    ("vie", "Vietnamese"),
    ("vol", "Volap\xfck"),
    ("vot", "Votic"),
    ("wak", "Wakashan languages"),
    ("wln", "Walloon"),
    ("war", "Waray"),
    ("was", "Washo"),
    ("cym", "Welsh"),
    ("fry", "Western Frisian"),
    ("wal", "Wolaitta; Wolaytta"),
    ("wol", "Wolof"),
    ("xho", "Xhosa"),
    ("sah", "Yakut"),
    ("yao", "Yao"),
    ("yap", "Yapese"),
    ("yid", "Yiddish"),
    ("yor", "Yoruba"),
    ("ypk", "Yupik languages"),
    ("znd", "Zande languages"),
    ("zap", "Zapotec"),
    ("zza", "Zaza; Dimili; Dimli; Kirdki; Kirmanjki; Zazaki"),
    ("zen", "Zenaga"),
    ("zha", "Zhuang; Chuang"),
    ("zul", "Zulu"),
    ("zun", "Zuni"),
)


def get_jats_article_types():
    return settings.JATS_ARTICLE_TYPES


STAGE_UNSUBMITTED = "Unsubmitted"
STAGE_UNASSIGNED = "Unassigned"
STAGE_ASSIGNED = "Assigned"
STAGE_UNDER_REVIEW = "Under Review"
STAGE_UNDER_REVISION = "Under Revision"
STAGE_REJECTED = "Rejected"
STAGE_ACCEPTED = "Accepted"
STAGE_EDITOR_COPYEDITING = "Editor Copyediting"
STAGE_AUTHOR_COPYEDITING = "Author Copyediting"
STAGE_FINAL_COPYEDITING = "Final Copyediting"
STAGE_TYPESETTING = "Typesetting"
STAGE_TYPESETTING_PLUGIN = "typesetting_plugin"
STAGE_PROOFING = "Proofing"
STAGE_READY_FOR_PUBLICATION = "pre_publication"
STAGE_PUBLISHED = "Published"
STAGE_PREPRINT_REVIEW = "preprint_review"
STAGE_PREPRINT_PUBLISHED = "preprint_published"
STAGE_ARCHIVED = "Archived"

NEW_ARTICLE_STAGES = {
    STAGE_UNSUBMITTED,
    STAGE_UNASSIGNED,
}

FINAL_STAGES = {
    # An Article stage is final when it won't transition into further stages
    STAGE_PUBLISHED,
    STAGE_REJECTED,
    STAGE_ARCHIVED,
}

REVIEW_STAGES = {
    STAGE_ASSIGNED,
    STAGE_UNDER_REVIEW,
    STAGE_UNDER_REVISION,
    STAGE_ACCEPTED,
}

# Stages used to determine if a review assignment is open
REVIEW_ACCESSIBLE_STAGES = {STAGE_ASSIGNED, STAGE_UNDER_REVIEW, STAGE_UNDER_REVISION}

COPYEDITING_STAGES = {
    STAGE_EDITOR_COPYEDITING,
    STAGE_AUTHOR_COPYEDITING,
    STAGE_FINAL_COPYEDITING,
}

PREPRINT_STAGES = {STAGE_PREPRINT_REVIEW, STAGE_PREPRINT_PUBLISHED}

PUBLISHED_STAGES = {
    STAGE_PUBLISHED,
    STAGE_PREPRINT_PUBLISHED,
}

STAGE_CHOICES = [
    (STAGE_UNSUBMITTED, "Unsubmitted"),
    (STAGE_UNASSIGNED, "Unassigned"),
    (STAGE_ASSIGNED, "Assigned to Editor"),
    (STAGE_UNDER_REVIEW, "Peer Review"),
    (STAGE_UNDER_REVISION, "Revision"),
    (STAGE_REJECTED, "Rejected"),
    (STAGE_ACCEPTED, "Accepted"),
    (STAGE_EDITOR_COPYEDITING, "Editor Copyediting"),
    (STAGE_AUTHOR_COPYEDITING, "Author Copyediting"),
    (STAGE_FINAL_COPYEDITING, "Final Copyediting"),
    (STAGE_TYPESETTING, "Typesetting"),
    (STAGE_TYPESETTING_PLUGIN, "typesetting_plugin"),
    (STAGE_PROOFING, "Proofing"),
    (STAGE_READY_FOR_PUBLICATION, "Pre Publication"),
    (STAGE_PUBLISHED, "Published"),
    (STAGE_PREPRINT_REVIEW, "Preprint Review"),
    (STAGE_PREPRINT_PUBLISHED, "Preprint Published"),
    (STAGE_ARCHIVED, "Archived"),
]

PLUGIN_WORKFLOW_STAGES = []


class ArticleFunding(models.Model):
    class Meta:
        ordering = ("name",)

    article = models.ForeignKey(
        "submission.Article",
        on_delete=models.CASCADE,
        null=True,
    )
    name = models.CharField(
        max_length=500,
        blank=False,
        null=False,
        help_text="Funder name",
    )
    fundref_id = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Funder DOI (optional). Enter as a full Uniform "
        "Resource Identifier (URI), such as "
        "https://dx.doi.org/10.13039/501100021082",
    )
    funding_id = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="The grant ID (optional). Enter the ID by itself",
    )
    funding_statement = models.TextField(
        blank=True, help_text=_("Additional information regarding this funding entry")
    )

    def __str__(self):
        return f"Article funding entry {self.pk}: {self.name}"


class ArticleStageLog(models.Model):
    article = models.ForeignKey(
        "Article",
        on_delete=models.CASCADE,
    )
    stage_from = models.CharField(max_length=200, blank=False, null=False)
    stage_to = models.CharField(max_length=200, blank=False, null=False)
    date_time = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-date_time",)

    def __str__(self):
        return "Article {article_pk} from {stage_from} to {stage_to} at {date_time}".format(
            article_pk=self.article.pk,
            stage_from=self.stage_from,
            stage_to=self.stage_to,
            date_time=self.date_time,
        )


class PublisherNote(AbstractLastModifiedModel):
    text = JanewayBleachField(max_length=4000, blank=False, null=False)
    sequence = models.PositiveIntegerField(default=999)
    creator = models.ForeignKey(
        "core.Account",
        default=None,
        null=True,
        on_delete=models.SET_NULL,
    )
    date_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sequence",)

    def __str__(self):
        return "{0}: {1}".format(self.creator.full_name(), self.date_time)


class Keyword(models.Model):
    word = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.word


class KeywordArticle(models.Model):
    keyword = models.ForeignKey(
        "submission.Keyword",
        on_delete=models.CASCADE,
    )
    article = models.ForeignKey(
        "submission.Article",
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        unique_together = ("keyword", "article")

    def __str__(self):
        return self.keyword.word

    def __repr__(self):
        return "KeywordArticle(%s, %d)" % (self.keyword.word, self.article.id)


class ArticleManager(models.Manager):
    use_in_migrations = True

    def get_queryset(self):
        return super(ArticleManager, self).get_queryset().all()


class ArticlePrefetchAuthorsManager(ArticleManager):
    def get_queryset(self):
        FrozenAuthor = apps.get_model("submission", "FrozenAuthor")
        return (
            super()
            .get_queryset()
            .all()
            .prefetch_related(
                models.Prefetch(
                    "frozenauthor_set",
                    queryset=FrozenAuthor.select_related("author"),
                    to_attr="prefetched_author_accounts",
                )
            )
        )


class ArticleSearchManager(BaseSearchManagerMixin):
    SORT_KEYS = {
        "-title",
        "title",
        "date_published",
        "-date_published",
    }

    def search(self, *args, **kwargs):
        queryset = super().search(*args, **kwargs)
        if not isinstance(queryset, RawQuerySet):
            queryset = queryset.filter(
                date_published__lte=timezone.now(),
                stage=STAGE_PUBLISHED,
            )
        return queryset

    def mysql_search(self, search_term, search_filters, sort=None, site=None):
        queryset = self.get_queryset().none()
        if not search_term or not any(search_filters.values()):
            return queryset
        querysets = []
        if search_filters.get("title"):
            querysets.append(self.get_queryset().filter(title__search=search_term))
        if search_filters.get("authors"):
            querysets.append(
                self.get_queryset().filter(frozenauthor__first_name__search=search_term)
            )
            querysets.append(
                self.get_queryset().filter(frozenauthor__last_name__search=search_term)
            )
        if search_filters.get("abstract"):
            querysets.append(self.get_queryset().filter(abstract__search=search_term))
        if search_filters.get("keywords"):
            querysets.append(
                self.get_queryset().filter(keywords__word__search=search_term)
            )
        if search_filters.get("full_text"):
            querysets.append(
                self.get_queryset().filter(
                    galley__file__text__contents__search=search_term
                )
            )
        for search_queryset in querysets:
            queryset |= search_queryset

        if sort in self.SORT_KEYS:
            queryset = queryset.order_by(sort)

        return queryset

    def postgres_search(self, search_term, search_filters, sort=None, site=None):
        queryset = self.get_queryset()
        if not search_term or not any(search_filters.values()):
            return queryset.none()
        queryset = queryset.filter(
            date_published__lte=timezone.now(),
            stage=STAGE_PUBLISHED,
        )
        if site:
            queryset = queryset.filter(journal=site)
        lookups, annotations = self.build_postgres_lookups(search_term, search_filters)
        if annotations:
            queryset = queryset.annotate(**annotations)
        if lookups:
            queryset = queryset.filter(**lookups)

        if not sort or sort not in self.SORT_KEYS:
            sort = "-relevance"

        # Postgresql requires adding the DISTINCT ON column to ORDER BY
        queryset = queryset.order_by("id").distinct("id")

        # Now we can order the result set based by another column
        # We can't use the ORM for sorting because it is not possible to select
        # a column from a subquery filter and postgres sorting requires
        # distinct fields to match order_by fields
        inner_sql = self.stringify_queryset(queryset)

        if "relevance" in sort:
            # Relevance is not a field but an annotation
            return Article.objects.raw(
                f"SELECT * from ({inner_sql}) AS search ORDER BY relevance DESC"
            )
        else:
            order_by_sql = self.build_order_by_sql(sort)

            return Article.objects.raw(
                f"SELECT * from ({inner_sql}) AS search {order_by_sql}"
            )
            return queryset.order_by(sort)

    def build_order_by_sql(self, sort_key):
        """Compiles and returns the ORDER BY statement in sql for the sort_key
        It sorts an empty queryset of this model first, delegating the
        translation of the sort_key into the correct column name. Then it
        invokes Django's compiler to generate equivalent ORDER BY statement
        """
        sorted_qs = self.none().order_by(sort_key)
        sql = sorted_qs._query
        sql_compiler = sorted_qs._query.get_compiler(DEFAULT_DB_ALIAS)
        query = sql_compiler.query
        order_by = sql_compiler.query.order_by
        order_strings = []
        for field in order_by:
            order_strings.append("%s %s" % get_order_dir(field, "ASC"))
        return "ORDER BY %s" % ", ".join(order_strings)

    def build_postgres_lookups(self, search_term, search_filters):
        """Build the necessary lookup expressions based on the provided filters

        Each Filter is provided an arbitrary weight:
            +---------------+---------+---------+
            | column        | Weight  | Factor  |
            +===============+=========+=========+
            | Title         | A       | 1       |
            | Keyword       | B       | .4      |
            | Author names  | B       | .4      |
            | Abstract      | C       | .2      |
            | Galley text   | D       | .1      |
            +---------------+---------+---------+
        Each result is annotated with a 'relevance' value that will be factored
        using the above weights. The results are then sorted based on relevance
        which will have an impact only when multiple search filters are
        combined.
        """
        lookups = {}
        annotations = {"relevance": models.Value(1.0, models.FloatField())}
        vectors = []
        if search_filters.get("title"):
            vectors.append(SearchVector("title", weight="A"))
        if search_filters.get("keywords"):
            vectors.append(SearchVector("keywords__word", weight="B"))
        if search_filters.get("authors"):
            vectors.append(SearchVector("frozenauthor__last_name", weight="B"))
            vectors.append(SearchVector("frozenauthor__first_name", weight="B"))
        if search_filters.get("abstract"):
            vectors.append(SearchVector("abstract", weight="C"))
        if search_filters.get("full_text"):
            FileTextModel = swapper.load_model("core", "FileText")
            field_type = FileTextModel._meta.get_field("contents")
            if isinstance(field_type, SearchVectorField):
                vectors.append(
                    model_utils.SearchVector("galley__file__text__contents", weight="D")
                )
            else:
                vectors.append(SearchVector("galley__file__text__contents", weight="D"))
        if vectors:
            # Combine all vectors
            vector = vectors[0]
            for v in vectors[1:]:
                vector += v
            query = SearchQuery(search_term)
            relevance = SearchRank(vector, query)
            annotations["relevance"] = relevance
            # Since we weight file contents as 'D', the returned relevance
            # values can range between .01 and .1
            lookups["relevance__gte"] = 0.01

        if search_filters.get("ORCID"):
            lookups["frozenauthor__author__orcid"] = search_term
            lookups["frozenauthor__frozen_orcid"] = search_term
        return lookups, annotations

    @staticmethod
    def stringify_queryset(queryset):
        sql, params = queryset.query.sql_with_params()
        with connection.cursor() as cursor:
            return cursor.mogrify(sql, params).decode()


class ActiveArticleManager(models.Manager):
    def get_queryset(self):
        return (
            super(ActiveArticleManager, self)
            .get_queryset()
            .exclude(
                stage__in=[STAGE_ARCHIVED, STAGE_REJECTED, STAGE_UNSUBMITTED],
            )
        )


class Article(AbstractLastModifiedModel):
    journal = models.ForeignKey(
        "journal.Journal",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    # Metadata
    owner = models.ForeignKey(
        "core.Account",
        null=True,
        on_delete=models.SET_NULL,
    )
    title = JanewayBleachCharField(
        max_length=999,
        help_text=_("Your article title"),
    )
    subtitle = models.CharField(
        # Note: subtitle is deprecated as of version 1.4.2
        max_length=999,
        blank=True,
        null=True,
        help_text=_("Do not use--deprecated in version 1.4.1 and later."),
    )
    abstract = JanewayBleachField(
        blank=True,
        null=True,
    )
    non_specialist_summary = JanewayBleachField(
        blank=True, null=True, help_text="A summary of the article for non specialists."
    )
    keywords = M2MOrderedThroughField(
        Keyword,
        blank=True,
        null=True,
        through="submission.KeywordArticle",
    )
    language = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        choices=LANGUAGE_CHOICES,
        help_text=_("The primary language of the article"),
    )
    section = models.ForeignKey(
        "Section", blank=True, null=True, on_delete=models.SET_NULL
    )
    jats_article_type_override = DynamicChoiceField(
        max_length=255,
        dynamic_choices=get_jats_article_types(),
        choices=tuple(),
        blank=True,
        null=True,
        help_text="The type of article as per the JATS standard. This field allows you to override the default for the section.",
        default=None,
    )

    @property
    def jats_article_type(self):
        return self.jats_article_type_override or self.section.jats_article_type

    license = models.ForeignKey(
        "Licence", blank=True, null=True, on_delete=models.SET_NULL
    )
    publisher_notes = models.ManyToManyField(
        "PublisherNote", blank=True, null=True, related_name="publisher_notes"
    )

    # Remote: a flag that specifies that this article is actually a _link_ to a remote instance
    # this is useful for overlay journals. The ToC display of an issue uses this flag to link to a DOI rather
    # than an internal URL
    is_remote = models.BooleanField(
        default=False,
        verbose_name="Remote article",
        help_text="Check if this article is remote",
    )
    remote_url = models.URLField(
        blank=True,
        null=True,
        help_text="If the article is remote, its URL should be added.",
    )

    # Author
    # The authors field is deprecated. Use FrozenAuthor or author_accounts instead.
    authors = models.ManyToManyField(
        "core.Account", blank=True, null=True, related_name="authors"
    )
    correspondence_author = models.ForeignKey(
        "core.Account",
        related_name="correspondence_author",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    competing_interests_bool = models.BooleanField(default=False)
    competing_interests = JanewayBleachField(
        blank=True,
        null=True,
        help_text="If you have any conflict "
        "of interests in the publication of this "
        "article please state them here.",
    )
    rights = JanewayBleachField(
        blank=True,
        null=True,
        help_text="A custom statement on the usage rights for this article"
        " and associated materials, to be rendered in the article page",
    )

    article_number = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Optional article number to be displayed on issue and article pages. Not to be confused with article ID.",
    )

    # Files
    manuscript_files = models.ManyToManyField(
        "core.File", null=True, blank=True, related_name="manuscript_files"
    )
    data_figure_files = models.ManyToManyField(
        "core.File", null=True, blank=True, related_name="data_figure_files"
    )
    supplementary_files = models.ManyToManyField(
        "core.SupplementaryFile", null=True, blank=True, related_name="supp"
    )
    source_files = models.ManyToManyField(
        "core.File",
        blank=True,
        related_name="source_files",
    )

    # Galley
    render_galley = models.ForeignKey(
        "core.Galley",
        related_name="render_galley",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    # Dates
    date_started = models.DateTimeField(auto_now_add=True)

    date_accepted = models.DateTimeField(blank=True, null=True)
    date_declined = models.DateTimeField(blank=True, null=True)
    date_submitted = models.DateTimeField(blank=True, null=True)
    date_published = DateTimePickerModelField(blank=True, null=True)
    date_updated = models.DateTimeField(blank=True, null=True)
    current_step = models.IntegerField(default=1)

    # Pages
    first_page = models.PositiveIntegerField(blank=True, null=True)
    last_page = models.PositiveIntegerField(blank=True, null=True)
    page_numbers = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        help_text=_("Custom page range. e.g.: 'I-VII' or 1-3,4-8"),
    )
    total_pages = models.PositiveIntegerField(blank=True, null=True)

    # Stage
    stage = DynamicChoiceField(
        max_length=200,
        blank=True,
        null=False,
        default=STAGE_UNSUBMITTED,
        choices=STAGE_CHOICES,
        dynamic_choices=PLUGIN_WORKFLOW_STAGES,
        help_text="<strong>WARNING</strong>: Manually changing the stage of a submission\
             overrides Janeway's workflow. It should only be changed to a value\
             which is know to be safe such as a stage an article has already\
             been a part of before.",
    )

    # Agreements
    publication_fees = models.BooleanField(default=False)
    submission_requirements = models.BooleanField(default=False)
    copyright_notice = models.BooleanField(default=False)
    comments_editor = JanewayBleachField(
        blank=True,
        null=True,
        verbose_name="Comments to the Editor",
        help_text=_("Add any comments you'd like the editor to consider here."),
    )

    # an image of recommended size: 750 x 324
    large_image_file = models.ForeignKey(
        "core.File",
        null=True,
        blank=True,
        related_name="image_file",
        on_delete=models.SET_NULL,
    )
    exclude_from_slider = models.BooleanField(default=False)

    thumbnail_image_file = models.ForeignKey(
        "core.File",
        null=True,
        blank=True,
        related_name="thumbnail_file",
        on_delete=models.SET_NULL,
    )

    # Whether or not we should display that this article has been "peer reviewed"
    peer_reviewed = models.BooleanField(default=True)

    # Whether or not this article was imported ie. not processed by this platform
    is_import = models.BooleanField(default=False)

    metric_stats = None

    # Agreement, this field records the submission checklist that was present when this article was submitted.
    article_agreement = JanewayBleachField(default="")

    custom_how_to_cite = JanewayBleachField(
        blank=True,
        null=True,
        help_text=_(
            "Custom 'how to cite' text. To be used only if the block"
            " generated by Janeway is not suitable."
        ),
    )

    publisher_name = models.CharField(
        max_length=999,
        null=True,
        blank=True,
        help_text=_(
            "Name of the publisher who published this article"
            " Only relevant to migrated articles from a different publisher"
        ),
    )

    publication_title = models.CharField(
        max_length=999,
        null=True,
        blank=True,
        help_text=_(
            "Name of the publisher who published this article"
            " Only relevant to migrated articles from a different publisher"
        ),
    )
    ISSN_override = models.CharField(
        max_length=999,
        null=True,
        blank=True,
        help_text=_(
            "Original ISSN of this article's journal when published"
            " Only relevant for back content published under a different title"
        ),
    )

    # iThenticate ID
    ithenticate_id = models.TextField(blank=True, null=True)
    ithenticate_score = models.IntegerField(blank=True, null=True)

    # Primary issue, allows the Editor to set the Submission's primary Issue
    primary_issue = models.ForeignKey(
        "journal.Issue",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="You can only assign an issue "
        "that this article is part of. "
        "You can add this article to an "
        "issue from the Issue Manager.",
    )
    projected_issue = models.ForeignKey(
        "journal.Issue",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="projected_issue",
        help_text="This field is for internal purposes only "
        "before publication. You can use it to "
        "track likely issue assignment before formally "
        "assigning an issue.",
    )

    # Meta
    meta_image = models.ImageField(
        blank=True, null=True, upload_to=article_media_upload, storage=fs
    )

    preprint_journal_article = models.ForeignKey(
        "submission.Article",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    reviews_shared = models.BooleanField(
        default=False,
        help_text="Marked true when an editor manually shares reviews with "
        "other reviewers using the decision helper page.",
    )

    objects = ArticleSearchManager()
    active_objects = ActiveArticleManager()

    class Meta:
        ordering = ("-date_published", "title")

    def __getattribute__(self, name):
        if name == "authors":
            warnings.warn(
                "The 'authors' field is deprecated. Use 'frozenauthor_set'.",
                DeprecationWarning,
                stacklevel=2,
            )
        return super().__getattribute__(name)

    @property
    def author_accounts(self):
        """
        Get the accounts connected to the article via a FrozenAuthor record.
        """
        return core_models.Account.objects.filter(frozenauthor__article=self).order_by(
            "frozenauthor__order"
        )

    # credits
    def authors_and_credits(self):
        """
        Returns a dictionary of all author records with any
        CRediT roles for the article.
        Respects the normal author order and orders roles A-Z by slug.
        :rtype: dict[Account | FrozenAuthor, QuerySet[CreditRecord]]
        """
        result = {}
        for frozen_author in self.frozen_authors():
            result[frozen_author] = frozen_author.credits
        return result

    @property
    def safe_title(self):
        if self.title:
            return mark_safe(self.title)
        else:
            return "[Untitled]"

    @property
    def how_to_cite(self):
        if self.custom_how_to_cite:
            return self.custom_how_to_cite

        template = "common/elements/how_to_cite.html"
        authors = self.frozenauthor_set.all()
        author_str = ""
        for author in authors:
            if author == authors.first():
                author_str = author.citation_name()
            elif not author == authors.last():
                author_str = author_str + f", {author.citation_name()}"
            else:
                author_str = author_str + f" & {author.citation_name()}"
        if author_str:
            author_str += ","
        year_str = ""
        if self.date_published:
            year_str = "({:%Y})".format(self.date_published)
        journal_str = "<i>%s</i>" % (self.publication_title or self.journal.name)
        issue_str = ""
        issue = self.issue
        if issue:
            if issue.volume:
                if issue.issue and issue.issue != "0":
                    issue_str = "%s(%s)" % (issue.volume, issue.issue)
                else:
                    issue_str = str(issue.volume)
            elif issue.issue and issue.issue != "0":
                issue_str = str(issue.issue)
            if self.article_number:
                issue_str += ": {}".format(self.article_number)

        doi_str = ""
        pages_str = ""
        if self.page_range:
            pages_str = " {0}.".format(self.page_range)
        doi = self.get_doi()
        if doi:
            doi_str = (
                'doi: <a href="https://doi.org/{0}">https://doi.org/{0}</a>'.format(doi)
            )

        context = {
            "author_str": author_str,
            "year_str": year_str,
            "title": self.safe_title,
            "journal_str": journal_str,
            "issue_str": issue_str,
            "doi_str": doi_str,
            "pages_str": pages_str,
        }
        return render_to_string(template, context)

    @property
    def page_range(self):
        if self.page_numbers:
            return self.page_numbers
        elif self.first_page and self.last_page:
            return "{}–{}".format(self.first_page, self.last_page)
        elif self.first_page:
            return "{}".format(self.first_page)
        else:
            return ""

    @property
    def metrics(self):
        # only do the metric calculation once per template call
        if not self.metric_stats:
            self.metric_stats = ArticleMetrics(self)
        return self.metric_stats

    @property
    def has_galley(self):
        return self.galley_set.all().exists()

    @staticmethod
    @cache(600)
    def publication_detail_settings(journal):
        display_date_accepted = journal.get_setting(
            group_name="article",
            setting_name="display_date_accepted",
        )
        display_date_submitted = journal.get_setting(
            group_name="article",
            setting_name="display_date_submitted",
        )
        return display_date_submitted, display_date_accepted

    @property
    def has_publication_details(self):
        """Determines if an article has any publication details"""
        display_date_submitted, display_date_accepted = (
            self.publication_detail_settings(self.journal)
        )
        return (
            self.page_range
            or self.article_number
            or self.publisher_name
            or self.publication_title
            or self.ISSN_override
            or (display_date_submitted and self.date_submitted)
            or (display_date_accepted and self.date_accepted)
            or self.date_published
        )

    @property
    def journal_title(self):
        return self.publication_title or self.journal.name

    @property
    def journal_issn(self):
        return self.ISSN_override or self.journal.issn

    @property
    def publisher(self):
        return self.publisher_name or self.journal.publisher or self.journal.press.name

    def journal_sections(self):
        return (
            (section.id, section.name) for section in self.journal.section_set.all()
        )

    @property
    def carousel_subtitle(self):
        carousel_text = ""

        idx = 0

        for author in self.frozenauthor_set.all():
            if idx > 0:
                idx = 1
                carousel_text += ", "

            if author.institution:
                carousel_text += author.full_name() + " ({0})".format(
                    author.institution
                )
            else:
                carousel_text += author.full_name()

            idx = 1

        return carousel_text

    @property
    def carousel_title(self):
        return self.safe_title

    @property
    def carousel_image_resolver(self):
        return "article_file_download"

    @property
    def pdfs(self):
        ret = self.galley_set.filter(type="pdf")
        return ret

    @property
    def get_render_galley(self):
        if self.render_galley:
            return self.render_galley

        ret = self.galley_set.filter(
            file__mime_type__in=files.XML_MIMETYPES,
        ).order_by(
            "sequence",
        )

        if len(ret) > 0:
            return ret[0]
        else:
            return None

    @property
    def xml_galleys(self):
        ret = self.galley_set.filter(file__mime_type__in=files.XML_MIMETYPES).order_by(
            "sequence"
        )

        return ret

    def all_galley_file_pks(self):
        """Returns all Galley and related file pks"""
        file_list = list()

        for galley in self.galley_set.all():
            file_list.append(galley.file.pk)

            if galley.css_file:
                file_list.append(galley.css_file.pk)

            for file in galley.images.all():
                file_list.append(file.pk)

        return file_list

    @property
    def has_all_supplements(self):
        for xml_file in self.xml_galleys:
            xml_file_contents = xml_file.get_file(self)

            souped_xml = BeautifulSoup(xml_file_contents, "lxml")

            elements = {"img": "src", "graphic": "xlink:href"}

            # iterate over all found elements
            for element, attribute in elements.items():
                images = souped_xml.findAll(element)

                # iterate over all found elements of each type in the elements dictionary
                for idx, val in enumerate(images):
                    # attempt to pull a URL from the specified attribute
                    url = val.get(attribute, None)

                    if not url:
                        return False

                    try:
                        named_files = self.data_figure_files.filter(
                            original_filename=url
                        ).first()

                        if not named_files:
                            return False

                    except core_models.File.DoesNotExist:
                        return False

        return True

    def index_full_text(self):
        """Indexes the render galley for full text search
        :return: A boolean indicating if a file has been processed
        """
        indexed = False

        # Delete currently indexed article files
        FileTextModel = swapper.load_model("core", "FileText")
        current = FileTextModel.objects.filter(file__article_id=self.pk)
        if current.exists():
            current.delete()

        # Generate new from best possible galley
        render_galley = self.get_render_galley
        if render_galley:
            indexed = render_galley.file.index_full_text()
        elif self.galley_set.exists():
            for galley in self.galley_set.all():
                indexed = galley.file.index_full_text()
                if indexed:
                    break
        return indexed

    @property
    @cache(300)
    def identifier(self):
        from identifiers import models as identifier_models

        try:
            type_to_fetch = "doi"
            return identifier_models.Identifier.objects.filter(
                id_type=type_to_fetch, article=self
            )[0]
        except BaseException:
            new_id = identifier_models.Identifier(
                id_type="id", identifier=self.id, article=self
            )
            return new_id

    def get_identifier(self, identifier_type, object=False):
        try:
            try:
                doi = identifier_models.Identifier.objects.get(
                    id_type=identifier_type, article=self
                )
            except identifier_models.Identifier.MultipleObjectsReturned:
                doi = identifier_models.Identifier.objects.filter(
                    id_type=identifier_type, article=self
                )[0]
            if not object:
                return doi.identifier
            else:
                return doi
        except identifier_models.Identifier.DoesNotExist:
            return None

    def get_doi(self):
        return self.get_identifier("doi")

    def get_doi_url(self):
        ident = self.get_identifier("doi", object=True)
        if ident:
            return ident.get_doi_url()
        return None

    @property
    def get_doi_object(self):
        return self.get_identifier("doi", object=True)

    @property
    @cache(30)
    def doi_pattern_preview(self):
        return id_logic.render_doi_from_pattern(self)

    @property
    def identifiers(self):
        from identifiers import models as identifier_models

        return identifier_models.Identifier.objects.filter(article=self)

    def get_pubid(self):
        return self.get_identifier("pubid")

    def non_correspondence_authors(self):
        if self.correspondence_author:
            return self.author_accounts.exclude(
                pk=self.correspondence_author.pk,
            )
        else:
            return self.author_accounts

    def is_unsubmitted(self):
        return self.stage == STAGE_UNSUBMITTED

    def is_accepted(self):
        if self.date_published:
            return True

        if ArticleStageLog.objects.filter(
            article=self,
            stage_to=STAGE_ACCEPTED,
        ).exists():
            return True

        if self.stage == STAGE_ACCEPTED:
            return True

        if (
            self.stage not in NEW_ARTICLE_STAGES | REVIEW_STAGES
            and self.stage != STAGE_REJECTED
        ):
            return True

        return False

    @cached_property
    def in_review_stages(self):
        return self.stage in REVIEW_STAGES

    def peer_reviews_for_author_consumption(self):
        return self.reviewassignment_set.filter(
            for_author_consumption=True,
        )

    @property
    def funders(self):
        """Method replaces the funders m2m model for backwards compat."""
        return ArticleFunding.objects.filter(article=self)

    def __str__(self):
        return "%s - %s" % (self.pk, truncatesmart(self.title))

    @staticmethod
    @cache(300)
    def get_article(journal, identifier_type, identifier):
        from identifiers import models as identifier_models

        try:
            article = None
            # resolve an article from an identifier type and an identifier
            if identifier_type.lower() == "id":
                # this is the hardcoded fallback type: using built-in id
                article = Article.objects.filter(
                    id=identifier,
                    journal=journal,
                )[0]
            else:
                # this looks up an article by an ID type and an identifier string
                article = identifier_models.Identifier.objects.filter(
                    id_type=identifier_type,
                    identifier=identifier,
                )[0].article

                if not article.journal == journal:
                    return None

            return article
        except BaseException:  # no article found
            # TODO: handle better and log
            return None

    @staticmethod
    def get_press_article(press, identifier_type, identifier):
        from identifiers import models as identifier_models

        try:
            article = None
            # resolve an article from an identifier type and an identifier
            if identifier_type.lower() == "id":
                # this is the hardcoded fallback type: using built-in id
                article = Article.objects.filter(id=identifier)[0]
            else:
                # this looks up an article by an ID type and an identifier string
                article = identifier_models.Identifier.objects.filter(
                    id_type=identifier_type, identifier=identifier
                )[0].article

            return article
        except BaseException:  # no article found
            # TODO: handle better and log
            return None

    @property
    @cache(600)
    def url(self):
        return self.journal.site_url(path=self.local_url)

    @property
    def local_url(self):
        from identifiers import models as identifier_models

        try:
            identifier = identifier_models.Identifier.objects.get(
                id_type="pubid",
                article=self,
            )
        except identifier_models.Identifier.DoesNotExist:
            identifier = identifier_models.Identifier(
                id_type="id", identifier=self.pk, article=self
            )

        url = reverse(
            "article_view",
            kwargs={
                "identifier_type": identifier.id_type,
                "identifier": identifier.identifier,
            },
        )

        return url

    @property
    def pdf_url(self):
        pdfs = self.pdfs
        path = reverse(
            "article_download_galley",
            kwargs={"article_id": self.pk, "galley_id": pdfs[0].pk},
        )
        return self.journal.site_url(path=path)

    def get_remote_url(self, request):
        parsed_uri = urlparse(
            "http" + ("", "s")[request.is_secure()] + "://" + request.META["HTTP_HOST"]
        )
        domain = "{uri.scheme}://{uri.netloc}".format(uri=parsed_uri)
        url = domain + self.local_url

        return url

    def step_to_url(self):
        funding_enabled = False
        if self.journal and getattr(self.journal, "submissionconfiguration", None):
            funding_enabled = self.journal.submissionconfiguration.funding

        if self.current_step == 1:
            return reverse("submit_info", kwargs={"article_id": self.id})
        elif self.current_step == 2:
            return reverse("submit_authors", kwargs={"article_id": self.id})
        elif self.current_step == 3:
            return reverse("submit_files", kwargs={"article_id": self.id})
        elif self.current_step == 4 and funding_enabled:
            return reverse("submit_funding", kwargs={"article_id": self.id})
        elif self.current_step == 4:
            return reverse("submit_review", kwargs={"article_id": self.id})
        else:
            return reverse("submit_review", kwargs={"article_id": self.id})

    def step_name(self):
        funding_enabled = False
        if self.journal and getattr(self.journal, "submissionconfiguration", None):
            funding_enabled = self.journal.submissionconfiguration.funding
        if self.current_step == 1:
            return "Article Information"
        elif self.current_step == 2:
            return "Article Authors"
        elif self.current_step == 3:
            return "Article Files"
        elif self.current_step == 4 and funding_enabled:
            return "Article Funding"
        elif self.current_step == 4:
            return "Review Article Submission"
        elif self.current_step == 5 and funding_enabled:
            return "Review Article Submission"
        else:
            return "Submission Complete"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            current_object = Article.objects.get(pk=self.pk)
            if current_object.stage != self.stage:
                ArticleStageLog.objects.create(
                    article=self, stage_from=current_object.stage, stage_to=self.stage
                )
        super(Article, self).save(*args, **kwargs)

    def folder_path(self):
        return os.path.join(settings.BASE_DIR, "files", "articles", str(self.pk))

    def production_managers(self):
        return [
            assignment.production_manager
            for assignment in self.productionassignment_set.all()
        ]

    def editor_list(self):
        return [assignment.editor for assignment in self.editorassignment_set.all()]

    def editors(self):
        return [
            {
                "editor": assignment.editor,
                "editor_type": assignment.editor_type,
                "assignment": assignment,
            }
            for assignment in self.editorassignment_set.all()
        ]

    def section_editors(self, emails=False):
        editors = [
            assignment.editor
            for assignment in self.editorassignment_set.filter(
                editor_type="section-editor"
            )
        ]

        if emails:
            return set([editor.email for editor in editors])

        else:
            return editors

    def editor_emails(self):
        return [
            assignment.editor.email for assignment in self.editorassignment_set.all()
        ]

    def contact_emails(self):
        emails = [fa.email for fa in self.frozenauthor_set.all() if fa.email]
        emails.append(self.owner.email)
        return set(emails)

    def peer_reviewers(self, emails=False, completed=False):
        if completed:
            assignments = self.completed_reviews_with_decision
        else:
            assignments = self.reviewassignment_set.all()
        if emails:
            return set(assignment.reviewer.email for assignment in assignments)
        else:
            return set(assignment.reviewer for assignment in assignments)

    def issues_list(self):
        from journal import models as journal_models

        return journal_models.Issue.objects.filter(
            journal=self.journal, articles__in=[self]
        )

    @cache(7200)
    def altmetrics(self):
        alm = self.altmetric_set.all()
        return {
            "twitter": alm.filter(source="twitter"),
            "wikipedia": alm.filter(source="wikipedia"),
            "reddit": alm.filter(source="reddit"),
            "hypothesis": alm.filter(source="hypothesis"),
            "wordpress": alm.filter(source="wordpress.com"),
            "crossref": alm.filter(source="crossref"),
        }

    @property
    @cache(300)
    def issue(self):
        """
        Yields the first issue in the current journal that contains this article.
        :return: an issue object or None
        """
        if self.primary_issue:
            return self.primary_issue

        issues = self.issues_list()

        if issues:
            issues = issues[0]
        else:
            return None

        return issues

    @property
    def issue_title(self):
        """The issue title in the context of the article

        When an article renders its issue title, it can include article
        dependant elements such as page ranges or article numbers. For this
        reason, we cannot render database cached issue title.
        """
        if not self.issue:
            return ""

        if self.issue.issue_type.code != "issue":
            return self.issue.issue_title
        else:
            template = Template(
                " • ".join(
                    [
                        title_part
                        for title_part in self.issue.issue_title_parts(article=self)
                        if title_part
                    ]
                )
            )
            return mark_safe(template.render(Context()))

    @property
    def issue_title_a11y(self):
        """The accessible issue title in the context of the article
        see issue_title above.
        """
        if not self.issue:
            return ""

        if self.issue.issue_type.code != "issue":
            return self.issue.issue_title
        else:
            template = Template(
                ", ".join(
                    [
                        title_part
                        for title_part in self.issue.issue_title_parts(article=self)
                        if title_part
                    ]
                )
            )
            return template.render(Context())

    def author_list(self):
        return ", ".join([author.full_name() for author in self.frozenauthor_set.all()])

    def bibtex_author_list(self):
        return " AND ".join(
            [author.full_name() for author in self.frozen_authors()],
        )

    def keyword_list_str(self, separator=","):
        if self.keywords.exists():
            return separator.join(kw.word for kw in self.keywords.all())
        return ""

    def can_edit(self, user):
        """
        Determines whether a user can edit the article.
        They can if:
          - they are staff of the press, or
          - they are a section editor on the article's section, or
          - they are an editor of the journal, or
          - they are the owner and the article is unsubmitted.
        """

        if user.is_staff:
            return True
        elif user in self.section_editors():
            return True
        elif not user.is_anonymous and user.is_editor(
            request=None,
            journal=self.journal,
        ):
            return True
        elif self.owner == user and self.is_unsubmitted():
            return True
        else:
            return False

    def current_review_round(self):
        try:
            return self.reviewround_set.all().order_by("-round_number")[0].round_number
        except IndexError:
            return 1

    def current_review_round_object(self):
        try:
            return self.reviewround_set.all().order_by("-round_number")[0]
        except IndexError:
            return None

    @property
    def active_reviews(self):
        return self.reviewassignment_set.filter(
            is_complete=False, date_declined__isnull=True
        )

    @property
    def completed_reviews(self):
        return self.reviewassignment_set.filter(
            is_complete=True, date_declined__isnull=True
        )

    @property
    def completed_reviews_with_permission(self):
        return self.completed_reviews.filter(permission_to_make_public=True)

    @property
    def public_reviews(self):
        return self.completed_reviews_with_permission.filter(display_public=True)

    @property
    def completed_reviews_with_decision(self):
        return self.reviewassignment_set.filter(
            is_complete=True,
            date_declined__isnull=True,
            decision__isnull=False,
        ).exclude(decision="withdrawn")

    @property
    def completed_reviews_with_decision_previous_rounds(self):
        completed_reviews = self.completed_reviews_with_decision
        return completed_reviews.filter(
            review_round__round_number__lt=self.current_review_round(),
        )

    def active_review_request_for_user(self, user):
        try:
            return self.reviewassignment_set.filter(
                is_complete=False, date_declined__isnull=True, reviewer=user
            ).first()
        except review_models.ReviewAssignment.DoesNotExist:
            return None

    def reviews_not_withdrawn(self):
        return self.reviewassignment_set.exclude(decision="withdrawn")

    def number_of_withdrawn_reviews(self):
        return self.reviewassignment_set.filter(decision="withdrawn").count()

    def accept_article(self, stage=None):
        self.date_accepted = timezone.now()
        self.date_declined = None

        if stage:
            self.stage = stage
        else:
            self.stage = STAGE_ACCEPTED

        if self.completed_reviews_with_decision.count() > 0:
            self.peer_reviewed = True

        self.save()

        if self.journal.use_crossref:
            id = id_logic.generate_crossref_doi_with_pattern(self)
            if self.journal.register_doi_at_acceptance:
                id.register()

    def decline_article(self):
        self.date_declined = timezone.now()
        self.date_accepted = None
        self.stage = STAGE_REJECTED

        self.incomplete_reviews().update(
            decision=RD.DECISION_WITHDRAWN.value,
            date_complete=timezone.now(),
            is_complete=True,
        )
        self.save()

    def undo_review_decision(self):
        self.date_accepted = None
        self.date_declined = None

        if review_models.EditorAssignment.objects.filter(article=self):
            self.stage = STAGE_ASSIGNED
        else:
            self.stage = STAGE_UNASSIGNED

        self.save()

    def accept_preprint(self, date, time):
        self.date_accepted = timezone.now()
        self.date_declined = None
        self.stage = STAGE_PREPRINT_PUBLISHED
        self.date_published = dateparser.parse(
            "{date} {time}".format(date=date, time=time)
        )
        self.save()

    def mark_reviews_shared(self):
        self.reviews_shared = True
        self.save()

    def user_is_author(self, user):
        if user.email in [account.email for account in self.author_accounts]:
            return True
        return False

    def has_manuscript_file(self):
        if self.manuscript_files.all():
            return True
        else:
            return False

    def is_under_revision(self):
        if self.revisionrequest_set.filter(date_completed__isnull=True):
            return True
        else:
            return False

    def get_next_galley_sequence(self):
        galley_sequences = [galley.sequence for galley in self.galley_set.all()]
        return len(galley_sequences) + 1

    @property
    def is_published(self):
        if (
            (self.stage == STAGE_PUBLISHED or self.stage == STAGE_PREPRINT_PUBLISHED)
            and self.date_published
            and self.date_published < timezone.now()
        ):
            return True
        else:
            return False

    @property
    def scheduled_for_publication(self):
        return bool(self.stage == STAGE_PUBLISHED and self.date_published)

    def snapshot_authors(self, article=None, force_update=True):
        """Creates/updates FrozenAuthor records for this article's authors
        :param article: (deprecated) should not pass this argument
        :param force_update: (bool) Whether or not to update existing records
        """
        raise DeprecationWarning("Use FrozenAuthor directly instead.")
        subq = models.Subquery(
            ArticleAuthorOrder.objects.filter(
                article=self, author__id=models.OuterRef("id")
            ).values_list("order")
        )
        authors = self.authors.annotate(order=subq).order_by("order")
        for author in authors:
            author.snapshot_as_author(self, force_update)

    def frozen_authors(self):
        return FrozenAuthor.objects.filter(article=self)

    def frozen_authors_for_jats_contribs(self):
        """
        Returns a list of dicts, each representing a frozen author and all data
        needed to render their full <contrib> block including affiliations.

        Each dict contains:
            - author: the FrozenAuthor object
            - affiliations: list of valid affiliation objects (with organisation name)
        """
        authors = self.frozen_authors().prefetch_related(
            "controlledaffiliation_set__organization__ror_display",
            "controlledaffiliation_set__organization__custom_label",
            "controlledaffiliation_set__organization__labels",
        )

        result = []

        for author in authors:
            valid_affiliations = []
            for affiliation in author.controlledaffiliation_set.all():
                org = affiliation.organization
                if not org:
                    continue
                org_name_obj = org.name
                if not org_name_obj:
                    continue
                name_value = org_name_obj.value
                if not name_value or not name_value.strip():
                    continue
                valid_affiliations.append(affiliation)

            result.append(
                {
                    "author": author,
                    "affiliations": valid_affiliations,
                }
            )

        return result

    def editor_override(self, editor):
        check = review_models.EditorOverride.objects.filter(article=self, editor=editor)

        if check:
            return True
        else:
            return False

    def active_revision_requests(self):
        return self.revisionrequest_set.filter(date_completed__isnull=True)

    def completed_revision_requests(self):
        return self.revisionrequest_set.filter(date_completed__isnull=False)

    def active_author_copyedits(self):
        author_copyedits = []

        for assignment in self.copyeditassignment_set.all():
            for review in assignment.active_author_reviews():
                author_copyedits.append(review)

        return author_copyedits

    @property
    def custom_fields(self):
        """Returns all the FieldAnswers configured for rendering"""
        return self.fieldanswer_set.filter(
            field__display=True,
            answer__isnull=False,
        )

    def get_meta_image_path(self):
        path = None
        if self.meta_image and self.meta_image.url:
            path = self.meta_image.url
        elif self.large_image_file and self.large_image_file.id:
            path = reverse(
                "article_file_download",
                kwargs={
                    "identifier_type": "id",
                    "identifier": self.pk,
                    "file_id": self.large_image_file.pk,
                },
            )
        elif self.thumbnail_image_file and self.thumbnail_image_file.id:
            path = reverse(
                "article_file_download",
                kwargs={
                    "identifier_type": "id",
                    "identifier": self.pk,
                    "file_id": self.thumbnail_image_file.pk,
                },
            )
        elif self.journal.default_large_image:
            path = self.journal.default_large_image.url

        if path:
            return self.journal.site_url(path=path)
        else:
            return ""

    def unlink_meta_file(self):
        path = os.path.join(self.meta_image.storage.base_location, self.meta_image.name)
        if os.path.isfile(path):
            os.unlink(path)

    def next_author_sort(self):
        raise DeprecationWarning("Use FrozenAuthor instead.")
        current_orders = [
            order.order for order in ArticleAuthorOrder.objects.filter(article=self)
        ]
        if not current_orders:
            return 0
        else:
            return max(current_orders) + 1

    def next_frozen_author_order(self):
        order = 0
        for author in FrozenAuthor.objects.filter(article=self):
            if author.order >= order:
                order = author.order + 1
        return order

    def subject_editors(self):
        editors = list()
        subjects = self.subject_set.all().prefetch_related("editors")

        for subject in subjects:
            for editor in subject.editors.all():
                editors.append(editor)

        return set(editors)

    def set_preprint_subject(self, subject):
        for preprint_subject in self.subject_set.all():
            preprint_subject.preprints.remove(self)

        subject.preprints.add(self)

    def get_subject_area(self):
        subjects = self.subject_set.all()

        if subjects:
            return subjects[0]
        else:
            return None

    @cache(600)
    def workflow_stages(self):
        return core_models.WorkflowLog.objects.filter(article=self)

    def distinct_workflow_elements(self):
        return core_models.WorkflowElement.objects.filter(
            pk__in=self.workflowlog_set.values_list("element").distinct()
        )

    @property
    def current_workflow_element(self):
        try:
            workflow_element_name = workflow.STAGES_ELEMENTS.get(
                self.stage,
            )
            return core_models.WorkflowElement.objects.get(
                journal=self.journal,
                element_name=workflow_element_name,
            )
        except (KeyError, core_models.WorkflowElement.DoesNotExist):
            return None

    @property
    def current_workflow_element_url(self):
        kwargs = {"article_id": self.pk}
        # STAGE_UNASSIGNED and STAGE_PUBLISHED arent elements so are hardcoded.
        if self.stage == STAGE_UNASSIGNED:
            path = reverse("review_unassigned_article", kwargs=kwargs)
        elif self.stage in FINAL_STAGES:
            path = reverse("manage_archive_article", kwargs=kwargs)
        elif not self.stage:
            logger.error(
                "Article #{} has no Stage.".format(
                    self.pk,
                )
            )
            return "?workflow_element_url=no_stage"
        else:
            element = self.current_workflow_element
            if element:
                path = reverse(element.jump_url, kwargs=kwargs)
            else:
                # In order to ensure the Dashboard renders we purposefully do
                # not raise an error message here.
                logger.error(
                    "There is no workflow element for stage {}.".format(
                        self.stage,
                    )
                )
                return "?workflow_element_url=no_element"
        return self.journal.site_url(path=path)

    def next_workflow_element(self):
        try:
            current_workflow_element = self.current_workflow_element
            journal_elements = list(self.journal.workflow().elements.all())
            i = journal_elements.index(current_workflow_element)
            return journal_elements[i + 1]
        except (IndexError, ValueError):
            return "No next workflow stage found"

    @cache(600)
    def render_sample_doi(self):
        return id_logic.render_doi_from_pattern(self)

    @property
    def registration_preview(self):
        return id_logic.preview_registration_information(self)

    def close_core_workflow_objects(self):
        from review import models as review_models
        from copyediting import models as copyedit_models
        from production import models as prod_models
        from proofing import models as proof_models

        review_models.ReviewAssignment.objects.filter(
            article=self,
            date_complete__isnull=True,
        ).update(
            date_declined=timezone.now(),
            date_complete=timezone.now(),
            is_complete=True,
        )

        copyedit_models.CopyeditAssignment.objects.filter(
            article=self,
            copyedit_accepted__isnull=True,
        ).update(
            copyeditor_completed=timezone.now(),
            copyedit_acknowledged=True,
            copyedit_accepted=timezone.now(),
            date_decided=timezone.now(),
            decision="cancelled",
        )
        copyedit_models.AuthorReview.objects.filter(
            assignment__article=self,
            date_decided__isnull=True,
        ).update(
            decision="accept",
            date_decided=timezone.now(),
        )

        prod_models.ProductionAssignment.objects.filter(
            article=self,
            closed__isnull=True,
        ).update(
            closed=timezone.now(),
        )
        prod_models.TypesetTask.objects.filter(
            assignment__article=self,
            completed__isnull=True,
        ).update(
            completed=timezone.now(),
        )

        proof_models.ProofingAssignment.objects.filter(
            article=self,
            completed__isnull=True,
        ).update(
            completed=timezone.now(),
        )

        proof_models.ProofingTask.objects.filter(
            round__assignment__article=self,
            completed__isnull=True,
        ).update(
            cancelled=True,
        )
        proof_models.TypesetterProofingTask.objects.filter(
            proofing_task__round__assignment__article=self,
            completed__isnull=True,
        ).update(
            cancelled=True,
        )

    def production_assignment_or_none(self):
        try:
            return self.productionassignment
        except exceptions.ObjectDoesNotExist:
            return None

    @property
    def citation_count(self):
        article_link_count = self.articlelink_set.all().count()
        book_link_count = self.booklink_set.all().count()

        return article_link_count + book_link_count

    def hidden_completed_reviews(self):
        return self.reviewassignment_set.filter(
            is_complete=True,
            date_complete__isnull=False,
            for_author_consumption=False,
        ).exclude(
            decision="withdrawn",
        )

    def incomplete_reviews(self):
        return self.reviewassignment_set.filter(
            is_complete=False, date_declined__isnull=True, decision__isnull=True
        )

    def ms_and_figure_files(self):
        return chain(self.manuscript_files.all(), self.data_figure_files.all())

    def fast_last_modified_date(self):
        """A faster way of calculating an approximate last modified date
        While not as accurate as `best_last_modified_date` this calculation
        covers most of the relevant relations when determining when an article
        has been last modified. Depending on the numner of related nodes, this
        function can be about 6 times faster than `best_last_modified_date`
        """
        last_mod_date = self.last_modified

        try:
            latest = self.galley_set.latest("last_modified").last_modified
            if latest > last_mod_date:
                last_mod_date = latest
        except core_models.Galley.DoesNotExist:
            pass

        try:
            latest = self.frozenauthor_set.latest("last_modified").last_modified
            if latest > last_mod_date:
                last_mod_date = latest
        except FrozenAuthor.DoesNotExist:
            pass

        try:
            latest = (
                core_models.File.objects.filter(article_id=self.pk)
                .latest("last_modified")
                .last_modified
            )
            if latest > last_mod_date:
                last_mod_date = latest
        except core_models.File.DoesNotExist:
            pass

        try:
            latest = self.issues.latest("last_modified").last_modified
            if latest > last_mod_date:
                last_mod_date = latest
        except journal_models.Journal.DoesNotExist:
            pass

        return last_mod_date

    @cache(600)
    def pinned(self):
        if journal_models.PinnedArticle.objects.filter(
            journal=self.journal,
            article=self,
        ):
            return True

    def get_clean_abstract(self):
        """
        Returns a JATS-safe abstract with only allowed inline tags and wrapped in <p>.
        """
        if not self.abstract:
            return ""
        return transform_utils.convert_html_abstract_to_jats(self.abstract)

    @property
    def iso639_1_lang_code(self):
        """Return the ISO 639-1 two-letter code for use in xml:lang."""
        if not self.language:
            return "en"

        lang = Lang(self.language)
        return lang.pt1 or "en"


class FrozenAuthorQueryset(model_utils.AffiliationCompatibleQueryset):
    AFFILIATION_RELATED_NAME = "frozen_author"


class FrozenAuthor(AbstractLastModifiedModel):
    """
    The main record of authorship in Janeway.
    Historically it was a shadow copy of some Account fields,
    with Account objects in Article.authors, but FrozenAuthor has
    since superseded Article.authors.
    """

    article = models.ForeignKey(
        "submission.Article",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        "core.Account",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    name_prefix = models.CharField(
        max_length=300,
        blank=True,
        help_text=_("Optional name prefix (e.g: Prof or Dr)"),
        validators=[plain_text_validator],
    )
    name_suffix = models.CharField(
        max_length=300,
        blank=True,
        help_text=_("Optional name suffix (e.g.: Jr or III)"),
        validators=[plain_text_validator],
    )
    first_name = models.CharField(
        max_length=300,
        blank=True,
        validators=[plain_text_validator],
    )
    middle_name = models.CharField(
        max_length=300,
        blank=True,
        validators=[plain_text_validator],
    )
    last_name = models.CharField(
        max_length=300,
        blank=True,
        validators=[plain_text_validator],
    )

    frozen_biography = JanewayBleachField(
        blank=True,
        verbose_name=_("Biography"),
    )
    order = models.PositiveIntegerField(default=1)

    is_corporate = models.BooleanField(
        default=False,
        help_text="Whether the author is an organization. "
        "The display name will be formed from the affiliation.",
    )
    frozen_email = models.EmailField(
        blank=True,
        verbose_name=_("Email"),
    )
    frozen_orcid = models.CharField(
        max_length=40,
        blank=True,
        validators=[validate_orcid],
        verbose_name=_("ORCID"),
        help_text=_(
            "ORCID to be displayed when no account is associated with this author."
        ),
    )
    display_email = models.BooleanField(
        default=False,
        help_text=_(
            "Whether to display this author's email address on the published article."
        ),
    )

    objects = FrozenAuthorQueryset.as_manager()

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"
        ordering = ("order", "pk")

    def __str__(self):
        return self.full_name()

    @property
    def owner(self):
        if self.author:
            return self.author
        elif self.article:
            return self.article.owner
        else:
            return None

    def can_edit(self, user):
        """
        Determines whether a user can edit the author record.
        They can if:
          - they are staff of the press, or
          - they are a section editor on the article's section, or
          - they are an editor of the journal, or
          - they are the author and the article is unsubmitted, or
          - they are the owner of the article,
            the author record has no associated account,
            and the article is unsubmitted.
        """

        if user.is_staff:
            return True
        elif self.article:
            if user in self.article.section_editors():
                return True
            elif not user.is_anonymous and user.is_editor(
                request=None,
                journal=self.article.journal,
            ):
                return True
            elif self.owner == user and self.article.is_unsubmitted():
                # FrozenAuthor.owner is a property that considers both
                # FrozenAuthor.author and FrozenAuthor.article.owner.
                return True
        return False

    def associate_with_account(self):
        if self.frozen_email:
            try:
                # Associate with account if one exists
                account = core_models.Account.objects.get(
                    username=self.frozen_email.lower()
                )
                self.author = account
                self.frozen_email = ""  # linked account, don't store this value
            except core_models.Account.DoesNotExist:
                pass

    @property
    def institution(self):
        affil = self.primary_affiliation()
        return str(affil.organization) if affil else ""

    @institution.setter
    def institution(self, value):
        core_models.ControlledAffiliation.get_or_create_without_ror(
            institution=value, frozen_author=self
        )

    @property
    def department(self):
        affil = self.primary_affiliation()
        return str(affil.department) if affil else ""

    @department.setter
    def department(self, value):
        core_models.ControlledAffiliation.get_or_create_without_ror(
            department=value,
            frozen_author=self,
        )

    @property
    def country(self):
        affil = self.primary_affiliation()
        organization = affil.organization if affil else None
        return organization.country if organization else None

    @country.setter
    def country(self, value):
        core_models.ControlledAffiliation.get_or_create_without_ror(
            country=value,
            frozen_author=self,
        )

    @property
    def credits(self):
        """
        Returns all the credit records for this frozen author
        """
        return self.creditrecord_set.all()

    def add_credit(self, credit_role_text):
        """
        Adds a credit role to the article for this frozen author
        """
        record, _ = CreditRecord.objects.get_or_create(
            frozen_author=self,
            role=credit_role_text,
        )

        return record

    def remove_credit(self, credit_role_text):
        """
        Removes a credit role from the article for this frozen author
        """
        try:
            record = CreditRecord.objects.get(
                frozen_author=self,
                role=credit_role_text,
            )
            record.delete()
            return record
        except CreditRecord.DoesNotExist:
            pass

    def full_name(self):
        if self.is_corporate:
            return self.corporate_name
        name_elements = [
            self.name_prefix,
            self.first_name,
            self.middle_name,
            self.last_name,
            self.name_suffix,
        ]
        return " ".join([each for each in name_elements if each])

    @property
    def dc_name_string(self):
        name_string = ""

        if self.is_corporate:
            return self.corporate_name

        if self.last_name:
            name_string += "{}{}{} ".format(
                self.last_name,
                " {}".format(self.name_suffix) if self.name_suffix else "",
                "," if self.first_name else "",
            )
        if self.first_name:
            name_string += "{}".format(self.first_name)
        if self.middle_name:
            name_string += " {}".format(self.middle_name)

        return name_string

    @property
    def email(self):
        if self.frozen_email:
            return self.frozen_email
        elif self.author:
            return self.author.email
        return None

    @property
    def real_email(self):
        if self.email and not self.email.endswith(settings.DUMMY_EMAIL_DOMAIN):
            return self.email
        else:
            return ""

    @property
    def orcid(self):
        if self.frozen_orcid:
            return self.frozen_orcid
        elif self.author:
            return self.author.orcid
        return None

    @property
    def orcid_uri(self):
        if not self.orcid:
            return ""
        result = COMPILED_ORCID_REGEX.search(self.orcid)
        if result:
            return f"https://orcid.org/{result.group(0)}"
        else:
            return ""

    @property
    def corporate_name(self):
        return self.primary_affiliation(as_object=False)

    @property
    def biography(self):
        if self.frozen_biography:
            return self.frozen_biography
        elif self.author:
            return self.author.biography
        return None

    def citation_name(self):
        if self.is_corporate:
            return self.corporate_name
        first_initial, middle_initial = "", ""

        if self.middle_name:
            middle_initial = " {0}.".format(self.middle_name[:1])
        if self.first_name:
            first_initial = "{0}.".format(self.first_name[:1])

        citation = "{last}, {first}{middle}".format(
            last=self.last_name, first=first_initial, middle=middle_initial
        )
        if self.name_suffix:
            citation = "{}, {}".format(citation, self.name_suffix)
        return citation

    def given_names(self):
        if self.middle_name:
            return "{first_name} {middle_name}".format(
                first_name=self.first_name, middle_name=self.middle_name
            )
        else:
            return self.first_name

    def affiliation(self):
        """
        Use `primary_affiliation` or `affiliations` instead.

        For backwards compatibility, this is a method.
        Different from repository.models.Preprint.affiliation,
        which is a property.
        :rtype: str
        """
        return self.primary_affiliation(as_object=False)

    def primary_affiliation(self, as_object=True):
        return core_models.ControlledAffiliation.get_primary(
            affiliated_object=self,
            as_object=as_object,
        )

    @property
    def affiliations(self):
        return core_models.ControlledAffiliation.objects.filter(
            frozen_author=self,
        )

    @property
    def is_correspondence_author(self):
        # early return if no email address available
        if not self.author or not self.real_email:
            return False
        elif self.article.journal.enable_correspondence_authors is True:
            corr_author = self.article.correspondence_author
            return corr_author and corr_author == self.author
        else:
            return True

    @classmethod
    def get_or_snapshot_if_email_found(cls, email, article):
        """
        Gets or creates a FrozenAuthor from an account
        with a particular email.
        """
        created = False
        try:
            author = cls.objects.get(
                models.Q(article=article)
                & (
                    models.Q(frozen_email=email)
                    | models.Q(author__username__iexact=email)
                )
            )
        except cls.DoesNotExist:
            try:
                account = core_models.Account.objects.get(email=email)
                author = account.snapshot_as_author(article)
                created = True
            except core_models.Account.DoesNotExist:
                author = None

        return author, created

    @classmethod
    def get_or_snapshot_if_orcid_found(cls, orcid, article):
        """
        Gets or creates a FrozenAuthor from an account
        with a particular orcid.
        Assumes orcid is cleaned to 16-digit ID, not the URI form.
        """
        created = False
        try:
            author = cls.objects.get(
                models.Q(article=article)
                & (
                    models.Q(frozen_orcid=orcid)
                    | models.Q(author__orcid__contains=orcid)
                )
            )
        except cls.DoesNotExist:
            try:
                account = core_models.Account.objects.get(
                    orcid__contains=orcid,
                )
                author = account.snapshot_as_author(article)
            except core_models.Account.DoesNotExist:
                author = None

        return author, created


class CreditRecord(AbstractLastModifiedModel):
    """Represents a CRediT record for an article"""

    class Meta:
        verbose_name = "CRediT record"
        verbose_name_plural = "CRediT records"
        constraints = [
            model_utils.check_exclusive_fields_constraint(
                "credit_record",
                ["frozen_author", "preprint_author"],
            )
        ]
        unique_together = [["frozen_author", "role"]]
        ordering = ["role"]

    frozen_author = models.ForeignKey(
        FrozenAuthor, blank=True, null=True, on_delete=models.CASCADE
    )
    preprint_author = models.ForeignKey(
        repository_models.PreprintAuthor,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    role = models.CharField(
        max_length=100,
        choices=CREDIT_ROLE_CHOICES,
        default="writing-original-draft",
    )

    def __str__(self):
        return self.get_role_display()

    @property
    def uri(self):
        return f"https://credit.niso.org/contributor-roles/{self.role}/"

    @staticmethod
    def all_roles(self):
        return CREDIT_ROLE_CHOICES


class Section(AbstractLastModifiedModel):
    journal = models.ForeignKey(
        "journal.Journal",
        on_delete=models.CASCADE,
    )
    number_of_reviewers = models.IntegerField(default=2)

    editors = models.ManyToManyField(
        "core.Account",
        help_text="Editors assigned will be notified of submissions,"
        " overruling the notification settings for the journal.",
    )
    section_editors = models.ManyToManyField(
        "core.Account",
        help_text="Section editors assigned will be notified of submissions,"
        " overruling the notification settings for the journal.",
        related_name="section_editors",
    )
    jats_article_type = DynamicChoiceField(
        max_length=255,
        dynamic_choices=get_jats_article_types(),
        choices=tuple(),
        blank=True,
        null=True,
        verbose_name="JATS default article type",
        help_text="The default JATS article type for articles in this section. This can be overridden on a per-article basis.",
    )
    auto_assign_editors = models.BooleanField(
        default=False,
        help_text="Articles submitted to this section will be automatically"
        " assigned to the editors and/or section editors selected above.",
    )
    is_filterable = models.BooleanField(
        default=True,
        help_text="Allows filtering article search results by this section.",
    )
    public_submissions = models.BooleanField(default=True)
    indexing = models.BooleanField(
        default=True, help_text="Whether this section is put forward for indexing"
    )
    sequence = models.PositiveIntegerField(
        default=0,
        help_text="Determines the order in which the section is rendered"
        " Sections can also be reorder by drag-and-drop",
    )
    name = models.CharField(
        max_length=200,
        null=True,
    )
    plural = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Pluralised name for the section (e.g: Article -> Articles)",
    )

    objects = model_utils.JanewayMultilingualManager()

    class Meta:
        ordering = ("sequence",)

    def __str__(self):
        if self.name:
            return self.name
        return f"Unnamed Section {self.pk}"

    def display_name_public_submission(self):
        """
        Returns a display name that informs the user if the section is
        close for submission.
        """
        name = f"Unnamed Section {self.pk}"
        if self.name:
            name = self.name
        if not self.public_submissions:
            name = f"{name} (Public Submission Closed)"

        return name

    def published_articles(self):
        return Article.objects.filter(section=self, stage=STAGE_PUBLISHED)

    def article_count(self):
        return Article.objects.filter(section=self).count()

    def editor_emails(self):
        return [editor.email for editor in self.editors.all()]

    def section_editor_emails(self):
        return [editor.email for editor in self.section_editors.all()]

    def all_editor_emails(self):
        return [
            editor.email for editor in self.section_editors.all() + self.editors.all()
        ]

    def issue_display(self):
        if self.plural:
            return self.plural
        return self.name


class Licence(AbstractLastModifiedModel):
    journal = models.ForeignKey(
        "journal.Journal", null=True, blank=True, on_delete=models.SET_NULL
    )
    press = models.ForeignKey(
        "press.Press", null=True, blank=True, on_delete=models.SET_NULL
    )

    name = models.CharField(max_length=300)
    short_name = models.CharField(max_length=15)
    url = models.URLField(max_length=1000)
    text = JanewayBleachField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    available_for_submission = models.BooleanField(default=True)

    class Meta:
        ordering = ("order", "name")

    def __str__(self):
        return "{short_name}".format(short_name=self.short_name)

    def object(self):
        if not self.journal:
            return self.press

        return self.journal


class Note(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
    )
    creator = models.ForeignKey(
        "core.Account",
        null=True,
        on_delete=models.SET_NULL,
    )
    text = JanewayBleachField()
    date_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-date_time",)


def field_kind_choices():
    return (
        ("text", "Text Field"),
        ("textarea", "Text Area"),
        ("check", "Check Box"),
        ("select", "Select"),
        ("email", "Email"),
        ("date", "Date"),
    )


def width_choices():
    return (
        ("third", "Third"),
        ("half", "Half"),
        ("full,", "Full"),
    )


class Field(models.Model):
    journal = models.ForeignKey(
        "journal.Journal",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    press = models.ForeignKey(
        "press.Press",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=50, choices=field_kind_choices())
    width = models.CharField(max_length=50, choices=width_choices(), default="full")
    choices = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Separate choices with the bar | character.",
    )
    required = models.BooleanField(default=True)
    order = models.IntegerField()
    display = models.BooleanField(
        default=False, help_text="Whether or not display this field in the article page"
    )
    help_text = models.TextField()

    class Meta:
        ordering = ("order", "name")

    def __str__(self):
        return "Field: {0} ({1})".format(self.name, self.kind)

    @property
    def object(self):
        if not self.journal:
            return self.press

        return self.journal


class FieldAnswer(models.Model):
    field = models.ForeignKey(Field, null=True, blank=True, on_delete=models.SET_NULL)
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
    )
    answer = JanewayBleachField()


class ArticleAuthorOrder(models.Model):
    """
    Deprecated. Use FrozenAuthor instead.
    """

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        "core.Account",
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order",)


class SubmissionConfiguration(models.Model):
    journal = models.OneToOneField(
        "journal.Journal",
        on_delete=models.CASCADE,
    )

    publication_fees = models.BooleanField(default=True)
    submission_check = models.BooleanField(default=True)
    copyright_notice = models.BooleanField(default=True)
    competing_interests = models.BooleanField(default=True)
    comments_to_the_editor = models.BooleanField(default=True)

    subtitle = models.BooleanField(default=False)
    abstract = models.BooleanField(default=True)
    language = models.BooleanField(default=True)
    license = models.BooleanField(default=True)
    keywords = models.BooleanField(default=True)
    section = models.BooleanField(default=True)
    funding = models.BooleanField(default=False)

    figures_data = models.BooleanField(
        default=True,
        verbose_name=_("Figures and Data Files"),
    )

    default_license = models.ForeignKey(
        Licence,
        null=True,
        blank=True,
        help_text=_("The default license applied when no option is presented"),
        on_delete=models.SET_NULL,
    )
    default_language = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        choices=LANGUAGE_CHOICES,
        help_text=_("The default language of articles when lang is hidden"),
    )
    default_section = models.ForeignKey(
        Section,
        null=True,
        blank=True,
        help_text=_("The default section of articles when no option is presented"),
        on_delete=models.SET_NULL,
    )
    submission_file_text = models.CharField(
        max_length=255,
        default="Manuscript File",
        help_text="During submission the author will be asked to upload a file"
        "that is considered the main text of the article. You can use"
        "this field to change the label for that file in submission.",
    )

    def __str__(self):
        return "SubmissionConfiguration for {0}".format(self.journal.name)

    def lang_section_license_width(self):
        if self.language and self.license:
            return "4"
        elif not self.language and not self.license:
            return "12"
        elif not self.language and self.license:
            return "6"
        elif self.language and not self.license:
            return "6"

    def handle_defaults(self, article):
        if not self.section and self.default_section:
            article.section = self.default_section

        if not self.language and self.default_language:
            article.language = self.default_language

        if not self.license and self.default_license:
            article.license = self.default_license

        article.save()


# Signals


@receiver(pre_delete, sender=FrozenAuthor)
def remove_author_from_article(sender, instance, **kwargs):
    """
    This signal will remove an author from a paper if the user deletes the
    frozen author record to ensure they are in sync.
    :param sender: FrozenAuthor class
    :param instance: FrozenAuthor instance
    :return: None
    """
    if (not instance.article.authors.exists()) and (
        not ArticleAuthorOrder.objects.filter(article=instance.article).exists()
    ):
        # Return early so long as deprecated models and fields are not being used.
        # This avoids triggering the deprecation warning in development.
        return
    raise DeprecationWarning("Authorship is now exclusively handled via FrozenAuthor.")
    try:
        ArticleAuthorOrder.objects.get(
            author=instance.author,
            article=instance.article,
        ).delete()
    except ArticleAuthorOrder.MultipleObjectsReturned:
        # the same account could be linked to the paper twice if the account
        # is linked to multiple FrozenAuthor records.
        ArticleAuthorOrder.objects.filter(
            author=instance.author,
            article=instance.article,
        ).first().delete()
    except ArticleAuthorOrder.DoesNotExist:
        pass

    instance.article.authors.remove(instance.author)


def order_keywords(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == "post_add":
        try:
            latest = (
                KeywordArticle.objects.filter(article=instance).latest("order").order
            )
        except KeywordArticle.DoesNotExist:
            latest = 0
        for pk in pk_set:
            latest += 1
            keyword_article = KeywordArticle.objects.get(
                keyword__pk=pk, article=instance
            )
            if keyword_article.order == 1 != latest:
                keyword_article.order = latest
                keyword_article.save()


m2m_changed.connect(order_keywords, sender=Article.keywords.through)


def backwards_compat_authors(
    sender, instance, action, reverse, model, pk_set, **kwargs
):
    """A signal to make the Article.authors backwards compatible
    As part of #4755, the dependency of Article on Account for author linking
    was removed. This signal is a backwards compatibility measure to ensure
    FrozenAuthor records are being updated correctly.
    """
    accounts = core_models.Account.objects.filter(pk__in=pk_set)
    if action == "post_add":
        subq = models.Subquery(
            ArticleAuthorOrder.objects.filter(
                article=instance, author__id=models.OuterRef("id")
            ).values_list("order")
        )
        accounts = accounts.annotate(order=subq).order_by("order")
        for account in accounts:
            account.snapshot_as_author(instance)
    if action in ["post_remove", "post_clear"]:
        instance.frozen_authors.filter(author__in=pk_set).delete()


m2m_changed.connect(backwards_compat_authors, sender=Article.authors.through)

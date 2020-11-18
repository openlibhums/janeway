__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from bs4 import BeautifulSoup
from urllib.parse import urlparse
import uuid
import os
from dateutil import parser as dateparser

from django.urls import reverse
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from hvad.models import TranslatableModel, TranslatedFields
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core import exceptions
from django.utils.html import mark_safe

from core.file_system import JanewayFileSystemStorage
from core import workflow
from identifiers import logic as id_logic
from metrics.logic import ArticleMetrics
from preprint import models as preprint_models
from review import models as review_models
from utils.function_cache import cache
from utils.logger import get_logger

logger = get_logger(__name__)

fs = JanewayFileSystemStorage()


def article_media_upload(instance, filename):
    try:
        filename = str(uuid.uuid4()) + '.' + str(filename.split('.')[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "articles/{0}/".format(instance.pk)
    return os.path.join(path, filename)


SALUTATION_CHOICES = [
    ('', '---'),
    ('Dr', 'Dr'),
    ('Prof', 'Prof'),
    ('Miss', 'Miss'),
    ('Ms', 'Ms'),
    ('Mrs', 'Mrs'),
    ('Mr', 'Mr'),
]

LANGUAGE_CHOICES = (
    (u'eng', u'English'), (u'abk', u'Abkhazian'), (u'ace', u'Achinese'), (u'ach', u'Acoli'), (u'ada', u'Adangme'),
    (u'ady', u'Adyghe; Adygei'), (u'aar', u'Afar'), (u'afh', u'Afrihili'), (u'afr', u'Afrikaans'),
    (u'afa', u'Afro-Asiatic languages'), (u'ain', u'Ainu'), (u'aka', u'Akan'), (u'akk', u'Akkadian'),
    (u'sqi', u'Albanian'),
    (u'ale', u'Aleut'), (u'alg', u'Algonquian languages'), (u'tut', u'Altaic languages'), (u'amh', u'Amharic'),
    (u'anp', u'Angika'), (u'apa', u'Apache languages'), (u'ara', u'Arabic'), (u'arg', u'Aragonese'),
    (u'arp', u'Arapaho'),
    (u'arw', u'Arawak'), (u'hye', u'Armenian'), (u'rup', u'Aromanian; Arumanian; Macedo-Romanian'),
    (u'art', u'Artificial languages'), (u'asm', u'Assamese'), (u'ast', u'Asturian; Bable; Leonese; Asturleonese'),
    (u'ath', u'Athapascan languages'), (u'aus', u'Australian languages'), (u'map', u'Austronesian languages'),
    (u'ava', u'Avaric'), (u'ave', u'Avestan'), (u'awa', u'Awadhi'), (u'aym', u'Aymara'), (u'aze', u'Azerbaijani'),
    (u'ban', u'Balinese'), (u'bat', u'Baltic languages'), (u'bal', u'Baluchi'), (u'bam', u'Bambara'),
    (u'bai', u'Bamileke languages'), (u'bad', u'Banda languages'), (u'bnt', u'Bantu languages'), (u'bas', u'Basa'),
    (u'bak', u'Bashkir'), (u'eus', u'Basque'), (u'btk', u'Batak languages'), (u'bej', u'Beja; Bedawiyet'),
    (u'bel', u'Belarusian'), (u'bem', u'Bemba'), (u'ben', u'Bengali'), (u'ber', u'Berber languages'),
    (u'bho', u'Bhojpuri'),
    (u'bih', u'Bihari languages'), (u'bik', u'Bikol'), (u'bin', u'Bini; Edo'), (u'bis', u'Bislama'),
    (u'byn', u'Blin; Bilin'), (u'zbl', u'Blissymbols; Blissymbolics; Bliss'),
    (u'nob', u'Bokm\xe5l, Norwegian; Norwegian Bokm\xe5l'), (u'bos', u'Bosnian'), (u'bra', u'Braj'),
    (u'bre', u'Breton'),
    (u'bug', u'Buginese'), (u'bul', u'Bulgarian'), (u'bua', u'Buriat'), (u'mya', u'Burmese'), (u'cad', u'Caddo'),
    (u'cat', u'Catalan; Valencian'), (u'cau', u'Caucasian languages'), (u'ceb', u'Cebuano'),
    (u'cel', u'Celtic languages'),
    (u'cai', u'Central American Indian languages'), (u'khm', u'Central Khmer'), (u'chg', u'Chagatai'),
    (u'cmc', u'Chamic languages'), (u'cha', u'Chamorro'), (u'che', u'Chechen'), (u'chr', u'Cherokee'),
    (u'chy', u'Cheyenne'), (u'chb', u'Chibcha'), (u'nya', u'Chichewa; Chewa; Nyanja'), (u'zho', u'Chinese'),
    (u'chn', u'Chinook jargon'), (u'chp', u'Chipewyan; Dene Suline'), (u'cho', u'Choctaw'),
    (u'chu', u'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic'),
    (u'chk', u'Chuukese'),
    (u'chv', u'Chuvash'), (u'nwc', u'Classical Newari; Old Newari; Classical Nepal Bhasa'),
    (u'syc', u'Classical Syriac'),
    (u'cop', u'Coptic'), (u'cor', u'Cornish'), (u'cos', u'Corsican'), (u'cre', u'Cree'), (u'mus', u'Creek'),
    (u'crp', u'Creoles and pidgins'), (u'cpe', u'Creoles and pidgins, English based'),
    (u'cpf', u'Creoles and pidgins, French-based'), (u'cpp', u'Creoles and pidgins, Portuguese-based'),
    (u'crh', u'Crimean Tatar; Crimean Turkish'), (u'hrv', u'Croatian'), (u'cus', u'Cushitic languages'),
    (u'ces', u'Czech'),
    (u'dak', u'Dakota'), (u'dan', u'Danish'), (u'dar', u'Dargwa'), (u'del', u'Delaware'), (u'din', u'Dinka'),
    (u'div', u'Divehi; Dhivehi; Maldivian'), (u'doi', u'Dogri'), (u'dgr', u'Dogrib'), (u'dra', u'Dravidian languages'),
    (u'dua', u'Duala'), (u'dum', u'Dutch, Middle (ca. 1050-1350)'), (u'nld', u'Dutch; Flemish'), (u'dyu', u'Dyula'),
    (u'dzo', u'Dzongkha'), (u'frs', u'Eastern Frisian'), (u'efi', u'Efik'), (u'egy', u'Egyptian (Ancient)'),
    (u'eka', u'Ekajuk'), (u'elx', u'Elamite'), (u'enm', u'English, Middle (1100-1500)'),
    (u'ang', u'English, Old (ca. 450-1100)'), (u'myv', u'Erzya'), (u'epo', u'Esperanto'), (u'est', u'Estonian'),
    (u'ewe', u'Ewe'), (u'ewo', u'Ewondo'), (u'fan', u'Fang'), (u'fat', u'Fanti'), (u'fao', u'Faroese'),
    (u'fij', u'Fijian'),
    (u'fil', u'Filipino; Pilipino'), (u'fin', u'Finnish'), (u'fiu', u'Finno-Ugrian languages'), (u'fon', u'Fon'),
    (u'fra', u'French'), (u'frm', u'French, Middle (ca. 1400-1600)'), (u'fro', u'French, Old (842-ca. 1400)'),
    (u'fur', u'Friulian'), (u'ful', u'Fulah'), (u'gaa', u'Ga'), (u'gla', u'Gaelic; Scottish Gaelic'),
    (u'car', u'Galibi Carib'), (u'glg', u'Galician'), (u'lug', u'Ganda'), (u'gay', u'Gayo'), (u'gba', u'Gbaya'),
    (u'gez', u'Geez'), (u'kat', u'Georgian'), (u'deu', u'German'), (u'gmh', u'German, Middle High (ca. 1050-1500)'),
    (u'goh', u'German, Old High (ca. 750-1050)'), (u'gem', u'Germanic languages'), (u'gil', u'Gilbertese'),
    (u'gon', u'Gondi'), (u'gor', u'Gorontalo'), (u'got', u'Gothic'), (u'grb', u'Grebo'),
    (u'grc', u'Greek, Ancient (to 1453)'), (u'ell', u'Greek, Modern (1453-)'), (u'grn', u'Guarani'),
    (u'guj', u'Gujarati'),
    (u'gwi', u"Gwich'in"), (u'hai', u'Haida'), (u'hat', u'Haitian; Haitian Creole'), (u'hau', u'Hausa'),
    (u'haw', u'Hawaiian'), (u'heb', u'Hebrew'), (u'her', u'Herero'), (u'hil', u'Hiligaynon'),
    (u'him', u'Himachali languages; Western Pahari languages'), (u'hin', u'Hindi'), (u'hmo', u'Hiri Motu'),
    (u'hit', u'Hittite'), (u'hmn', u'Hmong; Mong'), (u'hun', u'Hungarian'), (u'hup', u'Hupa'), (u'iba', u'Iban'),
    (u'isl', u'Icelandic'), (u'ido', u'Ido'), (u'ibo', u'Igbo'), (u'ijo', u'Ijo languages'), (u'ilo', u'Iloko'),
    (u'smn', u'Inari Sami'), (u'inc', u'Indic languages'), (u'ine', u'Indo-European languages'),
    (u'ind', u'Indonesian'),
    (u'inh', u'Ingush'), (u'ina', u'Interlingua (International Auxiliary Language Association)'),
    (u'ile', u'Interlingue; Occidental'), (u'iku', u'Inuktitut'), (u'ipk', u'Inupiaq'), (u'ira', u'Iranian languages'),
    (u'gle', u'Irish'), (u'mga', u'Irish, Middle (900-1200)'), (u'sga', u'Irish, Old (to 900)'),
    (u'iro', u'Iroquoian languages'), (u'ita', u'Italian'), (u'jpn', u'Japanese'), (u'jav', u'Javanese'),
    (u'jrb', u'Judeo-Arabic'), (u'jpr', u'Judeo-Persian'), (u'kbd', u'Kabardian'), (u'kab', u'Kabyle'),
    (u'kac', u'Kachin; Jingpho'), (u'kal', u'Kalaallisut; Greenlandic'), (u'xal', u'Kalmyk; Oirat'), (u'kam', u'Kamba'),
    (u'kan', u'Kannada'), (u'kau', u'Kanuri'), (u'kaa', u'Kara-Kalpak'), (u'krc', u'Karachay-Balkar'),
    (u'krl', u'Karelian'), (u'kar', u'Karen languages'), (u'kas', u'Kashmiri'), (u'csb', u'Kashubian'),
    (u'kaw', u'Kawi'),
    (u'kaz', u'Kazakh'), (u'kha', u'Khasi'), (u'khi', u'Khoisan languages'), (u'kho', u'Khotanese;Sakan'),
    (u'kik', u'Kikuyu; Gikuyu'), (u'kmb', u'Kimbundu'), (u'kin', u'Kinyarwanda'), (u'kir', u'Kirghiz; Kyrgyz'),
    (u'tlh', u'Klingon; tlhIngan-Hol'), (u'kom', u'Komi'), (u'kon', u'Kongo'), (u'kok', u'Konkani'),
    (u'kor', u'Korean'),
    (u'kos', u'Kosraean'), (u'kpe', u'Kpelle'), (u'kro', u'Kru languages'), (u'kua', u'Kuanyama; Kwanyama'),
    (u'kum', u'Kumyk'), (u'kur', u'Kurdish'), (u'kru', u'Kurukh'), (u'kut', u'Kutenai'), (u'lad', u'Ladino'),
    (u'lah', u'Lahnda'), (u'lam', u'Lamba'), (u'day', u'Land Dayak languages'), (u'lao', u'Lao'), (u'lat', u'Latin'),
    (u'lav', u'Latvian'), (u'lez', u'Lezghian'), (u'lim', u'Limburgan; Limburger; Limburgish'), (u'lin', u'Lingala'),
    (u'lit', u'Lithuanian'), (u'jbo', u'Lojban'), (u'nds', u'Low German; Low Saxon; German, Low; Saxon, Low'),
    (u'dsb', u'Lower Sorbian'), (u'loz', u'Lozi'), (u'lub', u'Luba-Katanga'), (u'lua', u'Luba-Lulua'),
    (u'lui', u'Luiseno'),
    (u'smj', u'Lule Sami'), (u'lun', u'Lunda'), (u'luo', u'Luo (Kenya and Tanzania)'), (u'lus', u'Lushai'),
    (u'ltz', u'Luxembourgish; Letzeburgesch'), (u'mkd', u'Macedonian'), (u'mad', u'Madurese'), (u'mag', u'Magahi'),
    (u'mai', u'Maithili'), (u'mak', u'Makasar'), (u'mlg', u'Malagasy'), (u'msa', u'Malay'), (u'mal', u'Malayalam'),
    (u'mlt', u'Maltese'), (u'mnc', u'Manchu'), (u'mdr', u'Mandar'), (u'man', u'Mandingo'), (u'mni', u'Manipuri'),
    (u'mno', u'Manobo languages'), (u'glv', u'Manx'), (u'mri', u'Maori'), (u'arn', u'Mapudungun; Mapuche'),
    (u'mar', u'Marathi'), (u'chm', u'Mari'), (u'mah', u'Marshallese'), (u'mwr', u'Marwari'), (u'mas', u'Masai'),
    (u'myn', u'Mayan languages'), (u'men', u'Mende'), (u'mic', u"Mi'kmaq; Micmac"), (u'min', u'Minangkabau'),
    (u'mwl', u'Mirandese'), (u'moh', u'Mohawk'), (u'mdf', u'Moksha'), (u'mol', u'Moldavian; Moldovan'),
    (u'mkh', u'Mon-Khmer languages'), (u'lol', u'Mongo'), (u'mon', u'Mongolian'), (u'mos', u'Mossi'),
    (u'mul', u'Multiple languages'), (u'mun', u'Munda languages'), (u'nqo', u"N'Ko"), (u'nah', u'Nahuatl languages'),
    (u'nau', u'Nauru'), (u'nav', u'Navajo; Navaho'), (u'nde', u'Ndebele, North; North Ndebele'),
    (u'nbl', u'Ndebele, South; South Ndebele'), (u'ndo', u'Ndonga'), (u'nap', u'Neapolitan'),
    (u'new', u'Nepal Bhasa; Newari'), (u'nep', u'Nepali'), (u'nia', u'Nias'), (u'nic', u'Niger-Kordofanian languages'),
    (u'ssa', u'Nilo-Saharan languages'), (u'niu', u'Niuean'), (u'zxx', u'No linguistic content; Not applicable'),
    (u'nog', u'Nogai'), (u'non', u'Norse, Old'), (u'nai', u'North American Indian languages'),
    (u'frr', u'Northern Frisian'), (u'sme', u'Northern Sami'), (u'nor', u'Norwegian'),
    (u'nno', u'Norwegian Nynorsk; Nynorsk, Norwegian'), (u'nub', u'Nubian languages'), (u'nym', u'Nyamwezi'),
    (u'nyn', u'Nyankole'), (u'nyo', u'Nyoro'), (u'nzi', u'Nzima'), (u'oci', u'Occitan (post 1500)'),
    (u'arc', u'Official Aramaic (700-300 BCE); Imperial Aramaic (700-300 BCE)'), (u'oji', u'Ojibwa'),
    (u'ori', u'Oriya'),
    (u'orm', u'Oromo'), (u'osa', u'Osage'), (u'oss', u'Ossetian; Ossetic'), (u'oto', u'Otomian languages'),
    (u'pal', u'Pahlavi'), (u'pau', u'Palauan'), (u'pli', u'Pali'), (u'pam', u'Pampanga; Kapampangan'),
    (u'pag', u'Pangasinan'), (u'pan', u'Panjabi; Punjabi'), (u'pap', u'Papiamento'), (u'paa', u'Papuan languages'),
    (u'nso', u'Pedi; Sepedi; Northern Sotho'), (u'fas', u'Persian'), (u'peo', u'Persian, Old (ca. 600-400 B.C.)'),
    (u'phi', u'Philippine languages'), (u'phn', u'Phoenician'), (u'pon', u'Pohnpeian'), (u'pol', u'Polish'),
    (u'por', u'Portuguese'), (u'pra', u'Prakrit languages'),
    (u'pro', u'Proven\xe7al, Old (to 1500); Occitan, Old (to 1500)'), (u'pus', u'Pushto; Pashto'), (u'que', u'Quechua'),
    (u'raj', u'Rajasthani'), (u'rap', u'Rapanui'), (u'rar', u'Rarotongan; Cook Islands Maori'),
    (u'qaa-qtz', u'Reserved for local use'), (u'roa', u'Romance languages'), (u'ron', u'Romanian'),
    (u'roh', u'Romansh'),
    (u'rom', u'Romany'), (u'run', u'Rundi'), (u'rus', u'Russian'), (u'sal', u'Salishan languages'),
    (u'sam', u'Samaritan Aramaic'), (u'smi', u'Sami languages'), (u'smo', u'Samoan'), (u'sad', u'Sandawe'),
    (u'sag', u'Sango'), (u'san', u'Sanskrit'), (u'sat', u'Santali'), (u'srd', u'Sardinian'), (u'sas', u'Sasak'),
    (u'sco', u'Scots'), (u'sel', u'Selkup'), (u'sem', u'Semitic languages'), (u'srp', u'Serbian'), (u'srr', u'Serer'),
    (u'shn', u'Shan'), (u'sna', u'Shona'), (u'iii', u'Sichuan Yi; Nuosu'), (u'scn', u'Sicilian'), (u'sid', u'Sidamo'),
    (u'sgn', u'Sign Languages'), (u'bla', u'Siksika'), (u'snd', u'Sindhi'), (u'sin', u'Sinhala; Sinhalese'),
    (u'sit', u'Sino-Tibetan languages'), (u'sio', u'Siouan languages'), (u'sms', u'Skolt Sami'),
    (u'den', u'Slave (Athapascan)'), (u'sla', u'Slavic languages'), (u'slk', u'Slovak'), (u'slv', u'Slovenian'),
    (u'sog', u'Sogdian'), (u'som', u'Somali'), (u'son', u'Songhai languages'), (u'snk', u'Soninke'),
    (u'wen', u'Sorbian languages'), (u'sot', u'Sotho, Southern'), (u'sai', u'South American Indian languages'),
    (u'alt', u'Southern Altai'), (u'sma', u'Southern Sami'), (u'spa', u'Spanish; Castilian'), (u'srn', u'Sranan Tongo'),
    (u'zgh', u'Standard Moroccan Tamazight'), (u'suk', u'Sukuma'), (u'sux', u'Sumerian'), (u'sun', u'Sundanese'),
    (u'sus', u'Susu'), (u'swa', u'Swahili'), (u'ssw', u'Swati'), (u'swe', u'Swedish'),
    (u'gsw', u'Swiss German; Alemannic; Alsatian'), (u'syr', u'Syriac'), (u'tgl', u'Tagalog'), (u'tah', u'Tahitian'),
    (u'tai', u'Tai languages'), (u'tgk', u'Tajik'), (u'tmh', u'Tamashek'), (u'tam', u'Tamil'), (u'tat', u'Tatar'),
    (u'tel', u'Telugu'), (u'ter', u'Tereno'), (u'tet', u'Tetum'), (u'tha', u'Thai'), (u'bod', u'Tibetan'),
    (u'tig', u'Tigre'), (u'tir', u'Tigrinya'), (u'tem', u'Timne'), (u'tiv', u'Tiv'), (u'tli', u'Tlingit'),
    (u'tpi', u'Tok Pisin'), (u'tkl', u'Tokelau'), (u'tog', u'Tonga (Nyasa)'), (u'ton', u'Tonga (Tonga Islands)'),
    (u'tsi', u'Tsimshian'), (u'tso', u'Tsonga'), (u'tsn', u'Tswana'), (u'tum', u'Tumbuka'), (u'tup', u'Tupi languages'),
    (u'tur', u'Turkish'), (u'ota', u'Turkish, Ottoman (1500-1928)'), (u'tuk', u'Turkmen'), (u'tvl', u'Tuvalu'),
    (u'tyv', u'Tuvinian'), (u'twi', u'Twi'), (u'udm', u'Udmurt'), (u'uga', u'Ugaritic'), (u'uig', u'Uighur; Uyghur'),
    (u'ukr', u'Ukrainian'), (u'umb', u'Umbundu'), (u'mis', u'Uncoded languages'), (u'und', u'Undetermined'),
    (u'hsb', u'Upper Sorbian'), (u'urd', u'Urdu'), (u'uzb', u'Uzbek'), (u'vai', u'Vai'), (u'ven', u'Venda'),
    (u'vie', u'Vietnamese'), (u'vol', u'Volap\xfck'), (u'vot', u'Votic'), (u'wak', u'Wakashan languages'),
    (u'wln', u'Walloon'), (u'war', u'Waray'), (u'was', u'Washo'), (u'cym', u'Welsh'), (u'fry', u'Western Frisian'),
    (u'wal', u'Wolaitta; Wolaytta'), (u'wol', u'Wolof'), (u'xho', u'Xhosa'), (u'sah', u'Yakut'), (u'yao', u'Yao'),
    (u'yap', u'Yapese'), (u'yid', u'Yiddish'), (u'yor', u'Yoruba'), (u'ypk', u'Yupik languages'),
    (u'znd', u'Zande languages'), (u'zap', u'Zapotec'), (u'zza', u'Zaza; Dimili; Dimli; Kirdki; Kirmanjki; Zazaki'),
    (u'zen', u'Zenaga'), (u'zha', u'Zhuang; Chuang'), (u'zul', u'Zulu'), (u'zun', u'Zuni'))

STAGE_UNSUBMITTED = 'Unsubmitted'
STAGE_UNASSIGNED = 'Unassigned'
STAGE_ASSIGNED = 'Assigned'
STAGE_UNDER_REVIEW = 'Under Review'
STAGE_UNDER_REVISION = 'Under Revision'
STAGE_REJECTED = 'Rejected'
STAGE_ACCEPTED = 'Accepted'
STAGE_EDITOR_COPYEDITING = 'Editor Copyediting'
STAGE_AUTHOR_COPYEDITING = 'Author Copyediting'
STAGE_FINAL_COPYEDITING = 'Final Copyediting'
STAGE_TYPESETTING = 'Typesetting'
STAGE_PROOFING = 'Proofing'
STAGE_READY_FOR_PUBLICATION = 'pre_publication'
STAGE_PUBLISHED = 'Published'
STAGE_PREPRINT_REVIEW = 'preprint_review'
STAGE_PREPRINT_PUBLISHED = 'preprint_published'

FINAL_STAGES = {
    # An Article stage is final when it won't transition into further stages
    STAGE_PUBLISHED,
    STAGE_REJECTED,
}

REVIEW_STAGES = {
    STAGE_ASSIGNED,
    STAGE_UNDER_REVIEW,
    STAGE_UNDER_REVISION
}

COPYEDITING_STAGES = {
    STAGE_EDITOR_COPYEDITING,
    STAGE_AUTHOR_COPYEDITING,
    STAGE_FINAL_COPYEDITING,
}

PREPRINT_STAGES = {
    STAGE_PREPRINT_REVIEW,
    STAGE_PREPRINT_PUBLISHED
}

PUBLISHED_STAGES = {
    STAGE_PUBLISHED,
    STAGE_PREPRINT_PUBLISHED,
}

STAGE_CHOICES = [
    (STAGE_UNSUBMITTED, 'Unsubmitted'),
    (STAGE_UNASSIGNED, 'Unassigned'),
    (STAGE_ASSIGNED, 'Assigned to Editor'),
    (STAGE_UNDER_REVIEW, 'Peer Review'),
    (STAGE_UNDER_REVISION, 'Revision'),
    (STAGE_REJECTED, 'Rejected'),
    (STAGE_ACCEPTED, 'Accepted'),
    (STAGE_EDITOR_COPYEDITING, 'Editor Copyediting'),
    (STAGE_AUTHOR_COPYEDITING, 'Author Copyediting'),
    (STAGE_FINAL_COPYEDITING, 'Final Copyediting'),
    (STAGE_TYPESETTING, 'Typesetting'),
    (STAGE_PROOFING, 'Proofing'),
    (STAGE_READY_FOR_PUBLICATION, 'Pre Publication'),
    (STAGE_PUBLISHED, 'Published'),
    (STAGE_PREPRINT_REVIEW, 'Preprint Review'),
    (STAGE_PREPRINT_PUBLISHED, 'Preprint Published')
]

PLUGIN_WORKFLOW_STAGES = []


class Funder(models.Model):
    class Meta:
        ordering = ('name',)

    name = models.CharField(max_length=500, blank=False, null=False)
    fundref_id = models.CharField(max_length=500, blank=True, null=True)
    funding_id = models.CharField(max_length=500, blank=True, null=True)


class ArticleStageLog(models.Model):
    article = models.ForeignKey('Article')
    stage_from = models.CharField(max_length=200, blank=False, null=False)
    stage_to = models.CharField(max_length=200, blank=False, null=False)
    date_time = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('-date_time',)

    def __str__(self):
        return "Article {article_pk} from {stage_from} to {stage_to} at {date_time}".format(article_pk=self.article.pk,
                                                                                            stage_from=self.stage_from,
                                                                                            stage_to=self.stage_to,
                                                                                            date_time=self.date_time)


class PublisherNote(models.Model):
    text = models.TextField(max_length=4000, blank=False, null=False)
    sequence = models.PositiveIntegerField(default=999)
    creator = models.ForeignKey('core.Account', default=None)
    date_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('sequence',)

    def __str__(self):
        return "{0}: {1}".format(self.creator.full_name(), self.date_time)


class Keyword(models.Model):
    word = models.CharField(max_length=200)

    def __str__(self):
        return self.word


class AllArticleManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return super(AllArticleManager, self).get_queryset().all()


class ArticleManager(models.Manager):
    def get_queryset(self):
        return super(ArticleManager, self).get_queryset().filter(is_preprint=False)


class PreprintManager(models.Manager):
    def get_queryset(self):
        return super(PreprintManager, self).get_queryset().filter(is_preprint=True)


class DynamicChoiceField(models.CharField):
    def __init__(self, dynamic_choices=(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dynamic_choices = dynamic_choices

    def formfield(self, *args, **kwargs):
        form_element = super().formfield(**kwargs)
        for choice in self.dynamic_choices:
            form_element.choices.append(choice)
        return form_element

    def validate(self, value, model_instance):
        """
        Validates value and throws ValidationError.
        """
        try:
            super().validate(value, model_instance)
        except exceptions.ValidationError as e:
            # If the raised exception is for invalid choice we check if the
            # choice is in dynamic choices.
            if e.code == 'invalid_choice':
                potential_values = set(
                    item[0] for item in self.dynamic_choices
                )
                if value not in potential_values:
                    raise


class Article(models.Model):
    journal = models.ForeignKey('journal.Journal', blank=True, null=True)
    # Metadata
    owner = models.ForeignKey('core.Account', null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=999, help_text=_('Your article title'))
    subtitle = models.CharField(max_length=999, blank=True, null=True,
                                help_text=_('Subtitle of the article display format; Title: Subtitle'))
    abstract = models.TextField(
        blank=True,
        null=True,
        help_text=_('Please avoid pasting content from word processors as they can add '
                    'unwanted styling to the abstract. You can retype the abstract '
                    'here or copy and paste it into notepad/a plain text editor before '
                    'pasting here.')
    )
    non_specialist_summary = models.TextField(blank=True, null=True, help_text='A summary of the article for'
                                                                               ' non specialists.')
    keywords = models.ManyToManyField(Keyword, blank=True, null=True)
    language = models.CharField(max_length=200, blank=True, null=True, choices=LANGUAGE_CHOICES,
                                help_text=_('The primary language of the article'))
    section = models.ForeignKey('Section', blank=True, null=True, on_delete=models.SET_NULL)
    license = models.ForeignKey('Licence', blank=True, null=True, on_delete=models.SET_NULL)
    publisher_notes = models.ManyToManyField('PublisherNote', blank=True, null=True, related_name='publisher_notes')

    # Remote: a flag that specifies that this article is actually a _link_ to a remote instance
    # this is useful for overlay journals. The ToC display of an issue uses this flag to link to a DOI rather
    # than an internal URL
    is_remote = models.BooleanField(default=False, verbose_name="Remote article",
                                    help_text="Check if this article is remote")
    remote_url = models.URLField(blank=True, null=True, help_text="If the article is remote, its URL should be added.")

    # Author
    authors = models.ManyToManyField('core.Account', blank=True, null=True, related_name='authors')
    correspondence_author = models.ForeignKey('core.Account', related_name='correspondence_author', blank=True,
                                              null=True, on_delete=models.SET_NULL)

    competing_interests_bool = models.BooleanField(default=False)
    competing_interests = models.TextField(blank=True, null=True, help_text="If you have any conflict "
                                                                            "of interests in the publication of this "
                                                                            "article please state them here.")

    # Files
    manuscript_files = models.ManyToManyField('core.File', null=True, blank=True, related_name='manuscript_files')
    data_figure_files = models.ManyToManyField('core.File', null=True, blank=True, related_name='data_figure_files')
    supplementary_files = models.ManyToManyField('core.SupplementaryFile', null=True, blank=True, related_name='supp')
    source_files = models.ManyToManyField(
        'core.File',
        blank=True,
        related_name='source_files',
    )

    # Galley
    render_galley = models.ForeignKey('core.Galley', related_name='render_galley', blank=True, null=True,
                                      on_delete=models.SET_NULL)

    # Dates
    date_started = models.DateTimeField(auto_now_add=True)

    date_accepted = models.DateTimeField(blank=True, null=True)
    date_declined = models.DateTimeField(blank=True, null=True)
    date_submitted = models.DateTimeField(blank=True, null=True)
    date_published = models.DateTimeField(blank=True, null=True)
    date_updated = models.DateTimeField(blank=True, null=True)
    current_step = models.IntegerField(default=1)

    # Pages
    page_numbers = models.CharField(max_length=20, blank=True, null=True)

    # Stage
    stage = DynamicChoiceField(
        max_length=200,
        blank=True,
        null=False,
        default=STAGE_UNSUBMITTED,
        choices=STAGE_CHOICES,
        dynamic_choices=PLUGIN_WORKFLOW_STAGES,
    )

    # Agreements
    publication_fees = models.BooleanField(default=False)
    submission_requirements = models.BooleanField(default=False)
    copyright_notice = models.BooleanField(default=False)
    comments_editor = models.TextField(blank=True, null=True, verbose_name="Comments to the Editor",
                                       help_text="Add any comments you'd like the editor to consider here.")

    # an image of recommended size: 750 x 324
    large_image_file = models.ForeignKey('core.File', null=True, blank=True, related_name='image_file',
                                         on_delete=models.SET_NULL)
    exclude_from_slider = models.BooleanField(default=False)

    thumbnail_image_file = models.ForeignKey('core.File', null=True, blank=True, related_name='thumbnail_file',
                                             on_delete=models.SET_NULL)

    # Whether or not we should display that this article has been "peer reviewed"
    peer_reviewed = models.BooleanField(default=True)

    # Whether or not this article was imported ie. not processed by this platform
    is_import = models.BooleanField(default=False)

    metric_stats = None

    # Agreement, this field records the submission checklist that was present when this article was submitted.
    article_agreement = models.TextField(default='')

    custom_how_to_cite = models.TextField(
        blank=True, null=True,
        help_text="Custom 'how to cite' text. To be used only if the block"
            " generated by Janeway is not suitable.",
    )

    # iThenticate ID
    ithenticate_id = models.TextField(blank=True, null=True)
    ithenticate_score = models.IntegerField(blank=True, null=True)

    # Primary issue, allows the Editor to set the Submission's primary Issue
    primary_issue = models.ForeignKey(
        'journal.Issue',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='You can only assign an Issue that this Article is part of.'
                  'You can add this article to and Issue from the Issue Manager.'
    )
    projected_issue = models.ForeignKey(
        'journal.Issue',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='projected_issue',
    )

    # Meta
    meta_image = models.ImageField(blank=True, null=True, upload_to=article_media_upload, storage=fs)

    is_preprint = models.BooleanField(default=False)
    preprint_decision_notification = models.BooleanField(default=False)
    preprint_journal_article = models.ForeignKey('submission.Article', blank=True, null=True)

    allarticles = AllArticleManager()
    objects = ArticleManager()
    preprints = PreprintManager()

    # funding
    funders = models.ManyToManyField('Funder', blank=True)

    class Meta:
        ordering = ('-date_published', 'title')

    @property
    def how_to_cite(self):
        if self.custom_how_to_cite:
            return self.custom_how_to_cite

        template = "common/elements/how_to_cite.html"
        authors = self.frozenauthor_set.all()
        author_str = " & ".join(a.citation_name() for a in authors)
        year_str = ""
        if self.date_published:
            year_str = "({:%Y})".format(self.date_published)
        journal_str = "<i>%s</i>" % self.journal.name
        issue_str = ""
        issue = self.issue
        if self.issue:
            issue_str = "%s(%s)" % (issue.volume, issue.issue)
        doi_str = ""
        doi = self.get_doi()
        if doi:
            doi_str = ('doi: <a href="https://doi.org/{0}">'
            'https://doi.org/{0}</a>'.format(doi))

        context = {
            "author_str": author_str,
            "year_str": year_str,
            "title": mark_safe(self.title),
            "journal_str": journal_str,
            "issue_str": issue_str,
            "doi_str": doi_str,
        }
        return render_to_string(template, context)

    @property
    def metrics(self):
        # only do the metric calculation once per template call
        if not self.metric_stats:
            self.metric_stats = ArticleMetrics(self)
        return self.metric_stats

    @property
    def has_galley(self):
        return self.galley_set.all().exists()

    def journal_sections(self):
        return ((section.id, section.name) for section in self.journal.section_set.all())

    @property
    def carousel_subtitle(self):
        carousel_text = ""

        idx = 0

        for author in self.frozenauthor_set.all():
            if idx > 0:
                idx = 1
                carousel_text += ', '

            if author.institution != '':
                carousel_text += author.full_name() + " ({0})".format(author.institution)
            else:
                carousel_text += author.full_name()

            idx = 1

        return carousel_text

    @property
    def carousel_title(self):
        return self.title

    @property
    def carousel_image_resolver(self):
        return 'article_file_download'

    @property
    def pdfs(self):
        ret = self.galley_set.filter(type="pdf")
        return ret

    @property
    def get_render_galley(self):
        if self.render_galley:
            return self.render_galley

        ret = self.galley_set.filter(
            file__mime_type="application/xml"
        ).order_by(
            "sequence",
        )

        if len(ret) > 0:
            return ret[0]
        else:
            return None

    @property
    def xml_galleys(self):
        ret = self.galley_set.filter(file__mime_type="application/xml").order_by(
            "sequence")

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

            souped_xml = BeautifulSoup(xml_file_contents, 'lxml')

            elements = {
                'img': 'src',
                'graphic': 'xlink:href'
            }

            from core import models as core_models

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
                        named_files = self.data_figure_files.filter(original_filename=url).first()

                        if not named_files:
                            return False

                    except core_models.File.DoesNotExist:
                        return False

        return True

    @property
    @cache(300)
    def identifier(self):
        from identifiers import models as identifier_models
        try:
            type_to_fetch = "doi"
            return identifier_models.Identifier.objects.filter(id_type=type_to_fetch, article=self)[0]
        except BaseException:
            new_id = identifier_models.Identifier(id_type="id", identifier=self.id, article=self)
            return new_id

    def get_identifier(self, identifier_type, object=False):
        from identifiers import models as identifier_models
        try:
            try:
                doi = identifier_models.Identifier.objects.get(id_type=identifier_type, article=self)
            except identifier_models.Identifier.MultipleObjectsReturned:
                doi = identifier_models.Identifier.objects.filter(id_type=identifier_type, article=self)[0]
            if not object:
                return doi.identifier
            else:
                return doi
        except identifier_models.Identifier.DoesNotExist:
            return None

    def get_doi(self):
        return self.get_identifier('doi')

    @property
    def identifiers(self):
        from identifiers import models as identifier_models
        return identifier_models.Identifier.objects.filter(article=self)

    def get_pubid(self):
        return self.get_identifier('pubid')

    def is_accepted(self):
        # return true for all stages after accepted
        return self.stage == "Published" or self.stage == "Accepted" or self.stage == "Editor Copyediting"\
            or self.stage == "Author Copyediting" or self.stage == "Final Copyediting"\
            or self.stage == "Typesetting" or self.stage == "Proofing"

    def __str__(self):
        return u'%s - %s' % (self.pk, self.title)

    @staticmethod
    @cache(300)
    def get_article(journal, identifier_type, identifier):
        from identifiers import models as identifier_models
        try:
            article = None
            # resolve an article from an identifier type and an identifier
            if identifier_type.lower() == 'id':
                # this is the hardcoded fallback type: using built-in id
                article = Article.allarticles.filter(id=identifier, journal=journal)[0]
            else:
                # this looks up an article by an ID type and an identifier string
                article = identifier_models.Identifier.objects.filter(
                    id_type=identifier_type, identifier=identifier)[0].article

                if article.is_published:
                    # check that the retrieved article is listed in an issue TOC for the current journal
                    article_journals = [issue.journal for issue in article.issues.all()]

                    if journal not in article_journals:
                        return None
                elif not article.journal == journal:
                    return None

            return article
        except BaseException:            # no article found
            # TODO: handle better and log
            return None

    @staticmethod
    def get_press_article(press, identifier_type, identifier):
        from identifiers import models as identifier_models
        try:
            article = None
            # resolve an article from an identifier type and an identifier
            if identifier_type.lower() == 'id':
                # this is the hardcoded fallback type: using built-in id
                article = Article.allarticles.filter(id=identifier)[0]
            else:
                # this looks up an article by an ID type and an identifier string
                article = identifier_models.Identifier.objects.filter(
                    id_type=identifier_type, identifier=identifier)[0].article

            return article
        except BaseException:            # no article found
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
                id_type='pubid',
                article=self,
            )
        except identifier_models.Identifier.DoesNotExist:
            identifier = identifier_models.Identifier(
                id_type="id",
                identifier=self.pk,
                article=self
            )

        url = reverse(
            'article_view',
            kwargs={'identifier_type': identifier.id_type,
                    'identifier': identifier.identifier}
        )

        return url

    @property
    def pdf_url(self):
        pdfs = self.pdfs
        path = reverse('article_download_galley', kwargs={
            'article_id': self.pk,
            'galley_id': pdfs[0].pk
        })
        return self.journal.site_url(path=path)

    def get_remote_url(self, request):
        parsed_uri = urlparse('http' + ('', 's')[request.is_secure()] + '://' + request.META['HTTP_HOST'])
        domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        url = domain + self.local_url

        return url

    def step_to_url(self):
        if self.current_step == 1:
            return reverse('submit_info', kwargs={'article_id': self.id})
        elif self.current_step == 2:
            return reverse('submit_authors', kwargs={'article_id': self.id})
        elif self.current_step == 3:
            return reverse('submit_files', kwargs={'article_id': self.id})
        elif self.current_step == 4:
            return reverse('submit_review', kwargs={'article_id': self.id})
        else:
            return None

    def step_name(self):
        if self.current_step == 1:
            return 'Article Information'
        elif self.current_step == 2:
            return 'Article Authors'
        elif self.current_step == 3:
            return 'Article Files'
        elif self.current_step == 4:
            return 'Review Article Submission'
        elif self.current_step == 5:
            return 'Submission Complete'

    def save(self, *args, **kwargs):
        if self.pk is not None:
            current_object = Article.allarticles.get(pk=self.pk)
            if current_object.stage != self.stage:
                ArticleStageLog.objects.create(article=self, stage_from=current_object.stage,
                                               stage_to=self.stage)
        super(Article, self).save(*args, **kwargs)

    def folder_path(self):
        return os.path.join(settings.BASE_DIR, 'files', 'articles', self.pk)

    def production_managers(self):
        return [assignment.production_manager for assignment in self.productionassignment_set.all()]

    def editor_list(self):
        return [assignment.editor for assignment in self.editorassignment_set.all()]

    def editors(self):
        return [{'editor': assignment.editor, 'editor_type': assignment.editor_type, 'assignment': assignment} for
                assignment in self.editorassignment_set.all()]

    def section_editors(self, emails=False):
        editors = [assignment.editor for assignment in self.editorassignment_set.filter(editor_type='section-editor')]

        if emails:
            return set([editor.email for editor in editors])

        else:
            return editors

    def editor_emails(self):
        return [assignment.editor.email for assignment in self.editorassignment_set.all()]

    def contact_emails(self):
        emails = [author.email for author in self.authors.all()]
        emails.append(self.owner.email)
        return set(emails)

    def peer_reviewers(self, emails=False):
        reviewers = [assignment.reviewer for assignment in self.reviewassignment_set.all()]

        if emails:
            return set([reviewer.email for reviewer in reviewers])

        return set(reviewers)

    def issues_list(self):
        from journal import models as journal_models
        return journal_models.Issue.objects.filter(journal=self.journal, articles__in=[self])

    @cache(7200)
    def altmetrics(self):
        alm = self.altmetric_set.all()
        return {
            'twitter': alm.filter(source='twitter'),
            'wikipedia': alm.filter(source='wikipedia'),
            'reddit': alm.filter(source='reddit'),
            'hypothesis': alm.filter(source='hypothesis'),
            'wordpress': alm.filter(source='wordpress.com'),
            'crossref': alm.filter(source='crossref'),
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

    def author_list(self):
        if self.is_accepted():
            return ", ".join([author.full_name() for author in self.frozen_authors()])
        else:
            return ", ".join([author.full_name() for author in self.authors.all()])

    def can_edit(self, user):
        # returns True if a user can edit an article
        # editing is always allowed when a user is staff
        # otherwise, the user must own the article and it
        # must not have already been published

        if user.is_staff:
            return True
        elif user in self.section_editors():
            return True
        elif not user.is_anonymous() and user.is_editor(
                request=None,
                journal=self.journal,
        ):
            return True
        else:
            if self.owner != user:
                return False

            if self.stage == STAGE_PUBLISHED or self.stage == STAGE_REJECTED:
                return False

            return True

    def current_review_round(self):
        try:
            return self.reviewround_set.all().order_by('-round_number')[0].round_number
        except IndexError:
            return 1

    def current_review_round_object(self):
        try:
            return self.reviewround_set.all().order_by('-round_number')[0]
        except IndexError:
            return None

    @property
    def active_reviews(self):
        return self.reviewassignment_set.filter(is_complete=False, date_declined__isnull=True)

    @property
    def completed_reviews(self):
        return self.reviewassignment_set.filter(is_complete=True, date_declined__isnull=True)

    @property
    def completed_reviews_with_decision(self):
        return self.reviewassignment_set.filter(is_complete=True,
                                                date_declined__isnull=True,
                                                review_round=self.current_review_round_object()
                                                ).exclude(decision='withdrawn')

    def active_review_request_for_user(self, user):
        try:
            return self.reviewassignment_set.filter(is_complete=False, date_declined__isnull=True,
                                                    reviewer=user).first()
        except review_models.ReviewAssignment.DoesNotExist:
            return None

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
            id.register()

    def decline_article(self):
        self.date_declined = timezone.now()
        self.date_accepted = None
        self.stage = STAGE_REJECTED
        self.save()

    def accept_preprint(self, date, time):
        self.date_accepted = timezone.now()
        self.date_declined = None
        self.stage = STAGE_PREPRINT_PUBLISHED
        self.date_published = dateparser.parse('{date} {time}'.format(date=date, time=time))
        self.save()

    def user_is_author(self, user):
        if user in self.authors.all():
            return True
        else:
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
        if (self.stage == STAGE_PUBLISHED or self.stage == STAGE_PREPRINT_PUBLISHED) and \
                self.date_published and self.date_published < timezone.now():
            return True
        else:
            return False

    def snapshot_authors(self, article=None, force_update=True):
        """ Creates/updates FrozenAuthor records for this article's authors
        :param article: (deprecated) should not pass this argument
        :param force_update: (bool) Whether or not to update existing records
        """
        subq = models.Subquery(ArticleAuthorOrder.objects.filter(
            article=self, author__id=models.OuterRef("id")
        ).values_list("order"))
        authors = self.authors.annotate(order=subq).order_by("order")
        for author in authors:
            author.snapshot_self(self, force_update)

    def frozen_authors(self):
        return FrozenAuthor.objects.filter(article=self)

    def editor_override(self, editor):
        check = review_models.EditorOverride.objects.filter(article=self, editor=editor)

        if check:
            return True
        else:
            return False

    def active_revision_requests(self):
        return self.revisionrequest_set.filter(date_completed__isnull=True)

    def active_author_copyedits(self):
        author_copyedits = []

        for assignment in self.copyeditassignment_set.all():
            for review in assignment.active_author_reviews():
                author_copyedits.append(review)

        return author_copyedits

    @property
    def custom_fields(self):
        """ Returns all the FieldAnswers configured for rendering"""
        return self.fieldanswer_set.filter(
            field__display=True,
            answer__isnull=False,
        )

    def get_meta_image_path(self):
        if self.meta_image and self.meta_image.url:
            return self.meta_image.url
        elif self.large_image_file and self.large_image_file.id:
            return reverse('article_file_download', kwargs={'identifier_type': 'id',
                                                            'identifier': self.pk,
                                                            'file_id': self.large_image_file.pk})
        elif self.thumbnail_image_file and self.thumbnail_image_file.id:
            return reverse('article_file_download', kwargs={'identifier_type': 'id',
                                                            'identifier': self.pk,
                                                            'file_id': self.thumbnail_image_file.pk})
        elif self.journal.default_large_image:
            return self.journal.default_large_image.url
        else:
            return ''

    def unlink_meta_file(self):
        path = os.path.join(self.meta_image.storage.base_location, self.meta_image.name)
        if os.path.isfile(path):
            os.unlink(path)

    def next_author_sort(self):
        current_orders = [order.order for order in ArticleAuthorOrder.objects.filter(article=self)]
        if not current_orders:
            return 0
        else:
            return max(current_orders) + 1

    def next_preprint_version(self):
        versions = [version.version for version in preprint_models.PreprintVersion.objects.filter(preprint=self)]
        if not versions:
            return 1
        else:
            return max(versions) + 1

    def subject_editors(self):
        editors = list()
        subjects = self.subject_set.all().prefetch_related('editors')

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
        from core import models as core_models
        return core_models.WorkflowLog.objects.filter(article=self)

    @property
    def current_workflow_element(self):
        from core import models as core_models
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
        kwargs = {'article_id': self.pk}
        # STAGE_UNASSIGNED and STAGE_PUBLISHED arent elements so are hardcoded.
        if self.stage == STAGE_UNASSIGNED:
            return reverse('review_unassigned_article', kwargs=kwargs)
        elif self.stage in FINAL_STAGES:
            return reverse('manage_archive_article', kwargs=kwargs)
        elif not self.stage:
            logger.error(
                'Article #{} has no Stage.'.format(
                    self.pk,
                )
            )
            return '?workflow_element_url=no_stage'
        else:
            element = self.current_workflow_element
            if element:
                return reverse(element.jump_url, kwargs=kwargs)
            else:
                # In order to ensure the Dashboard renders we purposefully do
                # not raise an error message here.
                logger.error(
                    'There is no workflow element for stage {}.'.format(
                        self.stage,
                    )
                )
                return '?workflow_element_url=no_element'

    @cache(600)
    def render_sample_doi(self):
        return id_logic.render_doi_from_pattern(self)

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
            decision='cancelled',
        )
        copyedit_models.AuthorReview.objects.filter(
            assignment__article=self,
            date_decided__isnull=True,
        ).update(
            decision='accept',
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


class FrozenAuthor(models.Model):
    article = models.ForeignKey('submission.Article', blank=True, null=True)
    author = models.ForeignKey('core.Account', blank=True, null=True)

    first_name = models.CharField(max_length=300, null=True, blank=True)
    middle_name = models.CharField(max_length=300, null=True, blank=True)
    last_name = models.CharField(max_length=300, null=True, blank=True)

    institution = models.CharField(max_length=1000)
    department = models.CharField(max_length=300, null=True, blank=True)
    country = models.ForeignKey('core.Country', null=True, blank=True)

    order = models.PositiveIntegerField(default=1)

    is_corporate = models.BooleanField(
            default=False,
            help_text="If enabled, the institution and department fields will "
                "be used as the author full name",
    )

    class Meta:
        ordering = ('order', 'pk')

    def __str__(self):
        return self.full_name()

    def full_name(self):
        if self.is_corporate:
            return self.corporate_name
        elif self.middle_name:
            return u"%s %s %s" % (self.first_name, self.middle_name, self.last_name)
        else:
            return u"%s %s" % (self.first_name, self.last_name)

    @property
    def corporate_name(self):
        name = self.institution
        if self.department:
            name = "{}, {}".format(self.department, name)
        return name

    def citation_name(self):
        if self.is_corporate:
            return self.corporate_name
        first_initial, middle_initial = '', ''

        if self.middle_name:
            middle_initial = ' {0}.'.format(self.middle_name[:1])
        if self.first_name:
            first_initial = '{0}.'.format(self.first_name[:1])

        return '{last} {first}{middle}'.format(last=self.last_name, first=first_initial, middle=middle_initial)

    def given_names(self):
        if self.middle_name:
            return '{first_name} {middle_name}'.format(first_name=self.first_name, middle_name=self.middle_name)
        else:
            return self.first_name

    def affiliation(self):
        if self.department:
            return '{inst} {dept}'.format(inst=self.institution, dept=self.department)
        else:
            return self.institution

    @property
    def is_correspondence_author(self):
        # early return if no email address available
        if (not self.author
                or settings.DUMMY_EMAIL_DOMAIN in self.author.email):
            return False

        elif self.article.journal.enable_correspondence_authors is True:
            if self.article.correspondence_author is not None:
                return self.article.correspondence_author == self.author
            else:
                order = ArticleAuthorOrder.objects.get(
                        article=self.article,
                        author=self.author,
                ).order
                return order == 0
        else:
            return True


class Section(TranslatableModel):
    journal = models.ForeignKey('journal.Journal')
    number_of_reviewers = models.IntegerField(default=2)

    editors = models.ManyToManyField('core.Account',
        help_text="Editors assigned will be notified of submissions,"
            " overruling the notification settings for the journal.",
    )
    section_editors = models.ManyToManyField('core.Account',
        help_text="Section editors assigned will be notified of submissions,"
            " overruling the notification settings for the journal.",
        related_name='section_editors',
    )
    auto_assign_editors = models.BooleanField(default=False,
        help_text="Articles submitted to this section will be automatically"
            " assigned to the editors and/or section editors selected above.",
    )

    is_filterable = models.BooleanField(default=True,
        help_text="Allows filtering article search results by this section.")
    public_submissions = models.BooleanField(default=True)
    indexing = models.BooleanField(default=True,
        help_text="Whether this section is put forward for indexing")
    sequence = models.PositiveIntegerField(default=0,
        help_text="Determines the order in which the section is rendered"
            " Sections can also be reorder by drag-and-drop",
    )

    translations = TranslatedFields(
        name=models.CharField(max_length=200),
        plural=models.CharField(max_length=200, null=True, blank=True,
            help_text="Pluralised name for the section"
                " (e.g: Article -> Articles)"
        )
    )

    class Meta:
        ordering = ('sequence',)

    def __str__(self):
        return self.safe_translation_getter('name', str(self.pk))

    def published_articles(self):
        return Article.objects.filter(section=self, stage=STAGE_PUBLISHED)

    def editor_emails(self):
        return [editor.email for editor in self.editors.all()]

    def section_editor_emails(self):
        return [editor.email for editor in self.section_editors.all()]

    def all_editor_emails(self):
        return [editor.email for editor in self.section_editors.all() + self.editors.all()]

    def issue_display(self):
        if self.lazy_translation_getter('plural', str(self.pk)):
            return self.lazy_translation_getter('plural', str(self.pk))
        else:
            return self.lazy_translation_getter('name', str(self.pk))


class Licence(models.Model):
    journal = models.ForeignKey('journal.Journal', null=True, blank=True, on_delete=models.SET_NULL)
    press = models.ForeignKey('press.Press', null=True, blank=True, on_delete=models.SET_NULL)

    name = models.CharField(max_length=300)
    short_name = models.CharField(max_length=15)
    url = models.URLField(max_length=1000)
    text = models.TextField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    available_for_submission = models.BooleanField(default=True)

    class Meta:
        ordering = ('order', 'name')

    def __str__(self):
        return '{short_name}'.format(short_name=self.short_name)

    def object(self):
        if not self.journal:
            return self.press

        return self.journal


class Note(models.Model):
    article = models.ForeignKey(Article)
    creator = models.ForeignKey('core.Account')
    text = models.TextField()
    date_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_time',)


def field_kind_choices():
    return (
        ('text', 'Text Field'),
        ('textarea', 'Text Area'),
        ('check', 'Check Box'),
        ('select', 'Select'),
        ('email', 'Email'),
        ('date', 'Date'),
    )


def width_choices():
    return (
        ('third', 'Third'),
        ('half', 'Half'),
        ('full,', 'Full'),
    )


class Field(models.Model):
    journal = models.ForeignKey('journal.Journal', blank=True, null=True)
    press = models.ForeignKey('press.Press', blank=True, null=True)
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=50, choices=field_kind_choices())
    width = models.CharField(max_length=50, choices=width_choices(), default='full')
    choices = models.CharField(max_length=1000, null=True, blank=True,
                               help_text='Separate choices with the bar | character.')
    required = models.BooleanField(default=True)
    order = models.IntegerField()
    display = models.BooleanField(
        default=False,
        help_text='Whether or not display this field in the article page'
    )
    help_text = models.TextField()

    class Meta:
        ordering = ('order', 'name')

    def __str__(self):
        return "Field: {0} ({1})".format(self.name, self.kind)

    @property
    def object(self):
        if not self.journal:
            return self.press

        return self.journal


class FieldAnswer(models.Model):
    field = models.ForeignKey(Field, null=True, blank=True, on_delete=models.SET_NULL)
    article = models.ForeignKey(Article)
    answer = models.TextField()


class ArticleAuthorOrder(models.Model):
    article = models.ForeignKey(Article)
    author = models.ForeignKey('core.Account')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('order',)


class SubmissionConfiguration(models.Model):
    journal = models.OneToOneField('journal.Journal')

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
        verbose_name=_('Figures and Data Files'),
    )

    default_license = models.ForeignKey(
        Licence,
        null=True,
        blank=True,
        help_text=_('The default license applied when no option is presented'),
    )
    default_language = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        choices=LANGUAGE_CHOICES,
        help_text=_('The default language of articles when lang is hidden'),
    )
    default_section = models.ForeignKey(
        Section,
        null=True,
        blank=True,
        help_text=_('The default section of '
                    'articles when no option is presented'),
    )
    submission_file_text = models.CharField(
        max_length=255,
        default='Manuscript File',
        help_text='During submission the author will be asked to upload a file'
                  'that is considered the main text of the article. You can use'
                  'this field to change the label for that file in submission.',
    )

    def __str__(self):
        return 'SubmissionConfiguration for {0}'.format(self.journal.name)

    def lang_section_license_width(self):
        if self.language and self.license:
            return '4'
        elif not self.language and not self.license:
            return '12'
        elif not self.language and self.license:
            return '6'
        elif self.language and not self.license:
            return '6'

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
    try:
        ArticleAuthorOrder.objects.get(
            author=instance.author,
            article=instance.article,
        ).delete()
    except ArticleAuthorOrder.DoesNotExist:
        pass

    instance.article.authors.remove(instance.author)

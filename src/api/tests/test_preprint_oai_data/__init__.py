import os

from django.conf import settings

DIR = os.path.join(settings.BASE_DIR, 'api', 'tests', 'test_preprint_oai_data')

with open(os.path.join(DIR, 'list_records_data_dc.xml'), 'r') as ref:
    LIST_RECORDS_DATA_DC = ref.read()

with open(os.path.join(DIR, 'list_records_data_jats.xml'), 'r') as ref:
    LIST_RECORDS_DATA_JATS = ref.read()

with open(os.path.join(DIR, 'get_record_data_dc.xml'), 'r') as ref:
    GET_RECORD_DATA_DC = ref.read()

with open(os.path.join(DIR, 'get_record_data_until.xml'), 'r') as ref:
    GET_RECORD_DATA_UNTIL = ref.read()

with open(os.path.join(DIR, 'get_record_data_jats.xml'), 'r') as ref:
    GET_RECORD_DATA_JATS = ref.read()

with open(os.path.join(DIR, 'list_identifiers_jats.xml'), 'r') as ref:
    LIST_IDENTIFIERS_JATS = ref.read()

with open(os.path.join(DIR, 'identify_data_dc.xml'), 'r') as ref:
    IDENTIFY_DATA_DC = ref.read()

with open(os.path.join(DIR, 'list_sets_data_dc.xml'), 'r') as ref:
    LIST_SETS_DATA_DC = ref.read()

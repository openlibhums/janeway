# Three records taken from the ROR data in schema version 1.2
ROR_RECORDS = [
    {
        "admin": {
            "created": {"date": "2018-11-14", "schema_version": "1.0"},
            "last_modified": {"date": "2024-12-11", "schema_version": "2.1"},
        },
        "domains": ["kea.dk"],
        "established": 2009,
        "external_ids": [
            {"all": ["grid.466211.6"], "preferred": "grid.466211.6", "type": "grid"},
            {"all": ["0000 0004 0469 3633"], "preferred": None, "type": "isni"},
            {"all": ["Q25044653"], "preferred": None, "type": "wikidata"},
        ],
        "id": "https://ror.org/00j1xwp39",
        "links": [
            {"type": "website", "value": "https://kea.dk"},
            {
                "type": "wikipedia",
                "value": "https://en.wikipedia.org/wiki/KEA_%E2%80%93_Copenhagen_School_of_Design_and_Technology",
            },
        ],
        "locations": [
            {
                "geonames_details": {
                    "continent_code": "EU",
                    "continent_name": "Europe",
                    "country_code": "DK",
                    "country_name": "Denmark",
                    "country_subdivision_code": "84",
                    "country_subdivision_name": "Capital Region",
                    "lat": 55.67594,
                    "lng": 12.56553,
                    "name": "Copenhagen",
                },
                "geonames_id": 2618425,
            }
        ],
        "names": [
            {
                "lang": "en",
                "types": ["ror_display", "label"],
                "value": "Copenhagen School of Design and Technology",
            },
            {"lang": None, "types": ["acronym"], "value": "KEA"},
            {
                "lang": "da",
                "types": ["label"],
                "value": "K\u00f8benhavns Erhvervsakademi",
            },
        ],
        "relationships": [],
        "status": "active",
        "types": ["education"],
    },
    {
        "admin": {
            "created": {"date": "2018-11-14", "schema_version": "1.0"},
            "last_modified": {"date": "2024-12-11", "schema_version": "2.1"},
        },
        "domains": ["kfe.re.kr"],
        "established": 1995,
        "external_ids": [
            {"all": ["501100003721"], "preferred": None, "type": "fundref"},
            {"all": ["grid.419380.7"], "preferred": "grid.419380.7", "type": "grid"},
        ],
        "id": "https://ror.org/013yz9b19",
        "links": [{"type": "website", "value": "https://www.kfe.re.kr/"}],
        "locations": [
            {
                "geonames_details": {
                    "continent_code": "AS",
                    "continent_name": "Asia",
                    "country_code": "KR",
                    "country_name": "South Korea",
                    "country_subdivision_code": "30",
                    "country_subdivision_name": "Daejeon",
                    "lat": 36.34913,
                    "lng": 127.38493,
                    "name": "Daejeon",
                },
                "geonames_id": 1835235,
            }
        ],
        "names": [
            {"lang": None, "types": ["acronym"], "value": "KFE"},
            {
                "lang": "en",
                "types": ["ror_display", "label"],
                "value": "Korea Institute of Fusion Energy",
            },
        ],
        "relationships": [],
        "status": "active",
        "types": ["facility", "funder"],
    },
    {
        "admin": {
            "created": {"date": "2018-11-14", "schema_version": "1.0"},
            "last_modified": {"date": "2024-12-11", "schema_version": "2.1"},
        },
        "domains": ["turing.ac.uk"],
        "established": 2015,
        "external_ids": [
            {"all": ["100012338"], "preferred": "100012338", "type": "fundref"},
            {"all": ["grid.499548.d"], "preferred": "grid.499548.d", "type": "grid"},
            {"all": ["0000 0004 5903 3632"], "preferred": None, "type": "isni"},
            {"all": ["Q16826821"], "preferred": None, "type": "wikidata"},
        ],
        "id": "https://ror.org/035dkdb55",
        "links": [
            {"type": "website", "value": "https://www.turing.ac.uk"},
            {
                "type": "wikipedia",
                "value": "https://en.wikipedia.org/wiki/Alan_Turing_Institute",
            },
        ],
        "locations": [
            {
                "geonames_details": {
                    "continent_code": "EU",
                    "continent_name": "Europe",
                    "country_code": "GB",
                    "country_name": "United Kingdom",
                    "country_subdivision_code": "ENG",
                    "country_subdivision_name": "England",
                    "lat": 51.50853,
                    "lng": -0.12574,
                    "name": "London",
                },
                "geonames_id": 2643743,
            }
        ],
        "names": [
            {
                "lang": "en",
                "types": ["ror_display", "label"],
                "value": "The Alan Turing Institute",
            }
        ],
        "relationships": [],
        "status": "active",
        "types": ["facility", "funder"],
    },
]

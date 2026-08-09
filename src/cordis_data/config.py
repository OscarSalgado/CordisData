"""Configuration constants for CORDIS data collection."""

# API endpoints
SEDIA_API_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
CORDIS_URL_TEMPLATE = "https://cordis.europa.eu/project/id/{project_id}?format=json"

# Rate limiting
SEDIA_MAX_WORKERS = 6
CORDIS_RATE_LIMIT = 2.0  # requests per second
CORDIS_ENRICHMENT_WORKERS = 3
CORDIS_TTL_DAYS = 90

# Fetch defaults
DEFAULT_WINDOW_DAYS = 90
CALLS_BATCH_SIZE = 100
PROJECTS_BATCH_SIZE = 50

# API keys
SEDIA_API_KEY = "SEDIA"
PROJECTS_API_KEY = "SEDIA_NONH2020_PROD"

# Status mappings
STATUS_MAP = {
    "31094501": "forthcoming",
    "31094502": "open",
    "31094503": "closed",
}

# EU Programme names
PROGRAMME_NAMES = {
    "43108390": "Horizon Europe",
    "43152860": "Digital Europe",
    "44181033": "European Defence Fund",
    "43353764": "Erasmus+",
    "43251814": "Creative Europe",
    "43251589": "CERV",
    "43252476": "Single Market Programme",
    "43252405": "LIFE",
    "43298916": "Euratom",
    "43332642": "EU4Health",
    "43251567": "Connecting Europe Facility",
    "43089234": "Innovation Fund",
    "43392145": "EMFAF",
    "43254019": "ESF+",
    "43254037": "European Solidarity Corps",
    "43253979": "Customs Programme",
    "43253995": "Fiscalis",
    "43251447": "AMIF",
    "43251530": "BMVI",
    "43251534": "CCEI",
    "43298203": "UCPM",
    "43252368": "ISF",
    "43252386": "Justice",
    "44416173": "Interregional Innovation",
    "45876777": "NDICI Global Europe",
    "43298664": "AGRIP",
    "43253706": "TSI",
    "43251882": "IMCAP",
    "43252449": "RFCS",
    "43252517": "SOCPL",
    "44773133": "IMREG",
    "44773066": "JTM",
    "31045243": "Horizon 2020",
    "45532249": "EU Agencies",
    "43252433": "Pericles IV",
    "42810547": "Europe Direct",
    "43697167": "European Parliament",
    "43253967": "Renewable Energy FM",
    "43251842": "EU Anti-Fraud (EUAF)",
    "111111": "EU External Action - Prospect (RELEX-PROSPECT)",
    "43637601": "Pilot Projects & Preparatory Actions",
    "31059643": "COSME",
    "46324255": "Technical assistance for ERDF, CF and JTF (ERDF-TA)",
    "47786028": "Business and Consumer Surveys",
    "47376280": "EU External Action - eGrants (RELEX2027)",
    # Legacy 2014-2020 programme ids
    "31076817": "Rights, Equality and Citizenship Programme (REC) (2014-2020)",
    "31065524": "Connecting Europe Facility (CEF) (2014-2020)",
    "31070247": "Justice Programme (JUST) (2014-2020)",
    "31061266": "3rd Health Programme (3HP) (2014-2020)",
    "31077817": "Internal Security Fund Police (ISFP) (2014-2020)",
    "111109": "1st Health Programme (1HP) (2014-2020)",
    "31077795": "Asylum, Migration and Integration Fund (AMIF) (2014-2020)",
    "111110": "2nd Health Programme (2HP) (2014-2020)",
    "31109727": "European Defence Industrial Development Programme (EDIDP) (2014-2020)",
    "31084392": "Hercule III (HERC) (2014-2020)",
    "31061225": "Research Fund for Coal & Steel (RFCS) (2014-2020)",
    "31072773": "Promotion of Agricultural Products (AGRIP) (2014-2020)",
    "31059093": "Erasmus+ (EPLUS) (2014-2020)",
    "31084250": "Pilot Projects & Preparatory Actions (PPPA) (2014-2020)",
    "31059083": "Creative Europe (CREA) (2014-2020)",
    "31082527": "Union Civil Protection Mechanism (UCPM) (2014-2020)",
    "31098847": "European Maritime and Fisheries Fund (EMFF) (2014-2020)",
    "42198993": "Support for Information Measures Relating to CAP (IMCAP) (2014-2020)",
    "31061273": "Consumer Programme (CP) (2014-2020)",
    "31107710": "LIFE (2014-2020)",
    "31114387": "EU Programme for Education, Training, Youth and Sport (2014-2020)",
    "31077833": "Internal Security Fund Borders and Visa (ISFB) (2014-2020)",
    "31059088": "Europe For Citizens (EFC) (2014-2020)",
    "42905358": "Structural Reform Support Programme (SRSP) (2014-2020)",
    "31088049": "European Statistics (ESTAT) (2014-2020)",
    "31059098": "EU Aid Volunteers (EUAID) (2014-2020)",
    "31075571": "Intra-Africa Academic Mobility Scheme (PANAF) (2014-2020)",
    "42992790": "European Solidarity Corps (ESC) (2014-2020)",
}

# Action type mappings
ACTION_TYPE_MAP = {
    "RIA": "Research and Innovation Action",
    "IA": "Innovation Action",
    "CSA": "Coordination and Support Action",
    "PPI": "Pre-Commercial Procurement",
    "CoFund": "Co-funding",
    "Prize": "Prize",
    "MSCA-SE": "MSCA Staff Exchange",
    "MSCA": "Marie Skłodowska-Curie Action",
    "Grant": "Grant",
}

"""
Shared species constants for the Sanjeevani dataset pipeline.
Single source of truth — imported by all other scripts.
"""

# (folder_name, botanical_name, ayurvedic_name, priority)
SPECIES = [
    ("Tulsi",              "Ocimum tenuiflorum",          "Tulasi",        "HIGH"),
    ("Neem",               "Azadirachta indica",           "Nimba",         "HIGH"),
    ("Brahmi",             "Bacopa monnieri",              "Brahmi",        "HIGH"),
    ("Ashwagandha",        "Withania somnifera",           "Ashwagandha",   "HIGH"),
    ("AloeVera",           "Aloe barbadensis",             "Kumari",        "HIGH"),
    ("Turmeric",           "Curcuma longa",                "Haridra",       "HIGH"),
    ("Ginger",             "Zingiber officinale",          "Shunti",        "HIGH"),
    ("Moringa",            "Moringa oleifera",             "Shigru",        "HIGH"),
    ("CurryLeaf",          "Murraya koenigii",             "Surabhi",       "HIGH"),
    ("Betel",              "Piper betle",                  "Nagavalli",     "HIGH"),
    ("Mint",               "Mentha spicata",               "Pudina",        "HIGH"),
    ("Lemongrass",         "Cymbopogon citratus",          "Bhustrina",     "HIGH"),
    ("IndianBeech",        "Millettia pinnata",            "Karanja",       "HIGH"),
    ("Amla",               "Phyllanthus emblica",          "Amalaki",       "HIGH"),
    ("Bael",               "Aegle marmelos",               "Bilva",         "HIGH"),
    ("Giloy",              "Tinospora cordifolia",         "Guduchi",       "HIGH"),
    ("Shatavari",          "Asparagus racemosus",          "Shatavari",     "HIGH"),
    ("GotoKola",           "Centella asiatica",            "Mandukaparni",  "HIGH"),
    ("Kalmegh",            "Andrographis paniculata",      "Kalamegh",      "HIGH"),
    ("Adulsa",             "Justicia adhatoda",            "Vasa",          "HIGH"),
    ("Haritaki",           "Terminalia chebula",           "Haritaki",      "HIGH"),
    ("Gudmar",             "Gymnema sylvestre",            "Madhunashini",  "HIGH"),
    ("Nirgundi",           "Vitex negundo",                "Nirgundi",      "HIGH"),
    ("BlackPepper",        "Piper nigrum",                 "Maricha",       "HIGH"),
    ("LongPepper",         "Piper longum",                 "Pippali",       "HIGH"),
    ("Guava",              "Psidium guajava",              "Amrud",         "MEDIUM"),
    ("Papaya",             "Carica papaya",                "Erandakarkati", "MEDIUM"),
    ("Bhringraj",          "Eclipta prostrata",            "Bhringaraja",   "MEDIUM"),
    ("Punarnava",          "Boerhavia diffusa",            "Punarnava",     "MEDIUM"),
    ("Karela",             "Momordica charantia",          "Karavella",     "MEDIUM"),
    ("Jamun",              "Syzygium cumini",              "Jambu",         "MEDIUM"),
    ("Hibiscus",           "Hibiscus rosa-sinensis",       "Japa",          "MEDIUM"),
    ("IndianPennywort",    "Hydrocotyle asiatica",         "BrahmaManduki", "MEDIUM"),
    ("Castor",             "Ricinus communis",             "Eranda",        "MEDIUM"),
    ("Mulethi",            "Glycyrrhiza glabra",           "Yastimadhu",    "MEDIUM"),
    ("Karpuravalli",       "Coleus aromaticus",            "Karpuravalli",  "MEDIUM"),
    ("InsulinPlant",       "Costus igneus",                "Keukand",       "MEDIUM"),
    ("Peepal",             "Ficus religiosa",              "Ashvattha",     "MEDIUM"),
    ("Banyan",             "Ficus benghalensis",           "Vata",          "MEDIUM"),
    ("Aparajita",          "Clitoria ternatea",            "Aparajita",     "MEDIUM"),
    ("Patharchatta",       "Bryophyllum pinnatum",         "Parnabeeja",    "MEDIUM"),
    ("Bringaraj",          "Eclipta alba",                 "Bhringaraja",   "MEDIUM"),
    ("HolyBasilVana",      "Ocimum gratissimum",           "VanaTulasi",    "MEDIUM"),
    ("Amruth",             "Tinospora sinensis",           "Amruth",        "MEDIUM"),
    ("Palash",             "Butea monosperma",             "Palasha",       "MEDIUM"),
    ("Vibhitaki",          "Terminalia bellirica",         "Vibhitaka",     "MEDIUM"),
    ("Arjuna",             "Terminalia arjuna",            "Arjuna",        "MEDIUM"),
    ("Sarpagandha",        "Rauvolfia serpentina",         "Sarpagandha",   "MEDIUM"),
    ("Vacha",              "Acorus calamus",               "Vacha",         "MEDIUM"),
    ("Chitraka",           "Plumbago zeylanica",           "Chitraka",      "MEDIUM"),
    ("Kutaja",             "Holarrhena pubescens",         "Kutaja",        "MEDIUM"),
    ("Kanchnaar",          "Bauhinia variegata",           "Kanchanara",    "MEDIUM"),
    ("Agathi",             "Sesbania grandiflora",         "Agasthya",      "MEDIUM"),
    ("BetelNut",           "Areca catechu",                "Puga",          "MEDIUM"),
    ("Vetiver",            "Chrysopogon zizanioides",      "Ushira",        "MEDIUM"),
    ("Pomegranate",        "Punica granatum",              "Dadima",        "MEDIUM"),
    ("Fenugreek",          "Trigonella foenum-graecum",    "Methi",         "MEDIUM"),
    ("IndianSarsaparilla", "Hemidesmus indicus",           "Anantamul",     "MEDIUM"),
    ("Clove",              "Syzygium aromaticum",          "Lavanga",       "MEDIUM"),
    ("SnakePlant",         "Sansevieria trifasciata",      "",              "LOW"),
    ("Lemon",              "Citrus limon",                 "Nimbuka",       "LOW"),
    ("Chamomile",          "Matricaria chamomilla",        "Babunah",       "LOW"),
    ("Devadaru",           "Cedrus deodara",               "Devadaru",      "LOW"),
    ("Yashad",             "Withania coagulans",           "PaneerDoda",    "LOW"),
    ("Shyonaka",           "Oroxylum indicum",             "Shyonaka",      "LOW"),
    ("Sesame",             "Sesamum indicum",              "Tila",          "LOW"),
    ("Coriander",          "Coriandrum sativum",           "Dhanyaka",      "LOW"),
]

HIGH_PRIORITY   = [s for s in SPECIES if s[3] == "HIGH"]
MEDIUM_PRIORITY = [s for s in SPECIES if s[3] == "MEDIUM"]
LOW_PRIORITY    = [s for s in SPECIES if s[3] == "LOW"]

# dict for fast lookup by folder name
SPECIES_MAP = {
    name: {"botanical": bot, "ayurvedic": ayu, "priority": pri}
    for name, bot, ayu, pri in SPECIES
}

# Dataset requirements
TOTAL_IMAGES_TARGET = 25000
MIN_IMAGES = 150
CRITICAL_THRESHOLD = 10

if __name__ == "__main__":
    print(f"Total species: {len(SPECIES)}")
    print(f"  HIGH:   {len(HIGH_PRIORITY)}")
    print(f"  MEDIUM: {len(MEDIUM_PRIORITY)}")
    print(f"  LOW:    {len(LOW_PRIORITY)}")

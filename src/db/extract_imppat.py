import json
import os

def generate_data():
    """Generates Ayurvedic knowledge base data for all major medicinal plants with multi-language support."""
    
    plants = [
        # 1. Neem
        {
            "species_name": "Azadirachta indica",
            "botanical_name": "Azadirachta indica A. Juss.",
            "common_name": "Neem",
            "common_names": {
                "en": "Neem (Indian Lilac)",
                "hi": "नीम (Neem)",
                "kn": "ಬೇವು (Bevu)",
                "ta": "வேம்பு (Vembu)",
                "te": "వేప (Vepa)",
                "ml": "ആര്യവേപ്പ് (Aryaveppu)"
            },
            "family": "Meliaceae",
            "region": "Throughout India",
            "habitat": "Tropical and subtropical regions",
            "profile": {
                "dosha_effect": "Balances Pitta and Kapha",
                "rasa": "Tikta (Bitter), Kashaya (Astringent)",
                "guna": "Laghu (Light), Ruksha (Dry)",
                "virya": "Sheeta (Cold)",
                "vipaka": "Katu (Pungent)",
                "prabhava": "Krimighna (Anti-microbial)"
            },
            "uses": [
                {"condition": "Skin disorders", "use_description": "Used for acne, eczema, fungal infections, and wound healing.", "classical_reference": "Charaka Samhita"},
                {"condition": "Fever", "use_description": "Used in bitter decoctions for reducing viral and malaria fevers.", "classical_reference": "Sushruta Samhita"},
                {"condition": "Dental hygiene", "use_description": "Twigs used as natural toothbrushes to prevent gingivitis.", "classical_reference": "Bhavaprakasha"}
            ],
            "phytochemicals": [
                {"compound_name": "Azadirachtin", "compound_class": "Limonoid", "pubchem_id": "5281303", "activity": "Insecticidal, anti-inflammatory"},
                {"compound_name": "Nimbin", "compound_class": "Triterpenoid", "pubchem_id": "101683", "activity": "Anti-inflammatory, anti-pyretic"}
            ],
            "contraindications": [
                {"condition": "Pregnancy", "severity": "High", "notes": "May possess abortifacient properties. Avoid during conception."}
            ]
        },
        # 2. Tulsi
        {
            "species_name": "Ocimum tenuiflorum",
            "botanical_name": "Ocimum tenuiflorum L.",
            "common_name": "Tulsi",
            "common_names": {
                "en": "Tulsi (Holy Basil)",
                "hi": "तुलसी (Tulsi)",
                "kn": "ತುಳಸಿ (Tulasi)",
                "ta": "துளசி (Thulasi)",
                "te": "తులసి (Tulasi)",
                "ml": "തുളസി (Thulasi)"
            },
            "family": "Lamiaceae",
            "region": "Throughout India",
            "habitat": "Cultivated across plains and home gardens",
            "profile": {
                "dosha_effect": "Balances Vata and Kapha",
                "rasa": "Katu (Pungent), Tikta (Bitter)",
                "guna": "Laghu (Light), Ruksha (Dry)",
                "virya": "Ushna (Hot)",
                "vipaka": "Katu (Pungent)",
                "prabhava": "Vishaghna (Anti-toxic)"
            },
            "uses": [
                {"condition": "Cough and Cold", "use_description": "Expectorant for respiratory conditions, bronchitis, and asthma.", "classical_reference": "Charaka Samhita"},
                {"condition": "Immunity and Stress", "use_description": "Adaptogenic herb that boosts resistance against stress.", "classical_reference": "Ayurvedic Pharmacopoeia"}
            ],
            "phytochemicals": [
                {"compound_name": "Eugenol", "compound_class": "Phenylpropene", "pubchem_id": "3314", "activity": "Analgesic, anti-inflammatory"}
            ],
            "contraindications": [
                {"condition": "Bleeding disorders", "severity": "Moderate", "notes": "May slow blood clotting in high doses."}
            ]
        },
        # 3. Ashwagandha
        {
            "species_name": "Withania somnifera",
            "botanical_name": "Withania somnifera (L.) Dunal",
            "common_name": "Ashwagandha",
            "common_names": {
                "en": "Ashwagandha (Indian Ginseng)",
                "hi": "अश्वगंधा (Ashwagandha)",
                "kn": "ಅಶ್ವಗಂಧ (Ashwagandha)",
                "ta": "அமுக்கிரா (Amukkira)",
                "te": "అశ్వగంధ (Ashwagandha)",
                "ml": "അമുക്കുരം (Amukkuram)"
            },
            "family": "Solanaceae",
            "region": "Drier parts of India",
            "habitat": "Dry and sub-tropical regions",
            "profile": {
                "dosha_effect": "Balances Vata and Kapha",
                "rasa": "Tikta (Bitter), Katu (Pungent), Madhura (Sweet)",
                "guna": "Laghu (Light), Snigdha (Unctuous)",
                "virya": "Ushna (Hot)",
                "vipaka": "Madhura (Sweet)",
                "prabhava": "Rasayana (Rejuvenative)"
            },
            "uses": [
                {"condition": "Anxiety and Stress", "use_description": "Powerful adaptogen to relieve chronic stress and cortisol levels.", "classical_reference": "Charaka Samhita"},
                {"condition": "Vitality and Strength", "use_description": "Enhances muscular strength, vitality, and stamina (Bala).", "classical_reference": "Sushruta Samhita"}
            ],
            "phytochemicals": [
                {"compound_name": "Withaferin A", "compound_class": "Steroidal lactone", "pubchem_id": "265237", "activity": "Anti-inflammatory, anti-tumor"}
            ],
            "contraindications": [
                {"condition": "Pregnancy", "severity": "High", "notes": "Avoid high therapeutic doses during pregnancy."}
            ]
        },
        # 4. Brahmi
        {
            "species_name": "Bacopa monnieri",
            "botanical_name": "Bacopa monnieri (L.) Wettst.",
            "common_name": "Brahmi",
            "common_names": {
                "en": "Brahmi (Water Hyssop)",
                "hi": "ब्राह्मी (Brahmi)",
                "kn": "ಬ್ರಾಹ್ಮೀ (Brahmi)",
                "ta": "பிராமி (Brahmi)",
                "te": "బ్రాహ్మి (Brahmi)",
                "ml": "ബ്രഹ്മി (Brahmi)"
            },
            "family": "Plantaginaceae",
            "region": "Wet, tropical environments",
            "habitat": "Marshy areas throughout India",
            "profile": {
                "dosha_effect": "Balances Vata, Pitta, and Kapha",
                "rasa": "Tikta (Bitter), Kashaya (Astringent)",
                "guna": "Laghu (Light)",
                "virya": "Sheeta (Cold)",
                "vipaka": "Madhura (Sweet)",
                "prabhava": "Medhya (Brain Tonic)"
            },
            "uses": [
                {"condition": "Memory loss", "use_description": "Enhances cognitive function, concentration, and intellect.", "classical_reference": "Sushruta Samhita"},
                {"condition": "Anxiety and Insomnia", "use_description": "Calms the nervous system and promotes peaceful sleep.", "classical_reference": "Charaka Samhita"}
            ],
            "phytochemicals": [
                {"compound_name": "Bacoside A", "compound_class": "Saponin", "pubchem_id": "119794", "activity": "Neuroprotective, memory-enhancing"}
            ],
            "contraindications": [
                {"condition": "Bradycardia", "severity": "Low", "notes": "May slightly reduce heart rate."}
            ]
        },
        # 5. Aloe Vera
        {
            "species_name": "Aloe barbadensis",
            "botanical_name": "Aloe vera (L.) Burm.f.",
            "common_name": "Aloe Vera",
            "common_names": {
                "en": "Aloe Vera (Ghritkumari)",
                "hi": "घृतकुमारी / एलोवेरा (Ghritkumari)",
                "kn": "ಲೋಳೆಸರ (Lolesara)",
                "ta": "கற்றாழை (Kattralai)",
                "te": "కలబంద (Kalabanda)",
                "ml": "കറ്റാർവാഴ (Kattarvazha)"
            },
            "family": "Asphodelaceae",
            "region": "Dry and coastal regions",
            "habitat": "Cultivated widely across arid zones",
            "profile": {
                "dosha_effect": "Balances all three doshas (Tridoshic)",
                "rasa": "Tikta (Bitter), Madhura (Sweet)",
                "guna": "Guru (Heavy), Snigdha (Unctuous), Picchila (Slimy)",
                "virya": "Sheeta (Cold)",
                "vipaka": "Madhura (Sweet)",
                "prabhava": "Rasayana (Rejuvenative)"
            },
            "uses": [
                {"condition": "Burns and wounds", "use_description": "Topical application speeds epithelial healing and cools inflammation.", "classical_reference": "Bhavaprakasha"},
                {"condition": "Digestive disorders", "use_description": "Soothes acid reflux and gently cleanses the bowels.", "classical_reference": "Ayurvedic Pharmacopoeia"}
            ],
            "phytochemicals": [
                {"compound_name": "Aloin", "compound_class": "Anthraquinone", "pubchem_id": "100234", "activity": "Laxative, soothing"}
            ],
            "contraindications": [
                {"condition": "Pregnancy", "severity": "High", "notes": "Oral consumption of yellow latex can cause uterine contractions."}
            ]
        },
        # 6. Turmeric
        {
            "species_name": "Curcuma longa",
            "botanical_name": "Curcuma longa L.",
            "common_name": "Turmeric",
            "common_names": {
                "en": "Turmeric (Haldi)",
                "hi": "हल्दी (Haldi)",
                "kn": "ಅರಿಶಿನ (Arishina)",
                "ta": "மஞ்சள் (Manjal)",
                "te": "పసుపు (Pasupu)",
                "ml": "മഞ്ഞൾ (Manjal)"
            },
            "family": "Zingiberaceae",
            "region": "Tropical India",
            "habitat": "Cultivated extensively across warm plains",
            "profile": {
                "dosha_effect": "Balances Vata, Pitta, and Kapha",
                "rasa": "Tikta (Bitter), Katu (Pungent)",
                "guna": "Ruksha (Dry), Laghu (Light)",
                "virya": "Ushna (Hot)",
                "vipaka": "Katu (Pungent)",
                "prabhava": "Krimighna (Anti-microbial)"
            },
            "uses": [
                {"condition": "Inflammation and Joint Pain", "use_description": "Reduces joint inflammation and arthritic swelling.", "classical_reference": "Charaka Samhita"},
                {"condition": "Wounds and Cuts", "use_description": "Antiseptic powder for preventing infection on fresh lacerations.", "classical_reference": "Sushruta Samhita"}
            ],
            "phytochemicals": [
                {"compound_name": "Curcumin", "compound_class": "Curcuminoid", "pubchem_id": "969516", "activity": "Anti-inflammatory, antioxidant"}
            ],
            "contraindications": [
                {"condition": "Gallstones", "severity": "Moderate", "notes": "May stimulate gallbladder contractions."}
            ]
        },
        # 7. Ginger
        {
            "species_name": "Zingiber officinale",
            "botanical_name": "Zingiber officinale Roscoe",
            "common_name": "Ginger",
            "common_names": {
                "en": "Ginger (Adrak / Shunthi)",
                "hi": "अदरक / सोंठ (Adrak)",
                "kn": "ಶುಂಠಿ (Shunti)",
                "ta": "இஞ்சி / சுக்கு (Inji)",
                "te": "అల్లం / శొంఠి (Allam)",
                "ml": "ഇഞ്ചി / ചുക്ക് (Inchi)"
            },
            "family": "Zingiberaceae",
            "region": "Throughout India",
            "habitat": "Cultivated in moist tropical areas",
            "profile": {
                "dosha_effect": "Balances Vata and Kapha",
                "rasa": "Katu (Pungent)",
                "guna": "Laghu (Light), Snigdha (Unctuous)",
                "virya": "Ushna (Hot)",
                "vipaka": "Madhura (Sweet)",
                "prabhava": "Deepana (Digestive Stimulant)"
            },
            "uses": [
                {"condition": "Indigestion and Bloating", "use_description": "Kindles digestive fire (Agni) and expels intestinal gas.", "classical_reference": "Charaka Samhita"},
                {"condition": "Nausea and Morning Sickness", "use_description": "Soothes motion sickness and nausea safely.", "classical_reference": "Bhavaprakasha"}
            ],
            "phytochemicals": [
                {"compound_name": "Gingerol", "compound_class": "Phenol", "pubchem_id": "442793", "activity": "Anti-emetic, anti-inflammatory"}
            ],
            "contraindications": [
                {"condition": "Bleeding disorders", "severity": "Low", "notes": "May inhibit platelet aggregation in large doses."}
            ]
        },
        # 8. Moringa
        {
            "species_name": "Moringa oleifera",
            "botanical_name": "Moringa oleifera Lam.",
            "common_name": "Moringa",
            "common_names": {
                "en": "Moringa (Drumstick Tree)",
                "hi": "सहजन (Sahjan / Moringa)",
                "kn": "ನುಗ್ಗೆಕಾಯಿ (Nuggekayi)",
                "ta": "முருங்கை (Murungai)",
                "te": "మునగ (Munaga)",
                "ml": "മുരിങ്ങ (Muringa)"
            },
            "family": "Moringaceae",
            "region": "Sub-Himalayan tracts and throughout India",
            "habitat": "Wild and cultivated across tropics",
            "profile": {
                "dosha_effect": "Balances Kapha and Vata",
                "rasa": "Katu (Pungent), Tikta (Bitter)",
                "guna": "Laghu (Light), Ruksha (Dry), Teekshna (Sharp)",
                "virya": "Ushna (Hot)",
                "vipaka": "Katu (Pungent)",
                "prabhava": "Krimighna (Anti-microbial)"
            },
            "uses": [
                {"condition": "Malnutrition and Fatigue", "use_description": "Nutrient powerhouse rich in iron, calcium, and bioavailable vitamins.", "classical_reference": "Ayurvedic Pharmacopoeia"},
                {"condition": "Joint pain and Gout", "use_description": "Pappu and leaf soup used to relieve chronic arthritis.", "classical_reference": "Sushruta Samhita"}
            ],
            "phytochemicals": [
                {"compound_name": "Quercetin", "compound_class": "Flavonoid", "pubchem_id": "5280343", "activity": "Antioxidant"}
            ],
            "contraindications": [
                {"condition": "Pregnancy", "severity": "High", "notes": "Avoid root and bark extracts during pregnancy."}
            ]
        },
        # 9. Amla
        {
            "species_name": "Phyllanthus emblica",
            "botanical_name": "Phyllanthus emblica L.",
            "common_name": "Amla",
            "common_names": {
                "en": "Amla (Indian Gooseberry)",
                "hi": "आंवला (Amla)",
                "kn": "ನೆಲ್ಲಿಕಾಯಿ (Nellikayi)",
                "ta": "நெல்லிக்காய் (Nellikai)",
                "te": "ఉసిరి (Usiri)",
                "ml": "നെല്ലിക്ക (Nellikka)"
            },
            "family": "Phyllanthaceae",
            "region": "Deciduous forests of India",
            "habitat": "Wild and cultivated across plains",
            "profile": {
                "dosha_effect": "Balances all three doshas (Tridoshic)",
                "rasa": "Amla (Sour), Madhura (Sweet), Tikta (Bitter), Kashaya (Astringent), Katu (Pungent)",
                "guna": "Guru (Heavy), Sheeta (Cold)",
                "virya": "Sheeta (Cold)",
                "vipaka": "Madhura (Sweet)",
                "prabhava": "Rasayana (Rejuvenative)"
            },
            "uses": [
                {"condition": "Immunity and Longevity", "use_description": "Supreme source of natural Vitamin C and rejuvenating antioxidant.", "classical_reference": "Charaka Samhita"},
                {"condition": "Hair loss and Greying", "use_description": "Nourishes scalp and prevents premature greying.", "classical_reference": "Bhavaprakasha"}
            ],
            "phytochemicals": [
                {"compound_name": "Gallic Acid", "compound_class": "Phenolic Acid", "pubchem_id": "370", "activity": "Antioxidant, anti-inflammatory"}
            ],
            "contraindications": [
                {"condition": "Hypoglycemia", "severity": "Low", "notes": "May potentiate insulin action; monitor blood sugar."}
            ]
        },
        # 10. Bael
        {
            "species_name": "Aegle marmelos",
            "botanical_name": "Aegle marmelos (L.) Corrêa",
            "common_name": "Bael",
            "common_names": {
                "en": "Bael (Bilva / Golden Apple)",
                "hi": "बेल / बिल्व (Bael / Bilva)",
                "kn": "ಬೇಲ (Bela)",
                "ta": "வில்வம் (Vilvam)",
                "te": "మారేడు (Maredu)",
                "ml": "കൂവളം (Koovalam)"
            },
            "family": "Rutaceae",
            "region": "Dry forests across India",
            "habitat": "Wild and cultivated near sacred groves",
            "profile": {
                "dosha_effect": "Balances Vata and Kapha",
                "rasa": "Kashaya (Astringent), Tikta (Bitter)",
                "guna": "Laghu (Light), Ruksha (Dry)",
                "virya": "Ushna (Hot)",
                "vipaka": "Katu (Pungent)",
                "prabhava": "Grahi (Bowel-binding)"
            },
            "uses": [
                {"condition": "Diarrhea and IBS", "use_description": "Unripe fruit pulp heals mucosal lining and controls chronic dysentery.", "classical_reference": "Charaka Samhita"},
                {"condition": "Diabetes", "use_description": "Leaf extract helps maintain healthy blood glucose levels.", "classical_reference": "Ayurvedic Pharmacopoeia"}
            ],
            "phytochemicals": [
                {"compound_name": "Marmelosin", "compound_class": "Coumarin", "pubchem_id": "31405", "activity": "Anthelmintic, anti-bacterial"}
            ],
            "contraindications": [
                {"condition": "Severe Constipation", "severity": "Moderate", "notes": "Astringent properties can aggravate dry constipation."}
            ]
        },
        # 11. Aparajita
        {
            "species_name": "Clitoria ternatea",
            "botanical_name": "Clitoria ternatea L.",
            "common_name": "Aparajita",
            "common_names": {
                "en": "Aparajita (Butterfly Pea)",
                "hi": "अपराजिता (Aparajita)",
                "kn": "ಶಂಖಪುಷ್ಪ (Shankhapushpa)",
                "ta": "சங்குப்பூ (Sangupoo)",
                "te": "శంఖపుష్పం (Shankhapushpam)",
                "ml": "ശംഖുപുഷ്പം (Shankhupushpam)"
            },
            "family": "Fabaceae",
            "region": "Tropical India",
            "habitat": "Climbing vine in moist and sunny areas",
            "profile": {
                "dosha_effect": "Balances all three doshas (Tridoshic)",
                "rasa": "Kashaya (Astringent), Tikta (Bitter)",
                "guna": "Laghu (Light), Ruksha (Dry)",
                "virya": "Sheeta (Cold)",
                "vipaka": "Katu (Pungent)",
                "prabhava": "Medhya (Brain Tonic)"
            },
            "uses": [
                {"condition": "Memory and Brain Health", "use_description": "Used as a Medhya Rasayana to enhance mental clarity and intellect.", "classical_reference": "Charaka Samhita"},
                {"condition": "Anxiety and Depression", "use_description": "Blue tea infused with flowers relieves neural exhaustion.", "classical_reference": "Bhavaprakasha"}
            ],
            "phytochemicals": [
                {"compound_name": "Ternatins", "compound_class": "Anthocyanin", "pubchem_id": "44259648", "activity": "Antioxidant, Neuroprotective"}
            ],
            "contraindications": [
                {"condition": "Pregnancy", "severity": "Moderate", "notes": "Use under guidance due to mild uterine stimulating potential."}
            ]
        },
        # 12. Giloy (Crucial for User's scan test!)
        {
            "species_name": "Tinospora cordifolia",
            "botanical_name": "Tinospora cordifolia (Willd.) Miers",
            "common_name": "Giloy",
            "common_names": {
                "en": "Giloy (Guduchi / Amrita)",
                "hi": "गिलोय / गुडूची (Giloy)",
                "kn": "ಅಮೃತಬಳ್ಳಿ (Amrutha Valli)",
                "ta": "சீந்தில் (Seenthil)",
                "te": "తిప్పతీగ (Tippa Teega)",
                "ml": "ചിറ്റമൃത് (Chittamruth)"
            },
            "family": "Menispermaceae",
            "region": "Throughout tropical India",
            "habitat": "Climbing shrub found on trees like Neem and Mango",
            "profile": {
                "dosha_effect": "Balances all three doshas (Tridoshic)",
                "rasa": "Tikta (Bitter), Kashaya (Astringent)",
                "guna": "Guru (Heavy), Snigdha (Unctuous)",
                "virya": "Ushna (Hot)",
                "vipaka": "Madhura (Sweet)",
                "prabhava": "Rasayana (Immunity Booster)"
            },
            "uses": [
                {"condition": "Chronic Fever and Dengue", "use_description": "Boosts blood platelet count and relieves recurrent febrile conditions.", "classical_reference": "Charaka Samhita"},
                {"condition": "Immunity and Allergy", "use_description": "Purifies blood, regulates immune response, and acts as cellular shield.", "classical_reference": "Sushruta Samhita"},
                {"condition": "Diabetes", "use_description": "Helps modulate glucose metabolism and prevents diabetic complications.", "classical_reference": "Bhavaprakasha"}
            ],
            "phytochemicals": [
                {"compound_name": "Tinosporide", "compound_class": "Diterpene", "pubchem_id": "141416", "activity": "Immunomodulatory, hepatoprotective"},
                {"compound_name": "Berberine", "compound_class": "Alkaloid", "pubchem_id": "2353", "activity": "Anti-microbial, anti-inflammatory"}
            ],
            "contraindications": [
                {"condition": "Autoimmune conditions", "severity": "Moderate", "notes": "Since it stimulates immunity, monitor in severe autoimmune disorders."}
            ]
        },
        # 13. Shatavari
        {
            "species_name": "Asparagus racemosus",
            "botanical_name": "Asparagus racemosus Willd.",
            "common_name": "Shatavari",
            "common_names": {
                "en": "Shatavari (Asparagus)",
                "hi": "शतावरी (Shatavari)",
                "kn": "ಶತಾವರಿ (Shatavari)",
                "ta": "சதாவரி (Thaneervittan)",
                "te": "శతావరి (Shatavari)",
                "ml": "ശതാവരി (Shatavari)"
            },
            "family": "Asparagaceae",
            "region": "Throughout tropical India",
            "habitat": "Rocky and low forest regions",
            "profile": {
                "dosha_effect": "Balances Vata and Pitta",
                "rasa": "Madhura (Sweet), Tikta (Bitter)",
                "guna": "Guru (Heavy), Snigdha (Unctuous)",
                "virya": "Sheeta (Cold)",
                "vipaka": "Madhura (Sweet)",
                "prabhava": "Rasayana (Female Reproductive Tonic)"
            },
            "uses": [
                {"condition": "Hormonal Balance", "use_description": "Supports female reproductive health, lactation, and menopause harmony.", "classical_reference": "Charaka Samhita"},
                {"condition": "Gastric Ulcers and Acidity", "use_description": "Soothes inflamed stomach lining and neutralizes excessive acid.", "classical_reference": "Sushruta Samhita"}
            ],
            "phytochemicals": [
                {"compound_name": "Shatavarin", "compound_class": "Steroidal saponin", "pubchem_id": "101968848", "activity": "Immunomodulatory, galactagogue"}
            ],
            "contraindications": [
                {"condition": "Kidney disorders", "severity": "Low", "notes": "Acts as a mild diuretic; consult doctor if on diuretics."}
            ]
        },
        # 14. Jamun
        {
            "species_name": "Syzygium cumini",
            "botanical_name": "Syzygium cumini (L.) Skeels",
            "common_name": "Jamun",
            "common_names": {
                "en": "Jamun (Black Plum)",
                "hi": "जामुन (Jamun)",
                "kn": "ನೇರಳೆ (Nerale)",
                "ta": "நாவல் (Naval)",
                "te": "నేరేడు (Neredu)",
                "ml": "ഞാവൽ (Njaval)"
            },
            "family": "Myrtaceae",
            "region": "Throughout Indian subcontinent",
            "habitat": "Riverbanks and tropical evergreen forests",
            "profile": {
                "dosha_effect": "Balances Pitta and Kapha",
                "rasa": "Kashaya (Astringent), Madhura (Sweet), Amla (Sour)",
                "guna": "Laghu (Light), Ruksha (Dry)",
                "virya": "Sheeta (Cold)",
                "vipaka": "Katu (Pungent)",
                "prabhava": "Mutrasangrahaniya (Reduces excess urination)"
            },
            "uses": [
                {"condition": "Diabetes Mellitus", "use_description": "Seed kernel powder lowers blood sugar and checks polyuria.", "classical_reference": "Charaka Samhita"},
                {"condition": "Diarrhea and Gum Health", "use_description": "Bark decoction tightens loose stools and treats bleeding gums.", "classical_reference": "Bhavaprakasha"}
            ],
            "phytochemicals": [
                {"compound_name": "Jamboline", "compound_class": "Glycoside", "pubchem_id": "5281855", "activity": "Anti-hyperglycemic"}
            ],
            "contraindications": [
                {"condition": "Fasting / Empty Stomach", "severity": "Low", "notes": "Do not consume large amounts on empty stomach."}
            ]
        },
        # 15. Adulsa / Vasaka
        {
            "species_name": "Justicia adhatoda",
            "botanical_name": "Justicia adhatoda L.",
            "common_name": "Adulsa",
            "common_names": {
                "en": "Adulsa (Vasaka / Malabar Nut)",
                "hi": "अडूसा / वासा (Adulsa / Vasa)",
                "kn": "ಆಡುಸೋಗೆ (Adusoge)",
                "ta": "ஆடாதோடை (Adathodai)",
                "te": "అడ్డసరం (Addasaram)",
                "ml": "ആടലോടകം (Adalodakam)"
            },
            "family": "Acanthaceae",
            "region": "Plains and lower Himalayas",
            "habitat": "Wild shrub along roadsides and waste grounds",
            "profile": {
                "dosha_effect": "Balances Pitta and Kapha",
                "rasa": "Tikta (Bitter), Kashaya (Astringent)",
                "guna": "Laghu (Light), Ruksha (Dry)",
                "virya": "Sheeta (Cold)",
                "vipaka": "Katu (Pungent)",
                "prabhava": "Kasa-shwasahara (Bronchodilator)"
            },
            "uses": [
                {"condition": "Severe Cough and Asthma", "use_description": "Dilates bronchial passages and expels thick phlegm.", "classical_reference": "Charaka Samhita"},
                {"condition": "Bleeding Disorders", "use_description": "Hemostatic herb for epistaxis (nosebleeds) and hemoptysis.", "classical_reference": "Sushruta Samhita"}
            ],
            "phytochemicals": [
                {"compound_name": "Vasicine", "compound_class": "Quinazoline alkaloid", "pubchem_id": "8935", "activity": "Bronchodilator, expectorant"}
            ],
            "contraindications": [
                {"condition": "Pregnancy", "severity": "High", "notes": "Uterotonic alkaloid; contraindicated in pregnancy."}
            ]
        },
        # 16. Bhringraj
        {
            "species_name": "Eclipta prostrata",
            "botanical_name": "Eclipta prostrata (L.) L.",
            "common_name": "Bhringraj",
            "common_names": {
                "en": "Bhringraj (False Daisy)",
                "hi": "भृंगराज (Bhringraj)",
                "kn": "ಗರಿಗ (Gariga)",
                "ta": "கரிசலாங்கண்ணி (Karisalanganni)",
                "te": "గుంటగలగర (Guntagalagara)",
                "ml": "കയ്യോന്നി (Kayyonni)"
            },
            "family": "Asteraceae",
            "region": "Throughout India",
            "habitat": "Moist soil, rice fields, and canal borders",
            "profile": {
                "dosha_effect": "Balances Vata and Kapha",
                "rasa": "Katu (Pungent), Tikta (Bitter)",
                "guna": "Ruksha (Dry), Laghu (Light)",
                "virya": "Ushna (Hot)",
                "vipaka": "Katu (Pungent)",
                "prabhava": "Keshya (Hair Rejuvenator)"
            },
            "uses": [
                {"condition": "Hair Fall and Alopecia", "use_description": "Oil massaged into scalp stops baldness and deepens natural hair color.", "classical_reference": "Charaka Samhita"},
                {"condition": "Liver Disorders and Jaundice", "use_description": "Protects hepatocytes and optimizes bile secretion.", "classical_reference": "Bhavaprakasha"}
            ],
            "phytochemicals": [
                {"compound_name": "Wedelolactone", "compound_class": "Coumestan", "pubchem_id": "5281812", "activity": "Hepatoprotective, hair follicle stimulant"}
            ],
            "contraindications": [
                {"condition": "Low Blood Pressure", "severity": "Low", "notes": "May mildly lower blood pressure."}
            ]
        }
    ]

    output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "ayurvedic_knowledge.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(plants, f, indent=4, ensure_ascii=False)
        
    print(f"Enriched Ayurvedic database ({len(plants)} plants) created successfully at {output_file}")

if __name__ == "__main__":
    generate_data()

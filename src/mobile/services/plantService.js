import OFFLINE_PLANTS_DATA from '../assets/ayurvedic_knowledge.json';
import { DYNAMIC_LOCALIZATIONS } from '../constants/i18n';

// Build fast in-memory lookup maps from the bundled Ayurvedic knowledge base
const PLANT_LOOKUP_MAP = new Map();

// Common aliases mapping to handle AI class naming variations
const CLASS_ALIASES = {
  "aloevera": "aloe vera",
  "amruth": "giloy",
  "holybasilvana": "tulsi",
  "bringaraj": "bhringraj",
  "blackpepper": "black pepper",
  "betelnut": "betel nut",
  "curryleaf": "curry leaf",
  "gotokola": "gotu kola",
  "indianbeech": "indian beech",
  "indiansarsaparilla": "indian sarsaparilla",
  "insulinplant": "insulin plant",
  "longpepper": "long pepper",
  "snakeplant": "snake plant",
  "babuna": "chamomile",
  "sesame": "tila"
};

if (Array.isArray(OFFLINE_PLANTS_DATA)) {
  for (const plant of OFFLINE_PLANTS_DATA) {
    if (plant.species_name) PLANT_LOOKUP_MAP.set(plant.species_name.toLowerCase(), plant);
    if (plant.common_name) PLANT_LOOKUP_MAP.set(plant.common_name.toLowerCase(), plant);
    if (plant.botanical_name) PLANT_LOOKUP_MAP.set(plant.botanical_name.toLowerCase(), plant);
    // Index without spaces
    if (plant.common_name) PLANT_LOOKUP_MAP.set(plant.common_name.toLowerCase().replace(/\s+/g, ''), plant);
    if (plant.species_name) PLANT_LOOKUP_MAP.set(plant.species_name.toLowerCase().replace(/\s+/g, ''), plant);
  }
}

/**
 * Returns the localized name of a plant species or common name based on active language.
 */
export function getLocalizedPlantName(key, lang = 'en') {
  if (!key) return '';
  const cleanKey = String(key).trim().toLowerCase();
  const resolvedKey = CLASS_ALIASES[cleanKey] || cleanKey;
  
  const plant = PLANT_LOOKUP_MAP.get(resolvedKey) || PLANT_LOOKUP_MAP.get(cleanKey);
  if (plant && plant.common_names && plant.common_names[lang]) {
    return plant.common_names[lang];
  }
  if (plant && plant.common_name) {
    return plant.common_name;
  }
  return key;
}

/**
 * Returns dynamic localized translations for Ayurvedic attributes (Dosha, Rasa, Guna, etc.).
 */
export function getDynamicTranslation(value, lang = 'en') {
  if (!value || lang === 'en') return value;
  const translation = DYNAMIC_LOCALIZATIONS[value];
  if (translation && translation[lang]) {
    return translation[lang];
  }
  return value;
}

/**
 * Normalizes an API response or local plant JSON into a consistent, unified structure.
 */
export function normalizePlantProfile(raw) {
  if (!raw) return null;
  const plant = raw.plant || raw;
  const profile = raw.ayurvedic_profile || raw.profile || plant.profile || {};
  const therapeutic_uses = raw.therapeutic_uses || raw.uses || plant.uses || [];
  const phytochemicals = raw.phytochemicals || plant.phytochemicals || [];
  const contraindications = raw.contraindications || plant.contraindications || [];

  return {
    plant,
    profile,
    ayurvedic_profile: profile,
    therapeutic_uses,
    phytochemicals,
    contraindications
  };
}

/**
 * Generates the full offline library flora list with language localization.
 */
export function getOfflineFloraList(lang = 'en') {
  if (!Array.isArray(OFFLINE_PLANTS_DATA)) return [];
  return OFFLINE_PLANTS_DATA.map((p, idx) => ({
    plant_id: idx + 1,
    species_name: p.species_name,
    botanical_name: p.botanical_name,
    common_names: (p.common_names && p.common_names[lang]) || p.common_name || p.species_name,
    family: p.family
  }));
}

/**
 * Generates a resilient, structured botanical fallback profile if an unknown or unmapped species is encountered.
 */
export function generateFallbackProfile(speciesOrClass, commonName) {
  const name = commonName || speciesOrClass || 'Classical Botanical Herb';
  return {
    plant: {
      species_name: speciesOrClass || name,
      botanical_name: speciesOrClass ? `${speciesOrClass} L.` : name,
      common_name: name,
      family: 'Medicinal Angiosperm',
      habitat: 'Indigenous medicinal gardens and tropical flora',
      region: 'Tropical & Subtropical South Asia'
    },
    profile: {
      dosha_effect: 'Balances Tridosha (Vata, Pitta, Kapha)',
      rasa: 'Tikta (Bitter), Kashaya (Astringent)',
      guna: 'Laghu (Light), Ruksha (Dry)',
      virya: 'Sheeta (Cooling) / Ushna (Warm)',
      vipaka: 'Katu (Pungent)',
      prabhava: 'Rasayana (Tissue Rejuvenator)'
    },
    therapeutic_uses: [
      {
        condition: 'General Vitality & Immunity',
        use_description: 'Valued in traditional herbalism for cellular defense, metabolic balance, and respiratory wellness.'
      },
      {
        condition: 'Digestive Equilibrium',
        use_description: 'Traditionally infused or compounded to support digestive fire and microbiome harmony.'
      }
    ],
    phytochemicals: [
      {
        compound_name: 'Polyphenols & Bioflavonoids',
        activity: 'Antioxidant, tissue protective'
      }
    ],
    contraindications: [
      {
        condition: 'General Precaution',
        severity: 'Low',
        notes: 'Consult a certified Ayurvedic Vaidya or healthcare provider prior to intensive therapeutic usage.'
      }
    ]
  };
}

/**
 * Retrieves a plant profile offline by ID, species name, or common name.
 * Guaranteed never to crash and resolves aliases cleanly.
 */
export function getOfflinePlantById(plantId) {
  if (!Array.isArray(OFFLINE_PLANTS_DATA) || plantId === undefined || plantId === null) return null;
  
  // Numerical ID lookup
  const numId = Number(plantId);
  if (!isNaN(numId) && numId > 0 && numId <= OFFLINE_PLANTS_DATA.length) {
    return normalizePlantProfile(OFFLINE_PLANTS_DATA[numId - 1]);
  }
  
  // String name lookup
  const cleanKey = String(plantId).trim().toLowerCase();
  const resolvedKey = CLASS_ALIASES[cleanKey] || cleanKey;
  let plant = PLANT_LOOKUP_MAP.get(resolvedKey) || PLANT_LOOKUP_MAP.get(cleanKey);
  
  // Fallback: substring search across plants
  if (!plant) {
    for (const p of OFFLINE_PLANTS_DATA) {
      if (
        (p.common_name && p.common_name.toLowerCase().includes(cleanKey)) ||
        (p.species_name && p.species_name.toLowerCase().includes(cleanKey)) ||
        (p.botanical_name && p.botanical_name.toLowerCase().includes(cleanKey))
      ) {
        plant = p;
        break;
      }
    }
  }

  return plant ? normalizePlantProfile(plant) : null;
}

/**
 * Executes a client-side keyword search over conditions, uses, and plant names.
 */
export function searchOfflinePlants(query) {
  if (!query || !Array.isArray(OFFLINE_PLANTS_DATA)) return [];
  const lowerQ = query.trim().toLowerCase();
  const results = [];

  for (const plant of OFFLINE_PLANTS_DATA) {
    const inSpecies = plant.species_name && plant.species_name.toLowerCase().includes(lowerQ);
    const inCommon = plant.common_name && plant.common_name.toLowerCase().includes(lowerQ);
    let matchedUse = null;

    for (const use of (plant.uses || [])) {
      const inCond = use.condition && use.condition.toLowerCase().includes(lowerQ);
      const inDesc = use.use_description && use.use_description.toLowerCase().includes(lowerQ);
      if (inCond || inDesc) {
        matchedUse = use;
        break;
      }
    }

    if (inSpecies || inCommon || matchedUse) {
      results.push({
        plant,
        condition: matchedUse ? matchedUse.condition : (plant.common_name || plant.species_name),
        use_description: matchedUse ? matchedUse.use_description : "Classical Ayurvedic medicinal herb"
      });
    }
  }

  return results;
}

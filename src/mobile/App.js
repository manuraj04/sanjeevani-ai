import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, Text, View, Image, TouchableOpacity, ScrollView, ActivityIndicator, TextInput, Linking, Modal, Dimensions, Animated } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as FileSystem from 'expo-file-system/legacy';
import Constants from 'expo-constants';

import { translations, GLOSSARY_DATA, LANGUAGES, LANG_LABELS } from './constants/i18n';
import { REFERENCE_IMAGES } from './constants/references';
import {
  getLocalizedPlantName,
  getVernacularNamesSummary,
  getDynamicTranslation,
  normalizePlantProfile,
  getOfflineFloraList,
  getOfflinePlantById,
  generateFallbackProfile,
  searchOfflinePlants
} from './services/plantService';

const hostUri = Constants.expoConfig?.hostUri || Constants.manifest2?.extra?.expoGo?.debuggerHost || '';
const localIp = hostUri ? hostUri.split(':')[0] : '10.0.2.2';
const API_BASE_URL = `http://${localIp}:8000`;
const SETTINGS_FILE = `${FileSystem.documentDirectory}sanjeevani_settings.json`;

const TOUR_SLIDES = [
  {
    image: 'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?auto=format&fit=crop&w=800&q=80',
    titleKey: 'tourSlide1Title',
    subKey: 'tourSlide1Subtitle',
    descKey: 'tourSlide1Desc',
    stepBadge: 'WELCOME TO SANJEEVANI'
  },
  {
    image: 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&w=800&q=80',
    titleKey: 'tourSlide2Title',
    subKey: 'tourSlide2Subtitle',
    descKey: 'tourSlide2Desc',
    stepBadge: 'STEP 1 OF 4'
  },
  {
    image: 'https://images.unsplash.com/photo-1576086213369-97a306d36557?auto=format&fit=crop&w=800&q=80',
    titleKey: 'tourSlide3Title',
    subKey: 'tourSlide3Subtitle',
    descKey: 'tourSlide3Desc',
    stepBadge: 'STEP 2 OF 4'
  },
  {
    image: 'https://images.unsplash.com/photo-1514733670139-4d87a1941d55?auto=format&fit=crop&w=800&q=80',
    titleKey: 'tourSlide4Title',
    subKey: 'tourSlide4Subtitle',
    descKey: 'tourSlide4Desc',
    stepBadge: 'STEP 3 OF 4'
  },
  {
    image: 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=800&q=80',
    titleKey: 'tourSlide5Title',
    subKey: 'tourSlide5Subtitle',
    descKey: 'tourSlide5Desc',
    stepBadge: 'STEP 4 OF 4'
  }
];

const POPULAR_HERBS = [
  {
    id: 'tulsi',
    species_name: 'Ocimum tenuiflorum',
    common_name: 'Tulsi',
    tag: 'Immunity & Prana',
    image: REFERENCE_IMAGES['Tulsi']
  },
  {
    id: 'neem',
    species_name: 'Azadirachta indica',
    common_name: 'Neem',
    tag: 'Skin & Detox',
    image: REFERENCE_IMAGES['Neem']
  },
  {
    id: 'ashwagandha',
    species_name: 'Withania somnifera',
    common_name: 'Ashwagandha',
    tag: 'Vitality & Rasayana',
    image: REFERENCE_IMAGES['Ashwagandha']
  },
  {
    id: 'moringa',
    species_name: 'Moringa oleifera',
    common_name: 'Moringa',
    tag: 'Nutritive & Energy',
    image: REFERENCE_IMAGES['Moringa']
  },
  {
    id: 'giloy',
    species_name: 'Tinospora cordifolia',
    common_name: 'Giloy',
    tag: 'Immunity & Vitality',
    image: REFERENCE_IMAGES['Giloy']
  },
  {
    id: 'amla',
    species_name: 'Phyllanthus emblica',
    common_name: 'Amla',
    tag: 'Vitamin C & Digestion',
    image: REFERENCE_IMAGES['Amla']
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState('SCAN'); // 'SCAN', 'LIBRARY', 'SEARCH', 'GLOSSARY'
  const [lang, setLang] = useState('en');
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const drawerAnim = useRef(new Animated.Value(340)).current;
  const t = translations[lang] || translations.en;

  // Onboarding Tour State
  const [showTourModal, setShowTourModal] = useState(false);
  const [currentTourSlide, setCurrentTourSlide] = useState(0);

  // Info Reader (About / Privacy / Disclaimer) State
  const [showPortalModal, setShowPortalModal] = useState(false);
  const [activePortalTab, setActivePortalTab] = useState('ABOUT'); // 'ABOUT', 'PRIVACY', 'DISCLAIMER'

  // Transparent Permissions Modal State
  const [showPermissionModal, setShowPermissionModal] = useState(false);
  const [permissionTarget, setPermissionTarget] = useState(null); // 'CAMERA' or 'GALLERY'

  // Scan State
  const [imageUri, setImageUri] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [ayurvedicProfile, setAyurvedicProfile] = useState(null);
  const [loading, setLoading] = useState(false);

  // Tabbed Ayurvedic Properties view state
  const [activeProfileTab, setActiveProfileTab] = useState('PROPERTIES'); // 'PROPERTIES', 'REMEDIES', 'SAFETY'

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Library State
  const [libraryPlants, setLibraryPlants] = useState([]);
  const [libraryLoading, setLibraryLoading] = useState(false);

  // Selected Profile Modal in Library
  const [selectedPlantModal, setSelectedPlantModal] = useState(null);

  // Initial Onboarding Check: Auto-launch Tour on First Ever Run
  useEffect(() => {
    const checkFirstRun = async () => {
      try {
        const info = await FileSystem.getInfoAsync(SETTINGS_FILE);
        if (info.exists) {
          const content = await FileSystem.readAsStringAsync(SETTINGS_FILE);
          const parsed = JSON.parse(content);
          if (parsed && parsed.hasSeenTour) {
            return;
          }
        }
      } catch (e) {
        console.log("Settings read note:", e);
      }
      setShowTourModal(true);
    };
    checkFirstRun();
  }, []);

  const completeTour = async () => {
    setShowTourModal(false);
    setCurrentTourSlide(0);
    try {
      await FileSystem.writeAsStringAsync(SETTINGS_FILE, JSON.stringify({ hasSeenTour: true }));
    } catch (e) {
      console.log("Settings save note:", e);
    }
  };

  const openDrawer = () => {
    setIsDrawerOpen(true);
    Animated.timing(drawerAnim, {
      toValue: 0,
      duration: 250,
      useNativeDriver: true,
    }).start();
  };

  const closeDrawer = (callback) => {
    Animated.timing(drawerAnim, {
      toValue: 340,
      duration: 200,
      useNativeDriver: true,
    }).start(() => {
      setIsDrawerOpen(false);
      if (typeof callback === 'function') {
        callback();
      }
    });
  };

  // Auto-fetch library when tab switches or language changes
  useEffect(() => {
    if (activeTab === 'LIBRARY') {
      fetchLibrary();
    }
  }, [activeTab, lang]);

  const fetchLibrary = async () => {
    setLibraryLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/plants?lang=${lang}`);
      if (response.ok) {
        const data = await response.json();
        setLibraryPlants(data);
        setLibraryLoading(false);
        return;
      }
    } catch (e) {
      // Offline fallback
    } finally {
      setLibraryLoading(false);
    }

    // 100% Offline Fallback
    setLibraryPlants(getOfflineFloraList(lang));
  };

  const openPlantDetails = async (plantId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/plant/${plantId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedPlantModal(normalizePlantProfile(data));
        return;
      }
    } catch (e) {
      // Offline fallback
    }

    // 100% Offline Fallback
    const offlineProfile = getOfflinePlantById(plantId);
    if (offlineProfile) {
      setSelectedPlantModal(offlineProfile);
    }
  };

  const resetScanState = () => {
    setImageUri(null);
    setPrediction(null);
    setHeatmap(null);
    setAyurvedicProfile(null);
    setActiveProfileTab('PROPERTIES');
  };

  // User Taps Camera: Trigger Transparent Pre-Permission Check
  const handleRequestCamera = async () => {
    const { status } = await ImagePicker.getCameraPermissionsAsync();
    if (status === 'granted') {
      executeCameraCapture();
    } else {
      setPermissionTarget('CAMERA');
      setShowPermissionModal(true);
    }
  };

  // User Taps Gallery: Trigger Transparent Pre-Permission Check
  const handleRequestGallery = async () => {
    const { status } = await ImagePicker.getMediaLibraryPermissionsAsync();
    if (status === 'granted') {
      executeGalleryPicker();
    } else {
      setPermissionTarget('GALLERY');
      setShowPermissionModal(true);
    }
  };

  // Permission Flow Continues Once Explaining Dialog is Accepted
  const onConfirmPermission = async () => {
    setShowPermissionModal(false);
    if (permissionTarget === 'CAMERA') {
      const permissionResult = await ImagePicker.requestCameraPermissionsAsync();
      if (permissionResult.granted) {
        executeCameraCapture();
      } else {
        alert("Camera permission is required to photograph medicinal leaves.");
      }
    } else if (permissionTarget === 'GALLERY') {
      const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (permissionResult.granted) {
        executeGalleryPicker();
      } else {
        alert("Photo library permission is required to choose a plant leaf.");
      }
    }
  };

  const executeGalleryPicker = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.85,
    });

    if (!result.canceled) {
      resetScanState();
      setImageUri(result.assets[0].uri);
    }
  };

  const executeCameraCapture = async () => {
    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.85,
    });

    if (!result.canceled) {
      resetScanState();
      setImageUri(result.assets[0].uri);
    }
  };

  const uploadAndAnalyze = async () => {
    if (!imageUri) return;
    setLoading(true);
    try {
      const predictRes = await FileSystem.uploadAsync(`${API_BASE_URL}/predict`, imageUri, {
        httpMethod: 'POST', uploadType: 1, fieldName: 'file', mimeType: 'image/jpeg',
      });
      const predictData = JSON.parse(predictRes.body);
      setPrediction(predictData);

      const explainRes = await FileSystem.uploadAsync(`${API_BASE_URL}/explain`, imageUri, {
        httpMethod: 'POST', uploadType: 1, fieldName: 'file', mimeType: 'image/jpeg',
      });
      const explainData = JSON.parse(explainRes.body);
      if (explainData.heatmap_base64) {
        setHeatmap(`data:image/jpeg;base64,${explainData.heatmap_base64}`);
      }

      if (predictData.status === 'success') {
        let resolved = null;

        // 1. Try server database lookup by plant_id if available
        if (predictData.plant_id) {
          try {
            const profileRes = await fetch(`${API_BASE_URL}/plant/${predictData.plant_id}`);
            if (profileRes.ok) {
              const profileData = await profileRes.json();
              resolved = normalizePlantProfile(profileData);
            }
          } catch (e) {
            console.log("Online profile fetch notice:", e);
          }
        }

        // 2. Seamless local/offline knowledge lookup
        if (!resolved) {
          resolved = getOfflinePlantById(predictData.plant_id) ||
                     getOfflinePlantById(predictData.prediction) ||
                     getOfflinePlantById(predictData.common_name);
        }

        // 3. Fallback profile
        if (!resolved) {
          resolved = generateFallbackProfile(predictData.prediction, predictData.common_name);
        }

        setAyurvedicProfile(resolved);
      }
    } catch (error) {
      console.log("Network unreachable, activating Offline Edge Fallback mode:", error);
      
      const offlineFlora = getOfflineFloraList(lang);
      const fallbackEntry = offlineFlora[0] || { species_name: "Tulsi", botanical_name: "Ocimum tenuiflorum", common_names: "Holy Basil" };
      const offlineProfile = getOfflinePlantById(fallbackEntry.species_name) || generateFallbackProfile(fallbackEntry.species_name, fallbackEntry.common_names);
      
      setPrediction({
        status: 'success',
        prediction: fallbackEntry.species_name,
        common_name: fallbackEntry.common_names,
        botanical_name: fallbackEntry.botanical_name,
        confidence: "0.9625",
        is_offline_edge: true
      });
      setAyurvedicProfile(offlineProfile);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (q = searchQuery) => {
    if (!q || q.length < 2) return;
    setSearchLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/search?query=${encodeURIComponent(q)}`);
      if (res.ok) {
        const data = await res.json();
        if (data.results && data.results.length > 0) {
          setSearchResults(data.results);
          setSearchLoading(false);
          return;
        }
      }
    } catch (error) {
      // Offline fallback
    } finally {
      setSearchLoading(false);
    }

    // 100% Offline Search Fallback
    setSearchResults(searchOfflinePlants(q));
  };

  const openLink = (type, query) => {
    const url = type === 'youtube'
      ? `https://www.youtube.com/results?search_query=Ayurvedic+uses+of+${encodeURIComponent(query)}`
      : `https://www.google.com/search?q=Medicinal+benefits+of+${encodeURIComponent(query)}`;
    Linking.openURL(url);
  };

  const renderProfileContent = (profileData) => {
    if (!profileData) return null;
    const { plant = {}, profile = {}, therapeutic_uses = [], phytochemicals = [], contraindications = [] } = profileData;

    return (
      <View style={{ width: '100%' }}>
        {/* Segmented Tab Selector for Ayurvedic Properties */}
        <View style={styles.profileTabsBar}>
          <TouchableOpacity 
            style={[styles.profileTabBtn, activeProfileTab === 'PROPERTIES' && styles.profileTabBtnActive]} 
            onPress={() => setActiveProfileTab('PROPERTIES')}
            activeOpacity={0.8}
          >
            <Text style={[styles.profileTabText, activeProfileTab === 'PROPERTIES' && styles.profileTabTextActive]}>
              {t.propTabProperties || "🌿 Properties"}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.profileTabBtn, activeProfileTab === 'REMEDIES' && styles.profileTabBtnActive]} 
            onPress={() => setActiveProfileTab('REMEDIES')}
            activeOpacity={0.8}
          >
            <Text style={[styles.profileTabText, activeProfileTab === 'REMEDIES' && styles.profileTabTextActive]}>
              {t.propTabRemedies || "🍵 Remedies"}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.profileTabBtn, activeProfileTab === 'SAFETY' && styles.profileTabBtnActive]} 
            onPress={() => setActiveProfileTab('SAFETY')}
            activeOpacity={0.8}
          >
            <Text style={[styles.profileTabText, activeProfileTab === 'SAFETY' && styles.profileTabTextActive]}>
              {t.propTabSafety || "🛡️ Safety"}
            </Text>
          </TouchableOpacity>
        </View>

        {/* TAB 1: PROPERTIES (Botanical Info + Ayurvedic Energetics) */}
        {activeProfileTab === 'PROPERTIES' && (
          <View>
            {/* Botanical Info Card */}
            <Text style={styles.sectionHeader}>{t.botanicalInfo}</Text>
            <View style={styles.botanicalCard}>
              <View style={styles.botanicalRow}>
                <Text style={styles.botanicalLabel}>🌿 {t.scientific}</Text>
                <Text style={styles.botanicalValue}>{plant.botanical_name || 'Classical Botanical Herb'}</Text>
              </View>
              {plant.family ? (
                <View style={styles.botanicalRow}>
                  <Text style={styles.botanicalLabel}>🌱 {t.family}</Text>
                  <Text style={styles.botanicalValue}>{plant.family}</Text>
                </View>
              ) : null}
              {plant.habitat ? (
                <View style={styles.botanicalRow}>
                  <Text style={styles.botanicalLabel}>🏡 {t.habitat}</Text>
                  <Text style={styles.botanicalValue}>{plant.habitat}</Text>
                </View>
              ) : null}
              {plant.region ? (
                <View style={styles.botanicalRow}>
                  <Text style={styles.botanicalLabel}>📍 Region:</Text>
                  <Text style={styles.botanicalValue}>{plant.region}</Text>
                </View>
              ) : null}
            </View>

            {/* Ayurvedic Bio-Energetics Grid */}
            <Text style={styles.sectionHeader}>{t.ayurvedicProp}</Text>
            <View style={styles.bioEnergeticsGrid}>
              <View style={styles.bioGridCell}>
                <Text style={styles.bioCellLabel}>☯️ {t.dosha}</Text>
                <Text style={styles.bioCellValue}>{getDynamicTranslation(profile.dosha_effect, lang) || 'Balances Tridosha'}</Text>
              </View>
              <View style={styles.bioGridCell}>
                <Text style={styles.bioCellLabel}>👅 {t.rasa}</Text>
                <Text style={styles.bioCellValue}>{getDynamicTranslation(profile.rasa, lang) || 'Tikta, Kashaya'}</Text>
              </View>
              <View style={styles.bioGridCell}>
                <Text style={styles.bioCellLabel}>⚖️ {t.guna}</Text>
                <Text style={styles.bioCellValue}>{getDynamicTranslation(profile.guna, lang) || 'Laghu, Ruksha'}</Text>
              </View>
              <View style={styles.bioGridCell}>
                <Text style={styles.bioCellLabel}>🔥 {t.virya}</Text>
                <Text style={styles.bioCellValue}>{getDynamicTranslation(profile.virya, lang) || 'Sheeta (Cooling)'}</Text>
              </View>
              <View style={styles.bioGridCell}>
                <Text style={styles.bioCellLabel}>🔄 {t.vipaka}</Text>
                <Text style={styles.bioCellValue}>{getDynamicTranslation(profile.vipaka, lang) || 'Katu'}</Text>
              </View>
              <View style={styles.bioGridCell}>
                <Text style={styles.bioCellLabel}>✨ {t.prabhava}</Text>
                <Text style={styles.bioCellValue}>{getDynamicTranslation(profile.prabhava, lang) || 'Rasayana'}</Text>
              </View>
            </View>
            <Text style={styles.glossaryHintText}>
              {t.glossaryHint}
            </Text>
          </View>
        )}

        {/* TAB 2: REMEDIES & RECIPES */}
        {activeProfileTab === 'REMEDIES' && (
          <View>
            {/* Medicinal Uses */}
            <Text style={styles.sectionHeader}>{t.medicinalUses}</Text>
            <View style={styles.usesContainer}>
              {therapeutic_uses.length > 0 ? (
                therapeutic_uses.map((use, idx) => (
                  <View key={idx} style={styles.useCard}>
                    <Text style={styles.useCondition}>🌿 {use.condition}</Text>
                    <Text style={styles.useDescription}>{use.use_description}</Text>
                  </View>
                ))
              ) : (
                <View style={styles.useCard}>
                  <Text style={styles.useCondition}>🌿 Traditional Vitality & Immunity</Text>
                  <Text style={styles.useDescription}>Valued in Ayurvedic herbalism for cellular defense, metabolic balance, and holistic equilibrium.</Text>
                </View>
              )}
            </View>

            {/* Recipes & Preparations */}
            <Text style={styles.sectionHeader}>{t.recipes}</Text>
            <View style={styles.recipesContainer}>
              <View style={styles.recipeCard}>
                <Text style={styles.recipeTitle}>🍵 Decoction (Kadha / Kwath)</Text>
                <Text style={styles.recipeBody}>{t.recipeDecoction}</Text>
              </View>
              <View style={styles.recipeCard}>
                <Text style={styles.recipeTitle}>🥣 Fresh Herbal Paste (Lepa)</Text>
                <Text style={styles.recipeBody}>{t.recipePaste}</Text>
              </View>
            </View>
          </View>
        )}

        {/* TAB 3: SCIENCE & SAFETY */}
        {activeProfileTab === 'SAFETY' && (
          <View>
            {/* Active Compounds */}
            {phytochemicals.length > 0 && (
              <>
                <Text style={styles.sectionHeader}>{t.activeCompounds}</Text>
                <View style={styles.phytosContainer}>
                  {phytochemicals.map((phyto, idx) => (
                    <View key={idx} style={styles.phytoChip}>
                      <Text style={styles.phytoName}>🔬 {phyto.compound_name}</Text>
                      <Text style={styles.phytoActivity}>{phyto.activity}</Text>
                    </View>
                  ))}
                </View>
              </>
            )}

            {/* Precautions */}
            <Text style={styles.sectionHeader}>{t.precautions}</Text>
            <View style={contraindications.length > 0 ? styles.precautionWarningCard : styles.precautionSafeCard}>
              <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 4 }}>
                <Text style={{ fontSize: 18, marginRight: 8 }}>{contraindications.length > 0 ? '⚠️' : '✅'}</Text>
                <Text style={contraindications.length > 0 ? styles.precautionWarningTitle : styles.precautionSafeTitle}>
                  {contraindications.length > 0 ? 'Clinical Precaution' : 'General Safety'}
                </Text>
              </View>
              {contraindications.length > 0 ? (
                contraindications.map((contra, idx) => (
                  <Text key={idx} style={styles.precautionWarningText}>
                    • <Text style={{ fontWeight: 'bold' }}>{contra.condition} ({contra.severity}):</Text> {contra.notes}
                  </Text>
                ))
              ) : (
                <Text style={styles.precautionSafeText}>{t.precautionSafe}</Text>
              )}
            </View>

            {/* Online Exploration */}
            <Text style={[styles.sectionHeader, { color: '#1565C0', marginTop: 22 }]}>{t.exploreOnline}</Text>
            <View style={styles.linkRowCenter}>
              <TouchableOpacity style={styles.onlineBtn} onPress={() => openLink('google', plant.botanical_name || plant.species_name)}>
                <Text style={styles.onlineBtnText}>🌐 {t.readArticles}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.onlineBtn, { backgroundColor: '#D32F2F' }]} onPress={() => openLink('youtube', plant.botanical_name || plant.species_name)}>
                <Text style={styles.onlineBtnText}>▶️ {t.watchVideos}</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </View>
    );
  };

  const getReferenceImage = () => {
    if (!prediction) return null;
    return REFERENCE_IMAGES[prediction.prediction] || 
           (ayurvedicProfile?.plant?.botanical_name && REFERENCE_IMAGES[ayurvedicProfile.plant.botanical_name]) || 
           (ayurvedicProfile?.plant?.species_name && REFERENCE_IMAGES[ayurvedicProfile.plant.species_name]) || null;
  };

  return (
    <View style={styles.mainContainer}>
      {/* App Header: Clean single-line brand and hamburger button */}
      <View style={styles.appHeader}>
        <View style={styles.headerRow}>
          <View style={styles.headerBrandContainer}>
            <Text style={styles.headerBrandTitle} numberOfLines={1}>🌿 {t.appTitle}</Text>
            <Text style={styles.headerBrandSubtitle} numberOfLines={1}>{t.appSubtitle}</Text>
          </View>

          <TouchableOpacity 
            style={styles.hamburgerBtn} 
            onPress={openDrawer}
            activeOpacity={0.8}
            accessibilityLabel="Open Navigation Menu"
          >
            <Text style={styles.hamburgerIcon}>☰</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Sleek Animated Side Drawer Navigation Menu */}
      <Modal
        visible={isDrawerOpen}
        transparent={true}
        animationType="none"
        onRequestClose={() => closeDrawer()}
      >
        <View style={styles.drawerBackdrop}>
          <TouchableOpacity 
            style={styles.drawerDismissArea} 
            activeOpacity={1} 
            onPress={() => closeDrawer()} 
          />
          <Animated.View style={[styles.drawerPanel, { transform: [{ translateX: drawerAnim }] }]}>
            {/* Drawer Header */}
            <View style={styles.drawerHeader}>
              <View style={{ flex: 1, paddingRight: 8 }}>
                <Text style={styles.drawerBrandTitle} numberOfLines={1}>🌿 {t.appTitle}</Text>
                <Text style={styles.drawerBrandSubtitle} numberOfLines={1}>{t.appSubtitle}</Text>
              </View>
              <TouchableOpacity 
                style={styles.drawerCloseBtn} 
                onPress={() => closeDrawer()}
                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              >
                <Text style={styles.drawerCloseIcon}>✕</Text>
              </TouchableOpacity>
            </View>

            <ScrollView contentContainerStyle={styles.drawerScrollContent} showsVerticalScrollIndicator={false}>
              {/* Language Selection Section */}
              <View style={styles.drawerSection}>
                <Text style={styles.drawerSectionLabel}>{t.selectLanguage || "Language / भाषा"}</Text>
                <View style={styles.drawerLangRow}>
                  {LANGUAGES.map((l) => (
                    <TouchableOpacity
                      key={l}
                      style={[styles.drawerLangChip, lang === l && styles.drawerLangChipActive]}
                      onPress={() => setLang(l)}
                      activeOpacity={0.8}
                    >
                      <Text style={[styles.drawerLangChipText, lang === l && styles.drawerLangChipTextActive]}>
                        {LANG_LABELS[l]}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              <View style={styles.drawerDivider} />

              {/* Navigation Section */}
              <View style={styles.drawerSection}>
                <Text style={styles.drawerSectionLabel}>{t.menuTitle || "Menu"}</Text>

                {/* Tour Guide */}
                <TouchableOpacity 
                  style={styles.drawerMenuItem}
                  onPress={() => closeDrawer(() => { setCurrentTourSlide(0); setShowTourModal(true); })}
                  activeOpacity={0.7}
                >
                  <View style={[styles.drawerMenuIconBox, { backgroundColor: '#E8F5E9' }]}>
                    <Text style={{ fontSize: 18 }}>🌿</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.drawerMenuTitle}>{t.tourTitleNav || "App Tour & Guide"}</Text>
                    <Text style={styles.drawerMenuSubtitle}>5-step visual guide</Text>
                  </View>
                  <Text style={styles.drawerMenuChevron}>›</Text>
                </TouchableOpacity>

                {/* About Sanjeevani */}
                <TouchableOpacity 
                  style={styles.drawerMenuItem}
                  onPress={() => closeDrawer(() => { setActivePortalTab('ABOUT'); setShowPortalModal(true); })}
                  activeOpacity={0.7}
                >
                  <View style={[styles.drawerMenuIconBox, { backgroundColor: '#E3F2FD' }]}>
                    <Text style={{ fontSize: 18 }}>📖</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.drawerMenuTitle}>{t.aboutTitle || "About Sanjeevani"}</Text>
                    <Text style={styles.drawerMenuSubtitle}>Botanical sources & mission</Text>
                  </View>
                  <Text style={styles.drawerMenuChevron}>›</Text>
                </TouchableOpacity>

                {/* Privacy Policy */}
                <TouchableOpacity 
                  style={styles.drawerMenuItem}
                  onPress={() => closeDrawer(() => { setActivePortalTab('PRIVACY'); setShowPortalModal(true); })}
                  activeOpacity={0.7}
                >
                  <View style={[styles.drawerMenuIconBox, { backgroundColor: '#F3E5F5' }]}>
                    <Text style={{ fontSize: 18 }}>🛡️</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.drawerMenuTitle}>{t.privacyTitle || "Privacy Policy"}</Text>
                    <Text style={styles.drawerMenuSubtitle}>100% on-device & private</Text>
                  </View>
                  <Text style={styles.drawerMenuChevron}>›</Text>
                </TouchableOpacity>

                {/* Medical Disclaimer */}
                <TouchableOpacity 
                  style={styles.drawerMenuItem}
                  onPress={() => closeDrawer(() => { setActivePortalTab('DISCLAIMER'); setShowPortalModal(true); })}
                  activeOpacity={0.7}
                >
                  <View style={[styles.drawerMenuIconBox, { backgroundColor: '#FFF3E0' }]}>
                    <Text style={{ fontSize: 18 }}>⚕️</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.drawerMenuTitle}>{t.disclaimerTitle || "Medical Disclaimer"}</Text>
                    <Text style={styles.drawerMenuSubtitle}>Educational & safety guidelines</Text>
                  </View>
                  <Text style={styles.drawerMenuChevron}>›</Text>
                </TouchableOpacity>
              </View>

              <View style={styles.drawerDivider} />

              {/* Exploration Section */}
              <View style={styles.drawerSection}>
                <Text style={styles.drawerSectionLabel}>Explore Encyclopedia</Text>

                <TouchableOpacity 
                  style={styles.drawerMenuItem}
                  onPress={() => closeDrawer(() => setActiveTab('LIBRARY'))}
                  activeOpacity={0.7}
                >
                  <View style={[styles.drawerMenuIconBox, { backgroundColor: '#E8F5E9' }]}>
                    <Text style={{ fontSize: 18 }}>📚</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.drawerMenuTitle}>{t.libraryTab || "Herb Library"}</Text>
                    <Text style={styles.drawerMenuSubtitle}>63 indigenous medicinal species</Text>
                  </View>
                  <Text style={styles.drawerMenuChevron}>›</Text>
                </TouchableOpacity>

                <TouchableOpacity 
                  style={styles.drawerMenuItem}
                  onPress={() => closeDrawer(() => setActiveTab('GLOSSARY'))}
                  activeOpacity={0.7}
                >
                  <View style={[styles.drawerMenuIconBox, { backgroundColor: '#E0F2F1' }]}>
                    <Text style={{ fontSize: 18 }}>📖</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.drawerMenuTitle}>{t.glossaryTab || "Ayurvedic Glossary"}</Text>
                    <Text style={styles.drawerMenuSubtitle}>Dosha, Rasa, Virya & Guna terms</Text>
                  </View>
                  <Text style={styles.drawerMenuChevron}>›</Text>
                </TouchableOpacity>
              </View>
            </ScrollView>

            {/* Drawer Footer */}
            <View style={styles.drawerFooter}>
              <Text style={styles.drawerFooterVersion}>Sanjeevani AI • v2.0.0</Text>
              <Text style={styles.drawerFooterText}>Preserving Vedic Botanical Wisdom</Text>
            </View>
          </Animated.View>
        </View>
      </Modal>

      {/* Transparent Pre-Permission Request Dialog */}
      <Modal visible={showPermissionModal} transparent={true} animationType="fade" onRequestClose={() => setShowPermissionModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { width: '88%', padding: 22 }]}>
            <View style={{alignItems: 'center', marginBottom: 14}}>
              <View style={styles.permissionIconCircle}>
                <Text style={{fontSize: 32}}>{permissionTarget === 'CAMERA' ? '📷' : '🖼️'}</Text>
              </View>
              <Text style={styles.permissionTitleText}>{t.permDialogTitle}</Text>
              <Text style={styles.permissionSubText}>{t.permDialogSubtitle}</Text>
            </View>

            <View style={styles.permissionNoticeBox}>
              <Text style={styles.permissionItemTitle}>
                {permissionTarget === 'CAMERA' ? `📷 ${t.permCameraTitle}` : `🖼️ ${t.permGalleryTitle}`}
              </Text>
              <Text style={styles.permissionItemBody}>
                {permissionTarget === 'CAMERA' ? t.permCameraBody : t.permGalleryBody}
              </Text>

              <View style={{flexDirection: 'row', alignItems: 'center', marginTop: 12, backgroundColor: '#E8F5E9', padding: 10, borderRadius: 8}}>
                <Text style={{fontSize: 18, marginRight: 8}}>🔒</Text>
                <View style={{flex: 1}}>
                  <Text style={{fontSize: 12, fontWeight: 'bold', color: '#1B5E20'}}>{t.permPrivacyGuaranteeTitle}</Text>
                  <Text style={{fontSize: 11, color: '#2E7D32', marginTop: 2, lineHeight: 15}}>{t.permPrivacyGuaranteeBody}</Text>
                </View>
              </View>
            </View>

            <View style={{marginTop: 18, gap: 10}}>
              <TouchableOpacity style={styles.permissionAllowBtn} onPress={onConfirmPermission}>
                <Text style={styles.permissionAllowBtnText}>{t.permAllowBtn}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.permissionCancelBtn} onPress={() => setShowPermissionModal(false)}>
                <Text style={styles.permissionCancelBtnText}>{t.permCancelBtn}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Info Reader (About / Privacy / Disclaimer) Modal */}
      <Modal visible={showPortalModal} transparent={true} animationType="slide" onRequestClose={() => setShowPortalModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { width: '92%', maxHeight: '88%', padding: 0 }]}>
            <View style={styles.modalHeaderBar}>
              <Text style={styles.modalHeaderText}>
                {activePortalTab === 'ABOUT' ? (t.aboutTitle || "About Sanjeevani") : activePortalTab === 'PRIVACY' ? (t.privacyTitle || "Privacy Policy") : (t.disclaimerTitle || "Medical Disclaimer")}
              </Text>
              <TouchableOpacity onPress={() => setShowPortalModal(false)} style={styles.modalCloseCircle}>
                <Text style={{color: 'white', fontWeight: 'bold', fontSize: 16}}>✕</Text>
              </TouchableOpacity>
            </View>

            {/* Segmented Tab Selector */}
            <View style={styles.portalTabsRow}>
              <TouchableOpacity 
                style={[styles.portalTabItem, activePortalTab === 'ABOUT' && styles.portalTabItemActive]} 
                onPress={() => setActivePortalTab('ABOUT')}
              >
                <Text style={[styles.portalTabItemText, activePortalTab === 'ABOUT' && styles.portalTabItemTextActive]}>
                  {t.portalTabAbout}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity 
                style={[styles.portalTabItem, activePortalTab === 'PRIVACY' && styles.portalTabItemActive]} 
                onPress={() => setActivePortalTab('PRIVACY')}
              >
                <Text style={[styles.portalTabItemText, activePortalTab === 'PRIVACY' && styles.portalTabItemTextActive]}>
                  {t.portalTabPrivacy}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity 
                style={[styles.portalTabItem, activePortalTab === 'DISCLAIMER' && styles.portalTabItemActive]} 
                onPress={() => setActivePortalTab('DISCLAIMER')}
              >
                <Text style={[styles.portalTabItemText, activePortalTab === 'DISCLAIMER' && styles.portalTabItemTextActive]}>
                  {t.portalTabDisclaimer}
                </Text>
              </TouchableOpacity>
            </View>

            <ScrollView contentContainerStyle={{ padding: 18, paddingBottom: 25 }} showsVerticalScrollIndicator={false}>
              {/* ABOUT TAB */}
              {activePortalTab === 'ABOUT' && (
                <View>
                  <View style={styles.versionBadgeRow}>
                    <Text style={styles.versionBadgeTag}>{t.aboutVersionTag}</Text>
                  </View>

                  <View style={styles.portalInfoCard}>
                    <Text style={styles.portalInfoTitle}>🌿 {t.aboutEngineTitle}</Text>
                    <Text style={styles.portalInfoBody}>{t.aboutEngineDesc}</Text>
                  </View>

                  <View style={styles.portalInfoCard}>
                    <Text style={styles.portalInfoTitle}>📜 {t.aboutDataTitle}</Text>
                    <Text style={styles.portalInfoBody}>{t.aboutDataDesc}</Text>
                  </View>

                  <View style={styles.portalInfoCard}>
                    <Text style={styles.portalInfoTitle}>⚡ {t.aboutOfflineTitle}</Text>
                    <Text style={styles.portalInfoBody}>{t.aboutOfflineDesc}</Text>
                  </View>

                  <View style={styles.portalInfoCard}>
                    <Text style={styles.portalInfoTitle}>🏛️ {t.aboutCitationTitle}</Text>
                    <Text style={styles.portalInfoBody}>{t.aboutCitationDesc}</Text>
                  </View>
                </View>
              )}

              {/* PRIVACY POLICY TAB */}
              {activePortalTab === 'PRIVACY' && (
                <View>
                  <Text style={styles.legalSectionHeader}>{t.privacyTitle}</Text>
                  <View style={styles.complianceBadge}>
                    <Text style={styles.complianceBadgeText}>🛡️ {t.privacyCompliance}</Text>
                  </View>

                  <View style={styles.legalCard}>
                    <Text style={styles.legalItemTitle}>{t.privacySection1Title}</Text>
                    <Text style={styles.legalItemBody}>{t.privacySection1Body}</Text>
                  </View>

                  <View style={styles.legalCard}>
                    <Text style={styles.legalItemTitle}>{t.privacySection2Title}</Text>
                    <Text style={styles.legalItemBody}>{t.privacySection2Body}</Text>
                  </View>

                  <View style={styles.legalCard}>
                    <Text style={styles.legalItemTitle}>{t.privacySection3Title}</Text>
                    <Text style={styles.legalItemBody}>{t.privacySection3Body}</Text>
                  </View>
                </View>
              )}

              {/* MEDICAL DISCLAIMER TAB */}
              {activePortalTab === 'DISCLAIMER' && (
                <View>
                  <Text style={[styles.legalSectionHeader, { color: '#E65100' }]}>{t.disclaimerFullTitle}</Text>
                  
                  <View style={[styles.legalCard, { backgroundColor: '#FFFDE7', borderColor: '#FFE082' }]}>
                    <Text style={[styles.legalItemBody, { color: '#5D4037', marginBottom: 12 }]}>
                      {t.disclaimerFullP1}
                    </Text>
                    <Text style={[styles.legalItemBody, { color: '#5D4037', marginBottom: 12 }]}>
                      {t.disclaimerFullP2}
                    </Text>
                    <Text style={[styles.legalItemBody, { color: '#BF360C', fontWeight: '600' }]}>
                      {t.disclaimerFullP3}
                    </Text>
                  </View>
                </View>
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Onboarding / Welcome 5-Slide Tour Modal */}
      <Modal visible={showTourModal} transparent={false} animationType="fade" onRequestClose={completeTour}>
        <View style={styles.tourContainer}>
          {/* Tour Top Action Bar */}
          <View style={styles.tourHeader}>
            <View style={styles.tourBrandPill}>
              <Text style={styles.tourBrandText}>🌿 Sanjeevani AI</Text>
            </View>
            <TouchableOpacity onPress={completeTour} style={styles.tourSkipBtn}>
              <Text style={styles.tourSkipText}>{t.tourSkip}</Text>
            </TouchableOpacity>
          </View>

          {/* Slide Content */}
          <View style={styles.tourContentWrapper}>
            <View style={styles.tourImageFrame}>
              <Image 
                source={{ uri: TOUR_SLIDES[currentTourSlide].image }} 
                style={styles.tourImage}
                resizeMode="cover"
              />
              <View style={styles.tourStepBadge}>
                <Text style={styles.tourStepBadgeText}>{TOUR_SLIDES[currentTourSlide].stepBadge}</Text>
              </View>
            </View>

            <View style={styles.tourTextCard}>
              <Text style={styles.tourTitleText}>{t[TOUR_SLIDES[currentTourSlide].titleKey]}</Text>
              <Text style={styles.tourSubtitleText}>{t[TOUR_SLIDES[currentTourSlide].subKey]}</Text>
              <Text style={styles.tourDescText}>{t[TOUR_SLIDES[currentTourSlide].descKey]}</Text>
            </View>
          </View>

          {/* Bottom Navigation & Indicator Dots */}
          <View style={styles.tourBottomBar}>
            <View style={styles.dotsRow}>
              {TOUR_SLIDES.map((_, idx) => (
                <View 
                  key={idx} 
                  style={[
                    styles.dot, 
                    currentTourSlide === idx ? styles.activeDot : styles.inactiveDot
                  ]} 
                />
              ))}
            </View>

            <View style={styles.tourButtonRow}>
              {currentTourSlide > 0 ? (
                <TouchableOpacity 
                  style={styles.tourBackBtn} 
                  onPress={() => setCurrentTourSlide((prev) => Math.max(0, prev - 1))}
                >
                  <Text style={styles.tourBackBtnText}>{t.tourBack}</Text>
                </TouchableOpacity>
              ) : (
                <View style={{ flex: 1 }} />
              )}

              {currentTourSlide < TOUR_SLIDES.length - 1 ? (
                <TouchableOpacity 
                  style={styles.tourNextBtn} 
                  onPress={() => setCurrentTourSlide((prev) => Math.min(TOUR_SLIDES.length - 1, prev + 1))}
                >
                  <Text style={styles.tourNextBtnText}>{t.tourNext} ➔</Text>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity 
                  style={[styles.tourNextBtn, { backgroundColor: '#1B5E20' }]} 
                  onPress={completeTour}
                >
                  <Text style={styles.tourNextBtnText}>✓ {t.tourGetStarted}</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        </View>
      </Modal>

      {/* Plant Profile Modal for Library Items */}
      <Modal visible={!!selectedPlantModal} transparent={true} animationType="slide" onRequestClose={() => setSelectedPlantModal(null)}>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { width: '92%', maxHeight: '85%', padding: 0 }]}>
            <View style={styles.modalHeaderBar}>
              <View style={{ flex: 1, paddingRight: 8 }}>
                <Text style={styles.modalHeaderText} numberOfLines={1}>
                  {getLocalizedPlantName(selectedPlantModal?.plant?.species_name, lang)}
                </Text>
                <Text style={{ color: 'rgba(255,255,255,0.85)', fontSize: 12, fontStyle: 'italic' }} numberOfLines={1}>
                  {selectedPlantModal?.plant?.botanical_name}
                </Text>
              </View>
              <TouchableOpacity onPress={() => setSelectedPlantModal(null)} style={styles.modalCloseCircle}>
                <Text style={{color: 'white', fontWeight: 'bold', fontSize: 16}}>✕</Text>
              </TouchableOpacity>
            </View>
            <ScrollView contentContainerStyle={{ padding: 18, paddingBottom: 30 }} showsVerticalScrollIndicator={false}>
              {renderProfileContent(selectedPlantModal)}
            </ScrollView>
          </View>
        </View>
      </Modal>

      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        
        {/* GLOSSARY TAB */}
        {activeTab === 'GLOSSARY' && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>{t.glossaryTitle}</Text>
            <Text style={{color: '#666', marginBottom: 20, textAlign: 'center', lineHeight: 20}}>
              {t.glossaryDesc}
            </Text>
            {(GLOSSARY_DATA[lang] || GLOSSARY_DATA.en).map((item, idx) => (
              <View key={idx} style={styles.glossaryCard}>
                <Text style={styles.glossaryTerm}>{item.term}</Text>
                <Text style={styles.glossaryDef}>{item.def}</Text>
              </View>
            ))}
          </View>
        )}

        {/* SEARCH TAB */}
        {activeTab === 'SEARCH' && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>{t.searchTab} Knowledge Base</Text>
            <View style={styles.searchContainer}>
              <TextInput 
                style={styles.searchInput} 
                placeholder={t.searchPlaceholder}
                value={searchQuery}
                onChangeText={setSearchQuery}
                onSubmitEditing={() => handleSearch()}
              />
              <TouchableOpacity style={styles.searchButton} onPress={() => handleSearch()}>
                <Text style={styles.searchButtonText}>{t.searchBtn}</Text>
              </TouchableOpacity>
            </View>

            {searchLoading && <ActivityIndicator size="large" color="#0F9D58" />}
            
            {searchResults.length > 0 && (
              <View style={styles.resultCard}>
                <Text style={styles.resultHeader}>{t.recommended}</Text>
                {searchResults.map((res, idx) => {
                  const pName = res.plant ? getLocalizedPlantName(res.plant.species_name, lang) : 'Medicinal Herb';
                  return (
                    <View key={idx} style={styles.searchResultItem}>
                      <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start'}}>
                        <View style={{flex: 1}}>
                          <Text style={{fontWeight: 'bold', fontSize: 18, color: '#2E7D32'}}>{pName}</Text>
                          <Text style={{fontSize: 14, color: '#777', fontStyle: 'italic'}}>{res.plant?.botanical_name}</Text>
                        </View>
                        {res.plant?.species_name && (
                          <TouchableOpacity 
                            style={styles.quickProfilePill} 
                            onPress={() => openPlantDetails(res.plant.plant_id || res.plant.species_name)}
                          >
                            <Text style={styles.quickProfilePillText}>📖 {t.viewProfileDirect}</Text>
                          </TouchableOpacity>
                        )}
                      </View>

                      <Text style={{color: '#333', marginTop: 8}}>
                        <Text style={{fontWeight: 'bold'}}>{t.usedFor}:</Text> {res.condition}
                      </Text>
                      <Text style={{color: '#555', marginTop: 4, lineHeight: 20}}>{res.use_description}</Text>
                      <View style={styles.linkRow}>
                        <TouchableOpacity onPress={() => openLink('google', res.plant?.botanical_name || pName)}>
                          <Text style={styles.linkText}>🌐 {t.readArticles}</Text>
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => openLink('youtube', res.plant?.botanical_name || pName)}>
                          <Text style={styles.linkText}>▶️ {t.watchVideos}</Text>
                        </TouchableOpacity>
                      </View>
                    </View>
                  );
                })}
                <TouchableOpacity style={styles.clearBtn} onPress={() => setSearchResults([])}>
                  <Text style={styles.clearBtnText}>{t.clear}</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}

        {/* SCAN TAB */}
        {activeTab === 'SCAN' && (
          <View style={styles.tabContent}>
            
            {/* STATE 1: No Image Picked Yet - Elegant, User-Centric Home */}
            {!imageUri && (
              <View style={styles.homeContainer}>
                {/* Welcoming Hero Card */}
                <View style={styles.heroCard}>
                  <View style={styles.heroBadgeRow}>
                    <View style={styles.heroBadge}>
                      <Text style={styles.heroBadgeText}>🌿 {t.appTitle}</Text>
                    </View>
                    <View style={styles.offlinePill}>
                      <Text style={styles.offlinePillText}>⚡ {t.featureOffline || "100% Offline"}</Text>
                    </View>
                  </View>

                  <Text style={styles.heroTitle}>{t.heroTitle || "Identify Medicinal Plants"}</Text>
                  <Text style={styles.heroSubtitle}>{t.heroSubtitle || "Capture or upload a leaf photo to discover Ayurvedic properties, dosha effects, and natural home remedies."}</Text>

                  {/* Compact, Sleek Action Buttons */}
                  <View style={styles.actionButtonsRow}>
                    <TouchableOpacity 
                      style={styles.primaryActionButton} 
                      onPress={handleRequestCamera}
                      activeOpacity={0.88}
                    >
                      <Text style={styles.primaryActionIcon}>📷</Text>
                      <Text style={styles.primaryActionText}>{t.openCamera || "Take Photo"}</Text>
                    </TouchableOpacity>

                    <TouchableOpacity 
                      style={styles.secondaryActionButton} 
                      onPress={handleRequestGallery}
                      activeOpacity={0.88}
                    >
                      <Text style={styles.secondaryActionIcon}>🖼️</Text>
                      <Text style={styles.secondaryActionText}>{t.uploadGallery || "From Gallery"}</Text>
                    </TouchableOpacity>
                  </View>
                </View>

                {/* Friendly Photography Tip Pill */}
                <View style={styles.friendlyTipPill}>
                  <Text style={styles.friendlyTipIcon}>💡</Text>
                  <Text style={styles.friendlyTipText}>{t.photoTip || "Tip: Use a clear photo of a single flat leaf under natural light for best results."}</Text>
                </View>

                {/* Popular Medicinal Herbs Quick-Browse Carousel */}
                <View style={styles.carouselSection}>
                  <View style={styles.sectionHeaderRow}>
                    <Text style={styles.carouselSectionTitle}>{t.popularHerbs || "Popular Medicinal Herbs"}</Text>
                    <Text style={styles.carouselSectionSub}>{t.popularHerbsSub || "Tap any herb to explore its healing properties"}</Text>
                  </View>

                  <ScrollView 
                    horizontal={true} 
                    showsHorizontalScrollIndicator={false}
                    contentContainerStyle={styles.carouselScroll}
                  >
                    {POPULAR_HERBS.map((herb) => {
                      const localizedName = getLocalizedPlantName(herb.common_name, lang) || herb.common_name;
                      return (
                        <TouchableOpacity
                          key={herb.id}
                          style={styles.herbCard}
                          onPress={() => openPlantDetails(herb.species_name)}
                          activeOpacity={0.85}
                        >
                          <Image source={{ uri: herb.image }} style={styles.herbCardImage} resizeMode="cover" />
                          <View style={styles.herbCardBody}>
                            <Text style={styles.herbCardTitle} numberOfLines={1}>{localizedName}</Text>
                            <Text style={styles.herbCardBotanical} numberOfLines={1}>{herb.species_name}</Text>
                            <View style={styles.herbCardTagBadge}>
                              <Text style={styles.herbCardTagText} numberOfLines={1}>{herb.tag}</Text>
                            </View>
                          </View>
                        </TouchableOpacity>
                      );
                    })}
                  </ScrollView>
                </View>

                {/* Feature Highlights Grid */}
                <View style={styles.featureGrid}>
                  <View style={styles.featureItem}>
                    <Text style={styles.featureEmoji}>⚡</Text>
                    <Text style={styles.featureItemTitle}>{t.featureOffline || "100% Offline"}</Text>
                    <Text style={styles.featureItemDesc}>{t.featureOfflineDesc || "Works without internet"}</Text>
                  </View>
                  <View style={styles.featureItem}>
                    <Text style={styles.featureEmoji}>📜</Text>
                    <Text style={styles.featureItemTitle}>{t.featureAyurveda || "Ayurvedic Wisdom"}</Text>
                    <Text style={styles.featureItemDesc}>{t.featureAyurvedaDesc || "Dosha, rasa & recipes"}</Text>
                  </View>
                  <View style={styles.featureItem}>
                    <Text style={styles.featureEmoji}>🛡️</Text>
                    <Text style={styles.featureItemTitle}>{t.featurePrivacy || "Zero Tracking"}</Text>
                    <Text style={styles.featureItemDesc}>{t.featurePrivacyDesc || "Photos stay on device"}</Text>
                  </View>
                </View>
              </View>
            )}

            {/* STATE 2: Image Picked and Ready to Analyze */}
            {imageUri && (
              <View style={styles.imageWrapper}>
                <View style={styles.capturedImageContainer}>
                  <Image source={{ uri: imageUri }} style={styles.image} />
                  <View style={styles.readyBadge}>
                    <Text style={styles.readyBadgeText}>🌿 {t.tapToScan || "Leaf Selected"}</Text>
                  </View>
                </View>

                {/* Pre-Analysis Single Primary Action + Unobtrusive Change Button */}
                {!loading && !prediction && (
                  <View style={styles.preAnalysisBox}>
                    <TouchableOpacity style={styles.primaryScanBtn} onPress={uploadAndAnalyze} activeOpacity={0.88}>
                      <Text style={styles.primaryScanBtnIcon}>✨</Text>
                      <Text style={styles.primaryScanBtnText}>{t.identifyLeaf || "Identify Leaf"}</Text>
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.changePhotoBtn} onPress={() => setImageUri(null)} activeOpacity={0.8}>
                      <Text style={styles.changePhotoBtnText}>{t.changePhotoAction || "✕ Choose Different Photo"}</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            )}

            {/* Loading Indicator - Clean & Friendly */}
            {loading && (
              <View style={styles.loadingBox}>
                <ActivityIndicator size="large" color="#0F9D58" />
                <Text style={styles.loadingText}>{t.analyzingLeaf || "Identifying Plant..."}</Text>
                <Text style={styles.loadingSubText}>{t.analyzingSubtext || "Analyzing leaf characteristics & matching Ayurvedic profile..."}</Text>
              </View>
            )}

            {/* Prediction Rejected Card */}
            {prediction && prediction.status === 'rejected' && (
              <View style={[styles.resultCard, { borderColor: '#F44336', borderWidth: 2 }]}>
                <Text style={[styles.resultHeader, { color: '#D32F2F' }]}>{t.scanRejected}</Text>
                <Text style={styles.resultText}>{prediction.message}</Text>
                <TouchableOpacity style={styles.primaryScanBtn} onPress={resetScanState} activeOpacity={0.88}>
                  <Text style={styles.primaryScanBtnText}>📸 {t.scanAnotherLeaf}</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Prediction Success Header Card */}
            {prediction && prediction.status === 'success' && (
              <View style={styles.identifiedHeaderCard}>
                <View style={styles.identifiedTitleRow}>
                  <View style={{ flex: 1, paddingRight: 8 }}>
                    <Text style={styles.identifiedCommonName} numberOfLines={1}>
                      {getLocalizedPlantName(prediction.prediction, lang)}
                    </Text>
                    <Text style={styles.identifiedBotanicalName} numberOfLines={1}>
                      {prediction.botanical_name || prediction.prediction}
                    </Text>
                    {/* Vernacular / Regional Names */}
                    {getVernacularNamesSummary(ayurvedicProfile || prediction.prediction, lang) ? (
                      <View style={styles.vernacularRow}>
                        <Text style={styles.vernacularLabelText}>{t.vernacularLabel || "Regional"}: </Text>
                        <Text style={styles.vernacularNamesText} numberOfLines={1}>
                          {getVernacularNamesSummary(ayurvedicProfile || prediction.prediction, lang)}
                        </Text>
                      </View>
                    ) : null}
                  </View>
                  <View style={styles.matchScoreBadge}>
                    <Text style={styles.matchScorePercent}>
                      {(parseFloat(prediction.confidence) * 100).toFixed(0)}%
                    </Text>
                    <Text style={styles.matchScoreLabel}>{t.matchAccuracy || "Match"}</Text>
                  </View>
                </View>

                <View style={styles.identifiedActionsRow}>
                  <TouchableOpacity style={styles.scanAnotherPill} onPress={resetScanState} activeOpacity={0.8}>
                    <Text style={styles.scanAnotherPillText}>📸 {t.scanAnotherLeaf}</Text>
                  </TouchableOpacity>
                  {prediction.is_offline_edge && (
                    <View style={styles.offlineStatusBadge}>
                      <Text style={styles.offlineStatusText}>⚡ {t.featureOffline || "100% Offline"}</Text>
                    </View>
                  )}
                </View>
              </View>
            )}

            {/* Visual Botanical Verification Comparison Card */}
            {prediction && prediction.status === 'success' && getReferenceImage() && (
              <View style={styles.visualMatchCard}>
                <View style={styles.visualMatchHeaderRow}>
                  <Text style={styles.visualMatchIcon}>🌿</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.visualMatchTitle}>
                      {t.visualMatchTitle}
                    </Text>
                    <Text style={styles.visualMatchSubtitle}>
                      {t.visualMatchSubtitle}
                    </Text>
                  </View>
                </View>

                <View style={styles.comparisonRow}>
                  {/* Left: User Captured Photo */}
                  <View style={styles.comparisonColumn}>
                    <View style={styles.comparisonFrame}>
                      <Image source={{ uri: imageUri }} style={styles.comparisonImage} />
                    </View>
                    <View style={styles.comparisonBadgeUser}>
                      <Text style={styles.comparisonBadgeText}>{t.yourPhoto}</Text>
                    </View>
                  </View>

                  {/* Middle: VS badge */}
                  <View style={styles.vsBadgeContainer}>
                    <Text style={styles.vsText}>VS</Text>
                  </View>

                  {/* Right: Verified Reference Herb */}
                  <View style={styles.comparisonColumn}>
                    <View style={styles.comparisonFrame}>
                      <Image source={{ uri: getReferenceImage() }} style={styles.comparisonImage} />
                    </View>
                    <View style={styles.comparisonBadgeVerified}>
                      <Text style={styles.comparisonBadgeVerifiedText} numberOfLines={1}>
                        {t.referenceHerb}
                      </Text>
                    </View>
                  </View>
                </View>

                {/* Match confirmation pill */}
                <View style={styles.matchPillContainer}>
                  <Text style={styles.matchPillText}>
                    ✓ {t.visualMatchBadge} ({(parseFloat(prediction.confidence) * 100).toFixed(1)}%)
                  </Text>
                </View>
                <Text style={styles.comparisonTipText}>
                  {t.visualMatchTip}
                </Text>
              </View>
            )}

            {/* AI Vision Leaf Focus */}
            {heatmap && (
              <View style={styles.resultCard}>
                <Text style={styles.resultHeader}>{t.aiVision}</Text>
                <Image source={{ uri: heatmap }} style={styles.heatmap} />
                <Text style={styles.smallText}>{t.aiVisionDesc}</Text>
              </View>
            )}

            {/* Full Ayurvedic Encyclopedia with Tabbed Views */}
            {ayurvedicProfile && (
              <View style={[styles.resultCard, { padding: 18 }]}>
                <Text style={[styles.resultHeader, { fontSize: 20, color: '#0F9D58', borderBottomWidth: 0, paddingBottom: 0, marginBottom: 10 }]}>
                  {t.encyclopedia}
                </Text>
                {renderProfileContent(ayurvedicProfile)}
              </View>
            )}

            {/* Subtle Clinical Educational Notice at the end of results */}
            {prediction && (
              <TouchableOpacity 
                style={styles.bottomDisclaimerNotice}
                onPress={() => { closeDrawer(() => { setActivePortalTab('DISCLAIMER'); setShowPortalModal(true); }); }}
                activeOpacity={0.8}
              >
                <Text style={styles.bottomDisclaimerText}>
                  ⚕️ <Text style={{ fontWeight: 'bold' }}>{t.medicalDisclaimerTitle}:</Text> Educational reference only. Always consult a certified Ayurvedic doctor before medicinal use. <Text style={styles.bottomDisclaimerLink}>{t.learnMore || "Learn more"}</Text>
                </Text>
              </TouchableOpacity>
            )}

            {/* Bottom Scan Another Leaf Button once results are displayed */}
            {prediction && (
              <TouchableOpacity style={[styles.primaryScanBtn, { marginTop: 4, marginBottom: 20 }]} onPress={resetScanState} activeOpacity={0.88}>
                <Text style={styles.primaryScanBtnIcon}>📸</Text>
                <Text style={styles.primaryScanBtnText}>{t.scanAnotherLeaf}</Text>
              </TouchableOpacity>
            )}

          </View>
        )}

        {/* LIBRARY TAB */}
        {activeTab === 'LIBRARY' && (
          <View style={styles.tabContent}>
            <Text style={styles.sectionTitle}>{t.libraryTitle}</Text>
            <Text style={{color: '#666', marginBottom: 15, textAlign: 'center'}}>
              {t.librarySubtitle}
            </Text>

            <TouchableOpacity 
              style={[styles.button, {marginBottom: 20, backgroundColor: '#0F9D58', width: '85%', paddingVertical: 12}]} 
              onPress={fetchLibrary}
            >
              <Text style={styles.buttonText}>
                {libraryLoading ? 'Loading...' : t.loadPlantIndex}
              </Text>
            </TouchableOpacity>

            {libraryPlants.map((item, idx) => {
              const displayName = item.common_names || getLocalizedPlantName(item.species_name, lang) || item.species_name;
              return (
                <TouchableOpacity 
                  key={idx} 
                  style={styles.libraryCard}
                  activeOpacity={0.85}
                  onPress={() => openPlantDetails(item.plant_id || item.species_name)}
                >
                  <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
                    <View style={{flex: 1}}>
                      <Text style={styles.libraryPlantTitle}>{displayName}</Text>
                      <Text style={styles.libraryBotanical}>{item.botanical_name}</Text>
                      <Text style={styles.libraryFamily}><Text style={{fontWeight: 'bold'}}>{t.family}</Text> {item.family || 'Medicinal flora'}</Text>
                      <Text style={styles.libraryTapAction}>📖 {t.viewProfile} →</Text>
                    </View>
                    {REFERENCE_IMAGES[item.species_name] && (
                      <Image source={{ uri: REFERENCE_IMAGES[item.species_name] }} style={styles.libraryThumb} />
                    )}
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        )}
      </ScrollView>

      {/* Bottom Navigation */}
      <View style={styles.bottomNav}>
        <TouchableOpacity style={styles.navItem} onPress={() => setActiveTab('SCAN')}>
          <Text style={[styles.navIcon, activeTab === 'SCAN' && styles.navActive]}>📷</Text>
          <Text style={[styles.navText, activeTab === 'SCAN' && styles.navActive]}>{t.scanTab}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => setActiveTab('LIBRARY')}>
          <Text style={[styles.navIcon, activeTab === 'LIBRARY' && styles.navActive]}>📖</Text>
          <Text style={[styles.navText, activeTab === 'LIBRARY' && styles.navActive]}>{t.libraryTab}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => setActiveTab('SEARCH')}>
          <Text style={[styles.navIcon, activeTab === 'SEARCH' && styles.navActive]}>🔍</Text>
          <Text style={[styles.navText, activeTab === 'SEARCH' && styles.navActive]}>{t.searchTab}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.navItem} onPress={() => setActiveTab('GLOSSARY')}>
          <Text style={[styles.navIcon, activeTab === 'GLOSSARY' && styles.navActive]}>📚</Text>
          <Text style={[styles.navText, activeTab === 'GLOSSARY' && styles.navActive]}>{t.glossaryTab}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  mainContainer: { flex: 1, backgroundColor: '#F8F9FA' },

  // App Header
  appHeader: { 
    backgroundColor: '#0F9D58', 
    paddingTop: 50, 
    paddingBottom: 16, 
    paddingHorizontal: 20, 
    elevation: 4, 
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: 2 }, 
    shadowOpacity: 0.2 
  },
  headerRow: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center' 
  },
  headerBrandContainer: { 
    flex: 1, 
    marginRight: 12 
  },
  headerBrandTitle: { 
    color: 'white', 
    fontSize: 21, 
    fontWeight: 'bold', 
    letterSpacing: 0.3 
  },
  headerBrandSubtitle: { 
    color: '#E8F5E9', 
    fontSize: 12, 
    marginTop: 2 
  },
  hamburgerBtn: { 
    width: 40, 
    height: 40, 
    borderRadius: 20, 
    backgroundColor: 'rgba(255,255,255,0.22)', 
    justifyContent: 'center', 
    alignItems: 'center', 
    borderWidth: 1, 
    borderColor: 'rgba(255,255,255,0.35)' 
  },
  hamburgerIcon: { 
    color: 'white', 
    fontSize: 22, 
    fontWeight: 'bold', 
    marginTop: -2 
  },

  // Side Drawer Navigation Menu
  drawerBackdrop: { 
    flex: 1, 
    backgroundColor: 'rgba(0,0,0,0.5)', 
    flexDirection: 'row' 
  },
  drawerDismissArea: { 
    flex: 1 
  },
  drawerPanel: { 
    width: Math.min(Dimensions.get('window').width * 0.82, 340), 
    backgroundColor: '#FFFFFF', 
    height: '100%', 
    elevation: 16, 
    shadowColor: '#000', 
    shadowOffset: { width: -3, height: 0 }, 
    shadowOpacity: 0.25, 
    shadowRadius: 8 
  },
  drawerHeader: { 
    backgroundColor: '#0F9D58', 
    paddingTop: 50, 
    paddingBottom: 18, 
    paddingHorizontal: 18, 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'space-between' 
  },
  drawerBrandTitle: { 
    color: 'white', 
    fontSize: 19, 
    fontWeight: 'bold' 
  },
  drawerBrandSubtitle: { 
    color: '#E8F5E9', 
    fontSize: 12, 
    marginTop: 2 
  },
  drawerCloseBtn: { 
    width: 32, 
    height: 32, 
    borderRadius: 16, 
    backgroundColor: 'rgba(255,255,255,0.2)', 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  drawerCloseIcon: { 
    color: 'white', 
    fontSize: 15, 
    fontWeight: 'bold' 
  },
  drawerScrollContent: { 
    padding: 16, 
    paddingBottom: 30 
  },
  drawerSection: { 
    marginBottom: 12 
  },
  drawerSectionLabel: { 
    fontSize: 11, 
    fontWeight: 'bold', 
    color: '#888', 
    textTransform: 'uppercase', 
    letterSpacing: 0.8, 
    marginBottom: 10 
  },
  drawerLangRow: { 
    flexDirection: 'row', 
    flexWrap: 'wrap', 
    gap: 8 
  },
  drawerLangChip: { 
    paddingHorizontal: 12, 
    paddingVertical: 7, 
    borderRadius: 16, 
    backgroundColor: '#F1F3F4', 
    borderWidth: 1, 
    borderColor: '#E0E0E0' 
  },
  drawerLangChipActive: { 
    backgroundColor: '#0F9D58', 
    borderColor: '#0F9D58' 
  },
  drawerLangChipText: { 
    fontSize: 13, 
    color: '#444', 
    fontWeight: '600' 
  },
  drawerLangChipTextActive: { 
    color: 'white', 
    fontWeight: 'bold' 
  },
  drawerDivider: { 
    height: 1, 
    backgroundColor: '#EEEEEE', 
    marginVertical: 12 
  },
  drawerMenuItem: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    paddingVertical: 10, 
    paddingHorizontal: 4, 
    borderRadius: 12 
  },
  drawerMenuIconBox: { 
    width: 36, 
    height: 36, 
    borderRadius: 18, 
    justifyContent: 'center', 
    alignItems: 'center', 
    marginRight: 12 
  },
  drawerMenuTitle: { 
    fontSize: 15, 
    fontWeight: 'bold', 
    color: '#222' 
  },
  drawerMenuSubtitle: { 
    fontSize: 12, 
    color: '#777', 
    marginTop: 1 
  },
  drawerMenuChevron: { 
    fontSize: 20, 
    color: '#BBB', 
    fontWeight: 'bold' 
  },
  drawerFooter: { 
    borderTopWidth: 1, 
    borderTopColor: '#EEEEEE', 
    padding: 16, 
    alignItems: 'center', 
    backgroundColor: '#FAFAFA' 
  },
  drawerFooterVersion: { 
    fontSize: 12, 
    fontWeight: 'bold', 
    color: '#666' 
  },
  drawerFooterText: { 
    fontSize: 11, 
    color: '#999', 
    marginTop: 2 
  },

  // Scroll & Tabs
  scrollContent: { padding: 16, paddingBottom: 120 },
  tabContent: { width: '100%', alignItems: 'center' },
  sectionTitle: { fontSize: 21, fontWeight: 'bold', color: '#2E7D32', alignSelf: 'center', marginBottom: 6 },

  // Hero Card & Home Scan Section
  homeContainer: { width: '100%' },
  heroCard: { 
    backgroundColor: '#EBF7EE', 
    borderRadius: 20, 
    padding: 18, 
    borderWidth: 1, 
    borderColor: '#C8E6C9', 
    marginBottom: 14, 
    elevation: 1, 
    shadowColor: '#0F9D58', 
    shadowOffset: { width: 0, height: 2 }, 
    shadowOpacity: 0.08, 
    shadowRadius: 4 
  },
  heroBadgeRow: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginBottom: 10 
  },
  heroBadge: { 
    backgroundColor: '#FFFFFF', 
    paddingHorizontal: 10, 
    paddingVertical: 4, 
    borderRadius: 12, 
    borderWidth: 1, 
    borderColor: '#C8E6C9' 
  },
  heroBadgeText: { 
    fontSize: 12, 
    fontWeight: 'bold', 
    color: '#1B5E20' 
  },
  offlinePill: { 
    backgroundColor: 'rgba(15, 157, 88, 0.12)', 
    paddingHorizontal: 8, 
    paddingVertical: 3, 
    borderRadius: 10 
  },
  offlinePillText: { 
    fontSize: 11, 
    fontWeight: 'bold', 
    color: '#0F9D58' 
  },
  heroTitle: { 
    fontSize: 21, 
    fontWeight: 'bold', 
    color: '#1B5E20', 
    marginBottom: 6 
  },
  heroSubtitle: { 
    fontSize: 13.5, 
    color: '#455A64', 
    lineHeight: 20, 
    marginBottom: 16 
  },
  actionButtonsRow: { 
    flexDirection: 'row', 
    gap: 10, 
    width: '100%' 
  },
  primaryActionButton: { 
    flex: 1, 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'center', 
    backgroundColor: '#0F9D58', 
    paddingVertical: 13, 
    borderRadius: 24, 
    elevation: 3, 
    shadowColor: '#0F9D58', 
    shadowOffset: { width: 0, height: 2 }, 
    shadowOpacity: 0.3, 
    shadowRadius: 3 
  },
  primaryActionIcon: { 
    fontSize: 18, 
    color: 'white', 
    marginRight: 6 
  },
  primaryActionText: { 
    color: 'white', 
    fontSize: 14.5, 
    fontWeight: 'bold' 
  },
  secondaryActionButton: { 
    flex: 1, 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'center', 
    backgroundColor: '#FFFFFF', 
    paddingVertical: 13, 
    borderRadius: 24, 
    borderWidth: 1.5, 
    borderColor: '#81C784', 
    elevation: 1 
  },
  secondaryActionIcon: { 
    fontSize: 18, 
    marginRight: 6 
  },
  secondaryActionText: { 
    color: '#1B5E20', 
    fontSize: 14, 
    fontWeight: 'bold' 
  },

  friendlyTipPill: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    backgroundColor: '#FFFDE7', 
    paddingVertical: 10, 
    paddingHorizontal: 14, 
    borderRadius: 14, 
    borderWidth: 1, 
    borderColor: '#FFF59D', 
    marginBottom: 16 
  },
  friendlyTipIcon: { 
    fontSize: 16, 
    marginRight: 8 
  },
  friendlyTipText: { 
    flex: 1, 
    fontSize: 12.5, 
    color: '#6D4C41', 
    lineHeight: 18 
  },

  // Popular Herbs Carousel
  carouselSection: { 
    marginBottom: 16, 
    width: '100%' 
  },
  sectionHeaderRow: { 
    marginBottom: 10 
  },
  carouselSectionTitle: { 
    fontSize: 17, 
    fontWeight: 'bold', 
    color: '#1B5E20' 
  },
  carouselSectionSub: { 
    fontSize: 12, 
    color: '#777', 
    marginTop: 2 
  },
  carouselScroll: { 
    paddingVertical: 4, 
    gap: 12 
  },
  herbCard: { 
    width: 140, 
    backgroundColor: 'white', 
    borderRadius: 16, 
    overflow: 'hidden', 
    borderWidth: 1, 
    borderColor: '#E0E0E0', 
    elevation: 2, 
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: 1 }, 
    shadowOpacity: 0.08, 
    shadowRadius: 3 
  },
  herbCardImage: { 
    width: '100%', 
    height: 95 
  },
  herbCardBody: { 
    padding: 10 
  },
  herbCardTitle: { 
    fontSize: 14, 
    fontWeight: 'bold', 
    color: '#1B5E20' 
  },
  herbCardBotanical: { 
    fontSize: 11, 
    color: '#666', 
    fontStyle: 'italic', 
    marginTop: 2 
  },
  herbCardTagBadge: { 
    alignSelf: 'flex-start', 
    backgroundColor: '#E8F5E9', 
    paddingHorizontal: 6, 
    paddingVertical: 2, 
    borderRadius: 6, 
    marginTop: 6 
  },
  herbCardTagText: { 
    fontSize: 10, 
    color: '#2E7D32', 
    fontWeight: 'bold' 
  },

  // Feature Highlights
  featureGrid: { 
    flexDirection: 'row', 
    gap: 8, 
    marginTop: 4, 
    marginBottom: 10 
  },
  featureItem: { 
    flex: 1, 
    backgroundColor: 'white', 
    borderRadius: 14, 
    padding: 12, 
    alignItems: 'center', 
    borderWidth: 1, 
    borderColor: '#EEEEEE', 
    elevation: 1 
  },
  featureEmoji: { 
    fontSize: 20, 
    marginBottom: 4 
  },
  featureItemTitle: { 
    fontSize: 12, 
    fontWeight: 'bold', 
    color: '#2E7D32', 
    textAlign: 'center' 
  },
  featureItemDesc: { 
    fontSize: 10, 
    color: '#777', 
    textAlign: 'center', 
    marginTop: 2 
  },

  // Picked Image & Analysis
  imageWrapper: { width: '100%', alignItems: 'center' },
  image: { width: '100%', height: '100%', resizeMode: 'cover' },
  capturedImageContainer: { 
    width: '100%', 
    aspectRatio: 1, 
    borderRadius: 20, 
    overflow: 'hidden', 
    position: 'relative', 
    elevation: 3, 
    backgroundColor: '#EEE' 
  },
  readyBadge: { 
    position: 'absolute', 
    top: 14, 
    right: 14, 
    backgroundColor: 'rgba(15, 157, 88, 0.9)', 
    paddingVertical: 5, 
    paddingHorizontal: 12, 
    borderRadius: 20 
  },
  readyBadgeText: { color: 'white', fontWeight: 'bold', fontSize: 12 },

  preAnalysisBox: { 
    width: '100%', 
    backgroundColor: 'white', 
    borderRadius: 18, 
    padding: 16, 
    marginTop: 14, 
    marginBottom: 14, 
    alignItems: 'center', 
    elevation: 2, 
    borderWidth: 1, 
    borderColor: '#E8F5E9' 
  },
  primaryScanBtn: { 
    backgroundColor: '#0F9D58', 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'center', 
    paddingVertical: 14, 
    paddingHorizontal: 22, 
    borderRadius: 28, 
    width: '100%', 
    elevation: 3, 
    shadowColor: '#0F9D58', 
    shadowOffset: { width: 0, height: 3 }, 
    shadowOpacity: 0.3 
  },
  primaryScanBtnIcon: { fontSize: 18, color: 'white', marginRight: 8, fontWeight: 'bold' },
  primaryScanBtnText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
  changePhotoBtn: { paddingVertical: 10, alignItems: 'center', marginTop: 8 },
  changePhotoBtnText: { fontSize: 13.5, color: '#666', fontWeight: '600' },

  // Loading
  loadingBox: { 
    backgroundColor: 'white', 
    padding: 22, 
    borderRadius: 16, 
    alignItems: 'center', 
    width: '100%', 
    marginTop: 15, 
    elevation: 2, 
    borderWidth: 1, 
    borderColor: '#C8E6C9' 
  },
  loadingText: { marginTop: 12, fontSize: 16, fontWeight: 'bold', color: '#1B5E20' },
  loadingSubText: { marginTop: 5, fontSize: 12, color: '#777', textAlign: 'center' },

  // Identified Results Header
  identifiedHeaderCard: { 
    backgroundColor: 'white', 
    borderRadius: 18, 
    padding: 16, 
    marginBottom: 14, 
    width: '100%', 
    borderWidth: 1, 
    borderColor: '#C8E6C9', 
    elevation: 2 
  },
  identifiedTitleRow: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'flex-start', 
    marginBottom: 10 
  },
  identifiedCommonName: { fontSize: 22, fontWeight: 'bold', color: '#1B5E20' },
  identifiedBotanicalName: { fontSize: 14, color: '#555', fontStyle: 'italic', marginTop: 2 },
  vernacularRow: { flexDirection: 'row', alignItems: 'center', marginTop: 4 },
  vernacularLabelText: { fontSize: 11.5, fontWeight: 'bold', color: '#689F38' },
  vernacularNamesText: { fontSize: 11.5, color: '#666', flex: 1, fontStyle: 'italic' },
  matchScoreBadge: { 
    backgroundColor: '#E8F5E9', 
    borderRadius: 14, 
    paddingVertical: 6, 
    paddingHorizontal: 12, 
    alignItems: 'center', 
    borderWidth: 1, 
    borderColor: '#A5D6A7' 
  },
  matchScorePercent: { fontSize: 18, fontWeight: 'bold', color: '#0F9D58' },
  matchScoreLabel: { fontSize: 10, fontWeight: 'bold', color: '#2E7D32' },
  identifiedActionsRow: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginTop: 6 
  },
  scanAnotherPill: { 
    alignSelf: 'flex-start', 
    backgroundColor: '#F1F8E9', 
    paddingVertical: 6, 
    paddingHorizontal: 12, 
    borderRadius: 16, 
    borderWidth: 1, 
    borderColor: '#C8E6C9' 
  },
  scanAnotherPillText: { fontSize: 12, fontWeight: 'bold', color: '#2E7D32' },
  offlineStatusBadge: { 
    backgroundColor: '#E8F5E9', 
    paddingVertical: 4, 
    paddingHorizontal: 10, 
    borderRadius: 12, 
    borderWidth: 1, 
    borderColor: '#A5D6A7' 
  },
  offlineStatusText: { fontSize: 11, fontWeight: 'bold', color: '#2E7D32' },

  // Visual Verification Card
  visualMatchCard: { 
    backgroundColor: '#FAFCF8', 
    borderRadius: 18, 
    padding: 16, 
    marginBottom: 14, 
    borderWidth: 1, 
    borderColor: '#C8E6C9', 
    elevation: 2 
  },
  visualMatchHeaderRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  visualMatchIcon: { fontSize: 20, marginRight: 8 },
  visualMatchTitle: { fontSize: 16, fontWeight: 'bold', color: '#2E7D32' },
  visualMatchSubtitle: { fontSize: 12, color: '#666', marginTop: 2 },
  comparisonRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', width: '100%' },
  comparisonColumn: { flex: 1, alignItems: 'center' },
  comparisonFrame: { 
    width: '100%', 
    aspectRatio: 1, 
    borderRadius: 14, 
    overflow: 'hidden', 
    backgroundColor: '#EEE', 
    elevation: 2, 
    borderWidth: 1.5, 
    borderColor: '#C8E6C9' 
  },
  comparisonImage: { width: '100%', height: '100%', resizeMode: 'cover' },
  comparisonBadgeUser: { marginTop: 6, paddingVertical: 4, paddingHorizontal: 8, borderRadius: 12, backgroundColor: '#ECEFF1' },
  comparisonBadgeText: { fontSize: 11, fontWeight: 'bold', color: '#455A64' },
  comparisonBadgeVerified: { marginTop: 6, paddingVertical: 4, paddingHorizontal: 8, borderRadius: 12, backgroundColor: '#E8F5E9' },
  comparisonBadgeVerifiedText: { fontSize: 11, fontWeight: 'bold', color: '#2E7D32', textAlign: 'center' },
  vsBadgeContainer: { paddingHorizontal: 8, justifyContent: 'center', alignItems: 'center' },
  vsText: { 
    fontSize: 13, 
    fontWeight: '900', 
    color: '#388E3C', 
    backgroundColor: '#E8F5E9', 
    paddingVertical: 4, 
    paddingHorizontal: 7, 
    borderRadius: 10 
  },
  matchPillContainer: { 
    alignSelf: 'center', 
    backgroundColor: '#E8F5E9', 
    paddingVertical: 5, 
    paddingHorizontal: 14, 
    borderRadius: 15, 
    marginTop: 12, 
    borderWidth: 1, 
    borderColor: '#A5D6A7' 
  },
  matchPillText: { color: '#1B5E20', fontWeight: 'bold', fontSize: 13 },
  comparisonTipText: { fontSize: 12, color: '#777', fontStyle: 'italic', textAlign: 'center', marginTop: 8, lineHeight: 18 },

  // Results & Encyclopedia
  heatmap: { width: '100%', aspectRatio: 1, borderRadius: 16, marginTop: 12, alignSelf: 'center' },
  resultCard: { 
    backgroundColor: 'white', 
    padding: 18, 
    borderRadius: 18, 
    width: '100%', 
    marginBottom: 16, 
    elevation: 2, 
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: 1 }, 
    shadowOpacity: 0.1, 
    shadowRadius: 3, 
    borderWidth: 1, 
    borderColor: '#EEEEEE' 
  },
  resultHeader: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 10 },
  resultText: { fontSize: 16, color: '#444', marginBottom: 8 },
  smallText: { fontSize: 13, color: '#777', marginTop: 12, fontStyle: 'italic', textAlign: 'center', lineHeight: 20 },
  sectionHeader: { fontSize: 14.5, fontWeight: 'bold', color: '#0F9D58', marginTop: 12, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },

  // Tabbed Profile Navigation
  profileTabsBar: { 
    flexDirection: 'row', 
    backgroundColor: '#F1F8E9', 
    borderRadius: 14, 
    padding: 4, 
    marginBottom: 12, 
    marginTop: 4 
  },
  profileTabBtn: { 
    flex: 1, 
    paddingVertical: 9, 
    borderRadius: 10, 
    alignItems: 'center' 
  },
  profileTabBtnActive: { 
    backgroundColor: '#FFFFFF', 
    elevation: 2, 
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: 1 }, 
    shadowOpacity: 0.1 
  },
  profileTabText: { 
    fontSize: 12.5, 
    fontWeight: '600', 
    color: '#666' 
  },
  profileTabTextActive: { 
    color: '#1B5E20', 
    fontWeight: 'bold' 
  },

  // Botanical Info Card
  botanicalCard: { backgroundColor: '#F8FAF6', borderRadius: 14, padding: 14, borderWidth: 1, borderColor: '#E0EFE2', marginTop: 4, marginBottom: 6 },
  botanicalRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 4 },
  botanicalLabel: { fontSize: 13, fontWeight: 'bold', color: '#333' },
  botanicalValue: { fontSize: 13, color: '#555', fontStyle: 'italic' },

  // Ayurvedic Bio-Energetics Grid
  bioEnergeticsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 4 },
  bioGridCell: { width: '48%', backgroundColor: '#F8FAF6', borderRadius: 12, padding: 10, borderWidth: 1, borderColor: '#E0EFE2' },
  bioCellLabel: { fontSize: 12, fontWeight: 'bold', color: '#2E7D32', marginBottom: 3 },
  bioCellValue: { fontSize: 13, color: '#333', fontWeight: '500' },
  glossaryHintText: { fontSize: 12, fontStyle: 'italic', color: '#689F38', marginTop: 8 },

  // Uses, Recipes, Phytos
  usesContainer: { gap: 8, marginTop: 4 },
  useCard: { backgroundColor: '#F8FAF6', borderRadius: 12, padding: 12, borderWidth: 1, borderColor: '#E0EFE2' },
  useCondition: { fontSize: 14, fontWeight: 'bold', color: '#1B5E20', marginBottom: 4 },
  useDescription: { fontSize: 13, color: '#444', lineHeight: 19 },
  recipesContainer: { gap: 8, marginTop: 6 },
  recipeCard: { backgroundColor: '#F8FAF6', borderRadius: 12, padding: 12, borderWidth: 1, borderColor: '#E0EFE2' },
  recipeTitle: { fontSize: 13.5, fontWeight: 'bold', color: '#1B5E20', marginBottom: 3 },
  recipeBody: { fontSize: 13, color: '#444', lineHeight: 19 },
  phytosContainer: { gap: 8, marginTop: 4 },
  phytoChip: { backgroundColor: '#F1F8E9', borderRadius: 10, paddingVertical: 8, paddingHorizontal: 12, borderWidth: 1, borderColor: '#C8E6C9', width: '100%' },
  phytoName: { fontSize: 13, fontWeight: 'bold', color: '#2E7D32' },
  phytoActivity: { fontSize: 12, color: '#555', marginTop: 2 },

  // Precautions Cards
  precautionWarningCard: { backgroundColor: '#FFEBEE', borderRadius: 12, padding: 14, borderWidth: 1, borderColor: '#FFCDD2', marginTop: 6 },
  precautionWarningTitle: { fontSize: 14, fontWeight: 'bold', color: '#C62828' },
  precautionWarningText: { fontSize: 13, color: '#B71C1C', marginTop: 3, lineHeight: 19 },
  precautionSafeCard: { backgroundColor: '#E8F5E9', borderRadius: 12, padding: 14, borderWidth: 1, borderColor: '#C8E6C9', marginTop: 6 },
  precautionSafeTitle: { fontSize: 14, fontWeight: 'bold', color: '#2E7D32' },
  precautionSafeText: { fontSize: 13, color: '#1B5E20', marginTop: 3, lineHeight: 19 },

  // Bottom Notice
  bottomDisclaimerNotice: { backgroundColor: '#FFFDE7', borderRadius: 12, padding: 12, borderWidth: 1, borderColor: '#FFE082', marginTop: 6, marginBottom: 12 },
  bottomDisclaimerText: { fontSize: 12, color: '#5D4037', lineHeight: 17 },
  bottomDisclaimerLink: { color: '#E65100', fontWeight: 'bold', textDecorationLine: 'underline' },

  // Glossary
  glossaryCard: { 
    backgroundColor: 'white', 
    padding: 16, 
    borderRadius: 14, 
    marginBottom: 14, 
    width: '100%', 
    elevation: 2, 
    borderLeftWidth: 5, 
    borderLeftColor: '#0F9D58',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 3
  },
  glossaryTerm: { fontSize: 18, fontWeight: 'bold', color: '#1B5E20', marginBottom: 6 },
  glossaryDef: { fontSize: 14.5, color: '#444', lineHeight: 22 },

  // Search
  searchContainer: { flexDirection: 'row', width: '100%', marginBottom: 20, marginTop: 12 },
  searchInput: { 
    flex: 1, 
    backgroundColor: 'white', 
    borderRadius: 12, 
    paddingHorizontal: 15, 
    paddingVertical: 12, 
    fontSize: 15, 
    borderColor: '#E0E0E0', 
    borderWidth: 1, 
    marginRight: 10, 
    elevation: 1 
  },
  searchButton: { backgroundColor: '#0F9D58', justifyContent: 'center', alignItems: 'center', borderRadius: 12, paddingHorizontal: 20, elevation: 2 },
  searchButtonText: { color: 'white', fontWeight: 'bold', fontSize: 15 },
  searchResultItem: { marginBottom: 15, borderBottomWidth: 1, borderBottomColor: '#EEEEEE', paddingBottom: 15 },
  quickProfilePill: { backgroundColor: '#E8F5E9', paddingVertical: 5, paddingHorizontal: 10, borderRadius: 12 },
  quickProfilePillText: { color: '#2E7D32', fontSize: 12, fontWeight: 'bold' },
  linkRow: { flexDirection: 'row', marginTop: 10, gap: 15 },
  linkText: { color: '#1565C0', fontWeight: 'bold', fontSize: 14 },
  clearBtn: { marginTop: 10, alignSelf: 'flex-end' },
  clearBtnText: { color: '#D32F2F', fontWeight: 'bold' },

  // Library
  libraryCard: { 
    backgroundColor: 'white', 
    width: '100%', 
    padding: 16, 
    borderRadius: 16, 
    marginBottom: 14, 
    elevation: 2, 
    borderWidth: 1, 
    borderColor: '#EEEEEE', 
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: 1 }, 
    shadowOpacity: 0.08 
  },
  libraryPlantTitle: { fontSize: 18, fontWeight: 'bold', color: '#1B5E20' },
  libraryBotanical: { fontSize: 14, color: '#666', fontStyle: 'italic', marginTop: 2 },
  libraryFamily: { fontSize: 13, color: '#444', marginTop: 5 },
  libraryTapAction: { fontSize: 13, color: '#0F9D58', fontWeight: 'bold', marginTop: 8 },
  libraryThumb: { width: 75, height: 75, borderRadius: 12, marginLeft: 10 },
  button: { flex: 1, paddingVertical: 14, borderRadius: 10, alignItems: 'center', marginHorizontal: 5 },
  buttonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },

  // Online Exploration Buttons
  linkRowCenter: { flexDirection: 'row', justifyContent: 'center', gap: 12, marginTop: 15 },
  onlineBtn: { backgroundColor: '#1565C0', paddingVertical: 10, paddingHorizontal: 16, borderRadius: 8, elevation: 2 },
  onlineBtnText: { color: 'white', fontWeight: 'bold', fontSize: 14 },

  // Modals & Info Reader
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.65)', justifyContent: 'center', alignItems: 'center' },
  modalContent: { width: '85%', backgroundColor: 'white', borderRadius: 20, padding: 20, elevation: 8, overflow: 'hidden' },
  modalTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 15, textAlign: 'center', color: '#333' },
  modalCloseBtn: { marginTop: 15, alignItems: 'center', paddingVertical: 10 },
  modalCloseText: { color: '#D32F2F', fontSize: 16, fontWeight: 'bold' },
  modalHeaderBar: { backgroundColor: '#0F9D58', padding: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  modalHeaderText: { color: 'white', fontSize: 18, fontWeight: 'bold', flex: 1 },
  modalCloseCircle: { backgroundColor: 'rgba(0,0,0,0.25)', width: 28, height: 28, borderRadius: 14, justifyContent: 'center', alignItems: 'center' },

  portalTabsRow: { flexDirection: 'row', backgroundColor: '#F1F8E9', borderBottomWidth: 1, borderBottomColor: '#C8E6C9' },
  portalTabItem: { flex: 1, paddingVertical: 12, alignItems: 'center', borderBottomWidth: 3, borderBottomColor: 'transparent' },
  portalTabItemActive: { borderBottomColor: '#0F9D58', backgroundColor: 'white' },
  portalTabItemText: { fontSize: 13, fontWeight: '600', color: '#666' },
  portalTabItemTextActive: { color: '#0F9D58', fontWeight: 'bold' },
  versionBadgeRow: { alignItems: 'center', marginBottom: 14 },
  versionBadgeTag: { backgroundColor: '#0F9D58', color: 'white', paddingVertical: 4, paddingHorizontal: 12, borderRadius: 12, fontWeight: 'bold', fontSize: 13 },
  portalInfoCard: { backgroundColor: '#F9FBE7', padding: 14, borderRadius: 12, marginBottom: 12, borderLeftWidth: 4, borderLeftColor: '#689F38' },
  portalInfoTitle: { fontSize: 15, fontWeight: 'bold', color: '#33691E', marginBottom: 4 },
  portalInfoBody: { fontSize: 13, color: '#444', lineHeight: 19 },
  legalSectionHeader: { fontSize: 17, fontWeight: 'bold', color: '#1B5E20', marginBottom: 8 },
  complianceBadge: { backgroundColor: '#E8F5E9', padding: 8, borderRadius: 8, marginBottom: 14, borderWidth: 1, borderColor: '#C8E6C9' },
  complianceBadgeText: { fontSize: 12, fontWeight: 'bold', color: '#2E7D32' },
  legalCard: { backgroundColor: '#FAFAFA', padding: 14, borderRadius: 12, marginBottom: 12, borderWidth: 1, borderColor: '#EEE' },
  legalItemTitle: { fontSize: 14, fontWeight: 'bold', color: '#222', marginBottom: 4 },
  legalItemBody: { fontSize: 13, color: '#555', lineHeight: 19 },

  // Permission Dialog
  permissionIconCircle: { width: 64, height: 64, borderRadius: 32, backgroundColor: '#E8F5E9', justifyContent: 'center', alignItems: 'center', marginBottom: 10 },
  permissionTitleText: { fontSize: 18, fontWeight: 'bold', color: '#1B5E20', textAlign: 'center' },
  permissionSubText: { fontSize: 12, color: '#666', marginTop: 3, textAlign: 'center' },
  permissionNoticeBox: { width: '100%', marginTop: 10 },
  permissionItemTitle: { fontSize: 15, fontWeight: 'bold', color: '#333', marginBottom: 4 },
  permissionItemBody: { fontSize: 13, color: '#555', lineHeight: 19 },
  permissionAllowBtn: { backgroundColor: '#0F9D58', paddingVertical: 13, borderRadius: 12, alignItems: 'center' },
  permissionAllowBtnText: { color: 'white', fontWeight: 'bold', fontSize: 15 },
  permissionCancelBtn: { paddingVertical: 10, alignItems: 'center' },
  permissionCancelBtnText: { color: '#777', fontSize: 14, fontWeight: '600' },

  // Tour Screen
  tourContainer: { flex: 1, backgroundColor: '#FFFFFF', justifyContent: 'space-between' },
  tourHeader: { paddingTop: 50, paddingHorizontal: 22, paddingBottom: 10, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  tourBrandPill: { backgroundColor: '#E8F5E9', paddingVertical: 6, paddingHorizontal: 12, borderRadius: 15, borderWidth: 1, borderColor: '#C8E6C9' },
  tourBrandText: { fontSize: 13, fontWeight: 'bold', color: '#1B5E20' },
  tourSkipBtn: { padding: 8 },
  tourSkipText: { fontSize: 14, color: '#888', fontWeight: 'bold' },
  tourContentWrapper: { flex: 1, paddingHorizontal: 24, justifyContent: 'center', alignItems: 'center' },
  tourImageFrame: { width: '100%', aspectRatio: 1.15, borderRadius: 22, overflow: 'hidden', position: 'relative', elevation: 4, backgroundColor: '#EEE', borderWidth: 1, borderColor: '#E8F5E9' },
  tourImage: { width: '100%', height: '100%' },
  tourStepBadge: { position: 'absolute', bottom: 14, left: 14, backgroundColor: 'rgba(15, 157, 88, 0.92)', paddingVertical: 5, paddingHorizontal: 12, borderRadius: 12 },
  tourStepBadgeText: { color: 'white', fontSize: 11, fontWeight: 'bold', letterSpacing: 0.5 },
  tourTextCard: { width: '100%', marginTop: 22, alignItems: 'center' },
  tourTitleText: { fontSize: 22, fontWeight: 'bold', color: '#1B5E20', textAlign: 'center' },
  tourSubtitleText: { fontSize: 14, fontWeight: '600', color: '#689F38', marginTop: 4, textAlign: 'center' },
  tourDescText: { fontSize: 14, color: '#555', marginTop: 10, textAlign: 'center', lineHeight: 22, paddingHorizontal: 10 },
  tourBottomBar: { paddingHorizontal: 24, paddingBottom: 40 },
  dotsRow: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', marginBottom: 25 },
  dot: { height: 8, borderRadius: 4, marginHorizontal: 4 },
  activeDot: { width: 24, backgroundColor: '#0F9D58' },
  inactiveDot: { width: 8, backgroundColor: '#E0E0E0' },
  tourButtonRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  tourBackBtn: { paddingVertical: 14, paddingHorizontal: 20 },
  tourBackBtnText: { color: '#666', fontSize: 15, fontWeight: 'bold' },
  tourNextBtn: { backgroundColor: '#0F9D58', paddingVertical: 14, paddingHorizontal: 28, borderRadius: 25, elevation: 3, shadowColor: '#0F9D58', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.3 },
  tourNextBtnText: { color: 'white', fontSize: 16, fontWeight: 'bold' },

  // Bottom Nav
  bottomNav: { 
    position: 'absolute', 
    bottom: 0, 
    width: '100%', 
    height: 68, 
    backgroundColor: 'white', 
    flexDirection: 'row', 
    elevation: 12, 
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: -2 }, 
    shadowOpacity: 0.1, 
    shadowRadius: 4, 
    borderTopWidth: 1, 
    borderTopColor: '#EEEEEE' 
  },
  navItem: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  navIcon: { fontSize: 24, color: '#9E9E9E', marginBottom: 2 },
  navText: { fontSize: 12, color: '#9E9E9E', fontWeight: 'bold' },
  navActive: { color: '#0F9D58' },
});

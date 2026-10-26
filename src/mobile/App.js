import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, Image, TouchableOpacity, ScrollView, ActivityIndicator, TextInput, Linking, Modal } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as FileSystem from 'expo-file-system/legacy';
import Constants from 'expo-constants';

import { translations, GLOSSARY_DATA, LANGUAGES, LANG_LABELS } from './constants/i18n';
import { REFERENCE_IMAGES } from './constants/references';
import {
  getLocalizedPlantName,
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

export default function App() {
  const [activeTab, setActiveTab] = useState('SCAN'); // 'SCAN', 'LIBRARY', 'SEARCH', 'GLOSSARY'
  const [lang, setLang] = useState('en');
  const [isLangModalVisible, setLangModalVisible] = useState(false);
  const t = translations[lang] || translations.en;

  // Scan State
  const [imageUri, setImageUri] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [ayurvedicProfile, setAyurvedicProfile] = useState(null);
  const [loading, setLoading] = useState(false);

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Library State
  const [libraryPlants, setLibraryPlants] = useState([]);
  const [libraryLoading, setLibraryLoading] = useState(false);

  // Selected Profile Modal in Library
  const [selectedPlantModal, setSelectedPlantModal] = useState(null);

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
      // Seamless offline fallback
    } finally {
      setLibraryLoading(false);
    }

    // 100% Offline Fallback: Load from indexed local catalog
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
      // Seamless offline fallback
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
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!result.canceled) {
      resetScanState();
      setImageUri(result.assets[0].uri);
    }
  };

  const takePhoto = async () => {
    const permissionResult = await ImagePicker.requestCameraPermissionsAsync();
    if (!permissionResult.granted) {
      alert("Camera permission is required to take a live picture!");
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
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

        // 2. Seamless local/offline knowledge lookup (by ID, prediction name, or common name)
        if (!resolved) {
          resolved = getOfflinePlantById(predictData.plant_id) ||
                     getOfflinePlantById(predictData.prediction) ||
                     getOfflinePlantById(predictData.common_name);
        }

        // 3. Guaranteed fallback profile so the Ayurvedic Encyclopedia card NEVER disappears
        if (!resolved) {
          resolved = generateFallbackProfile(predictData.prediction, predictData.common_name);
        }

        setAyurvedicProfile(resolved);
      }
    } catch (error) {
      alert("Offline notice: To scan new leaves with AI vision, ensure the local network or API server is running. You can still browse the Library, Search symptoms, and view the Glossary 100% offline.");
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
      // Seamless offline fallback
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

  // Helper to render Ayurvedic Profile details
  const renderProfileContent = (profileData) => {
    if (!profileData) return null;
    const { plant = {}, profile = {}, therapeutic_uses = [], phytochemicals = [], contraindications = [] } = profileData;

    return (
      <View>
        <Text style={[styles.resultHeader, { fontSize: 20, color: '#0F9D58', borderBottomWidth: 0, paddingBottom: 0 }]}>
          {t.encyclopedia}
        </Text>

        {/* Botanical Info */}
        <Text style={styles.sectionHeader}>{t.botanicalInfo}</Text>
        <View style={styles.bulletList}>
          <Text style={styles.bulletItem}>• <Text style={styles.boldText}>{t.scientific}</Text> {plant.botanical_name}</Text>
          <Text style={styles.bulletItem}>• <Text style={styles.boldText}>{t.family}</Text> {plant.family}</Text>
          <Text style={styles.bulletItem}>• <Text style={styles.boldText}>{t.habitat}</Text> {plant.habitat}</Text>
        </View>

        {/* Ayurvedic Properties */}
        <Text style={styles.sectionHeader}>{t.ayurvedicProp}</Text>
        <View style={styles.bulletList}>
          <Text style={styles.bulletItem}>• <Text style={styles.boldText}>{t.dosha}</Text> {getDynamicTranslation(profile.dosha_effect, lang) || 'Balances Vata & Pitta'}</Text>
          <Text style={styles.bulletItem}>• <Text style={styles.boldText}>{t.rasa}</Text> {getDynamicTranslation(profile.rasa, lang) || 'Tikta, Kashaya'}</Text>
          <Text style={styles.bulletItem}>• <Text style={styles.boldText}>{t.guna}</Text> {getDynamicTranslation(profile.guna, lang) || 'Laghu, Ruksha'}</Text>
          <Text style={styles.bulletItem}>• <Text style={styles.boldText}>{t.virya}</Text> {getDynamicTranslation(profile.virya, lang) || 'Sheeta'}</Text>
          <Text style={styles.bulletItem}>• <Text style={styles.boldText}>{t.vipaka}</Text> {getDynamicTranslation(profile.vipaka, lang) || 'Katu'}</Text>
          <Text style={styles.bulletItem}>• <Text style={styles.boldText}>{t.prabhava}</Text> {getDynamicTranslation(profile.prabhava, lang) || 'Rasayana'}</Text>
          <Text style={[styles.bulletItem, { fontStyle: 'italic', marginTop: 6, color: '#689F38' }]}>
            {t.glossaryHint}
          </Text>
        </View>

        {/* Medicinal Uses */}
        <Text style={styles.sectionHeader}>{t.medicinalUses}</Text>
        <View style={styles.bulletList}>
          {therapeutic_uses.length > 0 ? (
            therapeutic_uses.map((use, idx) => (
              <Text key={idx} style={styles.bulletItem}>
                • <Text style={styles.boldText}>{use.condition}:</Text> {use.use_description}
              </Text>
            ))
          ) : (
            <Text style={styles.bulletItem}>• Traditional immunity and digestive aid.</Text>
          )}
        </View>

        {/* Recipes & Preparations */}
        <Text style={styles.sectionHeader}>{t.recipes}</Text>
        <View style={styles.bulletList}>
          <Text style={styles.bulletItem}>• {t.recipeDecoction}</Text>
          <Text style={styles.bulletItem}>• {t.recipePaste}</Text>
        </View>

        {/* Active Compounds */}
        {phytochemicals.length > 0 && (
          <>
            <Text style={styles.sectionHeader}>{t.activeCompounds}</Text>
            <View style={styles.bulletList}>
              {phytochemicals.map((phyto, idx) => (
                <Text key={idx} style={styles.bulletItem}>
                  • <Text style={styles.boldText}>{phyto.compound_name}:</Text> {phyto.activity}
                </Text>
              ))}
            </View>
          </>
        )}

        {/* Precautions */}
        {contraindications.length > 0 ? (
          <>
            <Text style={[styles.sectionHeader, { color: '#D32F2F' }]}>{t.precautions}</Text>
            <View style={[styles.bulletList, { backgroundColor: '#FFEBEE', padding: 12, borderRadius: 8, marginTop: 4 }]}>
              {contraindications.map((contra, idx) => (
                <Text key={idx} style={[styles.bulletItem, { color: '#B71C1C' }]}>
                  • <Text style={styles.boldText}>{contra.condition} ({contra.severity}):</Text> {contra.notes}
                </Text>
              ))}
            </View>
          </>
        ) : (
          <>
            <Text style={[styles.sectionHeader, { color: '#388E3C' }]}>{t.precautions}</Text>
            <View style={styles.bulletList}>
              <Text style={styles.bulletItem}>• {t.precautionSafe}</Text>
            </View>
          </>
        )}

        {/* Online Exploration */}
        <Text style={[styles.sectionHeader, { color: '#1565C0', marginTop: 25 }]}>{t.exploreOnline}</Text>
        <View style={styles.linkRowCenter}>
          <TouchableOpacity style={styles.onlineBtn} onPress={() => openLink('google', plant.botanical_name || plant.species_name)}>
            <Text style={styles.onlineBtnText}>🌐 {t.readArticles}</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.onlineBtn, { backgroundColor: '#D32F2F' }]} onPress={() => openLink('youtube', plant.botanical_name || plant.species_name)}>
            <Text style={styles.onlineBtnText}>▶️ {t.watchVideos}</Text>
          </TouchableOpacity>
        </View>
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
      {/* App Header */}
      <View style={styles.appHeader}>
        <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
          <View>
            <Text style={styles.appTitle}>{t.appTitle}</Text>
            <Text style={styles.appSubtitle}>{t.appSubtitle}</Text>
          </View>
          <TouchableOpacity 
            style={styles.langToggle} 
            onPress={() => setLangModalVisible(true)}
          >
            <Text style={styles.langText}>{LANG_LABELS[lang]}</Text>
            <View style={styles.langIconBox}>
              <Text style={styles.langIconText}>A/文</Text>
            </View>
          </TouchableOpacity>
        </View>
      </View>

      {/* Language Selection Modal */}
      <Modal visible={isLangModalVisible} transparent={true} animationType="fade" onRequestClose={() => setLangModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Select Language / भाषा चुनें</Text>
            {LANGUAGES.map((l) => (
              <TouchableOpacity key={l} style={[styles.langOption, lang === l && styles.langOptionActive]} onPress={() => { setLang(l); setLangModalVisible(false); }}>
                <Text style={[styles.langOptionText, lang === l && styles.langOptionTextActive]}>{LANG_LABELS[l]}</Text>
              </TouchableOpacity>
            ))}
            <TouchableOpacity style={styles.modalCloseBtn} onPress={() => setLangModalVisible(false)}>
              <Text style={styles.modalCloseText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Plant Profile Modal for Library Items */}
      <Modal visible={!!selectedPlantModal} transparent={true} animationType="slide" onRequestClose={() => setSelectedPlantModal(null)}>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { width: '92%', maxHeight: '85%', padding: 0 }]}>
            <View style={styles.modalHeaderBar}>
              <Text style={styles.modalHeaderText} numberOfLines={1}>
                {getLocalizedPlantName(selectedPlantModal?.plant?.species_name, lang)}
              </Text>
              <TouchableOpacity onPress={() => setSelectedPlantModal(null)} style={styles.modalCloseCircle}>
                <Text style={{color: 'white', fontWeight: 'bold', fontSize: 16}}>✕</Text>
              </TouchableOpacity>
            </View>
            <ScrollView contentContainerStyle={{ padding: 18 }}>
              {renderProfileContent(selectedPlantModal)}
            </ScrollView>
          </View>
        </View>
      </Modal>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        
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
                      <Text style={{fontWeight: 'bold', fontSize: 18, color: '#2E7D32'}}>{pName}</Text>
                      <Text style={{fontSize: 14, color: '#777', fontStyle: 'italic'}}>{res.plant?.botanical_name}</Text>
                      <Text style={{color: '#333', marginTop: 6}}>
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
            {/* Image Box */}
            {imageUri ? (
              <View style={styles.imageWrapper}>
                <Image source={{ uri: imageUri }} style={styles.image} />
                
                {/* Appealing Action Bar: Directly Below The Taken Image */}
                <View style={styles.scanActionBelowImageBox}>
                  <TouchableOpacity style={styles.appealingScanBtn} onPress={resetScanState}>
                    <Text style={styles.appealingScanBtnIcon}>📸</Text>
                    <Text style={styles.appealingScanBtnText}>{t.scanAnotherLeaf}</Text>
                  </TouchableOpacity>
                  
                  <View style={styles.quickActionSmallRow}>
                    <TouchableOpacity style={styles.smallRetakeBtn} onPress={pickImage}>
                      <Text style={styles.smallRetakeText}>🖼️ {t.gallery}</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.smallRetakeBtn} onPress={takePhoto}>
                      <Text style={styles.smallRetakeText}>📷 {t.camera}</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              </View>
            ) : (
              <View style={{flexDirection: 'row', justifyContent: 'space-between', width: '100%', gap: 15, marginBottom: 10}}>
                <TouchableOpacity style={[styles.placeholder, {flex: 1, aspectRatio: 1}]} onPress={pickImage}>
                  <Text style={styles.placeholderIcon}>🖼️</Text>
                  <Text style={[styles.placeholderText, {fontSize: 16}]}>{t.gallery}</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.placeholder, {flex: 1, aspectRatio: 1}]} onPress={takePhoto}>
                  <Text style={styles.placeholderIcon}>📷</Text>
                  <Text style={[styles.placeholderText, {fontSize: 16}]}>{t.camera}</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Selected but not yet analyzed */}
            {imageUri && !loading && !prediction && (
              <View style={styles.actionRow}>
                <TouchableOpacity style={[styles.button, { backgroundColor: '#E0E0E0' }]} onPress={() => setImageUri(null)}>
                  <Text style={[styles.buttonText, { color: '#333' }]}>{t.retake}</Text>
                </TouchableOpacity>
                <TouchableOpacity style={[styles.button, styles.analyzeButton]} onPress={uploadAndAnalyze}>
                  <Text style={styles.buttonText}>{t.scanNow}</Text>
                </TouchableOpacity>
              </View>
            )}

            {loading && <ActivityIndicator size="large" color="#0F9D58" style={{ marginTop: 30 }} />}

            {/* Prediction Rejected Card */}
            {prediction && prediction.status === 'rejected' && (
              <View style={[styles.resultCard, { borderColor: '#F44336', borderWidth: 2 }]}>
                <Text style={[styles.resultHeader, { color: '#D32F2F' }]}>{t.scanRejected}</Text>
                <Text style={styles.resultText}>{prediction.message}</Text>
                <TouchableOpacity style={styles.clearBtn} onPress={resetScanState}>
                  <Text style={styles.clearBtnText}>{t.retake}</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Prediction Success Header Card */}
            {prediction && prediction.status === 'success' && (
              <View style={styles.resultCard}>
                <Text style={styles.resultHeader}>{t.identifiedSpecies}</Text>
                <Text style={styles.resultText}>
                  {t.commonName} <Text style={[styles.boldText, { color: '#1B5E20', fontSize: 18 }]}>
                    {getLocalizedPlantName(prediction.prediction, lang)}
                  </Text>
                </Text>
                <Text style={styles.resultText}>
                  {t.confidence} <Text style={styles.boldText}>{(prediction.confidence * 100).toFixed(1)}%</Text>
                </Text>
              </View>
            )}

            {/* Visual Botanical Comparison Card (Cleaned Single Emojis) */}
            {prediction && prediction.status === 'success' && getReferenceImage() && (
              <View style={[styles.resultCard, { padding: 16, backgroundColor: '#FAFCF8', borderColor: '#C8E6C9' }]}>
                <View style={{flexDirection: 'row', alignItems: 'center', marginBottom: 6}}>
                  <Text style={{fontSize: 18, marginRight: 6}}>🌿</Text>
                  <Text style={[styles.resultHeader, { marginBottom: 0, borderBottomWidth: 0, paddingBottom: 0, fontSize: 17, color: '#2E7D32' }]}>
                    {t.visualMatchTitle}
                  </Text>
                </View>
                <Text style={{color: '#666', fontSize: 13, marginBottom: 14}}>
                  {t.visualMatchSubtitle}
                </Text>

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
                        {t.referenceHerb}: {getLocalizedPlantName(prediction.prediction, lang)}
                      </Text>
                    </View>
                  </View>
                </View>

                {/* Match confirmation pill */}
                <View style={styles.matchPillContainer}>
                  <Text style={styles.matchPillText}>
                    ✓ {t.visualMatchBadge} ({(prediction.confidence * 100).toFixed(1)}%)
                  </Text>
                </View>
                <Text style={styles.comparisonTipText}>
                  {t.visualMatchTip}
                </Text>
              </View>
            )}

            {/* AI Vision Heatmap (Grad-CAM) */}
            {heatmap && (
              <View style={styles.resultCard}>
                <Text style={styles.resultHeader}>{t.aiVision}</Text>
                <Image source={{ uri: heatmap }} style={styles.heatmap} />
                <Text style={styles.smallText}>{t.aiVisionDesc}</Text>
              </View>
            )}

            {/* Full Ayurvedic Encyclopedia */}
            {ayurvedicProfile && (
              <View style={[styles.resultCard, { padding: 20 }]}>
                {renderProfileContent(ayurvedicProfile)}
              </View>
            )}

            {/* Medical Disclaimer Box (Single ⚕️ Symbol) */}
            <View style={styles.disclaimerStandaloneBox}>
              <View style={{flexDirection: 'row', alignItems: 'center', marginBottom: 8}}>
                <Text style={{fontSize: 22, marginRight: 8}}>⚕️</Text>
                <Text style={styles.disclaimerHeaderStandalone}>
                  {t.medicalDisclaimerTitle}
                </Text>
              </View>
              <Text style={styles.disclaimerTextStandalone}>
                {t.medicalDisclaimerBody}
              </Text>
            </View>

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
                <View key={idx} style={styles.libraryCard}>
                  <View style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start'}}>
                    <View style={{flex: 1}}>
                      <Text style={styles.libraryPlantTitle}>{displayName}</Text>
                      <Text style={styles.libraryBotanical}>{item.botanical_name}</Text>
                      <Text style={styles.libraryFamily}><Text style={{fontWeight: 'bold'}}>{t.family}</Text> {item.family || 'Medicinal flora'}</Text>
                    </View>
                    {REFERENCE_IMAGES[item.species_name] && (
                      <Image source={{ uri: REFERENCE_IMAGES[item.species_name] }} style={styles.libraryThumb} />
                    )}
                  </View>
                  
                  <TouchableOpacity 
                    style={styles.libraryActionBtn} 
                    onPress={() => openPlantDetails(item.plant_id || item.species_name)}
                  >
                    <Text style={styles.libraryActionBtnText}>📖 {t.viewProfile}</Text>
                  </TouchableOpacity>
                </View>
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
  appHeader: { 
    backgroundColor: '#0F9D58', 
    paddingTop: 50, 
    paddingBottom: 20, 
    paddingHorizontal: 20, 
    elevation: 4, 
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: 2 }, 
    shadowOpacity: 0.2 
  },
  appTitle: { color: 'white', fontSize: 24, fontWeight: 'bold' },
  appSubtitle: { color: '#E8F5E9', fontSize: 14, marginTop: 4 },
  langToggle: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    backgroundColor: 'rgba(255,255,255,0.18)', 
    paddingHorizontal: 12, 
    paddingVertical: 8, 
    borderRadius: 25,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)'
  },
  langText: { color: 'white', fontWeight: 'bold', fontSize: 16, marginRight: 8 },
  langIconBox: { backgroundColor: 'white', paddingHorizontal: 6, paddingVertical: 3, borderRadius: 6, elevation: 2 },
  langIconText: { color: '#0F9D58', fontSize: 12, fontWeight: 'bold' },
  scrollContent: { padding: 18, paddingBottom: 110 },
  tabContent: { width: '100%', alignItems: 'center' },
  sectionTitle: { fontSize: 21, fontWeight: 'bold', color: '#2E7D32', alignSelf: 'center', marginBottom: 6 },
  
  glossaryCard: { 
    backgroundColor: 'white', 
    padding: 16, 
    borderRadius: 12, 
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

  searchContainer: { flexDirection: 'row', width: '100%', marginBottom: 20, marginTop: 12 },
  searchInput: { 
    flex: 1, 
    backgroundColor: 'white', 
    borderRadius: 10, 
    paddingHorizontal: 15, 
    paddingVertical: 12, 
    fontSize: 15, 
    borderColor: '#E0E0E0', 
    borderWidth: 1, 
    marginRight: 10, 
    elevation: 1 
  },
  searchButton: { backgroundColor: '#0F9D58', justifyContent: 'center', alignItems: 'center', borderRadius: 10, paddingHorizontal: 20, elevation: 2 },
  searchButtonText: { color: 'white', fontWeight: 'bold', fontSize: 15 },
  searchResultItem: { marginBottom: 15, borderBottomWidth: 1, borderBottomColor: '#EEEEEE', paddingBottom: 15 },
  linkRow: { flexDirection: 'row', marginTop: 10, gap: 15 },
  linkText: { color: '#1565C0', fontWeight: 'bold', fontSize: 14 },
  
  actionRow: { flexDirection: 'row', justifyContent: 'space-between', width: '100%', marginTop: 16 },
  button: { flex: 1, paddingVertical: 14, borderRadius: 10, alignItems: 'center', marginHorizontal: 5 },

  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.6)', justifyContent: 'center', alignItems: 'center' },
  modalContent: { width: '85%', backgroundColor: 'white', borderRadius: 16, padding: 20, elevation: 8, overflow: 'hidden' },
  modalTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 15, textAlign: 'center', color: '#333' },
  langOption: { paddingVertical: 13, borderBottomWidth: 1, borderBottomColor: '#EEE', alignItems: 'center' },
  langOptionActive: { backgroundColor: '#E8F5E9' },
  langOptionText: { fontSize: 16, color: '#333' },
  langOptionTextActive: { color: '#0F9D58', fontWeight: 'bold' },
  modalCloseBtn: { marginTop: 15, alignItems: 'center', paddingVertical: 10 },
  modalCloseText: { color: '#D32F2F', fontSize: 16, fontWeight: 'bold' },
  analyzeButton: { backgroundColor: '#0F9D58', elevation: 3 },
  buttonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
  clearBtn: { marginTop: 10, alignSelf: 'flex-end' },
  clearBtnText: { color: '#D32F2F', fontWeight: 'bold' },

  linkRowCenter: { flexDirection: 'row', justifyContent: 'center', gap: 12, marginTop: 15 },
  onlineBtn: { backgroundColor: '#1565C0', paddingVertical: 10, paddingHorizontal: 16, borderRadius: 8, elevation: 2 },
  onlineBtnText: { color: 'white', fontWeight: 'bold', fontSize: 14 },
  
  placeholder: { 
    width: '100%', 
    aspectRatio: 1, 
    backgroundColor: '#E8F5E9', 
    borderRadius: 20, 
    justifyContent: 'center', 
    alignItems: 'center', 
    marginBottom: 10, 
    borderWidth: 2, 
    borderColor: '#A5D6A7', 
    borderStyle: 'dashed' 
  },
  placeholderIcon: { fontSize: 40, marginBottom: 10 },
  placeholderText: { color: '#2E7D32', fontSize: 17, fontWeight: 'bold' },
  
  imageWrapper: { width: '100%', alignItems: 'center' },
  image: { width: '100%', aspectRatio: 1, borderRadius: 20, marginBottom: 12, elevation: 3 },
  
  scanActionBelowImageBox: {
    width: '100%',
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 12,
    marginBottom: 15,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    borderWidth: 1,
    borderColor: '#E8F5E9',
    alignItems: 'center'
  },
  appealingScanBtn: {
    backgroundColor: '#0F9D58',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 13,
    paddingHorizontal: 20,
    borderRadius: 25,
    width: '100%',
    elevation: 2,
    shadowColor: '#0F9D58',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3
  },
  appealingScanBtnIcon: { fontSize: 18, color: 'white', marginRight: 8 },
  appealingScanBtnText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
  quickActionSmallRow: { flexDirection: 'row', justifyContent: 'center', gap: 15, marginTop: 8 },
  smallRetakeBtn: { paddingVertical: 6, paddingHorizontal: 12, borderRadius: 15, backgroundColor: '#F1F8E9' },
  smallRetakeText: { color: '#33691E', fontWeight: '600', fontSize: 13 },

  comparisonRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', width: '100%' },
  comparisonColumn: { flex: 1, alignItems: 'center' },
  comparisonFrame: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: 12,
    overflow: 'hidden',
    backgroundColor: '#EEE',
    elevation: 2,
    borderWidth: 1.5,
    borderColor: '#C8E6C9'
  },
  comparisonImage: { width: '100%', height: '100%', resizeMode: 'cover' },
  comparisonBadgeUser: {
    marginTop: 6,
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 12,
    backgroundColor: '#ECEFF1'
  },
  comparisonBadgeText: { fontSize: 11, fontWeight: 'bold', color: '#455A64' },
  comparisonBadgeVerified: {
    marginTop: 6,
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 12,
    backgroundColor: '#E8F5E9'
  },
  comparisonBadgeVerifiedText: { fontSize: 11, fontWeight: 'bold', color: '#2E7D32', textAlign: 'center' },
  vsBadgeContainer: {
    paddingHorizontal: 8,
    justifyContent: 'center',
    alignItems: 'center'
  },
  vsText: {
    fontSize: 14,
    fontWeight: '900',
    color: '#81C784',
    backgroundColor: '#E8F5E9',
    paddingVertical: 5,
    paddingHorizontal: 7,
    borderRadius: 12
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

  heatmap: { width: '100%', aspectRatio: 1, borderRadius: 16, marginTop: 12, alignSelf: 'center' },
  
  resultCard: { 
    backgroundColor: 'white', 
    padding: 18, 
    borderRadius: 16, 
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
  resultHeader: { fontSize: 18, fontWeight: 'bold', color: '#333', marginBottom: 12, borderBottomWidth: 1, borderBottomColor: '#eee', paddingBottom: 8 },
  resultText: { fontSize: 16, color: '#444', marginBottom: 8 },
  smallText: { fontSize: 13, color: '#777', marginTop: 12, fontStyle: 'italic', textAlign: 'center', lineHeight: 20 },
  
  sectionHeader: { fontSize: 15, fontWeight: 'bold', color: '#0F9D58', marginTop: 18, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  bulletList: { marginLeft: 0 },
  bulletItem: { fontSize: 14.5, color: '#444', marginBottom: 6, lineHeight: 22 },
  boldText: { fontWeight: 'bold', color: '#222' },

  disclaimerStandaloneBox: {
    backgroundColor: '#FFFDE7',
    padding: 16,
    borderRadius: 14,
    width: '100%',
    marginTop: 10,
    marginBottom: 20,
    borderWidth: 1.5,
    borderColor: '#FFE082',
    elevation: 2,
    shadowColor: '#F57F17',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2
  },
  disclaimerHeaderStandalone: { fontSize: 15, fontWeight: 'bold', color: '#E65100' },
  disclaimerTextStandalone: { fontSize: 13, color: '#5D4037', lineHeight: 20 },

  libraryCard: {
    backgroundColor: 'white',
    width: '100%',
    padding: 16,
    borderRadius: 14,
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
  libraryThumb: { width: 65, height: 65, borderRadius: 10, marginLeft: 10 },
  libraryActionBtn: {
    marginTop: 12,
    backgroundColor: '#0F9D58',
    paddingVertical: 9,
    borderRadius: 8,
    alignItems: 'center'
  },
  libraryActionBtnText: { color: 'white', fontWeight: 'bold', fontSize: 14 },

  modalHeaderBar: {
    backgroundColor: '#0F9D58',
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  modalHeaderText: { color: 'white', fontSize: 18, fontWeight: 'bold', flex: 1 },
  modalCloseCircle: {
    backgroundColor: 'rgba(0,0,0,0.2)',
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center'
  },

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

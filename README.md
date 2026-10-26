# 🌿 Sanjeevani Scan AI — Ayurvedic Botanical Scanner

Sanjeevani Scan AI is an offline-capable Ayurvedic botanical scanner and clinical knowledge engine that pairs deep learning computer vision with authentic Ayurvedic pharmacopoeia.

For the comprehensive system architecture, developer notes, and Intel Iris/CPU setup guide, please refer to **[ANTIGRAVITY_SYSTEM_GUIDE.md](file:///d:/Sanjeevani%20Scan%20AI/ANTIGRAVITY_SYSTEM_GUIDE.md)**.

---

## ⚡ Quick Start

### 1. Backend Server (FastAPI + PyTorch)
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 2. Mobile Client (React Native + Expo)
```powershell
cd src\mobile
npm install
npx expo start
```
Scan the displayed QR code with the **Expo Go** mobile app on your phone.

---

## 📦 Key Highlights
- **66 Plant Classes Recognized:** Powered by convolutional neural networks with Out-Of-Distribution rejection.
- **Grad-CAM Attention Heatmaps:** Visualizes which botanical features the AI used for identification.
- **63 Botanical Species Database:** Full Ayurvedic profiles (*Dosha, Rasa, Guna, Virya, Vipaka, Prabhava*), therapeutic uses, and phytochemicals.
- **FAISS Semantic Search:** Search herbs by symptom or disorder using vector similarity.
- **6 Indian Languages:** Full UI and glossary support in English, Hindi, Kannada, Tamil, Telugu, and Malayalam.
- **100% Offline Capability:** Bundled database enables search, library browsing, and glossary lookup without internet access.

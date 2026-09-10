import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium
import sqlite3
from database import init_db, get_all_shelters, get_user, save_or_update_user
from rules import evaluate_safesync, get_coordinates

# Initialize Database
init_db()

st.set_page_config(page_title="SAFESYNC Prototype", page_icon="🚨", layout="wide")

# Session State Defaults
defaults = {
    'username': 'ramesh',
    'name': 'Ramesh Kumar', 'location': 'Guntur Central', 'age': 70,
    'num_people': 6, 'children': 1, 'elderly': 2, 'disabilities': 1,
    'mobility': 'Limited Mobility', 'language': 'English',
    'hazard_type': 'Flood', 'severity': 'High',
    'battery_level': 100, 'offline_mode': False, 'low_battery_mode': False,
    'walkie_history': [], 'chat_history': [],
    'sos_triggered': False, 'fm_frequency': '93.5 FM'
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- TEXT-TO-SPEECH (TTS) AUDIO ASSISTANT ---
LANG_CODES = {
    'English': 'en-IN',
    'Telugu': 'te-IN',
    'Hindi': 'hi-IN',
    'Kannada': 'kn-IN',
    'Tamil': 'ta-IN'
}

def speak_text(text, lang_code):
    """Triggers browser-native voice audio in selected language."""
    clean_text = text.replace("'", "\\'").replace("\n", " ")
    js_code = f"""
    <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{clean_text}');
        msg.lang = '{lang_code}';
        msg.rate = 0.9;
        window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0, width=0)

# --- COMPLETE MULTILINGUAL TRANSLATION DICTIONARY ---
I18N = {
    'English': {
        'title': 'SAFESYNC',
        'subtitle': 'Intelligent Multi-Hazard Risk and Relocation Assistance System',
        'setup': '🚨 SAFESYNC Setup',
        'lang_select': '🌐 Language / భాష / भाषा / ಭಾಷೆ / மொழி',
        'offline_toggle': '📶 Offline Mode',
        'low_battery_toggle': '🔋 Low Battery Mode',
        'low_battery_warn': '🔋 LOW BATTERY MODE ENABLED — Minimal UI Active',
        'offline_walkie_warn': '📶 Mobile Network Unavailable – Walkie-Talkie & FM Broadcast Active',
        'hazard_config': 'Hazard Configuration',
        'hazard_type': 'Hazard Type',
        'severity_level': 'Severity Level',
        'nav_label': 'Navigation',
        'nav_dash': '1. Emergency Dashboard',
        'nav_walkie': '2. Walkie-Talkie & FM Broadcast',
        'nav_watch': '3. Smartwatch Simulation',
        'nav_assistant': '4. Multilingual AI Assistant',
        'metric_hazard': 'Active Hazard',
        'metric_severity': 'Severity',
        'metric_risk': 'Risk Score',
        'metric_affected': 'Affected People',
        'metric_vulnerability': 'Vulnerability',
        'metric_priority': 'Relocation Priority',
        'profile_header': '2. Habitation Profile Settings',
        'search_db': '🔍 Load Profile from DB',
        'save_db': '💾 Save Profile to DB',
        'name': 'Name',
        'location': 'Location (Search City/Address)',
        'num_people': 'Total Family Members',
        'children': 'Children',
        'elderly': 'Elderly Residents',
        'disabilities': 'Persons with Disabilities',
        'mobility': 'Mobility Status',
        'assess_header': '3. Red-Zone & Vulnerability Assessment',
        'zone_status': 'Zone Status',
        'calc_vuln': 'Calculated Vulnerability',
        'offline_map_msg': '📶 Offline/Low-Battery Mode active: Map rendering paused. Using local cached spatial text.',
        'shelter_header': '4. Shelter Capacity & Recommendation',
        'rec_shelter': 'Recommended Shelter',
        'distance': 'Distance',
        'avail_cap': 'Available Capacity',
        'status': 'Status',
        'all_shelters': 'Available System Shelters',
        'col_sname': 'Shelter Name',
        'col_sloc': 'Location',
        'col_stot': 'Total Cap',
        'col_socc': 'Occupied Cap',
        'col_sava': 'Available Cap',
        'col_sramp': 'Accessibility Ramp',
        'col_sdist': 'Distance',
        'alert_header': '5. Emergency Alert System',
        'alert_text': '🚨 CRITICAL ALERT — IMMEDIATE RELOCATION RECOMMENDED',
        'action_plan': 'Action Plan',
        'instruct': ['Move to a safe location.', 'Carry essential items.', 'Follow the recommended route.', 'Reach the assigned shelter.'],
        'btn_read_guidance': '🔊 Read Guidance Aloud (Voice Assistant)',
        'walkie_title': '📻 Walkie-Talkie & FM Emergency Broadcast Module',
        'walkie_sub': 'Direct Radio Simulation & FM Station Broadcasting (Offline Peer-to-Peer)',
        'radio_ctrl': 'Radio Controls',
        'status_label': 'Status',
        'status_online': 'ONLINE (P2P READY)',
        'status_offline': 'EMERGENCY MODE (OFFLINE MESH & FM BROADCAST)',
        'act_channel': 'Active Channel / FM Station',
        'quick_trans': 'Predefined Quick Transmissions',
        'btn_evac': '🚨 I need evacuation assistance',
        'btn_trapped': '⚠️ Person trapped',
        'btn_shelter': '🏫 Shelter required',
        'btn_ptt': '🎙️ HOLD TO TALK (Push-to-Talk)',
        'btn_bcast': '📢 EMERGENCY FM BROADCAST',
        'btn_read_latest': '📢 Read Latest Radio Message Aloud',
        'incoming_stream': 'Incoming Radio Frequency Stream',
        'voice_sent': '🎙️ [VOICE TRANSMISSION SENT]',
        'watch_title': '⌚ Smartwatch Interface Simulation',
        'watch_sub': 'SAFESYNC Wearable Notification & Alert Receiver',
        'watch_telemetry': 'Watch System Telemetry',
        'btn_sos': '🚨 TRIGGER SMARTWATCH SOS',
        'btn_cancel_sos': 'Cancel SOS Signal',
        'sos_active': '🆘 SOS DISTRESS SIGNAL ACTIVE! Coordinates broadcasted to nearest rescue unit.',
        'hazards': {
            'Flood': 'Flood 🌊', 'Cyclone': 'Cyclone 🌪️', 'Fire': 'Fire 🔥',
            'Earthquake': 'Earthquake 🌎', 'Gas Leak': 'Gas Leak 💨',
            'Building Collapse': 'Building Collapse 🏚️', 'Road Accident': 'Road Accident 🚗'
        },
        'severities': {'Low': 'Low', 'Medium': 'Medium', 'High': 'High', 'Critical': 'Critical'},
        'vulnerability_levels': {'Low': 'Low', 'Medium': 'Medium', 'High': 'High'},
        'relocation_priorities': {
            'Immediate Relocation': 'Immediate Relocation',
            'High Priority': 'High Priority',
            'Medium Priority': 'Medium Priority',
            'Low Priority': 'Low Priority'
        },
        'mobility_opts': {'Normal': 'Normal', 'Limited Mobility': 'Limited Mobility', 'Wheelchair': 'Wheelchair'},
        'channels': ['Rescue Team', 'Local Volunteers', 'Nearby Users', '93.5 FM Emergency Radio', '104.0 FM Disaster Alert']
    },
    'Telugu': {
        'title': 'సేఫ్‌సింక్ (SAFESYNC)',
        'subtitle': 'బహుళ-ప్రమాదాల రిస్క్ మరియు తరలింపు సహాయక వ్యవస్థ',
        'setup': '🚨 సేఫ్‌సింక్ అమరికలు',
        'lang_select': '🌐 భాష (Language)',
        'offline_toggle': '📶 ఆఫ్‌లైన్ మోడ్',
        'low_battery_toggle': '🔋 తక్కువ బ్యాటరీ మోడ్',
        'low_battery_warn': '🔋 తక్కువ బ్యాటరీ మోడ్ ప్రారంభించబడింది — పరిమిత స్క్రీన్',
        'offline_walkie_warn': '📶 మొబైల్ నెట్‌వర్క్ అందుబాటులో లేదు – వాకీ-టాకీ మరియు FM ప్రసారం సక్రియంగా ఉన్నాయి',
        'hazard_config': 'ప్రమాద ఎంపిక',
        'hazard_type': 'ప్రమాద రకం',
        'severity_level': 'తీవ్రత స్థాయి',
        'nav_label': 'నెవిగేషన్',
        'nav_dash': '1. అత్యవసర డాష్‌బోర్డ్',
        'nav_walkie': '2. వాకీ-టాకీ & FM ప్రసారం',
        'nav_watch': '3. స్మార్ట్‌వాచ్ సిమ్యులేషన్',
        'nav_assistant': '4. బహుభాషా AI అసిస్టెంట్',
        'metric_hazard': 'ప్రస్తుత ప్రమాదం',
        'metric_severity': 'తీవ్రత',
        'metric_risk': 'రిస్క్ స్కోర్',
        'metric_affected': 'బాధిత ప్రజలు',
        'metric_vulnerability': 'బాధపడే అవకాశం',
        'metric_priority': 'తరలింపు ప్రాధాన్యత',
        'profile_header': '2. నివాస ప్రొఫైల్ వివరాలు',
        'search_db': '🔍 డేటాబేస్ ప్రొఫైల్ తీసుకోండి',
        'save_db': '💾 ప్రొఫైల్ సేవ్ చేయండి',
        'name': 'పేరు',
        'location': 'ప్రాంతం (నగరం/చిరునామా శోధించండి)',
        'num_people': 'కుటుంబ సభ్యుల సంఖ్య',
        'children': 'పిల్లలు',
        'elderly': 'వృద్ధులు',
        'disabilities': 'దివ్యాంగులు',
        'mobility': 'కదలిక పరిస్థితి',
        'assess_header': '3. రెడ్-జోన్ & సున్నితత్వ అంచనా',
        'zone_status': 'జోన్ స్థితి',
        'calc_vuln': 'లెక్కింబడిన సున్నితత్వం',
        'offline_map_msg': '📶 ఆఫ్‌లైన్ మోడ్: మ్యాప్ నిలిపివేయబడింది. స్థానిక సమాచారం ఉపయోగించబడుతోంది.',
        'shelter_header': '4. ఆశ్రయ సామర్థ్యం & సిఫార్సు',
        'rec_shelter': 'సిఫార్సు చేయబడిన ఆశ్రయం',
        'distance': 'దూరం',
        'avail_cap': 'అందుబాటులో ఉన్న సామర్థ్యం',
        'status': 'స్థితి',
        'all_shelters': 'అందుబాటులో ఉన్న ఆశ్రయాలు',
        'col_sname': 'ఆశ్రయం పేరు',
        'col_sloc': 'ప్రాంతం',
        'col_stot': 'మొత్తం సామర్థ్యం',
        'col_socc': 'ఆక్రమిత సామర్థ్యం',
        'col_sava': 'మిగిలిన సామర్థ్యం',
        'col_sramp': 'ర్యాంప్ సౌకర్యం',
        'col_sdist': 'దూరం',
        'alert_header': '5. అత్యవసర హెచ్చరిక వ్యవస్థ',
        'alert_text': '🚨 అత్యవసర హెచ్చరిక — వెంటనే ఖాళీ చేయడం సిఫార్సు చేయబడింది',
        'action_plan': 'చర్యల ప్రణాళిక',
        'instruct': ['సురక్షితమైన ప్రాంతానికి వెళ్లండి.', 'ముఖ్యమైన వస్తువులను తీసుకెళ్లండి.', 'సిఫార్సు చేసిన మార్గాన్ని అనుసరించండి.', 'కేటాయించిన ఆశ్రయానికి చేరుకోండి.'],
        'btn_read_guidance': '🔊 సూచనలను వినండి (వాయిస్ అసిస్టెంట్)',
        'walkie_title': '📻 వాకీ-టాకీ & FM అత్యవసర ప్రసార మాడ్యూల్',
        'walkie_sub': 'రేడియో సిమ్యులేషన్ మరియు FM రేడియో ప్రసారం (ఆఫ్‌లైన్)',
        'radio_ctrl': 'రేడియో నియంత్రణలు',
        'status_label': 'స్థితి',
        'status_online': 'ఆన్‌లైన్',
        'status_offline': 'అత్యవసర ఆఫ్‌లైన్ మోడ్ (FM ప్రసారం)',
        'act_channel': 'ప్రస్తుత ఛానెల్ / FM స్టేషన్',
        'quick_trans': 'ముందస్తు సందేశాలు',
        'btn_evac': '🚨 నాకు ఖాళీ చేయడంలో సహాయం కావాలి',
        'btn_trapped': '⚠️ వ్యక్తులు చిక్కుకున్నారు',
        'btn_shelter': '🏫 ఆశ్రయం కావాలి',
        'btn_ptt': '🎙️ మాట్లాడటానికి నొక్కి ఉంచండి (PTT)',
        'btn_bcast': '📢 అత్యవసర FM ప్రసారం',
        'btn_read_latest': '📢 తాజా రేడియో సందేశాన్ని వినండి',
        'incoming_stream': 'రేడియో సందేశాలు',
        'voice_sent': '🎙️ [వాయిస్ మెసేజ్ పంపబడింది]',
        'watch_title': '⌚ స్మార్ట్‌వాచ్ ఇంటర్‌ఫేస్ సిమ్యులేషన్',
        'watch_sub': 'సేఫ్‌సింక్ ధరించగల హెచ్చరిక రిసీవర్',
        'watch_telemetry': 'వాచ్ సిస్టమ్ డేటా',
        'btn_sos': '🚨 స్మార్ట్‌వాచ్ SOS సక్రియం చేయండి',
        'btn_cancel_sos': 'SOS రద్దు చేయండి',
        'sos_active': '🆘 SOS అత్యవసర సంకేతం పంపబడింది! స్థానం రెస్క్యూ బృందానికి చేరింది.',
        'hazards': {
            'Flood': 'వరద 🌊', 'Cyclone': 'తుఫాను 🌪️', 'Fire': 'అగ్నిప్రమాదం 🔥',
            'Earthquake': 'భూకంపం 🌎', 'Gas Leak': 'గ్యాస్ లీకేజీ 💨',
            'Building Collapse': 'భవనం కూలిపోవడం 🏚️', 'Road Accident': 'రోడ్డు ప్రమాదం 🚗'
        },
        'severities': {'Low': 'తక్కువ', 'Medium': 'మధ్యస్థం', 'High': 'ఎక్కువ', 'Critical': 'అత్యంత క్లిష్టమైనది'},
        'vulnerability_levels': {'Low': 'తక్కువ', 'Medium': 'మధ్యస్థం', 'High': 'ఎక్కువ (High)'},
        'relocation_priorities': {
            'Immediate Relocation': 'వెంటనే ఖాళీ చేయాలి (Immediate)',
            'High Priority': 'అధిక ప్రాధాన్యత (High Priority)',
            'Medium Priority': 'మధ్యస్థ ప్రాధాన్యత (Medium Priority)',
            'Low Priority': 'తక్కువ ప్రాధాన్యత (Low Priority)'
        },
        'mobility_opts': {'Normal': 'సాధారణం', 'Limited Mobility': 'పరిమిత కదలిక', 'Wheelchair': 'వీల్‌చైర్'},
        'channels': ['రెస్క్యూ టీమ్', 'స్థానిక వాలంటీర్లు', 'సమీప వినియోగదారులు', '93.5 FM అత్యవసర రేడియో', '104.0 FM విపత్తు హెచ్చరిక']
    },
    'Hindi': {
        'title': 'सेफसिंक (SAFESYNC)',
        'subtitle': 'इंटेलिजेंट मल्टी-हार्ड रिस्क और रीलोकेशन सहायता प्रणाली',
        'setup': '🚨 सेफसिंक सेटिंग्स',
        'lang_select': '🌐 भाषा (Language)',
        'offline_toggle': '📶 ऑफलाइन मोड',
        'low_battery_toggle': '🔋 लो बैटरी मोड',
        'low_battery_warn': '🔋 लो बैटरी मोड सक्रिय — सीमित डिस्प्ले',
        'offline_walkie_warn': '📶 मोबाइल नेटवर्क उपलब्ध नहीं है – वॉकी-टॉकी और एफएम प्रसारण सक्रिय',
        'hazard_config': 'आपदा चयन',
        'hazard_type': 'आपदा का प्रकार',
        'severity_level': 'गंभीरता का स्तर',
        'nav_label': 'नेविगेशन',
        'nav_dash': '1. आपातकालीन डैशबोर्ड',
        'nav_walkie': '2. वॉकी-टॉकी और एफएम प्रसारण',
        'nav_watch': '3. स्मार्टवॉच सिमुलेशन',
        'nav_assistant': '4. बहुभाषी एआई सहायक',
        'metric_hazard': 'सक्रिय आपदा',
        'metric_severity': 'गंभीरता',
        'metric_risk': 'जोखिम स्कोर',
        'metric_affected': 'प्रभावित लोग',
        'metric_vulnerability': 'संवेदनशीलता',
        'metric_priority': 'निकासी प्राथमिकता',
        'profile_header': '2. आवास प्रोफ़ाइल सेटिंग्स',
        'search_db': '🔍 डेटाबेस से प्रोफ़ाइल लोड करें',
        'save_db': '💾 प्रोफ़ाइल सहेजें',
        'name': 'नाम',
        'location': 'स्थान (शहर/पता खोजें)',
        'num_people': 'परिवार के कुल सदस्य',
        'children': 'बच्चे',
        'elderly': 'बुजुर्ग नागरिक',
        'disabilities': 'दिव्यांग जन',
        'mobility': 'गतिशीलता की स्थिति',
        'assess_header': '3. रेड-ज़ोन और संवेदनशीलता मूल्यांकन',
        'zone_status': 'ज़ोन की स्थिति',
        'calc_vuln': 'आकलित संवेदनशीलता',
        'offline_map_msg': '📶 ऑफलाइन मोड: मानचित्र निष्पादित नहीं है। स्थानीय डेटा का उपयोग किया जा रहा है।',
        'shelter_header': '4. आश्रय क्षमता और सिफारिश',
        'rec_shelter': 'अनुशंसित आश्रय स्थल',
        'distance': 'दूरी',
        'avail_cap': 'उपलब्ध क्षमता',
        'status': 'स्थिति',
        'all_shelters': 'उपलब्ध प्रणाली आश्रय स्थल',
        'col_sname': 'आश्रय का नाम',
        'col_sloc': 'स्थान',
        'col_stot': 'कुल क्षमता',
        'col_socc': 'अधिकृत क्षमता',
        'col_sava': 'उपलब्ध क्षमता',
        'col_sramp': 'रैंप सुविधा',
        'col_sdist': 'दूरी',
        'alert_header': '5. आपातकालीन चेतावनी प्रणाली',
        'alert_text': '🚨 आपातकालीन चेतावनी — तत्काल निकासी की सिफारिश की गई है',
        'action_plan': 'कार्य योजना',
        'instruct': ['सुरक्षित स्थान पर जाएं।', 'आवश्यक सामान साथ रखें।', 'अनुशंसित मार्ग का पालन करें।', 'आवंटित आश्रय स्थल पर पहुंचे।'],
        'btn_read_guidance': '🔊 दिशा-निर्देश सुनें (वॉइस असिस्टेंट)',
        'walkie_title': '📻 वॉकी-टॉकी और एफएम आपातकालीन संचार मॉड्यूल',
        'walkie_sub': 'रेडियो सिमुलेशन और एफएम प्रसारण (ऑफलाइन)',
        'radio_ctrl': 'रेडियो नियंत्रण',
        'status_label': 'स्थिति',
        'status_online': 'ऑनलाइन',
        'status_offline': 'आपातकालीन मोड (ऑफलाइन एफएम प्रसारण)',
        'act_channel': 'सक्रिय चैनल / एफएम स्टेशन',
        'quick_trans': 'पूर्वनिर्धारित त्वरित संदेश',
        'btn_evac': '🚨 मुझे निकासी सहायता की आवश्यकता है',
        'btn_trapped': '⚠️ व्यक्ति फंसा हुआ है',
        'btn_shelter': '🏫 आश्रय की आवश्यकता है',
        'btn_ptt': '🎙️ बात करने के लिए दबाकर रखें (PTT)',
        'btn_bcast': '📢 आपातकालीन एफएम प्रसारण',
        'btn_read_latest': '📢 नवीनतम रेडियो संदेश सुनें',
        'incoming_stream': 'रेडियो संदेश स्ट्रीम',
        'voice_sent': '🎙️ [वॉयस मैसेज भेजा गया]',
        'watch_title': '⌚ स्मार्टवॉच इंटरफ़ेस सिमुलेशन',
        'watch_sub': 'सेफसिंक वेअरेबल अलर्ट रिसीवर',
        'watch_telemetry': 'वॉच सिस्टम टेलीमेट्री',
        'btn_sos': '🚨 स्मार्टवॉच SOS सक्रिय करें',
        'btn_cancel_sos': 'SOS रद्द करें',
        'sos_active': '🆘 SOS आपातकालीन संकेत सक्रिय! स्थान बचाव दल को भेजा गया।',
        'hazards': {
            'Flood': 'बाढ़ 🌊', 'Cyclone': 'चक्रवात 🌪️', 'Fire': 'आग 🔥',
            'Earthquake': 'भूकंप 🌎', 'Gas Leak': 'गैस रिसाव 💨',
            'Building Collapse': 'इमारत ढहना 🏚️', 'Road Accident': 'सड़क दुर्घटना 🚗'
        },
        'severities': {'Low': 'कम', 'Medium': 'मध्यम', 'High': 'उच्च', 'Critical': 'गंभीर'},
        'vulnerability_levels': {'Low': 'कम', 'Medium': 'मध्यम', 'High': 'उच्च (High)'},
        'relocation_priorities': {
            'Immediate Relocation': 'तत्काल निकासी (Immediate)',
            'High Priority': 'उच्च प्राथमिकता (High Priority)',
            'Medium Priority': 'मध्यम प्राथमिकता (Medium Priority)',
            'Low Priority': 'कम प्राथमिकता (Low Priority)'
        },
        'mobility_opts': {'Normal': 'सामान्य', 'Limited Mobility': 'सीमित गतिशीलता', 'Wheelchair': 'व्हीलचेयर'},
        'channels': ['बचाव दल', 'स्थानीय स्वयंसेवक', 'आस-पास के उपयोगकर्ता', '93.5 FM आपातकालीन रेडियो', '104.0 FM आपदा चेतावनी']
    },
    'Kannada': {
        'title': 'ಸೇಫ್‌ಸಿಂಕ್ (SAFESYNC)',
        'subtitle': 'ಬುದ್ಧಿವಂತ ಬಹು-ಅಪಾಯದ ರಿಸ್ಕ್ ಮತ್ತು ಸ್ಥಳಾಂತರ ಸಹಾಯ ವ್ಯವಸ್ಥೆ',
        'setup': '🚨 ಸೇಫ್‌ಸಿಂಕ್ සැಟಪ್',
        'lang_select': '🌐 ಭಾಷೆ (Language)',
        'offline_toggle': '📶 ಆಫ್‌ಲೈನ್ ಮೋಡ್',
        'low_battery_toggle': '🔋 ಕಡಿಮೆ ಬ್ಯಾಟರಿ ಮೋಡ್',
        'low_battery_warn': '🔋 ಕಡಿಮೆ ಬ್ಯಾಟರಿ ಮೋಡ್ ಸಕ್ರಿಯಗೊಳಿಸಲಾಗಿದೆ — ಕನಿಷ್ಠ ಸ್ಕ್ರೀನ್',
        'offline_walkie_warn': '📶 ಮೊಬೈಲ್ ನೆಟ್‌ವರ್ಕ್ ಲಭ್ಯವಿಲ್ಲ – ವಾಕಿ-ಟಾಕಿ ಮತ್ತು ಎಫ್‌ಎಂ ಪ್ರಸಾರ ಸಕ್ರಿಯವಾಗಿದೆ',
        'hazard_config': 'ಅಪಾಯದ ಆಯ್ಕೆ',
        'hazard_type': 'ಅಪಾಯದ ಪ್ರಕಾರ',
        'severity_level': 'ತೀವ್ರತೆಯ ಮಟ್ಟ',
        'nav_label': 'ನ್ಯಾವಿಗೇಷನ್',
        'nav_dash': '1. ತುರ್ತು ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
        'nav_walkie': '2. ವಾಕಿ-ಟಾಕಿ & ಎಫ್‌ಎಂ ಪ್ರಸಾರ',
        'nav_watch': '3. ಸ್ಮಾರ್ಟ್‌ವಾಚ್ ಸಿಮ್ಯುಲೇಶನ್',
        'nav_assistant': '4. ಬಹುಭಾಷಾ ಎಐ ಅಸಿಸ್ಟೆಂಟ್',
        'metric_hazard': 'ಸಕ್ರಿಯ ಅಪಾಯ',
        'metric_severity': 'ತೀವ್ರತೆ',
        'metric_risk': 'ಅಪಾಯದ ಸ್ಕೋರ್',
        'metric_affected': 'ಬಾಧಿತ ಜನರು',
        'metric_vulnerability': 'ಸೂಕ್ಷ್ಮತೆ (Vulnerability)',
        'metric_priority': 'ಸ್ಥಳಾಂತರ ಆದ್ಯತೆ',
        'profile_header': '2. ನಿವಾಸ ಪ್ರೊಫೈಲ್ ವಿವರಗಳು',
        'search_db': '🔍 ಡೇಟಾಬೇಸ್‌ನಿಂದ ಪ್ರೊಫೈಲ್ ಪಡೆಯಿರಿ',
        'save_db': '💾 ಪ್ರೊಫೈಲ್ ಉಳಿಸಿ',
        'name': 'ಹೆಸರು',
        'location': 'ಸ್ಥಳ (ನಗರ/ವಿಳಾಸ ಹುಡುಕಿ)',
        'num_people': 'ಕುಟುಂಬದ ಸದಸ್ಯರ ಸಂಖ್ಯೆ',
        'children': 'ಮಕ್ಕಳು',
        'elderly': 'ಹಿರಿಯ ನಾಗರಿಕರು',
        'disabilities': 'ವಿಕಲಚೇತನರು',
        'mobility': 'ಚಲನಶೀಲತೆ ಸ್ಥಿತಿ',
        'assess_header': '3. ರೆಡ್-ಝೋನ್ ಮತ್ತು ಸೂಕ್ಷ್ಮತೆಯ ಮೌಲ್ಯಮಾಪನ',
        'zone_status': 'ಝೋನ್ ಸ್ಥಿತಿ',
        'calc_vuln': 'ಲೆಕ್ಕಹಾಕಿದ ಸೂಕ್ಷ್ಮತೆ',
        'offline_map_msg': '📶 ಆಫ್‌ಲೈನ್ ಮೋಡ್: ಮ್ಯಾಪ್ ನಿಲ್ಲಿಸಲಾಗಿದೆ. ಸ್ಥಳೀಯ ಮಾಹಿತಿಯನ್ನು ಬಳಸಲಾಗುತ್ತಿದೆ.',
        'shelter_header': '4. ಆಶ್ರಯ ಸಾಮರ್ಥ್ಯ ಮತ್ತು ಶಿಫಾರಸು',
        'rec_shelter': 'ಶಿಫಾರಸು ಮಾಡಿದ ಆಶ್ರಯ',
        'distance': 'ದೂರ',
        'avail_cap': 'ಲಭ್ಯವಿರುವ ಸಾಮರ್ಥ್ಯ',
        'status': 'ಸ್ಥಿತಿ',
        'all_shelters': 'ಲಭ್ಯವಿರುವ ಆಶ್ರಯ ಕೇಂದ್ರಗಳು',
        'col_sname': 'ಆಶ್ರಯದ ಹೆಸರು',
        'col_sloc': 'ಸ್ಥಳ',
        'col_stot': 'ಒಟ್ಟು ಸಾಮರ್ಥ್ಯ',
        'col_socc': 'ಆಕ್ರಮಿತ ಸಾಮರ್ಥ್ಯ',
        'col_sava': 'ಉಳಿದ ಸಾಮರ್ಥ್ಯ',
        'col_sramp': 'ರ್ಯಾಂಪ್ ಸೌಲಭ್ಯ',
        'col_sdist': 'ದೂರ',
        'alert_header': '5. ತುರ್ತು ಎಚ್ಚರಿಕೆ ವ್ಯವಸ್ಥೆ',
        'alert_text': '🚨 ತುರ್ತು ಎಚ್ಚರಿಕೆ — ತಕ್ಷಣ ಖಾಲಿ ಮಾಡಲು ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ',
        'action_plan': 'ಕ್ರಿಯಾ ಯೋಜನೆ',
        'instruct': ['ಸುರಕ್ಷಿತ ಸ್ಥಳಕ್ಕೆ ತೆರಳಿ.', 'ಅಗತ್ಯ ವಸ್ತುಗಳನ್ನು ಒಯ್ಯಿರಿ.', 'ಶಿಫಾರಸು ಮಾಡಿದ ಮಾರ್ಗವನ್ನು ಅನುಸರಿಸಿ.', 'ನಿಗದಿತ ಆಶ್ರಯವನ್ನು ತಲುಪಿ.'],
        'btn_read_guidance': '🔊 ಸೂಚನೆಗಳನ್ನು ಕೇಳಿ (ವಾಯ್ಸ್ ಅಸಿಸ್ಟೆಂಟ್)',
        'walkie_title': '📻 ವಾಕಿ-ಟಾಕಿ & ಎಫ್‌ಎಂ ತುರ್ತು ಸಂವಹನ ಮಾಡ್ಯೂಲ್',
        'walkie_sub': 'ರೇಡಿಯೊ ಸಿಮ್ಯುಲೇಶನ್ ಮತ್ತು ಎಫ್‌ಎಂ ಪ್ರಸಾರ (ಆಫ್‌ಲೈನ್)',
        'radio_ctrl': 'ರೇಡಿಯೋ ನಿಯಂತ್ರಣಗಳು',
        'status_label': 'ಸ್ಥಿತಿ',
        'status_online': 'ಆನ್‌ಲೈನ್',
        'status_offline': 'ತುರ್ತು ಆಫ್‌ಲೈನ್ ಮೋಡ್ (ಎಫ್‌ಎಂ ಪ್ರಸಾರ)',
        'act_channel': 'ಸಕ್ರಿಯ ಚಾನೆಲ್ / ಎಫ್‌ಎಂ ಸ್ಟೇಷನ್',
        'quick_trans': 'ಪೂರ್ವನಿಯೋಜಿತ ಸಂದೇಶಗಳು',
        'btn_evac': '🚨 ನನಗೆ ಸ್ಥಳಾಂತರ ಸಹಾಯ ಬೇಕು',
        'btn_trapped': '⚠️ ವ್ಯಕ್ತಿ ಸಿಲುಕಿಕೊಂಡಿದ್ದಾರೆ',
        'btn_shelter': '🏫 ಆಶ್ರಯ ಅಗತ್ಯವಿದೆ',
        'btn_ptt': '🎙️ ಮಾತನಾಡಲು ಒತ್ತಿ ಹಿಡಿಯಿರಿ (PTT)',
        'btn_bcast': '📢 ತುರ್ತು ಎಫ್‌ಎಂ ಪ್ರಸಾರ',
        'btn_read_latest': '📢 ಇತ್ತೀಚಿನ ರೇಡಿಯೋ ಸಂದೇಶವನ್ನು ಕೇಳಿ',
        'incoming_stream': 'ರೇಡಿಯೋ ಸಂದೇಶಗಳು',
        'voice_sent': '🎙️ [ವಾಯ್ಸ್ ಮೆಸೇಜ್ ಕಳುಹಿಸಲಾಗಿದೆ]',
        'watch_title': '⌚ ಸ್ಮಾರ್ಟ್‌ವಾಚ್ ಇಂಟರ್‌ಫೇಸ್ ಸಿಮ್ಯುಲೇಶನ್',
        'watch_sub': 'ಸೇಫ್‌ಸಿಂಕ್ ಧರಿಸಬಹುದಾದ ಎಚ್ಚರಿಕೆ ರಿಸೀವರ್',
        'watch_telemetry': 'ವಾಚ್ ಸಿಸ್ಟಮ್ ಡೇಟಾ',
        'btn_sos': '🚨 ಸ್ಮಾರ್ಟ್‌ವಾಚ್ SOS ಸಕ್ರಿಯಗೊಳಿಸಿ',
        'btn_cancel_sos': 'SOS ರದ್ದುಗೊಳಿಸಿ',
        'sos_active': '🆘 SOS ತುರ್ತು ಸಂಕೇತ ಕಳುಹಿಸಲಾಗಿದೆ! ಸ್ಥಳವನ್ನು ರಕ್ಷಣಾ ತಂಡಕ್ಕೆ ತಲುಪಿಸಲಾಗಿದೆ.',
        'hazards': {
            'Flood': 'ಪ್ರವಾಹ 🌊', 'Cyclone': 'ಚಂಡಮಾರುತ 🌪️', 'Fire': 'ಬೆಂಕಿ ಅವಘಡ 🔥',
            'Earthquake': 'ಭೂಕಂಪ 🌎', 'Gas Leak': 'ಗ್ಯಾಸ್ ಸೋರಿಕೆ 💨',
            'Building Collapse': 'ಕಟ್ಟಡ ಕುಸಿತ 🏚️', 'Road Accident': 'ರಸ್ತೆ ಅಪಘಾತ 🚗'
        },
        'severities': {'Low': 'ಕಡಿಮೆ', 'Medium': 'ಮಧ್ಯಮ', 'High': 'ಹೆಚ್ಚು (High)', 'Critical': 'ಅತ್ಯಂತ ಗಂಭೀರ'},
        'vulnerability_levels': {'Low': 'ಕಡಿಮೆ', 'Medium': 'ಮಧ್ಯಮ', 'High': 'ಹೆಚ್ಚು (High)'},
        'relocation_priorities': {
            'Immediate Relocation': 'ತಕ್ಷಣ ಖಾಲಿ ಮಾಡಿ (Immediate)',
            'High Priority': 'ಹೆಚ್ಚಿನ ಆದ್ಯತೆ (High Priority)',
            'Medium Priority': 'ಮಧ್ಯಮ ಆದ್ಯತೆ (Medium Priority)',
            'Low Priority': 'ಕಡಿಮೆ ಆದ್ಯತೆ (Low Priority)'
        },
        'mobility_opts': {'Normal': 'ಸಾಮಾನ್ಯ', 'Limited Mobility': 'ಪರಿಮಿತ ಚಲನಶೀಲತೆ', 'Wheelchair': 'ವೀಲ್‌ಚೈರ್'},
        'channels': ['ರಕ್ಷಣಾ ತಂಡ', 'ಸ್ಥानीय ಸ್ವಯಂಸೇವಕರು', 'ಸಮೀಪದ ಬಳಕೆದಾರರು', '93.5 FM ತುರ್ತು ರೇಡಿಯೋ', '104.0 FM ವಿಪತ್ತು ಎಚ್ಚರಿಕೆ']
    },
    'Tamil': {
        'title': 'சேஃப்சின்க் (SAFESYNC)',
        'subtitle': 'புத்திசாலி பல்லாபத்து அபாயம் மற்றும் இடமாற்ற உதவி அமைப்பு',
        'setup': '🚨 சேஃப்சின்க் அமைப்புகள்',
        'lang_select': '🌐 மொழி (Language)',
        'offline_toggle': '📶 ஆஃப்லைன் முறை',
        'low_battery_toggle': '🔋 குறைந்த பேட்டரி முறை',
        'low_battery_warn': '🔋 குறைந்த பேட்டரி முறை செயல்படுத்தப்பட்டது — குறைந்தபட்ச திரை',
        'offline_walkie_warn': '📶 மொபைல் நெட்வொர்க் இல்லை – வாக்கி-டாக்கி மற்றும் எஃப்எம் ஒளிபரப்பு செயல்படுகிறது',
        'hazard_config': 'அபாயத் தேர்வு',
        'hazard_type': 'அபாய வகை',
        'severity_level': 'தீவிர நிலை',
        'nav_label': 'வழிசெலுத்தல்',
        'nav_dash': '1. அவசரக்கால டாஷ்போர்டு',
        'nav_walkie': '2. வாக்கி-டாக்கி & எஃப்எம் ஒளிபரப்பு',
        'nav_watch': '3. ஸ்மார்ட்வாட்ச் உருவகப்படுத்துதல்',
        'nav_assistant': '4. பன்மொழி AI உதவியாளர்',
        'metric_hazard': 'தற்போதைய அபாயம்',
        'metric_severity': 'தீவிரம்',
        'metric_risk': 'அபாய மதிப்பெண்',
        'metric_affected': 'பாதிக்கப்பட்ட மக்கள்',
        'metric_vulnerability': 'பாதிக்கப்படக்கூடிய நிலை',
        'metric_priority': 'இடமாற்ற முன்னுரிமை',
        'profile_header': '2. குடியிருப்பு சுயவிவர அமைப்புகள்',
        'search_db': '🔍 தரவுத்தளத்தில் இருந்து சுயவிவரத்தை ஏற்றவும்',
        'save_db': '💾 சுயவிவரத்தைச் சேமிக்கவும்',
        'name': 'பெயர்',
        'location': 'இருப்பிடம் (நகரம்/முகவரியைத் தேடுங்கள்)',
        'num_people': 'மொத்த குடும்ப உறுப்பினர்கள்',
        'children': 'குழந்தைகள்',
        'elderly': 'முதியவர்கள்',
        'disabilities': 'மாற்றுத்திறனாளிகள்',
        'mobility': 'நகர்வு நிலை',
        'assess_header': '3. ரெட்-ஜோன் மற்றும் பாதிப்பு மதிப்பீடு',
        'zone_status': 'மண்டல நிலை',
        'calc_vuln': 'கணக்கிடப்பட்ட பாதிப்பு',
        'offline_map_msg': '📶 ஆஃப்லைன் முறை: வரைபடம் இடைநிறுத்தப்பட்டுள்ளது. உள்ளூர் தரவு பயன்படுத்தப்படுகிறது.',
        'shelter_header': '4. தங்குமிட திறன் மற்றும் பரிந்துரை',
        'rec_shelter': 'பரிந்துரைக்கப்பட்ட தங்குமிடம்',
        'distance': 'தூரம்',
        'avail_cap': 'கிடைக்கும் திறன்',
        'status': 'நிலை',
        'all_shelters': 'கிடைக்கும் கணினி தங்குமிடங்கள்',
        'col_sname': 'தங்குமிடப் பெயர்',
        'col_sloc': 'இருப்பிடம்',
        'col_stot': 'மொத்த திறன்',
        'col_socc': 'ஆக்கிரமிக்கப்பட்ட திறன்',
        'col_sava': 'மீதமுள்ள திறன்',
        'col_sramp': 'சாய்வுப் பாதை வசதி',
        'col_sdist': 'தூரம்',
        'alert_header': '5. அவசரக்கால எச்சரிக்கை அமைப்பு',
        'alert_text': '🚨 அவசர எச்சரிக்கை — உடனடியாக வெளியேற பரிந்துரைக்கப்படுகிறது',
        'action_plan': 'செயல் திட்டம்',
        'instruct': ['பாதுகாப்பான இடத்திற்குச் செல்லவும்.', 'அத்தியாவசியப் பொருட்களை எடுத்துச் செல்லவும்.', 'பரிந்துரைக்கப்பட்ட வழியைப் பின்பற்றவும்.', 'ஒதுக்கப்பட்ட தங்குமிடத்தை அடையவும்.'],
        'btn_read_guidance': '🔊 அறிவுறுத்தல்களைக் கேட்கவும் (குரல் உதவியாளர்)',
        'walkie_title': '📻 வாக்கி-டாக்கி & எஃப்எம் அவசரக்கால தகவல் தொடர்பு தொகுதி',
        'walkie_sub': 'ரேடியோ உருவகப்படுத்துதல் மற்றும் எஃப்எம் ஒளிபரப்பு (ஆஃப்லைன்)',
        'radio_ctrl': 'ரேடியோ கட்டுப்பாடுகள்',
        'status_label': 'நிலை',
        'status_online': 'ஆன்லைன்',
        'status_offline': 'அவசரக்கால ஆஃப்லைன் முறை (எஃப்எம் ஒளிபரப்பு)',
        'act_channel': 'செயலில் உள்ள சேனல் / எஃப்எம் நிலையம்',
        'quick_trans': 'முன்வரையறுக்கப்பட்ட செய்திகள்',
        'btn_evac': '🚨 எனக்கு வெளியேற்ற உதவி தேவை',
        'btn_trapped': '⚠️ நபர் சிக்கியுள்ளார்',
        'btn_shelter': '🏫 தங்குமிடம் தேவை',
        'btn_ptt': '🎙️ பேச அழுத்திப் பிடிக்கவும் (PTT)',
        'btn_bcast': '📢 அவசர எஃப்எம் ஒளிபரப்பு',
        'btn_read_latest': '📢 சமீபத்திய ரேடியோ செய்தியைக் கேட்கவும்',
        'incoming_stream': 'ரேடியோ செய்திகள் Stream',
        'voice_sent': '🎙️ [குரல் செய்தி அனுப்பப்பட்டது]',
        'watch_title': '⌚ ஸ்மார்ட்வாட்ச் இடைமுக உருவகப்படுத்துதல்',
        'watch_sub': 'சேஃப்சின்க் அணியக்கூடிய எச்சரிக்கை ஏற்பி',
        'watch_telemetry': 'வாட்ச் கணினி தரவு',
        'btn_sos': '🚨 ஸ்மார்ட்வாட்ச் SOS ஐ இயக்கவும்',
        'btn_cancel_sos': 'SOS ஐ ரத்துசெய்',
        'sos_active': '🆘 SOS அவசர சமிக்ஞை அனுப்பப்பட்டது! இருப்பிடம் மீட்புக் குழுவிற்குச் சென்றடைந்தது.',
        'hazards': {
            'Flood': 'வெள்ளம் 🌊', 'Cyclone': 'புயல் 🌪️', 'Fire': 'தீ விபத்து 🔥',
            'Earthquake': 'நிலநடுக்கம் 🌎', 'Gas Leak': 'கேஸ் கசிவு 💨',
            'Building Collapse': 'கட்டிட சரிவு 🏚️', 'Road Accident': 'சாலை விபத்து 🚗'
        },
        'severities': {'Low': 'குறைந்த', 'Medium': 'மிதமான', 'High': 'அதிக (High)', 'Critical': 'மிகவும் தீவிரமானது'},
        'vulnerability_levels': {'Low': 'குறைந்த', 'Medium': 'மிதமான', 'High': 'அதிக (High)'},
        'relocation_priorities': {
            'Immediate Relocation': 'உடனடி இடமாற்றம் (Immediate)',
            'High Priority': 'அதிக முன்னுரிமை (High Priority)',
            'Medium Priority': 'மிதமான முன்னுரிமை (Medium Priority)',
            'Low Priority': 'குறைந்த முன்னுரிமை (Low Priority)'
        },
        'mobility_opts': {'Normal': 'சாதாரண', 'Limited Mobility': 'வரையறுக்கப்பட்ட நகர்வு', 'Wheelchair': 'சக்கர நாற்காலி'},
        'channels': ['மீட்புக் குழு', 'உள்ளூர் தன்னார்வலர்கள்', 'அருகிலுள்ள பயனர்கள்', '93.5 FM அவசர ரேடியோ', '104.0 FM பேரழிவு எச்சரிக்கை']
    }
}

# --- SIDEBAR CONTROLS & LANGUAGE INITIALIZATION ---
st.sidebar.title("🚨 SAFESYNC")

st.session_state['language'] = st.sidebar.selectbox(
    "🌐 Language / భాష / भाषा / ಭಾಷೆ / மொழி",
    ["English", "Telugu", "Hindi", "Kannada", "Tamil"],
    index=["English", "Telugu", "Hindi", "Kannada", "Tamil"].index(st.session_state['language'])
)

T = I18N[st.session_state['language']]
current_lang_code = LANG_CODES[st.session_state['language']]

st.session_state['offline_mode'] = st.sidebar.toggle(T['offline_toggle'], st.session_state['offline_mode'])
st.session_state['low_battery_mode'] = st.sidebar.toggle(T['low_battery_toggle'], st.session_state['low_battery_mode'])

st.sidebar.markdown("---")
st.sidebar.subheader(T['hazard_config'])

hazard_keys = list(T['hazards'].keys())
st.session_state['hazard_type'] = st.sidebar.selectbox(
    T['hazard_type'],
    hazard_keys,
    format_func=lambda x: T['hazards'][x],
    index=hazard_keys.index(st.session_state['hazard_type'])
)

sev_keys = list(T['severities'].keys())
st.session_state['severity'] = st.sidebar.select_slider(
    T['severity_level'],
    options=sev_keys,
    format_func=lambda x: T['severities'][x],
    value=st.session_state['severity']
)

st.sidebar.markdown("---")
nav_options = [T['nav_dash'], T['nav_walkie'], T['nav_watch'], T['nav_assistant']]
nav = st.sidebar.radio(T['nav_label'], nav_options)

# --- EVALUATE CORE LOGIC & LIVE GEOCODING ---
shelters = get_all_shelters()
user_lat, user_lon = get_coordinates(st.session_state['location'])

user_profile = {
    'num_people': st.session_state['num_people'],
    'children': st.session_state['children'],
    'elderly': st.session_state['elderly'],
    'disabilities': st.session_state['disabilities'],
    'mobility': st.session_state['mobility']
}
eval_res = evaluate_safesync(st.session_state['hazard_type'], st.session_state['severity'], user_profile, shelters, user_lat, user_lon)
rec_shelter = eval_res['recommended_shelter']

trans_vulnerability = T['vulnerability_levels'].get(eval_res['vulnerability_level'], eval_res['vulnerability_level'])
trans_priority = T['relocation_priorities'].get(eval_res['relocation_priority'], eval_res['relocation_priority'])

# --- PAGE 1: EMERGENCY DASHBOARD ---
if nav == T['nav_dash']:
    st.title(T['title'])
    st.caption(T['subtitle'])

    if st.session_state['low_battery_mode']:
        st.warning(T['low_battery_warn'])

    st.markdown(f"### {T['nav_dash']}")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric(T['metric_hazard'], T['hazards'][st.session_state['hazard_type']])
    m2.metric(T['metric_severity'], T['severities'][st.session_state['severity']])
    m3.metric(T['metric_risk'], f"{eval_res['risk_score']}/100")
    m4.metric(T['metric_affected'], st.session_state['num_people'])
    m5.metric(T['metric_vulnerability'], trans_vulnerability)
    m6.metric(T['metric_priority'], trans_priority)

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"### {T['profile_header']}")
        
        # SQLite Integration Actions
        db_col1, db_col2 = st.columns(2)
        if db_col1.button(T['search_db']):
            u_data = get_user(st.session_state['username'])
            if u_data:
                st.session_state['name'] = u_data['name']
                st.session_state['location'] = u_data['location']
                st.session_state['num_people'] = u_data['num_people']
                st.session_state['children'] = u_data['children']
                st.session_state['elderly'] = u_data['elderly']
                st.session_state['disabilities'] = u_data['disabilities']
                st.session_state['mobility'] = u_data['mobility']
                st.success("Profile loaded from Database!")
                st.rerun()

        if db_col2.button(T['save_db']):
            save_or_update_user(st.session_state['username'], {
                'name': st.session_state['name'],
                'location': st.session_state['location'],
                'num_people': st.session_state['num_people'],
                'children': st.session_state['children'],
                'elderly': st.session_state['elderly'],
                'disabilities': st.session_state['disabilities'],
                'mobility': st.session_state['mobility'],
                'language': st.session_state['language']
            })
            st.success("Profile saved to SQLite Database!")

        st.session_state['name'] = st.text_input(T['name'], st.session_state['name'])
        st.session_state['location'] = st.text_input(T['location'], st.session_state['location'])
        c1, c2 = st.columns(2)
        st.session_state['num_people'] = c1.number_input(T['num_people'], 1, 20, st.session_state['num_people'])
        st.session_state['children'] = c2.number_input(T['children'], 0, 10, st.session_state['children'])
        st.session_state['elderly'] = c1.number_input(T['elderly'], 0, 10, st.session_state['elderly'])
        st.session_state['disabilities'] = c2.number_input(T['disabilities'], 0, 10, st.session_state['disabilities'])
        
        mob_keys = list(T['mobility_opts'].keys())
        st.session_state['mobility'] = st.selectbox(
            T['mobility'],
            mob_keys,
            format_func=lambda x: T['mobility_opts'][x],
            index=mob_keys.index(st.session_state['mobility'])
        )

    with col_b:
        st.markdown(f"### {T['assess_header']}")
        st.write(f"**{T['zone_status']}:** :{eval_res['zone_color']}[{eval_res['risk_zone']}]")
        st.write(f"**{T['calc_vuln']}:** {trans_vulnerability}")
        st.write(f"**{T['metric_priority']}:** :{eval_res['priority_color']}[{trans_priority}]")

        if not st.session_state['offline_mode'] and not st.session_state['low_battery_mode']:
            # Live Map with OpenStreetMap / Folium & Multi-Hazard Buffers
            m = folium.Map(location=[user_lat, user_lon], zoom_start=13)
            
            # Draw Dynamic Risk Zone Circle (Red / Orange / Yellow / Green)
            folium.Circle(
                location=[user_lat, user_lon],
                radius=1500,
                color=eval_res['zone_color'],
                fill=True,
                fill_color=eval_res['zone_color'],
                fill_opacity=0.35,
                popup=f"Hazard Impact Radius ({eval_res['risk_zone']})"
            ).add_to(m)

            folium.Marker([user_lat, user_lon], popup=f"Location: {st.session_state['location']}", icon=folium.Icon(color="red")).add_to(m)
            
            for s in eval_res['all_shelters']:
                icon_color = "green" if s == rec_shelter else "blue"
                folium.Marker([s['lat'], s['lon']], popup=f"Shelter: {s['name']}\nCapacity: {s['available_capacity']}", icon=folium.Icon(color=icon_color)).add_to(m)

            if rec_shelter:
                folium.PolyLine([[user_lat, user_lon], [rec_shelter['lat'], rec_shelter['lon']]], color="blue", weight=3, opacity=0.8).add_to(m)
            st_folium(m, height=250, use_container_width=True)
        else:
            st.info(T['offline_map_msg'])

    st.markdown("---")

    st.markdown(f"### {T['shelter_header']}")
    if rec_shelter:
        st.success(f"**{T['rec_shelter']}:** {rec_shelter['name']} ({rec_shelter['location']})")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric(T['distance'], f"{rec_shelter['distance_km']} km")
        sc2.metric(T['avail_cap'], f"{rec_shelter['available_capacity']} / {rec_shelter['total_capacity']}")
        sc3.metric(T['status'], rec_shelter['status'])

    st.write(f"#### {T['all_shelters']}")
    st.dataframe([
        {
            T['col_sname']: s['name'],
            T['col_sloc']: s['location'],
            T['col_stot']: s['total_capacity'],
            T['col_socc']: s['occupied_capacity'],
            T['col_sava']: s['available_capacity'],
            T['col_sramp']: "Yes" if s['has_ramp'] else "No",
            T['col_sdist']: f"{s['distance_km']} km"
        } for s in eval_res['all_shelters']
    ], use_container_width=True)

    st.markdown("---")

    st.markdown(f"### {T['alert_header']}")
    if eval_res['relocation_priority'] in ["Immediate Relocation", "High Priority"]:
        st.error(f"🚨 **{T['alert_text']}**")

    st.markdown(f"**{T['action_plan']}:**")
    for idx, step in enumerate(T['instruct'], 1):
        st.write(f"**{idx}.** {step}")

    # Audio Assistant Guidance Button
    full_audio_script = f"{T['alert_text']}. " + " ".join(T['instruct'])
    if rec_shelter:
        full_audio_script += f" {T['rec_shelter']}: {rec_shelter['name']}."
        
    if st.button(T['btn_read_guidance'], type="primary"):
        speak_text(full_audio_script, current_lang_code)

# --- PAGE 2: WALKIE-TALKIE & FM BROADCAST SIMULATION ---
elif nav == T['nav_walkie']:
    st.title(T['walkie_title'])
    st.caption(T['walkie_sub'])

    if st.session_state['offline_mode']:
        st.error(f"🚨 **{T['offline_walkie_warn']}**")
        status_mode = T['status_offline']
    else:
        status_mode = T['status_online']

    w_col1, w_col2 = st.columns([1, 2])

    with w_col1:
        st.subheader(T['radio_ctrl'])
        st.info(f"**{T['status_label']}:** {status_mode}")
        channel = st.selectbox(T['act_channel'], T['channels'])
        
        st.markdown("---")
        st.write(f"**{T['quick_trans']}:**")
        
        if st.button(T['btn_evac']):
            msg = T['btn_evac']
            st.session_state['walkie_history'].append({"sender": st.session_state['name'], "text": msg, "channel": channel})
            speak_text(msg, current_lang_code)
            st.rerun()
            
        if st.button(T['btn_trapped']):
            msg = T['btn_trapped']
            st.session_state['walkie_history'].append({"sender": st.session_state['name'], "text": msg, "channel": channel})
            speak_text(msg, current_lang_code)
            st.rerun()

        if st.button(T['btn_shelter']):
            msg = T['btn_shelter']
            st.session_state['walkie_history'].append({"sender": st.session_state['name'], "text": msg, "channel": channel})
            speak_text(msg, current_lang_code)
            st.rerun()

        st.markdown("---")
        if st.button(T['btn_ptt'], type="primary", use_container_width=True):
            msg = T['voice_sent']
            st.session_state['walkie_history'].append({"sender": st.session_state['name'], "text": msg, "channel": channel})
            speak_text(msg, current_lang_code)
            st.rerun()

        if st.button(T['btn_bcast'], use_container_width=True):
            msg = f"FM BROADCAST WARNING [{channel}]: Critical hazard alert at {st.session_state['location']}. Evacuate immediately!"
            st.session_state['walkie_history'].append({"sender": "OFFLINE FM STATION", "text": msg, "channel": channel})
            speak_text(msg, current_lang_code)
            st.rerun()

    with w_col2:
        st.subheader(f"{T['incoming_stream']} — [{channel}]")
        
        if st.button(T['btn_read_latest']):
            if st.session_state['walkie_history']:
                latest = st.session_state['walkie_history'][-1]['text']
                speak_text(latest, current_lang_code)

        for msg in reversed(st.session_state['walkie_history']):
            if msg['channel'] == channel or "FM" in msg['sender'] or msg['sender'] == "SYSTEM BROADCAST":
                st.chat_message("user" if msg['sender'] == st.session_state['name'] else "assistant").write(f"**{msg['sender']}:** {msg['text']}")

# --- PAGE 3: SMARTWATCH SIMULATION ---
elif nav == T['nav_watch']:
    st.title(T['watch_title'])
    st.caption(T['watch_sub'])

    w_col, info_col = st.columns([1, 1])

    with w_col:
        watch_bg = "#330000" if eval_res['risk_zone'] in ["Red Zone", "Orange Zone"] else "#021A00"
        border_color = "#FF0000" if eval_res['risk_zone'] == "Red Zone" else "#FF9900" if eval_res['risk_zone'] == "Orange Zone" else "#00FF00"

        st.markdown(f"""
            <div style="width:280px; height:340px; background:{watch_bg}; border:8px solid {border_color}; border-radius:40px; padding:18px; margin:auto; text-align:center; color:#fff; font-family:sans-serif;">
                <div style="font-size:0.75rem; color:#aaa;">14:32 | 🔋 {st.session_state['battery_level']}%</div>
                <hr style="border-color:#555; margin:8px 0;">
                <div style="color:#ff4b4b; font-weight:bold; font-size:1.1rem;">🔴 {T['hazards'][st.session_state['hazard_type']].upper()}</div>
                <div style="font-size:0.8rem; color:#ffaa00; margin-top:4px;">{T['metric_risk']}: {eval_res['risk_score']} ({eval_res['risk_zone']})</div>
                <div style="font-size:0.75rem; color:#fff; margin-top:4px;">{T['metric_priority']}: <b>{trans_priority}</b></div>
                <div style="background:#222; padding:8px; border-radius:8px; font-size:0.75rem; margin:10px 0;">
                    📍 <b>{rec_shelter['name'] if rec_shelter else 'N/A'}</b><br>
                    {T['distance']}: {rec_shelter['distance_km'] if rec_shelter else '0'} km
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write(" ")
        if st.button(T['btn_sos'], type="primary", use_container_width=True):
            st.session_state['sos_triggered'] = True
            speak_text(T['sos_active'], current_lang_code)

    with info_col:
        st.subheader(T['watch_telemetry'])
        
        if st.session_state['sos_triggered']:
            st.error(T['sos_active'])
            if st.button(T['btn_cancel_sos']):
                st.session_state['sos_triggered'] = False
                st.rerun()

        st.json({
            "device": "SAFESYNC Watch v1",
            "hazard_alert": T['hazards'][st.session_state['hazard_type']],
            "risk_level": eval_res['risk_score'],
            "risk_zone": eval_res['risk_zone'],
            "relocation_priority": trans_priority,
            "recommended_shelter": rec_shelter['name'] if rec_shelter else None,
            "distance_km": rec_shelter['distance_km'] if rec_shelter else None
        })

# --- PAGE 4: MULTILINGUAL AI ASSISTANT ---
elif nav == T['nav_assistant']:
    st.title(f"🤖 {T['nav_assistant']}")
    st.caption("Ask questions about shelters, disaster safety, or emergency evacuation plans in any language.")

    # Render previous conversation
    for chat in st.session_state['chat_history']:
        with st.chat_message(chat['role']):
            st.write(chat['text'])

    user_query = st.chat_input("Type your emergency query here...")
    if user_query:
        st.session_state['chat_history'].append({"role": "user", "text": user_query})
        
        # Rule-based context-aware response generator
        q_lower = user_query.lower()
        if "shelter" in q_lower or "ఆశ్రయం" in q_lower or "आश्रय" in q_lower:
            reply = f"The nearest recommended shelter for you is {rec_shelter['name']} located at {rec_shelter['location']}, {rec_shelter['distance_km']} km away." if rec_shelter else "No specific shelter allocated."
        elif "risk" in q_lower or "zone" in q_lower or "రిస్క్" in q_lower:
            reply = f"Your current location ({st.session_state['location']}) is evaluated as {eval_res['risk_zone']} with a Risk Score of {eval_res['risk_score']}/100."
        else:
            reply = f"SAFESYNC AI Emergency Guidance: Stay calm. Keep your mobile battery safe, head towards {rec_shelter['name'] if rec_shelter else 'safe area'}, and follow official relocation notices."

        st.session_state['chat_history'].append({"role": "assistant", "text": reply})
        speak_text(reply, current_lang_code)
        st.rerun()

# PRD: Student Assessment Tracker

**Version:** 1.0
**Date:** 23 October 2026
**Tech Stack:** HTML + CSS (+ थोड़ा Vanilla JS) | Flask (Python) | SQLite → PostgreSQL | LangChain Deep Agents

---

## 1. Overview

### 1.1 समस्या
स्कूल में टीचर्स MCQ टेस्ट कागज़ पर लेते हैं। चेकिंग में समय लगता है, और स्टूडेंट को सिर्फ़ "इतने मार्क्स आए" पता चलता है, यह नहीं कि **कहाँ कमज़ोर है** और **क्या सुधारना है**।

### 1.2 समाधान
एक वेब-आधारित Assessment Tracker जिसमें:
- स्टूडेंट सिर्फ़ **नाम + क्लास** डालकर लाइव टेस्ट दे सके।
- टीचर **Admin Panel** से CSV अपलोड करके टेस्ट बनाए और लाइव करे।
- टेस्ट के बाद **PDF रिपोर्ट** बने (स्कूल लोगो, सब्जेक्ट, टेस्ट का नाम, तारीख, मार्क्स, गलतियाँ)।
- **LangChain Deep Agent** हर स्टूडेंट का गहरा विश्लेषण करके पर्सनलाइज़्ड फीडबैक दे (कौन से टॉपिक/टाइप में कमज़ोर, कितना समय लगा, क्या करना चाहिए)।

### 1.3 Goals
| # | Goal | Success Metric |
|---|------|----------------|
| G1 | टेस्ट बनाना आसान हो | CSV अपलोड से टेस्ट लाइव होने में < 3 मिनट |
| G2 | स्टूडेंट एंट्री बिना झंझट | Login/पासवर्ड नहीं, सिर्फ़ नाम + क्लास |
| G3 | तुरंत रिज़ल्ट | सबमिट के बाद < 5 सेकंड में स्कोर, AI फीडबैक < 30 सेकंड में |
| G4 | काम का फीडबैक | हर रिपोर्ट में कम से कम 3 टॉपिक-वार सुझाव |

### 1.4 Non-Goals (अभी नहीं)
- स्टूडेंट का पासवर्ड/OTP-आधारित लॉगिन
- नंबरिकल/सब्जेक्टिव सवाल (सिर्फ़ MCQ)
- मोबाइल ऐप (वेब रिस्पॉन्सिव रहेगा)
- पेरेंट पोर्टल

---

## 2. Users और Roles

| Role | कौन | क्या कर सकता है |
|------|-----|-----------------|
| **Student** | क्लास के बच्चे | नाम + क्लास डालना, लाइव टेस्ट देना, अपनी रिपोर्ट देखना/डाउनलोड करना |
| **Admin (Teacher)** | टीचर / स्कूल एडमिन | लॉगिन, टेस्ट बनाना, CSV अपलोड, समय/सवाल सेट, टेस्ट लाइव/बंद करना, सभी रिज़ल्ट देखना |

> Admin के लिए सरल लॉगिन (username + password) रहेगा। Student के लिए कोई पासवर्ड नहीं।

---

## 3. User Flows

### 3.1 Student Flow
1. होम पेज खोले → **नाम** और **क्लास** डाले → "Start" दबाए।
2. अगर उस क्लास के लिए कोई **लाइव टेस्ट** है, तो इंस्ट्रक्शन पेज दिखे (सब्जेक्ट, कुल सवाल, समय)। नहीं है तो "अभी कोई टेस्ट लाइव नहीं है" का मैसेज।
3. "Begin Test" दबाते ही **टाइमर** शुरू हो।
4. एक-एक सवाल (या पूरा पेज) सॉल्व करे; Next/Previous और Question Palette (answered / unanswered / marked for review)।
5. समय खत्म होने पर या Submit दबाने पर **ऑटो-सबमिट**।
6. Result पेज: स्कोर, सही/गलत संख्या, **PDF रिपोर्ट डाउनलोड** बटन।
7. AI फीडबैक तैयार होते समय "रिपोर्ट बन रही है…" दिखे, फिर रिपोर्ट में जुड़ जाए।

### 3.2 Admin Flow
1. Admin Login करे।
2. **Dashboard:** पिछले टेस्ट, लाइव टेस्ट, रिज़ल्ट का सारांश।
3. **Create Test:** टेस्ट नाम, सब्जेक्ट, क्लास, **कुल सवाल (N)**, **समय (मिनट)**, मार्क्स/सवाल, निगेटिव मार्किंग (वैकल्पिक)।
4. **CSV Template डाउनलोड** → भरे → अपलोड।
5. सिस्टम CSV को **वैलिडेट** करे (गलत पंक्तियों की सूची दिखाए)।
6. **Preview** देखकर "Make Live" (Enable) दबाए।
7. **Live Monitor:** कितने स्टूडेंट शुरू/खत्म किए।
8. "Close Test" दबाकर बंद करे।
9. **Results:** क्लास-वार टेबल, हर स्टूडेंट की रिपोर्ट, CSV/Excel एक्सपोर्ट।

---

## 4. Functional Requirements

### 4.1 Student Entry
- **FR-S1:** फ़ील्ड्स: Name (टेक्स्ट), Class (ड्रॉपडाउन, जैसे 6–12 + सेक्शन वैकल्पिक)।
- **FR-S2:** Name में सिर्फ़ अक्षर/स्पेस, 2–50 कैरेक्टर; खाली न हो।
- **FR-S3:** एक ही टेस्ट के लिए **समान नाम + क्लास** से दोबारा प्रयास पर चेतावनी/ब्लॉक (Admin सेटिंग: Allow re-attempt Y/N)।
- **FR-S4:** सेशन ब्राउज़र कुकी/टोकन पर चले ताकि रिफ्रेश करने पर टेस्ट जारी रहे और **टाइमर सर्वर-साइड** से चले (क्लाइंट से छेड़छाड़ न हो)।

### 4.2 Admin Panel
- **FR-A1:** Admin लॉगिन (हैश्ड पासवर्ड, सेशन)।
- **FR-A2:** टेस्ट बनाना: नाम, सब्जेक्ट, क्लास, कुल सवाल, अवधि, मार्क्स/सवाल, निगेटिव मार्किंग, सवाल/ऑप्शन शफल (Y/N)।
- **FR-A3:** **CSV Template** डाउनलोड बटन (नीचे फ़ॉर्मेट)।
- **FR-A4:** CSV अपलोड + वैलिडेशन।
- **FR-A5:** **सवालों की संख्या:** डिफ़ॉल्ट 20। अगर CSV में 20 से ज़्यादा सवाल हों, तो Admin तय करे कितने सवाल पूछे जाएँ (रैंडम चयन); कम हों तो चेतावनी।
- **FR-A6:** टेस्ट Enable/Disable (Live toggle)। एक क्लास के लिए एक समय में एक ही लाइव टेस्ट।
- **FR-A7:** Live Monitor पेज (शुरू किए / सबमिट किए स्टूडेंट्स)।
- **FR-A8:** रिज़ल्ट्स पेज: फ़िल्टर (क्लास, टेस्ट, तारीख), एक्सपोर्ट।
- **FR-A9:** स्कूल सेटिंग्स: **स्कूल का नाम और लोगो अपलोड** (PNG/JPG, ≤ 2MB)।

### 4.3 CSV Template Format

**कॉलम्स:**

| Column | Required | Description |
|--------|----------|-------------|
| `question_no` | हाँ | 1, 2, 3… |
| `question` | हाँ | सवाल का टेक्स्ट |
| `option_a` | हाँ | |
| `option_b` | हाँ | |
| `option_c` | हाँ | |
| `option_d` | हाँ | |
| `correct_option` | हाँ | A / B / C / D |
| `topic` | हाँ | जैसे "Fractions", "Algebra" (विश्लेषण के लिए ज़रूरी) |
| `question_type` | हाँ | `conceptual` / `numerical` / `application` / `recall` |
| `difficulty` | हाँ | `easy` / `medium` / `hard` |
| `explanation` | नहीं | सही उत्तर की व्याख्या (रिपोर्ट में दिखेगी) |

**वैलिडेशन नियम:**
- हर आवश्यक कॉलम मौजूद हो, `correct_option` ∈ {A,B,C,D}।
- ऑप्शन खाली न हों; डुप्लिकेट सवाल पर चेतावनी।
- UTF-8 एन्कोडिंग (हिंदी सवाल सपोर्टेड)।
- त्रुटि मिलने पर **पंक्ति संख्या + कारण** की सूची दिखे, और कुछ भी सेव न हो जब तक सब ठीक न हो।

**उदाहरण:**
```csv
question_no,question,option_a,option_b,option_c,option_d,correct_option,topic,question_type,difficulty,explanation
1,"What is 3/4 + 1/4?",1,"3/8","1/2","4/8",A,Fractions,numerical,easy,"Same denominator add numerators: 4/4 = 1"
```

### 4.4 Test Engine
- **FR-T1:** सर्वर टेस्ट शुरू होने का समय (`started_at`) सेव करे; शेष समय = `duration − (now − started_at)`।
- **FR-T2:** हर उत्तर पर ऑटो-सेव (AJAX) ताकि इंटरनेट कटने पर डेटा न जाए।
- **FR-T3:** **प्रति-सवाल समय ट्रैकिंग:** हर सवाल पर स्टूडेंट ने कितने सेकंड बिताए (क्लाइंट से भेजा, सर्वर वैलिडेट करे)।
- **FR-T4:** उत्तर बदलने की संख्या (answer-change count) भी रिकॉर्ड हो।
- **FR-T5:** समय खत्म → ऑटो-सबमिट (सर्वर-साइड गार्ड भी)।
- **FR-T6:** स्कोरिंग: `सही × मार्क्स − गलत × निगेटिव (यदि चालू)`।

### 4.5 Report (PDF)
रिपोर्ट में अनिवार्य:

| सेक्शन | विवरण |
|--------|-------|
| **Header** | स्कूल का **लोगो**, स्कूल का नाम |
| **Test Info** | असेसमेंट का **नाम**, **सब्जेक्ट**, **तारीख**, क्लास |
| **Student Info** | नाम, क्लास |
| **Score Summary** | कुल मार्क्स / अधिकतम, प्रतिशत, सही, गलत, छोड़े गए, लिया गया कुल समय |
| **Mistakes Section** | हर गलत सवाल: सवाल, स्टूडेंट का उत्तर, सही उत्तर, व्याख्या, टॉपिक |
| **Topic-wise Performance** | टॉपिक अनुसार सही/गलत (टेबल/बार चार्ट) |
| **Time Analysis** | औसत समय/सवाल, सबसे धीमे सवाल, समय बनाम सटीकता |
| **AI Feedback** | कमज़ोर क्षेत्र, ताकतें, सुधार सुझाव, अभ्यास योजना |
| **Footer** | जनरेट की तारीख/समय |

### 4.6 AI Evaluation (LangChain Deep Agents)
(विस्तार नीचे सेक्शन 7 में)

---

## 5. Non-Functional Requirements

| Area | Requirement |
|------|-------------|
| **Performance** | 60 एक साथ टेस्ट देने वाले स्टूडेंट्स बिना लैग के |
| **Reliability** | उत्तर ऑटो-सेव; सर्वर रीस्टार्ट पर सेशन बहाल |
| **Security** | Admin पासवर्ड bcrypt/werkzeug हैश; CSRF टोकन; फ़ाइल अपलोड वैलिडेशन; सवालों के सही उत्तर **कभी** क्लाइंट को न भेजे जाएँ |
| **Cheating गार्ड (बेसिक)** | सवाल/ऑप्शन शफल; सर्वर-साइड टाइमर; टैब-स्विच की गिनती लॉग (चेतावनी, ब्लॉक नहीं) |
| **Privacy** | सिर्फ़ नाम + क्लास स्टोर; कोई अनावश्यक PII नहीं; LLM को भेजे डेटा में **नाम न भेजें** (Student ID से अनामीकरण) |
| **Usability** | मोबाइल-रिस्पॉन्सिव; बड़े बटन; सरल भाषा |
| **Language** | UI अंग्रेज़ी + हिंदी विकल्प; AI फीडबैक चुनी हुई भाषा (English/Hindi/Hinglish) में |
| **Accessibility** | पर्याप्त कंट्रास्ट, कीबोर्ड नेविगेशन |

---

## 6. System Architecture

```
┌────────────────────────┐
│  Browser (HTML/CSS/JS) │
│  Student UI | Admin UI │
└───────────┬────────────┘
            │ HTTP / AJAX (JSON)
┌───────────▼────────────────────────────────┐
│              Flask Backend                 │
│  Blueprints: auth, admin, student, report  │
│  Services: csv_service, test_engine,       │
│            scoring, pdf_service            │
│  Background worker (RQ/Celery/Thread)      │
└───────┬─────────────────────┬──────────────┘
        │                     │
┌───────▼───────┐     ┌───────▼─────────────────────┐
│ SQLite/Postgres│     │  AI Evaluation Service      │
│ (SQLAlchemy)   │     │  LangChain Deep Agent       │
└───────────────┘     │  (LLM + tools + sub-agents) │
                      └─────────────────────────────┘
        │
┌───────▼───────────┐
│ File Storage       │  logos, uploaded CSVs, generated PDFs
└───────────────────┘
```

### 6.1 Tech Choices
| Layer | Choice | कारण |
|-------|--------|------|
| Frontend | HTML, CSS (Bootstrap/Tailwind CDN वैकल्पिक), Vanilla JS | आपकी ज़रूरत |
| Backend | Flask + Flask-SQLAlchemy + Flask-Login (Admin) | सरल, तेज़ |
| DB | SQLite (शुरुआत), बाद में PostgreSQL | आसान सेटअप → स्केल |
| PDF | WeasyPrint (HTML→PDF) या ReportLab | रिपोर्ट को HTML/CSS से डिज़ाइन कर सकते हैं |
| Charts | Matplotlib (PDF के लिए इमेज) / Chart.js (वेब पर) | |
| AI | LangChain + **Deep Agents** (`deepagents`) | आपकी ज़रूरत |
| Background jobs | शुरुआत: Python thread; बाद में RQ/Celery | AI में समय लगता है |

---

## 7. AI Evaluation Design (LangChain Deep Agents)

### 7.1 क्यों Deep Agent
सिर्फ़ एक prompt से "feedback बना दो" कहना सतही आउटपुट देता है। Deep Agent में **planning (to-do list)**, **sub-agents**, **virtual file system (डेटा/ड्राफ्ट रखने के लिए)** और **लंबे संदर्भ का प्रबंधन** होता है। इससे हर स्टूडेंट का **कई कोणों से** विश्लेषण संभव होता है।

### 7.2 Agent Architecture

```
Main Agent: "Evaluation Orchestrator"
   │  (to-do list बनाता है, sub-agents को काम बाँटता है, अंतिम रिपोर्ट जोड़ता है)
   │
   ├── Sub-agent 1: Performance Analyst
   │     काम: टॉपिक-वार / टाइप-वार / कठिनाई-वार सटीकता निकालना
   │
   ├── Sub-agent 2: Time & Behavior Analyst
   │     काम: प्रति-सवाल समय, जल्दबाज़ी (बहुत कम समय + गलत), अटकना (बहुत ज़्यादा समय),
   │           उत्तर बदलने का पैटर्न, छोड़े सवाल
   │
   ├── Sub-agent 3: Mistake Diagnoser
   │     काम: हर गलत सवाल की संभावित वजह (concept gap / careless / calculation / misread)
   │
   └── Sub-agent 4: Study Coach
         काम: ऊपर के नतीजों से 3–5 कार्य-योग्य सुझाव और छोटा अभ्यास प्लान
```

### 7.3 Tools (Python functions जिन्हें एजेंट कॉल करेगा)
| Tool | Input | Output |
|------|-------|--------|
| `get_attempt_data(attempt_id)` | attempt id | सवाल, उत्तर, सही/गलत, समय, topic, type, difficulty |
| `topic_accuracy(attempt_id)` | attempt id | टॉपिक → % सटीकता |
| `type_accuracy(attempt_id)` | attempt id | question_type → % सटीकता |
| `time_stats(attempt_id)` | attempt id | औसत समय, सबसे धीमे/तेज़ सवाल, outliers |
| `class_benchmark(test_id)` | test id | क्लास औसत (तुलना के लिए, अनामीकृत) |
| `past_attempts(student_key)` | स्टूडेंट की पहचान | पिछले टेस्टों की प्रगति (यदि उपलब्ध) |

> **ज़रूरी:** सारे आँकड़े (प्रतिशत, औसत) **Python कोड से गणना** हों, LLM से नहीं। LLM सिर्फ़ व्याख्या और सुझाव दे। इससे हैल्युसिनेशन घटता है।

### 7.4 Structured Output (JSON Schema)
एजेंट का अंतिम आउटपुट Pydantic स्कीमा में हो ताकि PDF में सीधे डाला जा सके:

```json
{
  "summary": "2-3 वाक्य का समग्र सार",
  "strengths": [{"topic": "...", "evidence": "..."}],
  "weak_areas": [{"topic": "...", "question_type": "...", "evidence": "...", "priority": "high|medium|low"}],
  "time_insights": ["..."],
  "mistake_patterns": [{"pattern": "careless|concept_gap|...", "details": "..."}],
  "action_plan": [{"step": "...", "estimated_time": "...", "resource_hint": "..."}],
  "encouragement": "एक प्रेरक वाक्य"
}
```

### 7.5 Guardrails
- LLM को **स्टूडेंट का नाम नहीं** जाएगा (सिर्फ़ anonymous ID)।
- टोन: सकारात्मक, रचनात्मक, कक्षा-स्तर के अनुरूप सरल भाषा।
- अगर डेटा कम है (जैसे < 5 सवाल हल किए) → जनरिक चेतावनी, गहरे निष्कर्ष नहीं।
- **Fallback:** AI फेल/टाइमआउट होने पर **नियम-आधारित (rule-based) फीडबैक** (टॉपिक सटीकता + समय) रिपोर्ट में जाए ताकि रिपोर्ट कभी खाली न रहे।
- आउटपुट वैलिडेशन: स्कीमा से मेल न खाए तो 1 बार रीट्राई।
- LLM कॉल्स के टोकन/लागत का लॉग, और प्रति-टेस्ट बजट सीमा।

### 7.6 Memory/Context
- Deep Agent का virtual file system: `/data/attempt.json`, `/analysis/*.md`, `/draft/feedback.json`।
- Admin सेटिंग में "फीडबैक भाषा" और "फीडबैक टोन" का कॉन्फ़िग (अगर `agent.md` जैसी memory फ़ाइल यूज़ करनी हो, तो स्कूल-स्तर के निर्देश वहीं रखें)।

### 7.7 Evaluation Trigger
1. स्टूडेंट Submit करे → स्कोरिंग तुरंत (सिंक्रोनस)।
2. Attempt का स्टेटस `scored` → बैकग्राउंड जॉब `ai_feedback` शुरू।
3. पूरा होने पर `report_ready` → PDF जनरेट।
4. Result पेज पोलिंग से स्टेटस चेक करके "Download Report" बटन सक्रिय करे।

---

## 8. Data Model

```
School_Settings(id, school_name, logo_path)

Admin(id, username, password_hash, created_at)

Test(id, name, subject, class_name, total_questions, duration_min,
     marks_per_q, negative_marking, shuffle, allow_reattempt,
     status[draft|live|closed], created_by, created_at, live_at, closed_at)

Question(id, test_id, q_no, text, opt_a, opt_b, opt_c, opt_d,
         correct_option, topic, question_type, difficulty, explanation)

Student(id, name, class_name, created_at)

Attempt(id, test_id, student_id, started_at, submitted_at,
        score, max_score, correct, wrong, skipped,
        total_time_sec, tab_switches,
        status[in_progress|scored|feedback_pending|report_ready|failed])

Answer(id, attempt_id, question_id, selected_option, is_correct,
       time_spent_sec, change_count, answered_at)

Feedback(id, attempt_id, json_payload, language, model_used,
         source[ai|fallback], created_at)

Report(id, attempt_id, pdf_path, generated_at)
```

**मुख्य रिश्ते:** Test 1—N Question | Test 1—N Attempt | Attempt 1—N Answer | Attempt 1—1 Feedback | Attempt 1—1 Report

---

## 9. API / Routes (Flask)

### Student
| Method | Route | काम |
|--------|-------|-----|
| GET | `/` | नाम + क्लास फ़ॉर्म |
| POST | `/start` | स्टूडेंट बनाना, लाइव टेस्ट खोजना |
| GET | `/test/instructions` | निर्देश पेज |
| POST | `/test/begin` | Attempt शुरू, टाइमर स्टार्ट |
| GET | `/test/questions` | सवाल (सही उत्तर बिना) |
| POST | `/test/answer` | उत्तर + समय ऑटो-सेव |
| POST | `/test/submit` | सबमिट + स्कोरिंग |
| GET | `/result/<attempt_id>` | रिज़ल्ट पेज |
| GET | `/result/<attempt_id>/status` | AI/रिपोर्ट स्टेटस (पोलिंग) |
| GET | `/report/<attempt_id>/download` | PDF डाउनलोड |

### Admin (`/admin/...`)
| Method | Route | काम |
|--------|-------|-----|
| GET/POST | `/admin/login`, `/admin/logout` | लॉगिन/लॉगआउट |
| GET | `/admin/dashboard` | डैशबोर्ड |
| GET/POST | `/admin/tests/new` | टेस्ट बनाना |
| GET | `/admin/template.csv` | CSV Template डाउनलोड |
| POST | `/admin/tests/<id>/upload` | CSV अपलोड + वैलिडेशन |
| GET | `/admin/tests/<id>/preview` | सवाल प्रीव्यू |
| POST | `/admin/tests/<id>/live` | लाइव करना |
| POST | `/admin/tests/<id>/close` | बंद करना |
| GET | `/admin/tests/<id>/monitor` | लाइव मॉनिटर |
| GET | `/admin/tests/<id>/results` | रिज़ल्ट तालिका |
| GET | `/admin/tests/<id>/results.csv` | एक्सपोर्ट |
| POST | `/admin/settings/logo` | लोगो अपलोड |

---

## 10. UI Screens

**Student:** (1) Entry, (2) Instructions, (3) Test Screen (टाइमर ऊपर, सवाल, 4 ऑप्शन, palette), (4) Submit Confirmation, (5) Result + Report Download।

**Admin:** (1) Login, (2) Dashboard, (3) Create Test, (4) CSV Upload + Errors, (5) Preview, (6) Live Monitor, (7) Results, (8) School Settings।

**डिज़ाइन सिद्धांत:** साफ़-सुथरा, स्कूल-फ्रेंडली रंग, बड़ा फ़ॉन्ट, टेस्ट पेज पर कोई ध्यान भटकाने वाली चीज़ नहीं।

---

## 11. Project Structure

```
assessment-tracker/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── blueprints/
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── student.py
│   │   └── report.py
│   ├── services/
│   │   ├── csv_service.py
│   │   ├── test_engine.py
│   │   ├── scoring.py
│   │   └── pdf_service.py
│   ├── ai/
│   │   ├── agent.py          # create_deep_agent(...) और sub-agents
│   │   ├── tools.py          # analysis tools
│   │   ├── schemas.py        # Pydantic output schema
│   │   ├── fallback.py       # rule-based feedback
│   │   └── prompts.py
│   ├── templates/            # Jinja2 HTML (student/, admin/, report/)
│   └── static/               # css, js, uploads (logo)
├── instance/                 # SQLite DB
├── reports/                  # generated PDFs
├── tests/
├── config.py
├── requirements.txt
├── .env                      # API keys (git में नहीं)
└── run.py
```

---

## 12. Development Plan (Milestones)

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **P0 – Setup** | 1–2 दिन | रिपो, Flask स्केलेटन, DB मॉडल, बेस टेम्पलेट |
| **P1 – Admin Core** | 3–4 दिन | लॉगिन, टेस्ट क्रिएशन, CSV Template, अपलोड + वैलिडेशन, लाइव/क्लोज़ |
| **P2 – Student Test** | 4–5 दिन | नाम/क्लास एंट्री, टेस्ट इंजन, सर्वर टाइमर, ऑटो-सेव, प्रति-सवाल समय, सबमिट + स्कोरिंग |
| **P3 – Report (बिना AI)** | 3 दिन | PDF: लोगो, टेस्ट इन्फो, स्कोर, गलतियाँ, टॉपिक चार्ट |
| **P4 – AI Evaluation** | 5–6 दिन | Deep Agent, tools, sub-agents, structured output, fallback, बैकग्राउंड जॉब, रिपोर्ट में इंटीग्रेशन |
| **P5 – Monitoring & Results** | 2–3 दिन | लाइव मॉनिटर, रिज़ल्ट टेबल, एक्सपोर्ट |
| **P6 – QA & Hardening** | 3–4 दिन | लोड टेस्ट, सिक्योरिटी, मोबाइल टेस्ट, बग फ़िक्स |
| **P7 – Pilot** | 1 सप्ताह | एक क्लास में असली टेस्ट, फीडबैक, सुधार |

**कुल अनुमान:** लगभग 5–6 सप्ताह (1 डेवलपर)।

---

## 13. Testing Strategy
- **Unit:** स्कोरिंग, CSV वैलिडेशन, टाइमर गणना, tools के आँकड़े।
- **Integration:** पूरा फ़्लो (CSV → लाइव → टेस्ट → रिपोर्ट)।
- **AI Eval:** 20–30 सैंपल attempts पर आउटपुट की मैनुअल जाँच (सटीकता, टोन, स्कीमा वैलिडिटी)।
- **Load:** 60 समवर्ती स्टूडेंट्स।
- **Edge cases:** समय खत्म होते ही सबमिट, ब्राउज़र रिफ्रेश, इंटरनेट कटना, डुप्लिकेट नाम, खराब CSV, बड़ा लोगो।

---

## 14. Risks और Mitigation

| Risk | असर | समाधान |
|------|-----|--------|
| LLM धीमा/फेल | रिपोर्ट में देरी | बैकग्राउंड जॉब + rule-based fallback |
| LLM की लागत | बजट | संक्षिप्त इनपुट, टोकन सीमा, कैशिंग, छोटा मॉडल sub-agents के लिए |
| स्टूडेंट नाम/क्लास गलत लिखें | रिज़ल्ट मिलान मुश्किल | क्लास ड्रॉपडाउन, Admin में नाम सुधारने का विकल्प |
| नकल | निष्पक्षता | शफलिंग, सर्वर टाइमर, tab-switch लॉग |
| बिना लॉगिन = कोई भी किसी के नाम से दे सकता है | डेटा की सटीकता | (भविष्य) रोल नंबर/क्लास कोड; अभी Admin मॉनिटर से निगरानी |
| खराब CSV | टेस्ट न बन पाए | कड़ा वैलिडेशन + स्पष्ट त्रुटि संदेश |
| AI का गलत/अनुचित फीडबैक | बच्चे पर असर | स्कीमा, टोन नियम, Admin द्वारा रिव्यू का विकल्प |

---

## 15. Future Enhancements
- रोल नंबर / क्लास कोड से सुरक्षित एंट्री
- समय के साथ प्रोग्रेस ट्रैकिंग (स्टूडेंट-वार ग्राफ़)
- क्लास-स्तर का AI विश्लेषण (टीचर के लिए: "क्लास इस टॉपिक में कमज़ोर है")
- सवाल बैंक + टैग से ऑटो टेस्ट जनरेशन
- पेरेंट को रिपोर्ट ईमेल/WhatsApp
- इमेज वाले सवाल, अधिक सवाल प्रकार
- बहु-स्कूल (multi-tenant) सपोर्ट

---

## 16. Open Questions (आपको तय करने हैं)
1. **निगेटिव मार्किंग** चाहिए या नहीं?
2. एक स्टूडेंट एक टेस्ट **दोबारा** दे सकता है या नहीं?
3. क्या सवाल **एक-एक करके** दिखें या पूरा पेज एक साथ?
4. रिपोर्ट सिर्फ़ **अंग्रेज़ी** में या **हिंदी/Hinglish** फीडबैक भी?
5. कौन सा **LLM** (Claude/OpenAI/अन्य) और बजट कितना?
6. डिप्लॉयमेंट कहाँ: स्कूल का लोकल सर्वर या क्लाउड?
7. क्या **Admin एक ही** होगा या कई टीचर्स के अलग-अलग लॉगिन?
8. स्टूडेंट रिपोर्ट तुरंत देखे या टीचर के **अप्रूव** करने के बाद?

---

## 17. Definition of Done (v1)
- [ ] Admin CSV Template डाउनलोड करके, भरकर, अपलोड करके टेस्ट लाइव कर सके
- [ ] Admin सवाल संख्या (डिफ़ॉल्ट 20) और समय तय कर सके
- [ ] स्टूडेंट सिर्फ़ नाम + क्लास से टेस्ट दे सके; टाइमर सर्वर-साइड
- [ ] सबमिट पर स्कोर तुरंत दिखे
- [ ] PDF में लोगो, सब्जेक्ट, टेस्ट नाम, तारीख, मार्क्स और सभी गलतियाँ हों
- [ ] Deep Agent से टॉपिक/टाइप/समय आधारित AI फीडबैक रिपोर्ट में जुड़े
- [ ] AI फेल होने पर fallback फीडबैक काम करे
- [ ] 60 समवर्ती स्टूडेंट्स पर टेस्ट सफल

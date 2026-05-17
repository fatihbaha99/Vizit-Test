const API_BASE = 'http://3.122.83.90:5000';

let currentQuestionIndex = 0;
let totalQuestions = 0;
let questions = [];
let hasAnswered = false;
let currentScore = 0;

let currentCaseIndex = 0;
let caseData = null;
let caseFollowups = [];

let currentLang = 'en';
let configData = null;

const screens = {
    setup: document.getElementById('setup-screen'),
    loading: document.getElementById('loading-screen'),
    quiz: document.getElementById('quiz-screen'),
    case: document.getElementById('case-screen'),
    results: document.getElementById('results-screen'),
    caseResults: document.getElementById('case-results-screen'),
    error: document.getElementById('error-screen')
};

function showScreen(screenName) {
    Object.values(screens).forEach(screen => screen.classList.add('hidden'));
    if (screens[screenName]) {
        screens[screenName].classList.remove('hidden');
    }
}

const LANG = {
    en: {
        appTitle: 'Vizit Medical Quiz Generator',
        appSubtitle: 'AI-powered medical quiz with 7 options',
        introText: 'This tool generates AI-powered medical quiz questions. Select your preferences below and click "Generate Questions" to start.',
        setupTitle: 'Configure Your Quiz',
        labelApiType: 'AI Model',
        labelQuestionType: 'Question Type',
        labelCategory: 'Category',
        labelTopic: 'Specific Topic (Optional)',
        hintTopic: 'Leave empty for general category questions',
        placeholderTopic: 'e.g., malnutrition, heart failure, diabetes...',
        labelDifficulty: 'Difficulty',
        labelCount: 'Number of Questions (1-20)',
        btnGenerate: 'Generate Questions',
        loadingTextMCQ: 'Generating medical questions...',
        loadingTextCase: 'Generating case study...',
        loadingHint: 'This may take a few seconds',
        questionOf: (n, total) => `Question ${n} of ${total}`,
        score: (s) => `Score: ${s}`,
        correct: 'Correct!',
        incorrect: 'Incorrect',
        correctAnswer: 'Correct Answer: ',
        explanation: 'Explanation: ',
        hint: 'Hint: ',
        secondChance: 'You have one more attempt.',
        noExplanation: 'No explanation available.',
        noQuestions: 'No questions were generated',
        invalidJSON: 'Invalid JSON from server: ',
        errorSubmit: 'Error submitting answer. Please try again.',
        errorResults: 'Error loading results.',
        excellent: 'Excellent!',
        goodJob: 'Good job!',
        keepPracticing: 'Keep practicing!',
        yourAnswer: 'Your answer: ',
        correctAnswerLabel: 'Correct answer: ',
        age: 'Age: ',
        gender: ' | Gender: ',
        occupation: ' | Occupation: ',
        nA: 'N/A',
        you: 'You',
        ai: 'AI',
        errorPrefix: 'Error: ',
        startDiscussion: 'Start the discussion',
        welcomeMsg: 'Welcome! Ask me anything about this case.',
        defaultHint: 'Review the relevant clinical guidelines for this condition.',
        prevBtn: 'Previous Question',
        nextBtn: 'Next Question',
        finishBtn: 'View Results',
        finishCase: 'Finish Case',
        restartQuiz: 'Start New Quiz',
        restartCase: 'Start New Case',
        tryAgain: 'Try Again',
        resultsTitle: 'Quiz Results',
        caseResultsTitle: 'Case Study Results',
        errorTitle: 'Error',
        sectionPatient: 'Patient Information',
        sectionComplaint: 'Chief Complaint',
        sectionHistory: 'History of Present Illness',
        sectionPhysical: 'Physical Examination',
        sectionLabs: 'Laboratory Results',
        sectionImaging: 'Imaging',
        chatPlaceholder: 'Ask about the case...',
        diffInt: 'Intermediate',
        diffDiff: 'Difficult',
        diffExp: 'Expert',
        diffGrand: 'Grand Master',
        typeMCQ: 'Multiple Choice',
        typeCase: 'Case Study'
    },
    tr: {
        appTitle: 'Vizit Tıbbi Soru Oluşturucu',
        appSubtitle: 'Yapay zeka destekli, 7 seçenekli tıbbi sınav',
        introText: 'Bu araç, yapay zeka destekli tıbbi sınav soruları oluşturur. Tercihlerinizi aşağıdan seçin ve başlamak için "Soru Oluştur"a tıklayın.',
        setupTitle: 'Sınavınızı Yapılandırın',
        labelApiType: 'AI Modeli',
        labelQuestionType: 'Soru Türü',
        labelCategory: 'Kategori',
        labelTopic: 'Özel Konu (İsteğe Bağlı)',
        hintTopic: 'Boş bırakılırsa genel kategori soruları',
        placeholderTopic: 'örn. malnütrisyon, kalp yetmezliği, diyabet...',
        labelDifficulty: 'Zorluk',
        labelCount: 'Soru Sayısı (1-20)',
        btnGenerate: 'Soru Oluştur',
        loadingTextMCQ: 'Tıbbi sorular oluşturuluyor...',
        loadingTextCase: 'Vaka çalışması oluşturuluyor...',
        loadingHint: 'Bu birkaç saniye sürebilir',
        questionOf: (n, total) => `Soru ${n} / ${total}`,
        score: (s) => `Puan: ${s}`,
        correct: 'Doğru!',
        incorrect: 'Yanlış',
        correctAnswer: 'Doğru Cevap: ',
        explanation: 'Açıklama: ',
        hint: 'İpucu: ',
        secondChance: 'Bir hakkınız daha var.',
        noExplanation: 'Açıklama mevcut değil.',
        noQuestions: 'Hiç soru oluşturulamadı',
        invalidJSON: 'Sunucudan geçersiz JSON: ',
        errorSubmit: 'Cevap gönderilirken hata oluştu. Lütfen tekrar deneyin.',
        errorResults: 'Sonuçlar yüklenirken hata oluştu.',
        excellent: 'Mükemmel!',
        goodJob: 'İyi iş!',
        keepPracticing: 'Pratik yapmaya devam et!',
        yourAnswer: 'Cevabınız: ',
        correctAnswerLabel: 'Doğru cevap: ',
        age: 'Yaş: ',
        gender: ' | Cinsiyet: ',
        occupation: ' | Meslek: ',
        nA: 'Yok',
        you: 'Sen',
        ai: 'AI',
        errorPrefix: 'Hata: ',
        startDiscussion: 'Tartışmayı başlat',
        welcomeMsg: 'Hoş geldin! Bu vaka hakkında istediğini sor.',
        defaultHint: 'Bu durumla ilgili klinik kılavuzları gözden geçirin.',
        prevBtn: 'Önceki Soru',
        nextBtn: 'Sonraki Soru',
        finishBtn: 'Sonuçları Gör',
        finishCase: 'Vakayı Bitir',
        restartQuiz: 'Yeni Sınav',
        restartCase: 'Yeni Vaka',
        tryAgain: 'Tekrar Dene',
        resultsTitle: 'Sınav Sonuçları',
        caseResultsTitle: 'Vaka Çalışması Sonuçları',
        errorTitle: 'Hata',
        sectionPatient: 'Hasta Bilgileri',
        sectionComplaint: 'Ana Şikayet',
        sectionHistory: 'Hastalık Öyküsü',
        sectionPhysical: 'Fizik Muayene',
        sectionLabs: 'Laboratuvar Sonuçları',
        sectionImaging: 'Görüntüleme',
        chatPlaceholder: 'Vaka hakkında soru sor...',
        diffInt: 'Orta',
        diffDiff: 'Zor',
        diffExp: 'Uzman',
        diffGrand: 'Grand Master',
        typeMCQ: 'Çoktan Seçmeli',
        typeCase: 'Vaka Çalışması'
    }
};

function t(key) {
    const tr = LANG[currentLang] || LANG.en;
    return typeof tr[key] === 'function' ? tr[key] : tr[key];
}

function translateUI() {
    const tr = LANG[currentLang] || LANG.en;

    document.getElementById('app-title').textContent = tr.appTitle;
    document.getElementById('app-subtitle').textContent = tr.appSubtitle;
    document.getElementById('intro-text').textContent = tr.introText;
    document.getElementById('setup-title').textContent = tr.setupTitle;
    document.getElementById('label-api-type').textContent = tr.labelApiType;
    document.getElementById('label-question-type').textContent = tr.labelQuestionType;
    document.getElementById('label-category').textContent = tr.labelCategory;
    document.getElementById('label-topic').textContent = tr.labelTopic;
    document.getElementById('hint-topic').textContent = tr.hintTopic;
    document.getElementById('topic').placeholder = tr.placeholderTopic;
    document.getElementById('label-difficulty').textContent = tr.labelDifficulty;
    document.getElementById('label-count').textContent = tr.labelCount;
    document.getElementById('btn-generate').textContent = tr.btnGenerate;
    document.getElementById('loading-hint').textContent = tr.loadingHint;
    document.getElementById('prev-btn').textContent = tr.prevBtn;
    document.getElementById('next-btn').textContent = tr.nextBtn;
    document.getElementById('finish-btn').textContent = tr.finishBtn;
    document.getElementById('case-finish-btn').textContent = tr.finishCase;
    document.getElementById('restart-btn').textContent = tr.restartQuiz;
    document.getElementById('case-restart-btn').textContent = tr.restartCase;
    document.getElementById('btn-try-again').textContent = tr.tryAgain;
    document.getElementById('results-title').textContent = tr.resultsTitle;
    document.getElementById('case-results-title').textContent = tr.caseResultsTitle;
    document.getElementById('error-title').textContent = tr.errorTitle;
    document.getElementById('section-patient').textContent = tr.sectionPatient;
    document.getElementById('section-complaint').textContent = tr.sectionComplaint;
    document.getElementById('section-history').textContent = tr.sectionHistory;
    document.getElementById('section-physical').textContent = tr.sectionPhysical;
    document.getElementById('section-labs').textContent = tr.sectionLabs;
    document.getElementById('section-imaging').textContent = tr.sectionImaging;
    document.getElementById('case-chat-input').placeholder = tr.chatPlaceholder;

    document.documentElement.lang = currentLang === 'tr' ? 'tr' : 'en';

    document.getElementById('lang-en').className = 'lang-btn' + (currentLang === 'en' ? ' active' : '');
    document.getElementById('lang-tr').className = 'lang-btn' + (currentLang === 'tr' ? ' active' : '');

    if (configData) {
        populateSelects();
    }
}

function populateSelects() {
    const tr = LANG[currentLang] || LANG.en;
    const isTr = currentLang === 'tr';

    // API type
    const apiSelect = document.getElementById('api-type');
    apiSelect.innerHTML = configData.supported_apis.map(a => `<option value="${a}">${a}</option>`).join('');

    // Question type
    const qtSelect = document.getElementById('question-type');
    qtSelect.innerHTML = configData.question_types.map(qt => {
        const label = isTr ? (qt === 'Multiple Choice' ? tr.typeMCQ : tr.typeCase) : qt;
        return `<option value="${qt}">${label}</option>`;
    }).join('');

    // Category
    const catSelect = document.getElementById('category');
    catSelect.innerHTML = Object.entries(configData.categories).map(([key, trName]) => {
        const label = isTr ? trName : key;
        const selected = key === 'Pediatrics' ? ' selected' : '';
        return `<option value="${key}"${selected}>${label}</option>`;
    }).join('');

    // Difficulty
    const diffSelect = document.getElementById('difficulty');
    diffSelect.innerHTML = configData.difficulties.map(d => {
        const diffLabels = { 'Intermediate': tr.diffInt, 'Difficult': tr.diffDiff, 'Expert': tr.diffExp, 'Grand Master': tr.diffGrand };
        const label = isTr ? diffLabels[d] || d : d;
        return `<option value="${d}">${label}</option>`;
    }).join('');

    // Initial difficulty description
    updateDifficultyDesc();
}

function updateDifficultyDesc() {
    const descEl = document.getElementById('difficulty-description');
    const diff = document.getElementById('difficulty').value;
    const descs = currentLang === 'tr' ? configData.difficulty_descriptions_tr : configData.difficulty_descriptions;
    descEl.textContent = descs[diff] || '';
}

async function switchLang(newLang) {
    if (newLang === currentLang) return;
    try {
        await fetch(`${API_BASE}/set-lang`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lang: newLang })
        });
        currentLang = newLang;
        translateUI();
    } catch (e) {
        console.error('Failed to switch language', e);
    }
}

// Init: fetch config on page load
(async function init() {
    try {
        const resp = await fetch(`${API_BASE}/config`);
        configData = await resp.json();
        currentLang = configData.lang || 'en';
        translateUI();
    } catch (e) {
        console.error('Failed to load config', e);
    }
})();

// Form events
document.getElementById('question-type').addEventListener('change', function() {
    const countGroup = document.getElementById('count-group');
    countGroup.style.display = this.value === 'Case Study' ? 'none' : 'block';
});

document.getElementById('difficulty').addEventListener('change', updateDifficultyDesc);

document.getElementById('quiz-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    currentQuestionIndex = 0;
    totalQuestions = 0;
    questions = [];
    hasAnswered = false;
    currentScore = 0;
    caseData = null;
    currentCaseIndex = 0;
    caseFollowups = [];
    attemptCount = {};

    const apiType = document.getElementById('api-type').value;
    const category = document.getElementById('category').value;
    const difficulty = document.getElementById('difficulty').value;
    const topic = document.getElementById('topic').value;
    const questionType = document.getElementById('question-type').value;
    const count = parseInt(document.getElementById('count').value) || 5;

    const tr = LANG[currentLang] || LANG.en;
    document.getElementById('loading-text').textContent = questionType === 'Case Study' ? tr.loadingTextCase : tr.loadingTextMCQ;

    showScreen('loading');

    try {
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                api_type: apiType,
                category,
                difficulty,
                topic,
                count,
                question_type: questionType,
                lang: currentLang
            })
        });

        const text = await response.text();

        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            document.getElementById('error-message').textContent = tr.invalidJSON + text.substring(0, 200);
            showScreen('error');
            return;
        }

        if (data.error) {
            document.getElementById('error-message').textContent = data.error + (data.details ? ': ' + data.details : '');
            showScreen('error');
            return;
        }

        if (data.type === 'case_study') {
            caseData = data.case;
            currentCaseIndex = 0;
            caseFollowups = [];
            showCaseStudy(caseData);
        } else {
            questions = data.questions;
            totalQuestions = data.total;
            currentQuestionIndex = 0;
            currentScore = 0;

            if (totalQuestions > 0) {
                showQuestion(0);
                showScreen('quiz');
            } else {
                document.getElementById('error-message').textContent = tr.noQuestions;
                showScreen('error');
            }
        }
    } catch (error) {
        document.getElementById('error-message').textContent = error.message || error;
        showScreen('error');
    }
});

function showQuestion(index) {
    currentQuestionIndex = index;
    const tr = LANG[currentLang] || LANG.en;

    const feedbackEl = document.getElementById('feedback');
    const feedbackContentEl = document.getElementById('feedback-content');
    if (feedbackEl) feedbackEl.style.display = 'none';
    if (feedbackContentEl) feedbackContentEl.innerHTML = '';

    const question = questions[index];
    if (!question) return;

    const qNum = document.getElementById('question-number');
    if (qNum) qNum.textContent = tr.questionOf(index + 1, totalQuestions);
    const qCat = document.getElementById('question-category');
    if (qCat) qCat.textContent = question.category || '';
    const qDiff = document.getElementById('question-difficulty');
    if (qDiff) qDiff.textContent = question.difficulty || '';

    const qText = document.getElementById('question-text');
    if (qText) qText.textContent = question.question;

    const optionsContainer = document.getElementById('options-container');
    if (optionsContainer) optionsContainer.innerHTML = '';

    const options = question.options || {};
    const letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];

    letters.forEach(letter => {
        if (options[letter]) {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.innerHTML = `
                <span class="option-letter">${letter}</span>
                <span class="option-text">${options[letter]}</span>
            `;
            btn.addEventListener('click', () => selectAnswer(letter, btn));
            optionsContainer.appendChild(btn);
        }
    });

    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const finishBtn = document.getElementById('finish-btn');

    if (question.answered || question.user_answer) {
        hasAnswered = true;
        const correctLetter = question.correct_answer;
        const isCorrect = question.is_correct;
        const userAnswer = question.user_answer;
        const optionBtns = document.querySelectorAll('.option-btn');
        optionBtns.forEach(b => {
            const bLetter = b.querySelector('.option-letter').textContent;
            if (bLetter === correctLetter) {
                b.classList.add('correct');
            } else if (bLetter === userAnswer) {
                b.classList.add(isCorrect ? 'correct' : 'incorrect');
            }
            b.disabled = true;
        });

        if (feedbackEl && feedbackContentEl) {
            feedbackEl.style.display = '';
            feedbackEl.classList.remove('correct', 'incorrect');
            feedbackEl.classList.add(isCorrect ? 'correct' : 'incorrect');
            feedbackContentEl.innerHTML = `
                <h4>${isCorrect ? tr.correct : tr.incorrect}</h4>
                <p><strong>${tr.correctAnswer}${correctLetter}</strong></p>
                <p>${options[correctLetter] || ''}</p>
                <div class="explanation"><strong>${tr.explanation}</strong> ${question.explanation || tr.noExplanation}</div>
            `;
        }

        document.getElementById('score-display').textContent = tr.score(currentScore);
        prevBtn.style.visibility = index === 0 ? 'hidden' : 'visible';
        if (index >= totalQuestions - 1) {
            nextBtn.style.visibility = 'hidden';
        } else {
            nextBtn.style.visibility = 'visible';
            nextBtn.disabled = false;
        }
    } else {
        hasAnswered = false;
        prevBtn.style.visibility = index === 0 ? 'hidden' : 'visible';
        if (index >= totalQuestions - 1) {
            nextBtn.style.visibility = 'hidden';
        } else {
            nextBtn.style.visibility = 'visible';
            nextBtn.disabled = false;
        }
    }

    const progressPercent = ((index + 1) / totalQuestions) * 100;
    document.getElementById('progress-fill').style.width = `${progressPercent}%`;
}

let attemptCount = {};

async function selectAnswer(letter, btn) {
    const tr = LANG[currentLang] || LANG.en;
    const question = questions[currentQuestionIndex];
    const qIndex = currentQuestionIndex;

    if (!attemptCount[qIndex]) attemptCount[qIndex] = 0;
    const isSecondChance = attemptCount[qIndex] > 0;
    attemptCount[qIndex]++;

    if (question.answered) return;
    btn.disabled = true;

    const optionBtns = document.querySelectorAll('.option-btn');

    try {
        const response = await fetch(`${API_BASE}/answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_index: currentQuestionIndex,
                answer: letter,
                second_chance: isSecondChance
            })
        });

        const data = await response.json();

        if (data.already_answered) {
            showQuestion(currentQuestionIndex);
            return;
        }

        const correctLetter = data.correct_answer;
        const options = questions[currentQuestionIndex].options || {};

        optionBtns.forEach(b => {
            const bLetter = b.querySelector('.option-letter').textContent;
            if (bLetter === correctLetter) {
                if (data.is_correct || attemptCount[qIndex] >= 2) {
                    b.classList.add('correct');
                }
            } else if (bLetter === letter && !data.is_correct) {
                b.classList.add('incorrect');
            }
        });

        const feedback = document.getElementById('feedback');
        const feedbackContent = document.getElementById('feedback-content');

        feedback.style.display = '';
        feedback.classList.remove('correct', 'incorrect');

        if (data.is_correct) {
            feedback.classList.add('correct');
            feedbackContent.innerHTML = `
                <h4>${tr.correct}</h4>
                <p><strong>${tr.correctAnswer}${correctLetter}</strong></p>
                <p>${options[correctLetter] || ''}</p>
                <div class="explanation"><strong>${tr.explanation}</strong> ${data.explanation || tr.noExplanation}</div>
            `;
            currentScore++;
            question.user_answer = letter;
            question.is_correct = true;
            question.answered = true;
            optionBtns.forEach(b => b.disabled = true);
        } else {
            feedback.classList.add('incorrect');

            if (attemptCount[qIndex] === 1) {
                feedbackContent.innerHTML = `
                    <h4>${tr.incorrect}</h4>
                    <p><strong>${tr.hint}</strong> ${data.hint || tr.defaultHint}</p>
                    <p class="second-chance-text">${tr.secondChance}</p>
                `;
            } else {
                feedbackContent.innerHTML = `
                    <h4>${tr.incorrect}</h4>
                    <p><strong>${tr.correctAnswer}${correctLetter}</strong></p>
                    <p>${options[correctLetter] || ''}</p>
                    <div class="explanation"><strong>${tr.explanation}</strong> ${data.explanation || tr.noExplanation}</div>
                `;
                question.user_answer = letter;
                question.is_correct = false;
                question.answered = true;
                optionBtns.forEach(b => b.disabled = true);
            }
        }

        document.getElementById('score-display').textContent = tr.score(currentScore);

        if (question.answered) {
            document.getElementById('prev-btn').style.visibility = currentQuestionIndex === 0 ? 'hidden' : 'visible';
            if (currentQuestionIndex >= totalQuestions - 1) {
                document.getElementById('next-btn').style.visibility = 'hidden';
            } else {
                document.getElementById('next-btn').style.visibility = 'visible';
                document.getElementById('next-btn').disabled = false;
            }
        }
    } catch (error) {
        console.error('Error submitting answer:', error);
        alert(tr.errorSubmit);
    }
}

function retryQuestion(optionBtns) {
    const feedback = document.getElementById('feedback');
    feedback.classList.add('hidden');
    optionBtns.forEach(b => {
        b.classList.remove('incorrect', 'correct');
        b.disabled = false;
    });
}

document.getElementById('next-btn').addEventListener('click', () => {
    if (currentQuestionIndex < totalQuestions - 1) {
        currentQuestionIndex++;
        showQuestion(currentQuestionIndex);
    }
});

document.getElementById('prev-btn').addEventListener('click', () => {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        showQuestion(currentQuestionIndex);
    }
});

document.getElementById('finish-btn').addEventListener('click', async () => {
    const tr = LANG[currentLang] || LANG.en;
    try {
        const response = await fetch(`${API_BASE}/results`);
        const data = await response.json();

        document.getElementById('final-score').textContent = `${data.score}/${data.total}`;

        const scoreCircle = document.getElementById('final-score');
        const percentage = (data.score / data.total) * 100;

        scoreCircle.classList.remove('excellent', 'good', 'poor');
        if (percentage >= 80) {
            scoreCircle.classList.add('excellent');
        } else if (percentage >= 60) {
            scoreCircle.classList.add('good');
        } else {
            scoreCircle.classList.add('poor');
        }

        document.getElementById('score-text').textContent =
            percentage >= 80 ? tr.excellent :
            percentage >= 60 ? tr.goodJob : tr.keepPracticing;

        const answersReview = document.getElementById('answers-review');
        answersReview.innerHTML = '';

        data.answers.forEach((answer, i) => {
            const question = questions[i] || {};
            const options = question.options || {};

            const item = document.createElement('div');
            item.className = `answer-item ${answer.is_correct ? 'correct' : 'incorrect'}`;
            item.innerHTML = `
                <h4>Q${i + 1}: ${(answer.question || '').substring(0, 100)}${(answer.question || '').length > 100 ? '...' : ''}</h4>
                <div class="answer-details">
                    <div>${tr.yourAnswer}<span class="${answer.is_correct ? 'correct-badge' : 'incorrect-badge'}">${answer.selected || ''}</span></div>
                    <div>${tr.correctAnswerLabel}<span class="correct-badge">${answer.correct || ''}</span></div>
                    <div>${options[answer.correct] || ''}</div>
                    <div class="explanation"><strong>${tr.explanation}</strong> ${answer.explanation || tr.noExplanation}</div>
                </div>
            `;
            answersReview.appendChild(item);
        });

        showScreen('results');
    } catch (error) {
        console.error('Error loading results:', error);
        alert(tr.errorResults);
    }
});

let caseChatHistory = [];

function showCaseStudy(caseData) {
    const tr = LANG[currentLang] || LANG.en;

    document.getElementById('case-title').textContent = caseData.case_title || (currentLang === 'tr' ? 'Tıbbi Vaka Çalışması' : 'Medical Case Study');
    document.getElementById('case-category').textContent = caseData.category || '';
    document.getElementById('case-difficulty').textContent = caseData.difficulty || '';

    const patient = caseData.patient || {};
    document.getElementById('case-patient').innerHTML = `
        ${tr.age}${patient.age || tr.nA}${tr.gender}${patient.gender || tr.nA}${tr.occupation}${patient.occupation || tr.nA}
    `;

    document.getElementById('case-complaint').textContent = caseData.chief_complaint || tr.nA;
    document.getElementById('case-history').textContent = caseData.history || tr.nA;
    document.getElementById('case-physical').textContent = caseData.physical_exam || tr.nA;

    const labs = caseData.labs || {};
    const labsContainer = document.getElementById('case-labs');
    labsContainer.innerHTML = '';
    for (const [key, value] of Object.entries(labs)) {
        const labItem = document.createElement('div');
        labItem.className = 'lab-item';
        labItem.innerHTML = `<strong>${key}:</strong> ${value}`;
        labsContainer.appendChild(labItem);
    }

    const imagingSection = document.getElementById('imaging-section');
    if (caseData.imaging) {
        imagingSection.style.display = 'block';
        document.getElementById('case-imaging').textContent = caseData.imaging;
    } else {
        imagingSection.style.display = 'none';
    }

    caseChatHistory = [];
    const messagesEl = document.getElementById('case-chat-messages');
    messagesEl.innerHTML = '';

    showScreen('case');

    setTimeout(async () => {
        try {
            const response = await fetch(`${API_BASE}/case/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: tr.startDiscussion, lang: currentLang })
            });
            const data = await response.json();
            if (!data.error) {
                addChatMessage('ai', data.response);
                caseChatHistory.push({ role: 'assistant', content: data.response });
            }
        } catch (e) {
            addChatMessage('ai', tr.welcomeMsg);
        }
    }, 500);
}

function addChatMessage(role, text) {
    const tr = LANG[currentLang] || LANG.en;
    const messagesEl = document.getElementById('case-chat-messages');
    const msg = document.createElement('div');
    msg.className = `chat-msg ${role}`;
    msg.innerHTML = `<div class="msg-label">${role === 'user' ? tr.you : tr.ai}</div><div>${text}</div>`;
    messagesEl.appendChild(msg);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

document.getElementById('case-chat-send').addEventListener('click', async () => {
    const tr = LANG[currentLang] || LANG.en;
    const input = document.getElementById('case-chat-input');
    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    addChatMessage('user', message);
    caseChatHistory.push({ role: 'user', content: message });

    document.getElementById('case-chat-send').disabled = true;

    try {
        const response = await fetch(`${API_BASE}/case/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, lang: currentLang })
        });

        const data = await response.json();
        if (data.error) {
            addChatMessage('ai', tr.errorPrefix + data.error);
        } else {
            addChatMessage('ai', data.response);
            caseChatHistory.push({ role: 'assistant', content: data.response });
        }
    } catch (error) {
        addChatMessage('ai', tr.errorPrefix + error.message);
    } finally {
        document.getElementById('case-chat-send').disabled = false;
        document.getElementById('case-chat-input').focus();
    }
});

document.getElementById('case-chat-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('case-chat-send').click();
    }
});

document.getElementById('case-finish-btn').addEventListener('click', async () => {
    try {
        await fetch(`${API_BASE}/reset`, { method: 'POST' });
        caseData = null;
        currentCaseIndex = 0;
        caseChatHistory = [];
        showScreen('setup');
    } catch (error) {
        console.error('Error resetting:', error);
        location.reload();
    }
});

document.getElementById('restart-btn').addEventListener('click', async () => {
    try {
        await fetch(`${API_BASE}/reset`, { method: 'POST' });
        questions = [];
        currentQuestionIndex = 0;
        totalQuestions = 0;
        hasAnswered = false;
        currentScore = 0;
        attemptCount = {};
        showScreen('setup');
    } catch (error) {
        console.error('Error resetting:', error);
        location.reload();
    }
});

document.getElementById('case-restart-btn').addEventListener('click', async () => {
    try {
        await fetch(`${API_BASE}/reset`, { method: 'POST' });
        caseData = null;
        currentCaseIndex = 0;
        caseFollowups = [];
        showScreen('setup');
    } catch (error) {
        console.error('Error resetting:', error);
        location.reload();
    }
});

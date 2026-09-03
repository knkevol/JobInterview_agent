// 순수 vanilla JS로 백엔드 JSON API(main.py)를 fetch()로 호출해서 화면을 갱신한다.
// 프레임워크 없이 "필요한 데이터를 요청하고, 받은 걸로 DOM을 직접 바꾼다"는 가장 기본적인 방식.

// 지금 진행 중인 면접의 상태(repo_id, session_id, question_id)를 기억해두는 변수.
// 서버(store.py)도 이 값들을 기억하고 있지만, 브라우저 쪽에서도
// "다음 요청에 어떤 id를 실어 보낼지" 알아야 하므로 여기 따로 저장해둔다.
let currentRepoId = null;
let currentSessionId = null;
let currentQuestionId = null;

// crypto.randomUUID(): 브라우저에 내장된 함수로, 무작위 고유 문자열을 만들어준다.
// 퀴즈 기능은 로그인이 없어서, 페이지를 열 때마다 이 값을 하나 만들어서
// "이 브라우저 탭이 곧 하나의 퀴즈 세션이다"라는 식별자로 사용한다.
const quizSessionId = crypto.randomUUID();
let currentQuizId = null;


function showTab(tabName) {
    // 하드코딩으로 2개(interview/quiz)만 처리하던 걸, 리스트 순회로 바꿔서
    // 탭이 몇 개로 늘어나도 이 함수는 안 고쳐도 되게 일반화했다.
    for (const name of ["interview", "quiz", "weak"]) {
        document.getElementById(`panel-${name}`).style.display = name === tabName ? "block" : "none";
        document.getElementById(`tab-${name}`).classList.toggle("active", name === tabName);
    }
    if (tabName === "weak") {
        fetchWeakTopics();
    }
}

function showStep(stepId) {
    // "면접 연습" 탭 안의 3단계(분석/질문/평가) 중 하나만 보이게 한다.
    for (const id of ["step-analyze", "step-question", "step-evaluation"]) {
        document.getElementById(id).classList.toggle("active", id === stepId);
    }
}


// ---------- 면접 연습 흐름 ----------

async function analyzeRepo() {
    const repoUrl = document.getElementById("repo-url-input").value;
    document.getElementById("analyze-status").textContent = "분석 중입니다... (LLM 호출이 여러 번 있어서 시간이 좀 걸립니다)";

    // fetch(): 브라우저 내장 함수로 HTTP 요청을 보낸다. async/await를 쓰면
    // "응답이 올 때까지 기다렸다가 다음 줄로 넘어간다"처럼 동기 코드처럼 쓸 수 있다.
    const response = await fetch("/repos/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl }),
    });

    if (!response.ok) {
        const error = await response.json();
        document.getElementById("analyze-status").textContent = "분석 실패: " + error.detail;
        return;
    }

    const data = await response.json();
    currentRepoId = data.repo_id;
    document.getElementById("analyze-status").textContent = `분석 완료 (파일 ${data.file_count}개)`;

    await startSession();
}

async function startSession() {
    const response = await fetch("/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_id: currentRepoId }),
    });
    const data = await response.json();
    currentSessionId = data.session_id;

    await fetchQuestion();
}

async function fetchQuestion() {
    const response = await fetch(`/sessions/${currentSessionId}/question`);
    const data = await response.json();
    currentQuestionId = data.question_id;

    document.getElementById("question-text").textContent = data.question;
    document.getElementById("answer-input").value = "";
    showStep("step-question");
}

async function submitAnswer() {
    const answer = document.getElementById("answer-input").value;

    const response = await fetch(`/questions/${currentQuestionId}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer: answer }),
    });
    const evaluation = await response.json();

    const container = document.getElementById("evaluation-result");
    container.innerHTML = ""; 
    container.appendChild(renderEvaluation(evaluation));

    showStep("step-evaluation");
}

async function fetchFollowup() {
    const response = await fetch(`/questions/${currentQuestionId}/followup`);
    const data = await response.json();

    if (!data.question_id) {
        const message = document.createElement("p");
        message.textContent = data.message;
        document.getElementById("evaluation-result").appendChild(message);
        return;
    }

    currentQuestionId = data.question_id;
    document.getElementById("question-text").textContent = `[깊이 ${data.depth}] ${data.question}`;
    document.getElementById("answer-input").value = "";
    showStep("step-question");
}

function addLabeledText(parent, label, text) {
    if (!text) return; // 빈 문자열/undefined면 아예 안 그린다 (빈 줄이 여러 개 생기는 걸 방지)
    const p = document.createElement("p");
    const strong = document.createElement("strong");
    strong.textContent = label + ": ";
    p.appendChild(strong);
    // createTextNode: <strong> 태그 없이 순수 텍스트만 추가할 때 쓴다.
    // textContent로 덮어쓰면 방금 넣은 strong까지 지워지므로, 이렇게 이어 붙인다.
    p.appendChild(document.createTextNode(text));
    parent.appendChild(p);
    return p;
}

// "근거 코드", "내 답변"처럼 <h4> 제목이 붙은 섹션 박스를 만들어서 parent에 붙이고,
// 그 안에 내용을 더 채울 수 있도록 섹션 자체를 반환한다.
function addSection(parent, title) {
    const section = document.createElement("div");
    section.className = "hb-section";
    const h4 = document.createElement("h4");
    h4.textContent = title;
    section.appendChild(h4);
    parent.appendChild(section);
    return section;
}

// 평가 결과의 점수 뱃지/문단/근거 인용을 카드/태그 칩으로 나눠 그린 <div>를 만들어 돌려준다.
function renderEvaluation(evaluation) {
    const section = addSection(document.createElement("div"), "평가 결과");

    const scoreRow = document.createElement("div");
    scoreRow.className = "score-row";
    // [["총점", 82], ["일치도", 75], ...] 같은 [라벨, 값] 쌍 배열을 순회하며 뱃지를 만든다.
    for (const [label, value] of [["총점", evaluation.score], ["일치도", evaluation.accuracy], ["깊이", evaluation.depth]]) {
        const badge = document.createElement("span");
        badge.className = "score-badge";
        badge.textContent = `${label} ${value}`;
        scoreRow.appendChild(badge);
    }
    section.appendChild(scoreRow);

    addLabeledText(section, "장점", evaluation.strengths);
    addLabeledText(section, "기술적으로 잘못된 점", evaluation.incorrect_points);

    if (evaluation.mismatches_with_repo && evaluation.mismatches_with_repo.length > 0) {
        addLabeledText(section, "실제 구현과 다른 점", `${evaluation.mismatches_with_repo.length}건`);

        for (const m of evaluation.mismatches_with_repo) {
            const card = document.createElement("div");
            // verified가 true면 "verified" 클래스를 추가로 붙여서 초록 테두리로 구분한다.
            card.className = "mismatch-card" + (m.verified ? " verified" : "");

            const verifiedTag = document.createElement("div");
            verifiedTag.textContent = m.verified ? "✅ evidence 원문에서 확인됨" : "⚠️ evidence 원문에서 확인 안 됨";
            card.appendChild(verifiedTag);

            addLabeledText(card, "주장", m.claim);

            const quotePre = document.createElement("pre");
            quotePre.className = "code-block";
            quotePre.textContent = m.evidence_quote;
            card.appendChild(quotePre);

            addLabeledText(card, "설명", m.explanation);
            section.appendChild(card);
        }
    }

    addLabeledText(section, "부족한 설명", evaluation.missing_explanations);
    addLabeledText(section, "모범 답안", evaluation.model_answer);
    addLabeledText(section, "추가 설명", evaluation.further_explanation);

    // study_recommendations/related_concepts: 문자열 배열을 태그 칩으로 나열
    for (const [label, list] of [["공부하면 좋을 것", evaluation.study_recommendations], ["관련 개념", evaluation.related_concepts]]) {
        if (!list || list.length === 0) continue;
        const p = document.createElement("p");
        const strong = document.createElement("strong");
        strong.textContent = label + ": ";
        p.appendChild(strong);
        for (const tagText of list) {
            const tag = document.createElement("span");
            tag.className = "tag";
            tag.textContent = tagText;
            p.appendChild(tag);
        }
        section.appendChild(p);
    }

    return section;
}

async function fetchHistory() {
    if (!currentSessionId) {
        document.getElementById("history-result").textContent = "먼저 저장소를 분석해서 세션을 시작하세요.";
        return;
    }

    const response = await fetch(`/sessions/${currentSessionId}/history`);
    const data = await response.json();

    const container = document.getElementById("history-result");
    container.innerHTML = "";

    if (data.length === 0) {
        container.textContent = "아직 기록이 없습니다.";
        return;
    }

    for (const item of data) {
        const details = document.createElement("details");

        const summary = document.createElement("summary");
        summary.textContent = `[깊이 ${item.depth}] ${item.question}`;
        details.appendChild(summary);

        const evidenceSection = addSection(details, "근거 코드");
        const evMeta = document.createElement("div");
        evMeta.textContent = `${item.reference_evidence.file_path} · ${item.reference_evidence.class_name}::${item.reference_evidence.method_name}`;
        evidenceSection.appendChild(evMeta);
        const evPre = document.createElement("pre");
        evPre.className = "code-block";
        evPre.textContent = item.reference_evidence.snippet;
        evidenceSection.appendChild(evPre);

        const answerSection = addSection(details, "내 답변");
        // ?? : item.answer가 null/undefined일 때만 오른쪽 문구를 쓰는 널 병합 연산자
        addLabeledText(answerSection, "답변", item.answer ?? "(아직 답변 안 함)");

        if (item.evaluation) {
            details.appendChild(renderEvaluation(item.evaluation));
        }

        container.appendChild(details);
    }
}

// ---------- CS 퀴즈 흐름 ----------

async function fetchQuiz() {
    const response = await fetch(`/quiz/random?session_id=${quizSessionId}`);

    if (!response.ok) {
        document.getElementById("quiz-question").textContent = "풀 수 있는 문제가 더 없습니다.";
        document.getElementById("quiz-category").textContent = "";
        return;
    }

    const quiz = await response.json();
    currentQuizId = quiz.id;
    document.getElementById("quiz-category").textContent = `[${quiz.category}]`;
    document.getElementById("quiz-question").textContent = quiz.question;
    document.getElementById("quiz-answer-input").value = "";
    document.getElementById("quiz-result").textContent = "";
}

async function submitQuizAnswer() {
    const answer = document.getElementById("quiz-answer-input").value;

    const response = await fetch(`/quiz/${currentQuizId}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: quizSessionId, answer: answer }),
    });
    const result = await response.json();

    document.getElementById("quiz-result").textContent =
        (result.is_correct ? "정답입니다! " : "오답입니다. ") +
        `정답: ${result.correct_answer}\n해설: ${result.explanation}`;
}

// ---------- AI 퀴즈 흐름 (호출마다 비용 발생) ----------
let currentLLMQuizQuestion = null;
let currentLLMQuizCategory = null;

async function fetchLLMQuiz() {
    document.getElementById("llm-quiz-status").textContent = "AI가 문제를 만드는 중입니다...";

    const response = await fetch("/quiz/llm/generate");
    const data = await response.json();

    currentLLMQuizQuestion = data.question;
    currentLLMQuizCategory = data.category;

    document.getElementById("llm-quiz-category").textContent = `[${data.category}]`;
    document.getElementById("llm-quiz-question").textContent = data.question;
    document.getElementById("llm-quiz-answer-input").value = "";
    document.getElementById("llm-quiz-result").textContent = "";
    document.getElementById("llm-quiz-status").textContent = "";
}

async function submitLLMQuizAnswer() {
    const answer = document.getElementById("llm-quiz-answer-input").value;

    const response = await fetch("/quiz/llm/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            question: currentLLMQuizQuestion,
            category: currentLLMQuizCategory,
            answer: answer,
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        document.getElementById("llm-quiz-result").textContent = "채점 실패: " + JSON.stringify(error.detail);
        return;
    }

    const result = await response.json();

    document.getElementById("llm-quiz-result").textContent =
        (result.is_correct ? "정답입니다! " : "오답입니다. ") +
        `모범 답안: ${result.model_answer}\n설명: ${result.explanation}`;
}

// 페이지가 처음 열리면 CS 퀴즈 탭도 미리 문제 하나를 받아둔다.
fetchQuiz();

// ---------- 취약 주제 대시보드 ----------
async function fetchWeakTopics() {
    const response = await fetch("/weak-topics");
    const data = await response.json();

    const container = document.getElementById("weak-topics-result");
    container.innerHTML = "";

    if (data.length === 0) {
        container.textContent = "아직 2회 이상 반복된 취약 주제가 없습니다.";
        return;
    }

    for (const item of data) {
        const details = document.createElement("details");

        const summary = document.createElement("summary");
        summary.textContent = `${item.topic} — ${item.occurrence_count}회 등장`;
        details.appendChild(summary);

        for (const occ of item.occurrences) {
            const card = document.createElement("div");
            card.className = "hb-section";
            const p = document.createElement("p");
            p.textContent = `[점수 ${occ.score}] ${occ.question}`;
            card.appendChild(p);
            addLabeledText(card, "부족했던 설명", occ.missing_explanations);
            details.appendChild(card);
        }

        container.appendChild(details);
    }
}
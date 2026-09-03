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
    // 탭 버튼과 패널을 보이거나 숨기는, 순수 DOM 조작.
    document.getElementById("panel-interview").style.display = tabName === "interview" ? "block" : "none";
    document.getElementById("panel-quiz").style.display = tabName === "quiz" ? "block" : "none";
    document.getElementById("tab-interview").classList.toggle("active", tabName === "interview");
    document.getElementById("tab-quiz").classList.toggle("active", tabName === "quiz");
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

    // JSON.stringify(값, null, 2): 객체를 보기 좋게 줄바꿈/들여쓰기 넣어서 문자열로 바꿔준다.
    // (진짜 화면 디자인 대신, "기본 폼과 리스트만"이라는 설계문서 방향에 맞춰 결과를 그대로 보여준다.)
    document.getElementById("evaluation-result").textContent = JSON.stringify(evaluation, null, 2);
    showStep("step-evaluation");
}

async function fetchFollowup() {
    const response = await fetch(`/questions/${currentQuestionId}/followup`);
    const data = await response.json();

    if (!data.question_id) {
        // question_id가 없다는 건 8단계가 다 끝났다는 뜻 (followup_generator.py가 None을 반환한 경우).
        // 평가 결과 화면에 안내 메시지만 이어붙이고, 질문 화면으로는 넘어가지 않는다.
        document.getElementById("evaluation-result").textContent += "\n\n" + data.message;
        return;
    }

    currentQuestionId = data.question_id;
    document.getElementById("question-text").textContent = `[깊이 ${data.depth}] ${data.question}`;
    document.getElementById("answer-input").value = "";
    showStep("step-question");
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
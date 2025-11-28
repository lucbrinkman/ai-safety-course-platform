let discordSdk = null;

// Quiz questions - facilitator training
const questions = [
    {
        q: "Your main role as facilitator is to:",
        options: [
            "Lecture on content and provide expert answers",
            "Guide discussion and help group learn from each other",
            "Make sure everyone agrees with your interpretation",
            "Assign grades to participants"
        ],
        correct: 1
    },
    {
        q: "When a participant gives an incorrect answer, you should:",
        options: [
            "Immediately correct them",
            "Ignore it and move on",
            "Ask follow-up questions to help them reconsider",
            "Tell other participants they're wrong"
        ],
        correct: 2
    },
    {
        q: "If the group goes off-topic, the best approach is to:",
        options: [
            "Let them continue indefinitely",
            "Abruptly cut them off",
            "Gently redirect back to the main topic",
            "End the session early"
        ],
        correct: 2
    },
    {
        q: "How should you handle a participant who dominates discussion?",
        options: [
            "Let them continue - they're engaged",
            "Publicly call them out",
            "Invite quieter members to share their thoughts",
            "Remove them from the group"
        ],
        correct: 2
    },
    {
        q: "Before each session, a facilitator should:",
        options: [
            "Memorize all the answers",
            "Review the material and prepare discussion questions",
            "Nothing - just show up",
            "Write a lecture script"
        ],
        correct: 1
    },
    {
        q: "When you don't know the answer to a question, you should:",
        options: [
            "Make something up",
            "Ignore the question",
            "Admit it and explore the question together or follow up later",
            "End the discussion"
        ],
        correct: 2
    },
    {
        q: "The ideal facilitator creates an environment that is:",
        options: [
            "Competitive and challenging",
            "Safe, inclusive, and encourages participation",
            "Formal and lecture-based",
            "Unstructured and spontaneous"
        ],
        correct: 1
    },
    {
        q: "How should you handle disagreements between participants?",
        options: [
            "Pick a side and defend it",
            "Shut down the discussion",
            "Encourage respectful dialogue and explore different perspectives",
            "Ask them to leave"
        ],
        correct: 2
    },
    {
        q: "Active listening as a facilitator means:",
        options: [
            "Waiting for your turn to speak",
            "Taking notes on everything said",
            "Fully engaging, paraphrasing, and asking clarifying questions",
            "Nodding occasionally"
        ],
        correct: 2
    },
    {
        q: "At the end of a session, it's important to:",
        options: [
            "Leave immediately",
            "Summarize key points and preview next session",
            "Assign homework grades",
            "Criticize participation levels"
        ],
        correct: 1
    }
];

const PASSING_SCORE = 0.8; // 80% to pass

let currentQuestion = 0;
let score = 0;
let answered = false;

// DOM elements - grabbed after DOM is ready
let progressEl, questionContainer, questionEl, optionsEl;
let resultContainer, resultEmoji, resultTitle, resultScore, resultMessage;
let restartBtn, statusEl;

function init() {
    // Get DOM elements
    progressEl = document.getElementById("progress");
    questionContainer = document.getElementById("question-container");
    questionEl = document.getElementById("question");
    optionsEl = document.getElementById("options");
    resultContainer = document.getElementById("result-container");
    resultEmoji = document.getElementById("result-emoji");
    resultTitle = document.getElementById("result-title");
    resultScore = document.getElementById("result-score");
    resultMessage = document.getElementById("result-message");
    restartBtn = document.getElementById("restart");
    statusEl = document.getElementById("status");

    // Set up restart button
    restartBtn.addEventListener("click", restart);

    // Check if we're inside Discord's iframe
    const urlParams = new URLSearchParams(window.location.search);
    const isInDiscord = urlParams.has('frame_id');

    if (isInDiscord) {
        import("https://esm.sh/@discord/embedded-app-sdk")
            .then(({ DiscordSDK }) => {
                const CLIENT_ID = "1443580851681230888";
                discordSdk = new DiscordSDK(CLIENT_ID);
                return setupDiscord();
            })
            .catch((error) => {
                console.error("Failed to load Discord SDK:", error);
                statusEl.textContent = "SDK load failed - playing locally";
                showQuestion();
            });
    } else {
        statusEl.textContent = "Local mode (not in Discord)";
        showQuestion();
    }
}

async function setupDiscord() {
    try {
        // Add timeout so we don't hang forever
        const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error("SDK timeout")), 5000)
        );

        await Promise.race([discordSdk.ready(), timeoutPromise]);
        statusEl.textContent = "Connected to Discord!";
        showQuestion();
    } catch (error) {
        console.error("Discord SDK error:", error);
        statusEl.textContent = "Playing locally";
        showQuestion();
    }
}

function showQuestion() {
    answered = false;
    const q = questions[currentQuestion];

    progressEl.textContent = `Question ${currentQuestion + 1}/${questions.length}`;
    questionEl.textContent = q.q;

    optionsEl.innerHTML = "";
    q.options.forEach((option, index) => {
        const btn = document.createElement("button");
        btn.className = "option";
        btn.textContent = `${String.fromCharCode(65 + index)}) ${option}`;
        btn.addEventListener("click", () => selectAnswer(index));
        optionsEl.appendChild(btn);
    });
}

function selectAnswer(index) {
    if (answered) return;
    answered = true;

    const q = questions[currentQuestion];
    const buttons = optionsEl.querySelectorAll(".option");

    // Disable all buttons
    buttons.forEach(btn => btn.disabled = true);

    // Mark correct and incorrect
    buttons.forEach((btn, i) => {
        if (i === q.correct) {
            btn.classList.add("correct");
        } else if (i === index && index !== q.correct) {
            btn.classList.add("incorrect");
        }
    });

    if (index === q.correct) {
        score++;
    }

    // Move to next question after delay
    setTimeout(() => {
        currentQuestion++;
        if (currentQuestion < questions.length) {
            showQuestion();
        } else {
            showResults();
        }
    }, 1500);
}

function showResults() {
    questionContainer.style.display = "none";
    progressEl.style.display = "none";
    resultContainer.style.display = "block";

    const percentage = Math.round((score / questions.length) * 100);
    const passed = score / questions.length >= PASSING_SCORE;

    if (passed) {
        resultContainer.classList.add("passed");
        resultContainer.classList.remove("failed");
        resultEmoji.textContent = "🎉";
        resultTitle.textContent = "Congratulations! You passed!";
        resultMessage.innerHTML = `
            <strong>Next steps:</strong><br>
            • Check #facilitator-lounge for resources<br>
            • You'll be matched to cohorts that need facilitators<br>
            • Access discussion templates and tips<br><br>
            Welcome to the team! 🌟
        `;
        restartBtn.style.display = "none";
    } else {
        resultContainer.classList.add("failed");
        resultContainer.classList.remove("passed");
        resultEmoji.textContent = "😔";
        resultTitle.textContent = "Not quite there yet";
        resultMessage.innerHTML = `
            You need ${Math.round(PASSING_SCORE * 100)}% to pass.<br><br>
            Review the facilitator guidelines and try again!
        `;
        restartBtn.style.display = "inline-block";
    }

    resultScore.textContent = `Score: ${score}/${questions.length} (${percentage}%)`;
}

function restart() {
    currentQuestion = 0;
    score = 0;
    answered = false;

    questionContainer.style.display = "block";
    progressEl.style.display = "block";
    resultContainer.style.display = "none";
    resultContainer.classList.remove("passed", "failed");

    showQuestion();
}

// Start the app
init();

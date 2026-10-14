/**
 * Practice Questions Generator & Mock Examination Runner
 * Supports MCQs, Short-Answer, Long-Answer, plus Full Timed Mock Exams with real countdown.
 */

// ==================== PRACTICE QUESTIONS ====================
let activePracticeData = null;

document.addEventListener("DOMContentLoaded", () => {
  initQuestionGenerator();
  initMockTestGenerator();
});

function initQuestionGenerator() {
  const btn = document.getElementById("generateQuestionsBtn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const notes = (document.getElementById("notesInput")?.value || "").trim();
    if (!notes) {
      showToast("Please enter or upload study notes first.", "warning");
      return;
    }

    const qType = document.getElementById("questionTypeSelect")?.value || "mcq";
    const difficulty = document.getElementById("questionDifficultySelect")?.value || "medium";
    const numQuestions = parseInt(document.getElementById("questionCountSelect")?.value || "5", 10);
    const subject = document.getElementById("subjectInput")?.value || "General Studies";

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Generating ${numQuestions} ${qType.toUpperCase()} questions...`;

    try {
      const res = await fetch("/api/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          notes,
          num_questions: numQuestions,
          difficulty,
          q_type: qType,
          subject
        })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        showToast(data.error || "Failed to generate questions.", "danger");
        return;
      }

      activePracticeData = data.data;
      renderPracticeQuestions(data.data, qType);

      const demoBanner = document.getElementById("practiceDemoBanner");
      if (demoBanner) demoBanner.style.display = data.is_demo ? "flex" : "none";

      const container = document.getElementById("practiceQuestionsContainer");
      if (container) {
        container.style.display = "block";
        container.scrollIntoView({ behavior: "smooth" });
      }

      showToast(`Generated ${numQuestions} practice questions!`, "success");

    } catch (err) {
      showToast("Network error generating questions.", "danger");
    } finally {
      btn.disabled = false;
      btn.innerHTML = "📝 Generate Practice Questions";
    }
  });
}

function renderPracticeQuestions(data, qType) {
  const container = document.getElementById("practiceQuestionsList");
  if (!container) return;

  container.innerHTML = "";
  const questions = data.questions || [];

  if (questions.length === 0) {
    container.innerHTML = "<p>No questions generated.</p>";
    return;
  }

  questions.forEach((q, idx) => {
    const card = document.createElement("div");
    card.className = "card";
    card.style.marginBottom = "1.25rem";

    if (qType === "mcq") {
      card.innerHTML = `
        <div style="font-weight: 700; margin-bottom: 0.75rem; font-size: 1.05rem;">
          <span style="color: var(--primary);">Q${idx + 1}.</span> ${escapeHtml(q.question)}
        </div>
        <div class="options-list" id="practice-mcq-options-${idx}">
          ${q.options.map((opt, optIdx) => `
            <div class="option-item" onclick="checkPracticeMcq(${idx}, ${optIdx}, ${q.correct_answer})">
              <span class="option-letter">${String.fromCharCode(65 + optIdx)}</span>
              <span>${escapeHtml(opt)}</span>
            </div>
          `).join("")}
        </div>
        <div id="practice-mcq-feedback-${idx}" style="display: none; margin-top: 0.75rem; padding: 0.75rem 1rem; border-radius: var(--radius-sm); font-size: 0.9rem;">
          <div style="font-weight: 700; margin-bottom: 0.25rem;" id="practice-mcq-status-${idx}"></div>
          <div style="color: var(--text-secondary);">${escapeHtml(q.explanation)}</div>
        </div>
      `;
    } else if (qType === "short") {
      card.innerHTML = `
        <div style="font-weight: 700; margin-bottom: 0.75rem; font-size: 1.05rem;">
          <span style="color: var(--primary);">Q${idx + 1}.</span> ${escapeHtml(q.question)}
        </div>
        <div style="margin-bottom: 0.75rem;">
          <button class="btn btn-secondary btn-sm" onclick="toggleAnswerVisibility('short-ans-${idx}', this)">
            👁️ Reveal Model Answer
          </button>
        </div>
        <div id="short-ans-${idx}" style="display: none; background: var(--bg-tertiary); padding: 1rem; border-radius: var(--radius-sm); border-left: 3px solid var(--primary);">
          <div style="font-weight: 600; margin-bottom: 0.35rem; color: var(--primary);">Model Answer:</div>
          <p style="margin-bottom: 0.5rem;">${escapeHtml(q.model_answer)}</p>
          ${q.key_points && q.key_points.length ? `
            <div style="font-size: 0.85rem; font-weight: 600; margin-top: 0.5rem;">Key Points:</div>
            <ul style="margin-left: 1.25rem; font-size: 0.85rem;">
              ${q.key_points.map(kp => `<li>${escapeHtml(kp)}</li>`).join("")}
            </ul>
          ` : ""}
          ${q.important_keywords && q.important_keywords.length ? `
            <div style="margin-top: 0.5rem; font-size: 0.85rem;">
              <strong>Keywords:</strong>
              ${q.important_keywords.map(kw => `<span style="background: var(--primary-light); color: var(--primary); padding: 0.15rem 0.45rem; border-radius: 4px; margin-left: 0.25rem; font-weight: 600;">${escapeHtml(kw)}</span>`).join("")}
            </div>
          ` : ""}
        </div>
      `;
    } else { // long answer
      card.innerHTML = `
        <div style="font-weight: 700; margin-bottom: 0.75rem; font-size: 1.05rem;">
          <span style="color: var(--primary);">Q${idx + 1}.</span> ${escapeHtml(q.question)}
        </div>
        <div style="margin-bottom: 0.75rem;">
          <button class="btn btn-secondary btn-sm" onclick="toggleAnswerVisibility('long-ans-${idx}', this)">
            📋 Reveal Outline & Rubric
          </button>
        </div>
        <div id="long-ans-${idx}" style="display: none; background: var(--bg-tertiary); padding: 1rem; border-radius: var(--radius-sm); border-left: 3px solid var(--secondary);">
          <div style="font-weight: 600; margin-bottom: 0.35rem; color: var(--secondary);">Structured Answer Outline:</div>
          <ul style="margin-left: 1.25rem; margin-bottom: 0.75rem;">
            ${(q.answer_outline || []).map(line => `<li>${escapeHtml(line)}</li>`).join("")}
          </ul>
          ${q.main_concepts ? `
            <div style="font-size: 0.85rem; margin-bottom: 0.5rem;">
              <strong>Key Concepts to Cover:</strong> ${q.main_concepts.join(", ")}
            </div>
          ` : ""}
          ${q.evaluation_rubric ? `
            <div style="font-size: 0.85rem; padding: 0.5rem; background: var(--bg-secondary); border-radius: 4px;">
              <strong>Examiner Rubric:</strong> ${escapeHtml(q.evaluation_rubric)}
            </div>
          ` : ""}
        </div>
      `;
    }

    container.appendChild(card);
  });
}

function checkPracticeMcq(qIdx, selectedOptIdx, correctOptIdx) {
  const optionsContainer = document.getElementById(`practice-mcq-options-${qIdx}`);
  if (!optionsContainer) return;

  const optionElements = optionsContainer.querySelectorAll(".option-item");
  optionElements.forEach((el, i) => {
    el.onclick = null; // freeze further clicks
    if (i === correctOptIdx) {
      el.classList.add("correct");
    } else if (i === selectedOptIdx) {
      el.classList.add("incorrect");
    }
  });

  const feedback = document.getElementById(`practice-mcq-feedback-${qIdx}`);
  const statusEl = document.getElementById(`practice-mcq-status-${qIdx}`);
  if (feedback && statusEl) {
    feedback.style.display = "block";
    if (selectedOptIdx === correctOptIdx) {
      feedback.style.background = "var(--success-light)";
      statusEl.style.color = "var(--success)";
      statusEl.textContent = "🎉 Correct Answer!";
    } else {
      feedback.style.background = "var(--danger-light)";
      statusEl.style.color = "var(--danger)";
      statusEl.textContent = `❌ Incorrect (Correct was option ${String.fromCharCode(65 + correctOptIdx)})`;
    }
  }
}

function toggleAnswerVisibility(elemId, btn) {
  const el = document.getElementById(elemId);
  if (!el) return;
  if (el.style.display === "none") {
    el.style.display = "block";
    btn.textContent = "🙈 Hide Answer";
  } else {
    el.style.display = "none";
    btn.textContent = "👁️ Reveal Answer";
  }
}

async function savePracticeQuestionsToLibrary() {
  if (!activePracticeData) return;

  const title = (document.getElementById("topicInput")?.value || "Practice Questions").trim();
  const subject = (document.getElementById("subjectInput")?.value || "General").trim();
  const qType = document.getElementById("questionTypeSelect")?.value || "mcq";

  try {
    const res = await fetch("/api/materials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: `${title} (${qType.toUpperCase()} Set)`,
        subject: subject,
        material_type: "questions",
        content: activePracticeData,
        source_snippet: `${activePracticeData.questions?.length || 0} questions on ${subject}.`
      })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast("Practice questions saved to your Library! 📚", "success");
    } else {
      showToast(data.error || "Failed to save questions.", "danger");
    }
  } catch (err) {
    showToast("Failed to save questions to database.", "danger");
  }
}

// ==================== MOCK EXAM RUNNER ====================
let mockExamData = null;
let currentExamIndex = 0;
let userExamAnswers = {}; // { qIndex: selectedOptionIndex }
let examTimerInterval = null;
let examSecondsRemaining = 0;
let examTotalSeconds = 0;

function initMockTestGenerator() {
  const btn = document.getElementById("startMockTestBtn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const notes = (document.getElementById("notesInput")?.value || "").trim();
    if (!notes) {
      showToast("Please enter or upload study notes first.", "warning");
      return;
    }

    const numQuestions = parseInt(document.getElementById("mockQuestionCountSelect")?.value || "10", 10);
    const difficulty = document.getElementById("mockDifficultySelect")?.value || "medium";
    const minutes = parseInt(document.getElementById("mockTimerMinutesSelect")?.value || "10", 10);
    const subject = document.getElementById("subjectInput")?.value || "General Examination";

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Assembling ${numQuestions}-Question Mock Exam...`;

    try {
      const res = await fetch("/api/mock-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          notes,
          num_questions: numQuestions,
          difficulty,
          subject
        })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        showToast(data.error || "Failed to generate mock test.", "danger");
        return;
      }

      mockExamData = data.test_data;
      startMockExamSession(minutes);

      const demoBanner = document.getElementById("mockTestDemoBanner");
      if (demoBanner) demoBanner.style.display = data.is_demo ? "flex" : "none";

      const container = document.getElementById("mockExamActiveContainer");
      if (container) {
        container.style.display = "block";
        container.scrollIntoView({ behavior: "smooth" });
      }

      showToast(`Mock Exam started! You have ${minutes} minutes.`, "info");

    } catch (err) {
      showToast("Network error starting mock exam.", "danger");
    } finally {
      btn.disabled = false;
      btn.innerHTML = "🎯 Launch Mock Exam";
    }
  });
}

function startMockExamSession(durationMinutes) {
  currentExamIndex = 0;
  userExamAnswers = {};
  examTotalSeconds = durationMinutes * 60;
  examSecondsRemaining = examTotalSeconds;

  // Clear any existing timer
  if (examTimerInterval) clearInterval(examTimerInterval);

  updateExamTimerDisplay();
  examTimerInterval = setInterval(() => {
    examSecondsRemaining--;
    updateExamTimerDisplay();

    if (examSecondsRemaining <= 0) {
      clearInterval(examTimerInterval);
      showToast("Time's up! Automatically submitting your mock test...", "warning");
      submitMockExam();
    }
  }, 1000);

  // Render first question
  document.getElementById("mockExamResultCard").style.display = "none";
  document.getElementById("mockExamActiveCard").style.display = "block";
  renderMockQuestion(0);
}

function updateExamTimerDisplay() {
  const timerEl = document.getElementById("examTimerDisplay");
  if (!timerEl) return;

  const mins = Math.floor(examSecondsRemaining / 60);
  const secs = examSecondsRemaining % 60;
  timerEl.textContent = `⏱️ ${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;

  if (examSecondsRemaining < 120) {
    timerEl.style.color = "var(--danger)";
    timerEl.style.animation = "pulse 1s infinite";
  } else {
    timerEl.style.color = "inherit";
    timerEl.style.animation = "none";
  }
}

function renderMockQuestion(idx) {
  if (!mockExamData || !mockExamData.questions) return;
  const questions = mockExamData.questions;
  const q = questions[idx];

  const qNumberEl = document.getElementById("mockExamQuestionNumber");
  const qTextEl = document.getElementById("mockExamQuestionText");
  const optionsContainer = document.getElementById("mockExamOptionsList");
  const prevBtn = document.getElementById("mockExamPrevBtn");
  const nextBtn = document.getElementById("mockExamNextBtn");
  const submitBtn = document.getElementById("mockExamSubmitBtn");

  if (qNumberEl) qNumberEl.textContent = `Question ${idx + 1} of ${questions.length}`;
  if (qTextEl) qTextEl.textContent = q.question;

  if (optionsContainer) {
    optionsContainer.innerHTML = q.options.map((opt, optIdx) => {
      const isSelected = userExamAnswers[idx] === optIdx;
      return `
        <div class="option-item ${isSelected ? "selected" : ""}" onclick="selectMockAnswer(${idx}, ${optIdx})">
          <span class="option-letter">${String.fromCharCode(65 + optIdx)}</span>
          <span>${escapeHtml(opt)}</span>
        </div>
      `;
    }).join("");
  }

  // Navigation buttons
  if (prevBtn) prevBtn.disabled = idx === 0;
  if (idx === questions.length - 1) {
    if (nextBtn) nextBtn.style.display = "none";
    if (submitBtn) submitBtn.style.display = "inline-flex";
  } else {
    if (nextBtn) nextBtn.style.display = "inline-flex";
    if (submitBtn) submitBtn.style.display = "none";
  }

  renderQuestionTrackerDots();
}

function selectMockAnswer(qIdx, optIdx) {
  userExamAnswers[qIdx] = optIdx;
  renderMockQuestion(qIdx);
}

function mockExamNext() {
  if (currentExamIndex < mockExamData.questions.length - 1) {
    currentExamIndex++;
    renderMockQuestion(currentExamIndex);
  }
}

function mockExamPrev() {
  if (currentExamIndex > 0) {
    currentExamIndex--;
    renderMockQuestion(currentExamIndex);
  }
}

function renderQuestionTrackerDots() {
  const trackerEl = document.getElementById("mockExamTracker");
  if (!trackerEl || !mockExamData) return;

  trackerEl.innerHTML = mockExamData.questions.map((_, idx) => {
    const isAnswered = userExamAnswers[idx] !== undefined;
    const isCurrent = idx === currentExamIndex;

    let bg = "var(--border-color)";
    let border = "transparent";

    if (isAnswered) bg = "var(--primary)";
    if (isCurrent) border = "2px solid var(--secondary)";

    return `
      <div onclick="jumpToMockQuestion(${idx})" style="
        width: 24px; height: 24px; border-radius: 50%;
        background-color: ${bg}; border: ${border};
        color: ${isAnswered ? "#fff" : "var(--text-secondary)"};
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 0.75rem; font-weight: 700; cursor: pointer; margin: 0 3px;
      ">${idx + 1}</div>
    `;
  }).join("");
}

function jumpToMockQuestion(idx) {
  currentExamIndex = idx;
  renderMockQuestion(idx);
}

async function submitMockExam() {
  if (examTimerInterval) clearInterval(examTimerInterval);

  const questions = mockExamData.questions || [];
  let score = 0;
  const details = [];

  questions.forEach((q, idx) => {
    const userAnswer = userExamAnswers[idx];
    const isCorrect = userAnswer === q.correct_answer;
    if (isCorrect) score++;

    details.push({
      question: q.question,
      options: q.options,
      user_answer: userAnswer !== undefined ? userAnswer : null,
      correct_answer: q.correct_answer,
      is_correct: isCorrect,
      explanation: q.explanation,
      topic: q.topic || "General"
    });
  });

  const percentage = Math.round((score / questions.length) * 100);
  const timeSpent = examTotalSeconds - examSecondsRemaining;

  // Display Scoreboard
  document.getElementById("mockExamActiveCard").style.display = "none";
  const resultCard = document.getElementById("mockExamResultCard");
  resultCard.style.display = "block";

  const scoreEl = document.getElementById("mockFinalScore");
  const percentEl = document.getElementById("mockFinalPercentage");
  const timeEl = document.getElementById("mockFinalTime");
  const reviewContainer = document.getElementById("mockExamReviewBreakdown");

  if (scoreEl) scoreEl.textContent = `${score} / ${questions.length}`;
  if (percentEl) percentEl.textContent = `${percentage}%`;
  if (timeEl) timeEl.textContent = `${Math.floor(timeSpent / 60)}m ${timeSpent % 60}s`;

  // Render comprehensive review breakdown
  if (reviewContainer) {
    reviewContainer.innerHTML = details.map((item, idx) => `
      <div style="padding: 1rem; border-radius: var(--radius-sm); margin-bottom: 1rem; border: 1px solid var(--border-color); background: var(--bg-secondary);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <div style="font-weight: 700;">
            <span style="color: var(--primary);">Q${idx + 1}.</span> ${escapeHtml(item.question)}
          </div>
          <span style="font-size: 0.8rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 4px; ${item.is_correct ? "background: var(--success-light); color: var(--success);" : "background: var(--danger-light); color: var(--danger);"}">
            ${item.is_correct ? "✅ Correct (+1)" : "❌ Incorrect (0)"}
          </span>
        </div>
        <div style="font-size: 0.9rem; margin-bottom: 0.5rem;">
          <div>Your Answer: <strong>${item.user_answer !== null ? String.fromCharCode(65 + item.user_answer) + ". " + escapeHtml(item.options[item.user_answer]) : "Unanswered"}</strong></div>
          <div style="color: var(--success);">Correct Answer: <strong>${String.fromCharCode(65 + item.correct_answer)}. ${escapeHtml(item.options[item.correct_answer])}</strong></div>
        </div>
        <div style="font-size: 0.85rem; color: var(--text-secondary); background: var(--bg-tertiary); padding: 0.5rem 0.75rem; border-radius: 4px;">
          💡 <strong>Explanation:</strong> ${escapeHtml(item.explanation)}
        </div>
      </div>
    `).join("");
  }

  showToast(`Exam complete! You scored ${percentage}%.`, "success");
  resultCard.scrollIntoView({ behavior: "smooth" });

  // Save to SQLite
  const subject = document.getElementById("subjectInput")?.value || "General";
  const title = (document.getElementById("topicInput")?.value || "Mock Exam").trim();

  try {
    await fetch("/api/quiz-results", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        subject: subject,
        score: score,
        total_questions: questions.length,
        time_spent_seconds: timeSpent,
        details: details
      })
    });
  } catch (err) {
    console.error("Failed to auto-record quiz result:", err);
  }
}

function retryMockExam() {
  if (confirm("Do you want to retry this mock examination?")) {
    const minutes = parseInt(document.getElementById("mockTimerMinutesSelect")?.value || "10", 10);
    startMockExamSession(minutes);
  }
}

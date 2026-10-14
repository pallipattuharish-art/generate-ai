/**
 * Study Assistant Workspace - File Upload, Notes Editor, Summarizer & Concept Explainer
 */

document.addEventListener("DOMContentLoaded", () => {
  initFileUpload();
  initTextCounter();
  initSummarizer();
  initConceptExplainer();
});

// Current active notes state
let currentNotes = "";
let currentSubject = "";
let currentTopic = "";

function updateWordAndCharCount(text) {
  const charCount = text.length;
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;

  const charEl = document.getElementById("charCount");
  const wordEl = document.getElementById("wordCount");
  if (charEl) charEl.textContent = `${charCount.toLocaleString()} chars`;
  if (wordEl) wordEl.textContent = `${wordCount.toLocaleString()} words`;
}

function initTextCounter() {
  const notesTextarea = document.getElementById("notesInput");
  if (notesTextarea) {
    notesTextarea.addEventListener("input", (e) => {
      currentNotes = e.target.value;
      updateWordAndCharCount(currentNotes);
    });
  }

  const subjectInput = document.getElementById("subjectInput");
  if (subjectInput) {
    subjectInput.addEventListener("input", (e) => currentSubject = e.target.value);
  }

  const topicInput = document.getElementById("topicInput");
  if (topicInput) {
    topicInput.addEventListener("input", (e) => currentTopic = e.target.value);
  }
}

// File Upload Handler
function initFileUpload() {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");

  if (!dropZone || !fileInput) return;

  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileUpload(e.target.files[0]);
    }
  });
}

async function handleFileUpload(file) {
  const uploadStatus = document.getElementById("uploadStatus");
  const notesTextarea = document.getElementById("notesInput");

  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  if (uploadStatus) {
    uploadStatus.innerHTML = `<span class="spinner spinner-primary"></span> Extracting readable text from <strong>${escapeHtml(file.name)}</strong>...`;
    uploadStatus.style.display = "block";
  }

  try {
    const res = await fetch("/api/upload", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      if (data.is_scanned) {
        showToast(data.error, "warning");
      } else {
        showToast(data.error || "Failed to process document.", "danger");
      }
      if (uploadStatus) uploadStatus.innerHTML = `<span style="color:var(--danger)">⚠️ ${escapeHtml(data.error)}</span>`;
      return;
    }

    // Success: Populate text area
    notesTextarea.value = data.text;
    currentNotes = data.text;
    updateWordAndCharCount(data.text);

    // Auto set topic or subject if empty
    const subjectInput = document.getElementById("subjectInput");
    if (subjectInput && !subjectInput.value) {
      const baseName = file.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
      subjectInput.value = baseName;
      currentSubject = baseName;
    }

    if (uploadStatus) {
      uploadStatus.innerHTML = `<span style="color:var(--success)">✅ Successfully extracted ${data.word_count.toLocaleString()} words (${data.character_count.toLocaleString()} chars) from <strong>${escapeHtml(data.filename)}</strong>.</span>`;
    }
    showToast(`Loaded text from ${data.filename}! You can now edit it or generate study materials.`, "success");

  } catch (err) {
    showToast("Network error uploading file. Please try again.", "danger");
    if (uploadStatus) uploadStatus.innerHTML = `<span style="color:var(--danger)">⚠️ Network upload error: ${escapeHtml(err.message)}</span>`;
  }
}

// Clear Notes
function clearNotes() {
  if (confirm("Are you sure you want to clear the notes editor?")) {
    const notesInput = document.getElementById("notesInput");
    if (notesInput) notesInput.value = "";
    currentNotes = "";
    updateWordAndCharCount("");
    const uploadStatus = document.getElementById("uploadStatus");
    if (uploadStatus) uploadStatus.style.display = "none";
    showToast("Notes cleared.", "info");
  }
}

// Load Sample Notes (CSE beginner-friendly)
function loadSampleNotes() {
  const sample = `TOPIC: Fundamental Data Structures & Algorithm Complexity

An algorithm is a well-defined sequence of computational steps that transforms an input into a desired output. Analyzing algorithm performance requires understanding time complexity and space complexity, typically represented using Asymptotic Big-O notation.

1. Linear Data Structures:
- Arrays: Contiguous memory blocks offering O(1) random index access, but O(n) worst-case insertion and deletion when elements must shift.
- Linked Lists: Dynamic chains of nodes with data and pointer references. Insertion and deletion at known positions is O(1), but searching requires sequential traversal O(n).
- Stacks: LIFO (Last In, First Out) structure with push, pop, and peek operations executing in O(1) constant time. Used in call stacks and undo operations.
- Queues: FIFO (First In, First Out) structure with enqueue and dequeue operations executing in O(1) time. Used in CPU job scheduling and asynchronous message buffers.

2. Important Algorithmic Principles:
- Binary Search: Halves the search space on sorted sequences with time complexity O(log n).
- Time Complexity Rule: T(n) = c * f(n).
- Best practice: Always check boundary values (empty arrays, single elements, null pointers) to avoid runtime segmentation faults or exceptions.`;

  const notesInput = document.getElementById("notesInput");
  const subjectInput = document.getElementById("subjectInput");
  const topicInput = document.getElementById("topicInput");

  if (notesInput) notesInput.value = sample;
  if (subjectInput) subjectInput.value = "Computer Science (CSE)";
  if (topicInput) topicInput.value = "Data Structures & Big-O";

  currentNotes = sample;
  currentSubject = "Computer Science (CSE)";
  currentTopic = "Data Structures & Big-O";
  updateWordAndCharCount(sample);
  showToast("Loaded sample study notes!", "success");
}

// ==================== Feature 2: Summarizer ====================
let lastGeneratedSummary = "";

function initSummarizer() {
  const btn = document.getElementById("generateSummaryBtn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const notes = (document.getElementById("notesInput")?.value || "").trim();
    if (!notes) {
      showToast("Please enter or upload study notes first.", "warning");
      return;
    }

    const lengthMode = document.getElementById("summaryLengthSelect")?.value || "medium";
    const subject = document.getElementById("subjectInput")?.value || "General Studies";
    const topic = document.getElementById("topicInput")?.value || "";

    const outputBox = document.getElementById("summaryOutput");
    const container = document.getElementById("summaryResultContainer");
    const demoBanner = document.getElementById("summaryDemoBanner");

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Generating ${lengthMode} summary...`;

    try {
      const res = await fetch("/api/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          notes: notes,
          length: lengthMode,
          subject: subject,
          topic: topic
        })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        showToast(data.error || "Failed to generate summary.", "danger");
        return;
      }

      lastGeneratedSummary = data.summary;
      if (outputBox) outputBox.innerHTML = renderMarkdown(data.summary);
      if (container) container.style.display = "block";

      if (demoBanner) {
        demoBanner.style.display = data.is_demo ? "flex" : "none";
      }

      showToast("Summary generated successfully!", "success");
      container.scrollIntoView({ behavior: "smooth" });

    } catch (err) {
      showToast("Network error generating summary.", "danger");
    } finally {
      btn.disabled = false;
      btn.innerHTML = "✨ Generate Summary";
    }
  });
}

function copySummary() {
  if (lastGeneratedSummary) {
    copyToClipboard(lastGeneratedSummary, "Summary copied to clipboard!");
  }
}

function downloadSummary() {
  if (lastGeneratedSummary) {
    const filename = `Summary_${(currentTopic || "Notes").replace(/\s+/g, "_")}.txt`;
    downloadTextFile(filename, lastGeneratedSummary);
  }
}

async function saveSummaryToLibrary() {
  if (!lastGeneratedSummary) return;

  const title = (document.getElementById("topicInput")?.value || "Study Summary").trim();
  const subject = (document.getElementById("subjectInput")?.value || "General").trim();

  try {
    const res = await fetch("/api/materials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title + " (Summary)",
        subject: subject,
        material_type: "summary",
        content: lastGeneratedSummary,
        source_snippet: currentNotes.slice(0, 200)
      })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast("Summary saved to your Library! 📚", "success");
    } else {
      showToast(data.error || "Failed to save summary.", "danger");
    }
  } catch (err) {
    showToast("Failed to save summary to database.", "danger");
  }
}

// ==================== Feature 3: Concept Explainer ====================
let lastGeneratedExplanation = "";

function initConceptExplainer() {
  const btn = document.getElementById("explainConceptBtn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const concept = (document.getElementById("conceptInput")?.value || "").trim();
    if (!concept) {
      showToast("Please enter a concept or select text from your notes to explain.", "warning");
      return;
    }

    const level = document.getElementById("explainLevelSelect")?.value || "beginner";
    const language = document.getElementById("explainLanguageSelect")?.value || "english";
    const notes = (document.getElementById("notesInput")?.value || "").trim();

    const outputBox = document.getElementById("explanationOutput");
    const container = document.getElementById("explanationResultContainer");
    const demoBanner = document.getElementById("explanationDemoBanner");

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Explaining in ${language === "telugu" ? "Telugu" : "English"} (${level})...`;

    try {
      const res = await fetch("/api/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          concept: concept,
          level: level,
          language: language,
          notes: notes
        })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        showToast(data.error || "Failed to explain concept.", "danger");
        return;
      }

      lastGeneratedExplanation = data.explanation;
      if (outputBox) outputBox.innerHTML = renderMarkdown(data.explanation);
      if (container) container.style.display = "block";

      if (demoBanner) {
        demoBanner.style.display = data.is_demo ? "flex" : "none";
      }

      showToast(`Explained ${concept} successfully!`, "success");
      container.scrollIntoView({ behavior: "smooth" });

    } catch (err) {
      showToast("Network error generating concept explanation.", "danger");
    } finally {
      btn.disabled = false;
      btn.innerHTML = "💡 Explain Concept";
    }
  });
}

function copyExplanation() {
  if (lastGeneratedExplanation) {
    copyToClipboard(lastGeneratedExplanation, "Explanation copied to clipboard!");
  }
}

function downloadExplanation() {
  if (lastGeneratedExplanation) {
    const concept = (document.getElementById("conceptInput")?.value || "Concept").replace(/\s+/g, "_");
    downloadTextFile(`Explanation_${concept}.txt`, lastGeneratedExplanation);
  }
}

async function saveExplanationToLibrary() {
  if (!lastGeneratedExplanation) return;

  const concept = (document.getElementById("conceptInput")?.value || "Concept Explanation").trim();
  const subject = (document.getElementById("subjectInput")?.value || "General").trim();
  const lang = document.getElementById("explainLanguageSelect")?.value || "english";

  try {
    const res = await fetch("/api/materials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: `${concept} (${lang.toUpperCase()})`,
        subject: subject,
        material_type: "explanation",
        content: lastGeneratedExplanation,
        source_snippet: currentNotes.slice(0, 200)
      })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast("Explanation saved to your Library! 📚", "success");
    } else {
      showToast(data.error || "Failed to save explanation.", "danger");
    }
  } catch (err) {
    showToast("Failed to save explanation to database.", "danger");
  }
}

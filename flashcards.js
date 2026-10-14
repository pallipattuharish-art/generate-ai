/**
 * Interactive Flashcard Deck Manager
 * Supports 3D Flip animations, Previous/Next, Shuffle, Mark as Known/Review Again, and Saving.
 */

let activeFlashcards = [];
let currentCardIndex = 0;
let knownCardIds = new Set();
let reviewCardIds = new Set();

document.addEventListener("DOMContentLoaded", () => {
  initFlashcardGenerator();
  initFlashcardKeyboardControls();
});

function initFlashcardGenerator() {
  const btn = document.getElementById("generateFlashcardsBtn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const notes = (document.getElementById("notesInput")?.value || "").trim();
    if (!notes) {
      showToast("Please enter or upload study notes first.", "warning");
      return;
    }

    const count = parseInt(document.getElementById("flashcardCountSelect")?.value || "10", 10);
    const subject = document.getElementById("subjectInput")?.value || "General Studies";

    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Generating ${count} flashcards...`;

    try {
      const res = await fetch("/api/flashcards", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes, count, subject })
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        showToast(data.error || "Failed to generate flashcards.", "danger");
        return;
      }

      activeFlashcards = data.flashcards || [];
      if (activeFlashcards.length === 0) {
        showToast("No flashcards were generated. Try adding more detailed notes.", "warning");
        return;
      }

      currentCardIndex = 0;
      knownCardIds.clear();
      reviewCardIds.clear();

      renderCurrentFlashcard();
      document.getElementById("flashcardContainer").style.display = "block";

      const demoBanner = document.getElementById("flashcardsDemoBanner");
      if (demoBanner) demoBanner.style.display = data.is_demo ? "flex" : "none";

      showToast(`Generated ${activeFlashcards.length} revision flashcards!`, "success");
      document.getElementById("flashcardContainer").scrollIntoView({ behavior: "smooth" });

    } catch (err) {
      showToast("Network error generating flashcards.", "danger");
    } finally {
      btn.disabled = false;
      btn.innerHTML = "🎴 Generate Flashcards";
    }
  });
}

function renderCurrentFlashcard() {
  if (!activeFlashcards || activeFlashcards.length === 0) return;

  const card = activeFlashcards[currentCardIndex];
  const innerCard = document.getElementById("flashcardInner");
  const cardFront = document.getElementById("cardFrontText");
  const cardBack = document.getElementById("cardBackText");
  const categoryTag = document.getElementById("cardCategoryTag");
  const progressText = document.getElementById("cardProgressText");
  const progressBar = document.getElementById("cardProgressBar");
  const prevBtn = document.getElementById("prevCardBtn");
  const nextBtn = document.getElementById("nextCardBtn");

  // Ensure card is flipped back to front upon changing
  if (innerCard) {
    innerCard.classList.remove("is-flipped");
  }

  if (cardFront) cardFront.textContent = card.front;
  if (cardBack) cardBack.textContent = card.back;
  if (categoryTag) categoryTag.textContent = card.category || "Concept";

  // Update Progress
  const total = activeFlashcards.length;
  if (progressText) progressText.textContent = `Card ${currentCardIndex + 1} of ${total}`;
  if (progressBar) progressBar.style.width = `${((currentCardIndex + 1) / total) * 100}%`;

  if (prevBtn) prevBtn.disabled = currentCardIndex === 0;
  if (nextBtn) nextBtn.disabled = currentCardIndex === total - 1;

  updateKnownCounts();
}

function flipCard() {
  const innerCard = document.getElementById("flashcardInner");
  if (innerCard) {
    innerCard.classList.toggle("is-flipped");
  }
}

function nextCard() {
  if (currentCardIndex < activeFlashcards.length - 1) {
    currentCardIndex++;
    renderCurrentFlashcard();
  }
}

function prevCard() {
  if (currentCardIndex > 0) {
    currentCardIndex--;
    renderCurrentFlashcard();
  }
}

function shuffleCards() {
  if (!activeFlashcards || activeFlashcards.length <= 1) return;

  for (let i = activeFlashcards.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [activeFlashcards[i], activeFlashcards[j]] = [activeFlashcards[j], activeFlashcards[i]];
  }

  currentCardIndex = 0;
  renderCurrentFlashcard();
  showToast("Flashcards shuffled!", "info");
}

function markCardKnown() {
  if (!activeFlashcards.length) return;
  const cardId = activeFlashcards[currentCardIndex].id || currentCardIndex;
  knownCardIds.add(cardId);
  reviewCardIds.delete(cardId);
  updateKnownCounts();

  // Automatically advance to next card if available
  if (currentCardIndex < activeFlashcards.length - 1) {
    setTimeout(nextCard, 200);
  } else {
    showToast("Great job! You reached the end of the deck.", "success");
  }
}

function markCardReview() {
  if (!activeFlashcards.length) return;
  const cardId = activeFlashcards[currentCardIndex].id || currentCardIndex;
  reviewCardIds.add(cardId);
  knownCardIds.delete(cardId);
  updateKnownCounts();

  if (currentCardIndex < activeFlashcards.length - 1) {
    setTimeout(nextCard, 200);
  }
}

function updateKnownCounts() {
  const knownEl = document.getElementById("knownCount");
  const reviewEl = document.getElementById("reviewCount");
  if (knownEl) knownEl.textContent = `${knownCardIds.size} Known`;
  if (reviewEl) reviewEl.textContent = `${reviewCardIds.size} Review Again`;
}

function initFlashcardKeyboardControls() {
  document.addEventListener("keydown", (e) => {
    // Only process if flashcard container is visible and active
    const container = document.getElementById("flashcardContainer");
    if (!container || container.style.display === "none") return;

    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

    if (e.code === "Space") {
      e.preventDefault();
      flipCard();
    } else if (e.code === "ArrowRight") {
      nextCard();
    } else if (e.code === "ArrowLeft") {
      prevCard();
    }
  });
}

async function saveFlashcardsToLibrary() {
  if (!activeFlashcards || activeFlashcards.length === 0) return;

  const title = (document.getElementById("topicInput")?.value || "Flashcard Deck").trim();
  const subject = (document.getElementById("subjectInput")?.value || "General").trim();

  try {
    const res = await fetch("/api/materials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title + ` (${activeFlashcards.length} Cards)`,
        subject: subject,
        material_type: "flashcards",
        content: activeFlashcards,
        source_snippet: `${activeFlashcards.length} flashcards generated from study notes.`
      })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showToast("Flashcard deck saved to your Library! 🎴", "success");
    } else {
      showToast(data.error || "Failed to save flashcards.", "danger");
    }
  } catch (err) {
    showToast("Failed to save flashcards to database.", "danger");
  }
}

/**
 * Global Application Utilities & Theme Controller
 */

// Theme Controller (Light/Dark)
(function initTheme() {
  const savedTheme = localStorage.getItem("study_theme") || "light";
  document.documentElement.setAttribute("data-theme", savedTheme);
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("study_theme", next);

  const icon = document.getElementById("themeIcon");
  if (icon) {
    icon.textContent = next === "dark" ? "☀️" : "🌙";
  }
}

// Toast Notifications
function showToast(message, type = "info") {
  let container = document.getElementById("toastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "toastContainer";
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  const iconMap = {
    success: "✅",
    danger: "❌",
    warning: "⚠️",
    info: "ℹ️"
  };

  toast.innerHTML = `<span>${iconMap[type] || "ℹ️"}</span><span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Simple & Safe Markdown to HTML formatter
function renderMarkdown(mdText) {
  if (!mdText) return "";

  let html = escapeHtml(mdText);

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3 class="rendered-h3">$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2 class="rendered-h2">$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1 class="rendered-h1">$1</h1>');

  // Bold & Italics
  html = html.replace(/\*\*\*(.*?)\*\*\*/gim, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');

  // Bullet points
  html = html.replace(/^\- (.*$)/gim, '<li class="rendered-li">$1</li>');
  html = html.replace(/(<li.*<\/li>)/gms, '<ul class="rendered-ul">$1</ul>');

  // Numbered lists
  html = html.replace(/^\d+\.\s+(.*$)/gim, '<li class="rendered-oli">$1</li>');

  // Line breaks to paragraphs
  html = html.split(/\n\n+/).map(para => {
    if (para.startsWith('<h') || para.startsWith('<ul') || para.startsWith('<li')) {
      return para;
    }
    return `<p>${para.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  return html;
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// Copy to Clipboard
async function copyToClipboard(text, successMessage = "Copied to clipboard!") {
  try {
    await navigator.clipboard.writeText(text);
    showToast(successMessage, "success");
  } catch (err) {
    showToast("Failed to copy text. Please select and copy manually.", "warning");
  }
}

// Download text file
function downloadTextFile(filename, text) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "study-notes.txt";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast("Downloaded file successfully!", "success");
}

// Mobile Menu Toggle
function toggleMobileMenu() {
  const links = document.getElementById("navLinks");
  if (links) {
    links.style.display = links.style.display === "flex" ? "none" : "flex";
    links.style.flexDirection = "column";
    links.style.position = "absolute";
    links.style.top = "70px";
    links.style.left = "0";
    links.style.width = "100%";
    links.style.backgroundColor = "var(--bg-secondary)";
    links.style.padding = "1rem";
    links.style.borderBottom = "1px solid var(--border-color)";
  }
}

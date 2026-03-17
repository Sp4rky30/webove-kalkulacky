function updateThemeButton() {
    const button = document.getElementById("themeToggle");
    if (!button) return;
    button.textContent = document.body.classList.contains("dark") ? "☀️ Světlý režim" : "🌙 Tmavý režim";
}

function dispatchThemeChange() {
    document.dispatchEvent(
        new CustomEvent("themechange", {
            detail: { dark: document.body.classList.contains("dark") },
        })
    );
}

function applyStoredTheme() {
    const savedTheme = localStorage.getItem("theme");
    document.body.classList.toggle("dark", savedTheme === "dark");
    updateThemeButton();
    dispatchThemeChange();
}

function toggleTheme() {
    document.body.classList.toggle("dark");
    localStorage.setItem("theme", document.body.classList.contains("dark") ? "dark" : "light");
    updateThemeButton();
    dispatchThemeChange();
}

window.updateThemeButton = updateThemeButton;
window.applyStoredTheme = applyStoredTheme;
window.toggleTheme = toggleTheme;

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyStoredTheme, { once: true });
} else {
    applyStoredTheme();
}

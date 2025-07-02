function toggleSearchBar() {
  const bar = document.getElementById("searchBar");
  const icon = document.getElementById("toggleIcon");
  bar.classList.toggle("collapsed");
  icon.textContent = bar.classList.contains("collapsed") ? "▼" : "▲";
}

console.log("📱 手機搜尋 JS 已載入");

  const selectedCategoryMobile = "{{ category|default:'' }}";
  const selectedChapterMobile = "{{ chapter|default:'' }}";
  const selectedNumberMobile = "{{ number|default:'' }}";

  // 🔁 浮動按鈕展開/收合
  function toggleMobileSearchBar() {
    const searchBar = document.getElementById("mobileSearchBar");
    if (searchBar) {
      searchBar.classList.toggle("show");
      console.log("🔁 展開 / 收合 搜尋欄");
    }
  }

  // ⛏ 載入章節
  function fetchChaptersMobile(isInit = false) {
    const category = document.getElementById("category_select").value;
    const chapterSelect = document.getElementById("chapter_select");
    const numberSelect = document.getElementById("number_select");

    chapterSelect.innerHTML = '<option value="">章節</option>';
    numberSelect.innerHTML = '<option value="">題號</option>';
    if (!category) return;

    fetch(`/get_chapters_by_category/?category=${encodeURIComponent(category)}`)
      .then(res => res.json())
      .then(data => {
        data.chapters.forEach(ch => {
          const opt = document.createElement("option");
          opt.value = ch;
          opt.textContent = ch;
          if (isInit && ch == selectedChapterMobile) opt.selected = true;
          chapterSelect.appendChild(opt);
        });

        if (isInit && selectedChapterMobile) {
          fetchNumbersMobile(true);
        }
      })
      .catch(err => console.error("❌ 無法取得章節", err));
  }

  // ⛏ 載入題號
  function fetchNumbersMobile(isInit = false) {
    const category = document.getElementById("category_select").value;
    const chapter = document.getElementById("chapter_select").value;
    const numberSelect = document.getElementById("number_select");

    numberSelect.innerHTML = '<option value="">題號</option>';
    if (!category || !chapter) return;

    fetch(`/get_numbers_by_chapter/?category=${encodeURIComponent(category)}&chapter=${encodeURIComponent(chapter)}`)
      .then(res => res.json())
      .then(data => {
        data.numbers.forEach(num => {
          const opt = document.createElement("option");
          opt.value = num;
          opt.textContent = num;
          if (isInit && num == selectedNumberMobile) opt.selected = true;
          numberSelect.appendChild(opt);
        });
      })
      .catch(err => console.error("❌ 無法取得題號", err));
  }

  // ✅ 頁面載入還原下拉內容
  document.addEventListener("DOMContentLoaded", () => {
    const fab = document.querySelector(".search-fab");
    if (fab) fab.addEventListener("click", toggleMobileSearchBar);

    const catEl = document.getElementById("category_select");
    if (selectedCategoryMobile && catEl) {
      catEl.value = selectedCategoryMobile;
      fetchChaptersMobile(true);
    }
  });

  // ✅ 手動觸發 onchange 綁定
  document.getElementById("category_select").addEventListener("change", () => fetchChaptersMobile());
  document.getElementById("chapter_select").addEventListener("change", () => fetchNumbersMobile());
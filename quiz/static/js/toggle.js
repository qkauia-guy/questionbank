console.log("💻 桌機搜尋 JS 已載入");

const mockSelectedCategory = "{{ category|default:'' }}";
const mockSelectedChapter = "{{ chapter|default:'' }}";
const mockSelectedNumber = "{{ number|default:'' }}";

function isMobile() {
  return window.innerWidth <= 768;
}

function handleCategoryChange() {
  if (isMobile()) {
    fetchChaptersMobile();
  } else {
    fetchMockChapters();
  }
}

function handleChapterChange() {
  if (isMobile()) {
    fetchNumbersMobile();
  } else {
    fetchMockNumbers();
  }
}

function fetchMockChapters() {
  const category = document.getElementById("mock_category").value;
  const chapterSelect = document.getElementById("mock_chapter");
  const numberSelect = document.getElementById("mock_number");

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
        if (ch == mockSelectedChapter) opt.selected = true;
        chapterSelect.appendChild(opt);
      });

      // 自動載入對應的題號
      if (mockSelectedChapter) fetchMockNumbers();
    })
    .catch(err => console.error("❌ 無法取得章節", err));
}

function fetchMockNumbers() {
  const category = document.getElementById("mock_category").value;
  const chapter = document.getElementById("mock_chapter").value;
  const numberSelect = document.getElementById("mock_number");

  numberSelect.innerHTML = '<option value="">題號</option>';
  if (!category || !chapter) return;

  fetch(`/get_numbers_by_chapter/?category=${encodeURIComponent(category)}&chapter=${encodeURIComponent(chapter)}`)
    .then(res => res.json())
    .then(data => {
      data.numbers.forEach(num => {
        const opt = document.createElement("option");
        opt.value = num;
        opt.textContent = num;
        if (num == mockSelectedNumber) opt.selected = true;
        numberSelect.appendChild(opt);
      });
    })
    .catch(err => console.error("❌ 無法取得題號", err));
}

function fetchChaptersMobile() {
  fetchMockChapters();
}

function fetchNumbersMobile() {
  fetchMockNumbers();
}

// ✅ 頁面一載入就還原欄位（Category → Chapter → Number）
window.addEventListener("DOMContentLoaded", () => {
  const categoryEl = document.getElementById("mock_category");
  const chapterEl = document.getElementById("mock_chapter");
  const numberEl = document.getElementById("mock_number");

  if (mockSelectedCategory && categoryEl) {
    categoryEl.value = mockSelectedCategory;

    fetch(`/get_chapters_by_category/?category=${encodeURIComponent(mockSelectedCategory)}`)
      .then(res => res.json())
      .then(data => {
        chapterEl.innerHTML = '<option value="">章節</option>';
        data.chapters.forEach(ch => {
          const opt = document.createElement("option");
          opt.value = ch;
          opt.textContent = ch;
          if (ch == mockSelectedChapter) opt.selected = true;
          chapterEl.appendChild(opt);
        });

        // 如果章節也選了，就自動 fetch 題號
        if (mockSelectedChapter) {
          fetch(`/get_numbers_by_chapter/?category=${encodeURIComponent(mockSelectedCategory)}&chapter=${encodeURIComponent(mockSelectedChapter)}`)
            .then(res => res.json())
            .then(data => {
              numberEl.innerHTML = '<option value="">題號</option>';
              data.numbers.forEach(num => {
                const opt = document.createElement("option");
                opt.value = num;
                opt.textContent = num;
                if (num == mockSelectedNumber) opt.selected = true;
                numberEl.appendChild(opt);
              });
            });
        }
      });
  }
});

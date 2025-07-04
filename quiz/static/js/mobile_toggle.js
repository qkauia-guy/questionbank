function toggleSearchBarMock() {
  const bar = document.getElementById("mobileSearchBar-mock");
  if (bar) {
    bar.classList.toggle("active");
  } else {
    console.error("⚠️ mobileSearchBar-mock not found");
  }
}

function fetchNumbersMobile() {
  const chapterSelect = document.getElementById("chapter_mobile");
  const selectedChapter = chapterSelect.value;

  fetch(`/get_numbers/?chapter=${selectedChapter}`)
    .then(response => response.json())
    .then(data => {
      const numberSelect = document.getElementById("number_mobile");
      numberSelect.innerHTML = '<option value="">題號</option>';
      data.numbers.forEach(num => {
        const option = document.createElement("option");
        option.value = num;
        option.textContent = num;
        numberSelect.appendChild(option);
      });
    })
    .catch(error => {
      console.error("取得題號失敗：", error);
    });
}

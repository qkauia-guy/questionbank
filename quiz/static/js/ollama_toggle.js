const ollamaHost = location.hostname === "localhost" || location.hostname === "127.0.0.1"
    ? "http://localhost:11434"
    : `http://${location.hostname}:11434`;

document.addEventListener("DOMContentLoaded", function () {
  const ollamaSwitch = document.getElementById("ollamaSwitch");
  
    
  fetch(`${ollamaHost}/api/tags`, { method: "GET" })
    .then((res) => {
      if (!res.ok) throw new Error("Ollama not responding");
      return res.json();
    })
    .then((data) => {
      console.log("✅ Ollama is running!", data);

      // 可選：自動啟用 AI 模式
      // if (!ollamaSwitch.checked) {
      //   ollamaSwitch.checked = true;
      //   fetch("/toggle-ollama?enable=true");
      // }
    })
    .catch((err) => {
      console.warn("⚠️ Ollama 未啟動或未安裝");

      // Swal.fire({
      //   title: "⚠️ 找不到 Ollama",
      //   text: "AI 解釋功能需本機已安裝並啟動 Ollama。\n將自動關閉 AI 功能。",
      //   icon: "warning",
      //   confirmButtonText: "我了解了",
      // });

      // 強制關閉 AI 開關
      // if (ollamaSwitch && ollamaSwitch.checked) {
      //   ollamaSwitch.checked = false;
      //   fetch("/toggle-ollama?enable=false");
      // }
    });

  // 開關切換事件
  window.toggleOllama = function (checkbox) {
    fetch(`/toggle-ollama?enable=${checkbox.checked}`)
      .then(res => res.json())
      .then(data => {
        if (!data.enabled) {
          alert("⚠️ AI 模式已關閉");
        } else {
          alert("✅ AI 模式已啟用");
        }
      });
  };
});


function toggleOllama(checkbox) {
  fetch(`/toggle-ollama?enable=${checkbox.checked}`)
    .then(res => res.json())
    .then(data => {
      if (!data.enabled) {
        alert("⚠️ 已關閉 AI 模式。");
      } else {
        alert("✅ AI 模式已啟用");
      }
    });
}

function fetchOllamaModels() {
    fetch(`${ollamaHost}/api/tags`)
    .then((res) => res.json())
    .then((data) => {
      const select = document.getElementById("modelSelect");
      if (!select) return;

      // 清空舊的 options
      select.innerHTML = "";

      data.models.forEach((model) => {
        const opt = document.createElement("option");
        opt.value = model.name;
        opt.textContent = model.name;
        select.appendChild(opt);
      });

      // 設定預設值（localStorage 儲存）
      const stored = localStorage.getItem("ollama_model");
      if (stored) select.value = stored;
    })
    .catch(() => {
      console.warn("⚠️ 無法取得 Ollama 模型列表");
    });
}

function saveModelChoice(selectElement) {
  const model = selectElement.value;
  localStorage.setItem("ollama_model", model);

  // 可選：立即通知後端
  fetch(`/set-ollama-model?model=${encodeURIComponent(model)}`);
}

// 初始載入
window.addEventListener("DOMContentLoaded", () => {
  fetchOllamaModels();
});
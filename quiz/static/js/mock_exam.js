document.addEventListener("DOMContentLoaded", function () {
  const canvas = document.getElementById("overlayCanvas");
  const ctx = canvas.getContext("2d");
  const toggleBtn = document.getElementById("togglePenBtn");

  let isDrawing = false;
  let penEnabled = false;
  let brushColor = "#000000";
  let brushSize = 2;
  let penAlpha = 1;
  let currentMode = "normal";

  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);

  canvas.addEventListener("mousedown", (e) => {
    if (!penEnabled) return;
    isDrawing = true;
    ctx.beginPath();
    ctx.moveTo(e.clientX, e.clientY);
  });

  canvas.addEventListener("mousemove", (e) => {
    if (isDrawing && penEnabled) {
      ctx.lineTo(e.clientX, e.clientY);
      ctx.stroke();
    }
  });

  canvas.addEventListener("mouseup", () => {
    isDrawing = false;
  });

  document.getElementById("penColor")?.addEventListener("change", function () {
    brushColor = this.value;
    updateBrushStyle();
  });

  document.getElementById("brushSize")?.addEventListener("input", function () {
    brushSize = parseInt(this.value);
    updateBrushStyle();
  });

  document.getElementById("penAlpha")?.addEventListener("input", function () {
    penAlpha = parseFloat(this.value);
    updateBrushStyle();
  });

  document.getElementById("penMode")?.addEventListener("change", function () {
    currentMode = this.value;
    updateBrushStyle();
  });


  function updateBrushStyle() {
    ctx.lineWidth = brushSize;

    if (currentMode === "eraser") {
      ctx.globalCompositeOperation = "destination-out";
      ctx.strokeStyle = "rgba(0,0,0,1)";
    } else {
      ctx.globalCompositeOperation = "source-over";

      if (currentMode === "highlighter") {
        // 強制螢光黃色 + 透明度
        ctx.strokeStyle = "rgba(255,255,0,0.3)"; // 螢光黃 + 半透明
      } else {
        ctx.strokeStyle = convertHexToRgba(brushColor, penAlpha);
      }
    }
  }


  function convertHexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  toggleBtn.addEventListener("click", () => {
    penEnabled = !penEnabled;
    canvas.style.pointerEvents = penEnabled ? "auto" : "none";
    toggleBtn.textContent = penEnabled ? "🛑 關閉畫筆" : "✏️ 開啟畫筆";
  });

  window.clearOverlayCanvas = function () {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  updateBrushStyle(); // 初始化筆刷設定
});

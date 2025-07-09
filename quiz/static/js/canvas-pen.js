const canvas = document.getElementById("overlayCanvas");
const ctx = canvas.getContext("2d");

let isDrawing = false;
let penEnabled = false;

let mode = "normal";
let color = "#000000";
let size = 2;
let alpha = 1;

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

// 🎯 畫筆啟用 / 關閉
document.getElementById("togglePenBtn").addEventListener("click", () => {
  penEnabled = !penEnabled;

  canvas.style.pointerEvents = penEnabled ? "auto" : "none";
  document.getElementById("togglePenBtn").textContent = penEnabled ? "🛑 關閉畫筆" : "✏️ 開啟畫筆";
});

// 🖍️ 筆刷參數綁定
document.getElementById("penMode").addEventListener("change", e => mode = e.target.value);
document.getElementById("penColor").addEventListener("change", e => color = e.target.value);
document.getElementById("brushSize").addEventListener("input", e => size = e.target.value);
document.getElementById("penAlpha").addEventListener("input", e => alpha = e.target.value);

// 🧹 清除畫面
function clearOverlayCanvas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// ✏️ 實作畫筆邏輯
let lastX = 0;
let lastY = 0;

canvas.addEventListener("mousedown", e => {
  if (!penEnabled) return;

  isDrawing = true;
  [lastX, lastY] = [e.offsetX, e.offsetY];
});

canvas.addEventListener("mousemove", e => {
  if (!isDrawing || !penEnabled) return;

  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  if (mode === "eraser") {
    ctx.globalCompositeOperation = "destination-out";
    ctx.strokeStyle = "rgba(0,0,0,1)";
    ctx.lineWidth = size * 2;
  } else {
    ctx.globalCompositeOperation = "source-over";
    ctx.strokeStyle = color;
    ctx.globalAlpha = (mode === "highlighter") ? 0.3 : alpha;
    ctx.lineWidth = size;
  }

  ctx.beginPath();
  ctx.moveTo(lastX, lastY);
  ctx.lineTo(e.offsetX, e.offsetY);
  ctx.stroke();

  [lastX, lastY] = [e.offsetX, e.offsetY];
});

canvas.addEventListener("mouseup", () => isDrawing = false);
canvas.addEventListener("mouseleave", () => isDrawing = false);

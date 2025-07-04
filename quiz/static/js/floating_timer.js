let seconds = 0;
const MAX_TIME = 120;

const timerDisplay = document.getElementById("timer");
const usedTimeInput = document.getElementById("used_time");
const timerBox = document.getElementById("floating-timer");

const updateTimer = () => {
  seconds += 1;
  timerDisplay.textContent = seconds;
  usedTimeInput.value = seconds;

  if (seconds === MAX_TIME) {
    alert("⏱︎ 已超過建議作答時間！");
    if (timerBox) {
      timerBox.style.background = "#ffe6e6";
      timerBox.style.color = "#ff0000";
      timerBox.style.borderColor = "#ff0000";
    }
  }
};

let timer = setInterval(updateTimer, 1000);

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    clearInterval(timer);
  } else {
    timer = setInterval(updateTimer, 1000);
  }
});
let seconds = 0;
const MAX_TIME = 120;
const REMINDER_TIME = 60;
let timer = null;

const timerDisplay = document.getElementById("timer");
const usedTimeInput = document.getElementById("used_time");
const timerBox = document.getElementById("floating-timer");

const updateTimer = () => {
  seconds += 1;
  timerDisplay.textContent = seconds;
  usedTimeInput.value = seconds;

  // 60 秒提醒：加上橘色
  if (seconds === REMINDER_TIME) {
    console.log("⚠️ 60 秒提醒觸發");
    timerBox.classList.add("reminder-warning");
  }

  // 120 秒警告：紅色並跳通知
  if (seconds === MAX_TIME) {
    alert("⏱︎ 已超過建議作答時間！");
    timerBox.classList.remove("reminder-warning");
    timerBox.classList.add("reminder-danger");
  }
};

timer = setInterval(updateTimer, 1000);

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    clearInterval(timer);
    timer = null;
  } else if (!timer) {
    timer = setInterval(updateTimer, 1000);
  }
});

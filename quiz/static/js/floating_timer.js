let seconds = 0;
  let timer = null;
  let timerStopped = false;

  const MAX_TIME = 120;
  const REMINDER_TIME = 60;

  const timerDisplay = document.getElementById("timer");
  const usedTimeInput = document.getElementById("used_time");
  const timerBox = document.getElementById("floating-timer");

  function updateTimer() {
    if (timerStopped) return;

    seconds += 1;
    timerDisplay.textContent = seconds;
    usedTimeInput.value = seconds;

    if (seconds === REMINDER_TIME) {
      timerBox.classList.add("reminder-warning");
    }

    if (seconds === MAX_TIME) {
      alert("⏱︎ 已超過建議作答時間！");
      timerBox.classList.remove("reminder-warning");
      timerBox.classList.add("reminder-danger");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    // 啟動計時器
    timer = setInterval(updateTimer, 1000);

    // 送出表單時停止計時
    const form = document.querySelector("form");
    if (form) {
      form.addEventListener("submit", () => {
        clearInterval(timer);
        timerStopped = true;
      });
    }
  });

  // 避免背景持續計時
  document.addEventListener("visibilitychange", () => {
    if (document.hidden && timer) {
      clearInterval(timer);
      timer = null;
    } else if (!document.hidden && !timer && !timerStopped) {
      timer = setInterval(updateTimer, 1000);
    }
  });
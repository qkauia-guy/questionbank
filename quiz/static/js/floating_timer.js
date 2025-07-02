let seconds = 0;
  const timerDisplay = document.getElementById("timer");
  const usedTimeInput = document.getElementById("used_time");

  const updateTimer = () => {
    seconds += 1;
    timerDisplay.textContent = seconds;
    usedTimeInput.value = seconds;
  };

  // 每秒更新一次
  let timer = setInterval(updateTimer, 1000);

  // 切離頁面時暫停，回來時恢復
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      clearInterval(timer);
    } else {
      timer = setInterval(updateTimer, 1000);
    }
  });
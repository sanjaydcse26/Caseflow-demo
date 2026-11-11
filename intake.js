(() => {
  const steps = [...document.querySelectorAll(".step")];
  const prev = document.getElementById("prev");
  const next = document.getElementById("next");
  const submit = document.getElementById("submit");
  const bar = document.getElementById("progress-bar");
  const label = document.getElementById("progress-label");
  const breathing = document.getElementById("breathing");
  const warning = document.getElementById("urgent-warning");
  let current = 0;

  function showStep() {
    steps.forEach((step, i) => step.classList.toggle("active", i === current));
    prev.disabled = current === 0;
    next.hidden = current === steps.length - 1;
    submit.hidden = current !== steps.length - 1;
    label.textContent = `Step ${current + 1} of ${steps.length}`;
    bar.style.width = `${((current + 1) / steps.length) * 100}%`;
  }
  function validCurrentStep() {
    const fields = [...steps[current].querySelectorAll("input, textarea, select")];
    for (const field of fields) {
      if (field.type === "checkbox" && !field.checked && field.required) {
        field.reportValidity(); return false;
      }
      if (field.required && !field.checkValidity()) {
        field.reportValidity(); return false;
      }
    }
    return true;
  }
  next.addEventListener("click", () => {
    if (validCurrentStep() && current < steps.length - 1) { current++; showStep(); }
  });
  prev.addEventListener("click", () => { if (current > 0) { current--; showStep(); } });
  breathing.addEventListener("change", () => { warning.hidden = breathing.value === "No"; });
  showStep();
})();

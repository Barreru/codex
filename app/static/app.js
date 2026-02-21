async function getQuestionnaire() {
  const r = await fetch('/api/questionnaire');
  return r.json();
}

function renderQuestions(q) {
  const container = document.getElementById('questions');
  for (const [script, prompts] of Object.entries(q)) {
    prompts.forEach((prompt, idx) => {
      const id = `${script}-${idx}`;
      const wrapper = document.createElement('label');
      wrapper.innerHTML = `${prompt}<input type="number" min="1" max="12" value="6" id="${id}" />`;
      container.appendChild(wrapper);
    });
  }
}

function collectProfilePayload() {
  const scripts = ['avoidance', 'worship', 'status', 'vigilance'];
  const payload = {};
  scripts.forEach((script) => {
    payload[script] = Array.from({ length: 4 }, (_, idx) => Number(document.getElementById(`${script}-${idx}`).value));
  });
  return payload;
}

async function postJson(path, body) {
  const r = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

document.getElementById('profile-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const output = document.getElementById('profile-output');
  try {
    const data = await postJson('/api/profile', collectProfilePayload());
    output.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    output.textContent = err.message;
  }
});

document.getElementById('scenario-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const payload = Object.fromEntries(form.entries());
  for (const key of ['gross_monthly_income', 'rent', 'utilities', 'transportation', 'groceries', 'discretionary', 'target_savings_rate']) {
    payload[key] = Number(payload[key]);
  }
  const output = document.getElementById('scenario-output');
  try {
    const data = await postJson('/api/scenario', payload);
    output.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    output.textContent = err.message;
  }
});

document.getElementById('cancel-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const payload = Object.fromEntries(form.entries());
  payload.monthly_cost = Number(payload.monthly_cost);
  payload.user_consent = !!e.target.user_consent.checked;

  const output = document.getElementById('cancel-output');
  try {
    const data = await postJson('/api/subscription/cancel-script', payload);
    output.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    output.textContent = err.message;
  }
});

getQuestionnaire().then(renderQuestions);

// Progress tracking via Server-Sent Events
(function () {
  const percent = document.getElementById('progress-percent');
  const bar = document.getElementById('progress-bar');
  const counter = document.getElementById('progress-counter');
  const title = document.getElementById('progress-title');
  const subtitle = document.getElementById('progress-subtitle');
  const currentPrefix = document.getElementById('current-prefix');
  const currentMessage = document.getElementById('current-message');
  const doneCard = document.getElementById('done-card');
  const logContainer = document.getElementById('log-container');

  let seenMessages = new Set();

  function nowTime() {
    const d = new Date();
    return d.toTimeString().slice(0, 8);
  }

  function addLog(level, text) {
    const key = level + '|' + text;
    if (seenMessages.has(key)) return;
    seenMessages.add(key);
    const div = document.createElement('div');
    div.className = 'flex gap-4 items-start';
    const colorClass = level === 'SUCCES' ? 'text-tertiary' : level === 'ERREUR' ? 'text-error' : 'text-primary';
    div.innerHTML = `
      <span class="text-outline-variant font-medium shrink-0">${nowTime()}</span>
      <p class="text-on-surface-variant"><span class="${colorClass} font-bold">${level} :</span> ${text}</p>
    `;
    logContainer.appendChild(div);
    logContainer.scrollTop = logContainer.scrollHeight;
  }

  function updateUI(state) {
    const total = state.progress_total || 0;
    const current = state.progress_current || 0;
    const pct = total > 0 ? Math.round((current / total) * 100) : (state.status === 'done' ? 100 : 0);

    percent.textContent = pct;
    bar.style.width = pct + '%';
    counter.textContent = `${current} sur ${total} dossier${total > 1 ? 's' : ''}`;

    if (state.progress_message) {
      title.textContent = state.progress_message;
      currentMessage.textContent = state.progress_message;
    }
    if (state.progress_prefix) {
      currentPrefix.textContent = `Demande N°${state.progress_prefix}`;
      addLog('INFO', `Traitement de la demande ${state.progress_prefix}`);
    }

    if (state.status === 'done') {
      title.textContent = 'Extraction terminée.';
      subtitle.textContent = `${state.total_demandes} demande(s) traitée(s), ${state.avec_tableau} avec tableau.`;
      doneCard.classList.remove('opacity-40');
      bar.style.width = '100%';
      percent.textContent = '100';
      addLog('SUCCES', `${state.total_demandes} dossier(s) traité(s), ${state.avec_tableau} avec tableau`);
      // Redirect after a short pause
      setTimeout(() => {
        window.location.href = `/resultats/${state.job_id}`;
      }, 1500);
    } else if (state.status === 'error') {
      title.textContent = 'Erreur de traitement';
      subtitle.textContent = state.error || 'Une erreur inconnue est survenue.';
      addLog('ERREUR', state.error || 'Erreur inconnue');
    }
  }

  const es = new EventSource(`/progress/${JOB_ID}`);
  es.onmessage = (event) => {
    try {
      const state = JSON.parse(event.data);
      updateUI(state);
      if (state.status === 'done' || state.status === 'error') {
        es.close();
      }
    } catch (e) {
      console.error('SSE parse error:', e);
    }
  };
  es.onerror = () => {
    console.warn('SSE connection lost, retrying…');
  };
})();

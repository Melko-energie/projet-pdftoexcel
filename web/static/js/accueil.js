// Upload page : click-to-browse, drag & drop, preview, submit
(function () {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const selectedFiles = document.getElementById('selected-files');
  const submitBtn = document.getElementById('submit-btn');
  const submitHint = document.getElementById('submit-hint');
  const form = document.getElementById('upload-form');

  function humanSize(bytes) {
    const mb = bytes / (1024 * 1024);
    return mb >= 1 ? mb.toFixed(1) + ' MB' : (bytes / 1024).toFixed(0) + ' KB';
  }

  function renderFileList(files) {
    selectedFiles.innerHTML = '';
    if (!files || files.length === 0) {
      selectedFiles.classList.add('hidden');
      submitBtn.disabled = true;
      if (submitHint) submitHint.textContent = 'Déposez au moins un fichier pour activer le bouton';
      return;
    }
    selectedFiles.classList.remove('hidden');
    submitBtn.disabled = false;
    if (submitHint) submitHint.textContent = `${files.length} fichier(s) prêt(s) — cliquez pour lancer`;
    for (const f of files) {
      const div = document.createElement('div');
      div.className = 'flex items-center justify-between p-4 bg-surface-container-low rounded-lg';
      div.innerHTML = `
        <div class="flex items-center gap-3 min-w-0">
          <span class="material-symbols-outlined text-outline shrink-0">description</span>
          <span class="font-medium text-on-surface-variant truncate">${f.name}</span>
        </div>
        <span class="text-sm text-outline shrink-0 ml-4">${humanSize(f.size)}</span>
      `;
      selectedFiles.appendChild(div);
    }
  }

  // Click anywhere on drop zone → open file picker
  dropZone.addEventListener('click', () => {
    fileInput.click();
  });

  // File input change
  fileInput.addEventListener('change', () => {
    renderFileList(fileInput.files);
  });

  // Drag & drop
  ['dragenter', 'dragover'].forEach((evt) => {
    dropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add('border-primary/60', 'bg-primary/5');
    });
  });
  ['dragleave', 'drop'].forEach((evt) => {
    dropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('border-primary/60', 'bg-primary/5');
    });
  });
  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      fileInput.files = dt.files;
      renderFileList(fileInput.files);
    }
  });

  // Submit handler : show a loading state
  form.addEventListener('submit', (e) => {
    if (submitBtn.disabled) {
      e.preventDefault();
      return;
    }
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="material-symbols-outlined animate-spin">autorenew</span> Upload en cours…';
  });
})();

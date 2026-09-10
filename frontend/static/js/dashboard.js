document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('uploadForm');
  const fileInput = document.getElementById('fileInput');
  const dropzone = document.getElementById('dropzone');
  const selectedFileName = document.getElementById('selectedFileName');
  const processBtn = document.getElementById('processBtn');
  const statusAlert = document.getElementById('statusAlert');
  const refreshBtn = document.getElementById('refreshBtn');
  const documentsTableBody = document.getElementById('documentsTableBody');

  // Drag & drop behavior
  dropzone.addEventListener('click', () => fileInput.click());

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      fileInput.files = files;
      showSelectedFile(files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      showSelectedFile(fileInput.files[0]);
    }
  });

  function showSelectedFile(file) {
    selectedFileName.innerHTML = `<i class="fa-solid fa-file"></i> Selected: <strong>${file.name}</strong> (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
  }

  // Load documents list
  async function loadDocuments() {
    try {
      const response = await fetch('/api/v1/documents');
      const data = await response.json();
      renderTable(data.documents || []);
    } catch (err) {
      console.error('Failed to load documents list:', err);
      documentsTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--fail-red);">Error loading documents list.</td></tr>`;
    }
  }

  function renderTable(documents) {
    if (documents.length === 0) {
      documentsTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">No documents processed yet. Upload a document above to get started!</td></tr>`;
      return;
    }

    documentsTableBody.innerHTML = documents.map(doc => {
      const statusBadge = doc.processing_status === 'PASS' 
        ? `<span class="badge badge-pass"><i class="fa-solid fa-check"></i> PASS</span>`
        : `<span class="badge badge-fail"><i class="fa-solid fa-xmark"></i> FAILED</span>`;
      
      const confStr = doc.overall_confidence ? `${Math.round(doc.overall_confidence * 100)}%` : 'N/A';
      const formattedDate = new Date(doc.processed_at).toLocaleString();

      return `
        <tr>
          <td>
            <strong>${doc.document_name}</strong>
          </td>
          <td><span style="text-transform: uppercase; font-size: 0.8rem; letter-spacing: 0.05em; color: var(--accent-cyan);">${doc.document_type}</span></td>
          <td>${statusBadge}</td>
          <td>${confStr}</td>
          <td><small style="color: var(--text-muted);">${formattedDate}</small></td>
          <td>
            <a href="/view/${encodeURIComponent(doc.document_name)}" class="btn-secondary" style="padding: 0.35rem 0.75rem;">
              <i class="fa-solid fa-eye"></i> View Result
            </a>
          </td>
        </tr>
      `;
    }).join('');
  }

  // Handle Form Submission
  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!fileInput.files || fileInput.files.length === 0) {
      showAlert('Please select or drag a file to upload.', 'fail');
      return;
    }

    const formData = new FormData(uploadForm);
    
    // UI Processing state
    processBtn.disabled = true;
    processBtn.innerHTML = `<div class="spinner"></div> Processing Document...`;
    statusAlert.style.display = 'none';
    showAlert('⏳ Uploading and processing your document. This may take up to 60 seconds on first request...', 'info');

    // Abort controller — 120 second timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    try {
      const response = await fetch('/api/v1/documents/process', {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      const result = await response.json();

      if (response.ok) {
        if (result.processing_status === 'PASS') {
          showAlert(`✅ Document processed successfully! Status: PASS. Redirecting to result...`, 'pass');
        } else {
          showAlert(`⚠️ Document processed. Status: FAILED. Check file validation / calculations. Redirecting to result...`, 'fail');
        }
        
        // Refresh table and redirect after 1.5 seconds
        loadDocuments();
        setTimeout(() => {
          window.location.href = `/view/${encodeURIComponent(result.document_name)}`;
        }, 1500);

      } else {
        const errorMsg = result.error ? result.error.message : 'Upload failed.';
        showAlert(`Error: ${errorMsg}`, 'fail');
      }

    } catch (err) {
      clearTimeout(timeoutId);
      console.error('Error submitting form:', err);
      if (err.name === 'AbortError') {
        showAlert(`⏰ Request timed out (>120s). The server may be under heavy load. Please try again.`, 'fail');
      } else {
        showAlert(`Network or server error: ${err.message}`, 'fail');
      }
    } finally {
      processBtn.disabled = false;
      processBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> Process Document`;
    }
  });

  function showAlert(msg, type) {
    statusAlert.style.display = 'block';
    if (type === 'pass') {
      statusAlert.style.background = 'rgba(16, 185, 129, 0.15)';
      statusAlert.style.border = '1px solid var(--pass-green)';
      statusAlert.style.color = '#6ee7b7';
    } else if (type === 'info') {
      statusAlert.style.background = 'rgba(6, 182, 212, 0.10)';
      statusAlert.style.border = '1px solid var(--accent-cyan)';
      statusAlert.style.color = '#67e8f9';
    } else {
      statusAlert.style.background = 'rgba(239, 68, 68, 0.15)';
      statusAlert.style.border = '1px solid var(--fail-red)';
      statusAlert.style.color = '#fca5a5';
    }
    statusAlert.innerHTML = msg;
  }

  refreshBtn.addEventListener('click', loadDocuments);

  // Initial load
  loadDocuments();
});

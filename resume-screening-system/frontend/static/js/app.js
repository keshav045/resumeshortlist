/**
 * app.js
 * ──────
 * Frontend logic for the ResumeAI Dashboard.
 * Vanilla JS + Fetch API — no frameworks.
 */

const API = '';  // same origin as FastAPI

// ── State ────────────────────────────────────────────────────────────
let pendingFiles    = [];
let currentResumeId = null;

// ══════════════════════════════════════════════════════════════════════
// NAVIGATION
// ══════════════════════════════════════════════════════════════════════
function showSection(name, navElement) {
  // Remove active from all sections and nav items
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  // Activate the target section
  const section = document.getElementById(`sec-${name}`);
  if (section) section.classList.add('active');

  // Activate the clicked nav item
  if (navElement) {
    navElement.classList.add('active');
  }

  // Lazy-load data when switching sections
  if (name === 'match')    loadResumeSelect();
  if (name === 'database') loadAllResumes();

  // Close sidebar on mobile
  closeSidebar();
}

// ══════════════════════════════════════════════════════════════════════
// MOBILE SIDEBAR
// ══════════════════════════════════════════════════════════════════════
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  sidebar.classList.toggle('open');
  overlay.classList.toggle('show');
}

function closeSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (sidebar) sidebar.classList.remove('open');
  if (overlay) overlay.classList.remove('show');
}

// ══════════════════════════════════════════════════════════════════════
// THEME TOGGLE
// ══════════════════════════════════════════════════════════════════════
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
  localStorage.setItem('theme', isDark ? 'light' : 'dark');
}

// Restore saved theme
(function restoreTheme() {
  const saved = localStorage.getItem('theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
    const toggle = document.getElementById('themeToggle');
    if (toggle) toggle.checked = (saved === 'light');
  }
})();

// ══════════════════════════════════════════════════════════════════════
// UPLOAD: File selection, queue, and upload
// ══════════════════════════════════════════════════════════════════════
function handleFileSelect(event) {
  addToQueue([...event.target.files]);
  event.target.value = '';  // reset so same file can be re-selected
}

function handleDrop(event) {
  event.preventDefault();
  document.getElementById('uploadZone').classList.remove('drag');
  const files = [...event.dataTransfer.files].filter(f =>
    f.name.toLowerCase().endsWith('.pdf')
  );
  if (files.length === 0) {
    toast('Only PDF files are accepted');
    return;
  }
  addToQueue(files);
}

function addToQueue(files) {
  files.forEach(file => {
    if (!pendingFiles.find(f => f.name === file.name)) {
      pendingFiles.push(file);
    }
  });
  renderQueue();
}

function renderQueue() {
  const container = document.getElementById('uploadQueue');
  const btn = document.getElementById('uploadBtn');

  container.innerHTML = pendingFiles.map((f, i) => `
    <div class="queue-item" style="animation-delay: ${i * 0.05}s">
      <span class="q-icon">
        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
      </span>
      <span class="q-name">${escapeHtml(f.name)}</span>
      <span class="q-size">${formatFileSize(f.size)}</span>
      <span class="q-remove" onclick="removeFromQueue(${i})" title="Remove">✕</span>
    </div>
  `).join('');

  btn.style.display = pendingFiles.length ? 'inline-flex' : 'none';
}

function removeFromQueue(index) {
  pendingFiles.splice(index, 1);
  renderQueue();
}

async function uploadAll() {
  if (!pendingFiles.length) return;

  const log = document.getElementById('uploadLog');
  const btn = document.getElementById('uploadBtn');
  log.innerHTML = '';
  btn.disabled = true;
  btn.textContent = 'Uploading…';

  for (const file of pendingFiles) {
    addLog(`Uploading ${file.name}…`, 'info', log);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res  = await fetch(`${API}/upload-resume`, { method: 'POST', body: formData });
      const data = await res.json();

      if (res.ok) {
        addLog(`✓ ${file.name} — candidate: ${data.candidate_name}`, 'success', log);
      } else {
        addLog(`✗ ${file.name} — ${data.detail}`, 'error', log);
      }
    } catch (e) {
      addLog(`✗ ${file.name} — network error`, 'error', log);
    }
  }

  pendingFiles = [];
  renderQueue();
  updateStats();
  toast('All uploads complete');
  btn.disabled = false;
  btn.textContent = 'Upload All Resumes';
}

// ══════════════════════════════════════════════════════════════════════
// JOB DESCRIPTION
// ══════════════════════════════════════════════════════════════════════
async function saveJD() {
  const title  = document.getElementById('jdTitle').value;
  const text   = document.getElementById('jdText').value;
  const status = document.getElementById('jdStatus');

  if (text.trim().length < 50) {
    status.textContent = 'Job description is too short. Add more detail (50+ characters).';
    status.className = 'status-msg err';
    return;
  }

  const formData = new FormData();
  formData.append('title', title);
  formData.append('description', text);

  try {
    const res  = await fetch(`${API}/job-description`, { method: 'POST', body: formData });
    const data = await res.json();

    if (res.ok) {
      status.textContent = `✓ Saved "${data.title}" (${data.word_count} words)`;
      status.className   = 'status-msg ok';
      document.getElementById('stat-jd-text').textContent = data.title;
      toast('Job description saved');
    } else {
      status.textContent = `✗ ${data.detail}`;
      status.className   = 'status-msg err';
    }
  } catch (e) {
    status.textContent = '✗ Could not connect to server. Is it running?';
    status.className   = 'status-msg err';
  }
}

function loadSampleJD() {
  document.getElementById('jdTitle').value = 'Senior Python / ML Engineer';
  document.getElementById('jdText').value = `We are looking for a Senior Python Engineer with Machine Learning experience.

Required Skills:
- Python (3+ years)
- Machine Learning, Scikit-learn, TensorFlow or PyTorch
- FastAPI or Flask (REST API development)
- SQL databases (PostgreSQL or SQLite)
- Git, Docker
- NLP experience is a strong plus
- Data analysis with Pandas and NumPy

Nice to have:
- AWS or GCP cloud experience
- React or Vue for frontend
- Strong communication and teamwork skills

You will build and maintain ML pipelines, design REST APIs, and collaborate with cross-functional teams.`;

  toast('Sample JD loaded — click Save to apply');
}

// ══════════════════════════════════════════════════════════════════════
// MATCH: Load dropdown & run analysis
// ══════════════════════════════════════════════════════════════════════
async function loadResumeSelect() {
  const sel = document.getElementById('matchSelect');
  sel.innerHTML = '<option value="">Loading…</option>';

  try {
    const res  = await fetch(`${API}/resumes`);
    const data = await res.json();

    if (data.length) {
      sel.innerHTML = data.map(r =>
        `<option value="${r.id}">${r.candidate_name} — ${escapeHtml(r.filename)}</option>`
      ).join('');
    } else {
      sel.innerHTML = '<option value="">No resumes uploaded yet</option>';
    }
  } catch (e) {
    sel.innerHTML = '<option value="">Error loading resumes</option>';
  }
}

async function matchResume() {
  const id = document.getElementById('matchSelect').value;
  if (!id) {
    toast('Select a resume first');
    return;
  }

  const resultDiv = document.getElementById('matchResult');
  resultDiv.style.display = 'none';

  const formData = new FormData();
  formData.append('resume_id', id);

  toast('Analyzing resume…');

  try {
    const res  = await fetch(`${API}/match-resume`, { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) {
      toast(data.detail);
      return;
    }

    currentResumeId = id;
    renderMatchResult(data);
    toast('Analysis complete');
  } catch (e) {
    toast('Network error — is the server running?');
  }
}

function renderMatchResult(data) {
  const score = data.match_score;

  // Reset the arc first for re-animation
  const arc = document.getElementById('scoreArc');
  arc.style.transition = 'none';
  arc.style.strokeDashoffset = 314;

  // Force reflow to restart animation
  void arc.offsetWidth;

  // Set new value
  arc.style.transition = 'stroke-dashoffset 1.4s cubic-bezier(0.4, 0, 0.2, 1)';
  const offset = 314 - (score / 100) * 314;
  arc.style.strokeDashoffset = offset;

  // Color the arc by score tier
  if (score >= 70) {
    arc.style.stroke = '#4ade80';
  } else if (score >= 40) {
    arc.style.stroke = '#fbbf24';
  } else {
    arc.style.stroke = '#f87171';
  }

  // Animated counter for score
  animateCounter('scoreNumber', 0, score, 1200, '%');

  // Meta information
  document.getElementById('scoreCandidate').textContent = data.candidate_name;
  document.getElementById('scoreJob').textContent = data.job_title || 'Job Description';

  // Score label
  let label;
  if (score >= 70) {
    label = 'Strong Match';
    document.getElementById('scoreLabel').style.color = 'var(--green)';
  } else if (score >= 40) {
    label = 'Partial Match';
    document.getElementById('scoreLabel').style.color = 'var(--amber)';
  } else {
    label = 'Weak Match';
    document.getElementById('scoreLabel').style.color = 'var(--red)';
  }
  document.getElementById('scoreLabel').textContent = label;

  // Skill clouds
  renderSkillCloud('matchingSkills', data.matching_skills, 'skill-match');
  renderSkillCloud('missingSkills',  data.missing_skills,  'skill-miss');
  renderSkillCloud('extraSkills',    data.extra_skills,    'skill-extra');

  // Summary
  document.getElementById('resumeSummary').textContent =
    data.summary || 'No summary available.';

  // Show results
  document.getElementById('matchResult').style.display = 'block';
  updateStats();
}

function renderSkillCloud(elementId, skills, cssClass) {
  const el = document.getElementById(elementId);
  if (!skills || skills.length === 0) {
    el.innerHTML = '<span class="skill-none">None identified</span>';
  } else {
    el.innerHTML = skills.map((s, i) =>
      `<span class="skill-tag ${cssClass}" style="animation-delay: ${i * 0.04}s">${escapeHtml(s)}</span>`
    ).join('');
  }
}

async function downloadReport() {
  if (!currentResumeId) return;
  toast('Generating PDF report…');
  window.open(`${API}/report/${currentResumeId}`, '_blank');
}

// ══════════════════════════════════════════════════════════════════════
// RANKINGS
// ══════════════════════════════════════════════════════════════════════
async function rankAll() {
  const container = document.getElementById('rankResults');
  container.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <span>Ranking all resumes — this may take a moment…</span>
    </div>`;

  try {
    const res  = await fetch(`${API}/rank-resumes`);
    const data = await res.json();

    if (!res.ok) {
      container.innerHTML = `<p style="color:var(--red);font-weight:500;">${data.detail}</p>`;
      return;
    }

    if (!data.rankings || !data.rankings.length) {
      container.innerHTML = `<p style="color:var(--text-2)">No resumes to rank yet. Upload some first!</p>`;
      return;
    }

    container.innerHTML = `
      <p style="color:var(--text-2);margin-bottom:20px;font-size:14px;font-weight:500;">
        ${data.total_resumes} resume${data.total_resumes !== 1 ? 's' : ''} ranked for
        <strong style="color:var(--text-1)">${escapeHtml(data.job_title)}</strong>
      </p>
      <table class="rank-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Candidate</th>
            <th>File</th>
            <th>Score</th>
            <th style="min-width:120px;">Match</th>
          </tr>
        </thead>
        <tbody>
          ${data.rankings.map(r => `
            <tr>
              <td>
                <span class="rank-badge ${r.rank <= 3 ? 'rank-' + r.rank : 'rank-n'}">
                  ${r.rank}
                </span>
              </td>
              <td style="font-weight:600;">${escapeHtml(r.candidate_name)}</td>
              <td style="color:var(--text-3);font-size:13px;">${escapeHtml(r.filename)}</td>
              <td style="font-weight:700;color:${
                r.match_score >= 70 ? 'var(--green)' :
                r.match_score >= 40 ? 'var(--amber)' : 'var(--red)'
              }">
                ${r.match_score.toFixed(1)}%
              </td>
              <td>
                <div class="score-bar">
                  <div class="score-bar-fill" style="width:${r.match_score}%"></div>
                </div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>`;

    // Update top stat
    document.getElementById('stat-top-text').textContent =
      `Best: ${data.rankings[0].match_score.toFixed(1)}%`;

    updateStats();
    toast('Ranking complete');
  } catch (e) {
    container.innerHTML = `<p style="color:var(--red);font-weight:500;">Network error — is the server running?</p>`;
  }
}

// ══════════════════════════════════════════════════════════════════════
// ALL RESUMES (Database view)
// ══════════════════════════════════════════════════════════════════════
async function loadAllResumes() {
  const container = document.getElementById('allResumes');
  container.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <span>Loading resumes…</span>
    </div>`;

  try {
    const res  = await fetch(`${API}/resumes`);
    const data = await res.json();

    if (!data.length) {
      container.innerHTML = `<p style="color:var(--text-2)">No resumes uploaded yet. Go to Upload to add some!</p>`;
      return;
    }

    container.innerHTML = `
      <table class="rank-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Candidate</th>
            <th>File</th>
            <th>Score</th>
            <th>Uploaded</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${data.map(r => `
            <tr id="row-${r.id}">
              <td style="color:var(--text-3);font-weight:600;">#${r.id}</td>
              <td style="font-weight:600;">${escapeHtml(r.candidate_name)}</td>
              <td style="color:var(--text-3);font-size:13px;">${escapeHtml(r.filename)}</td>
              <td style="font-weight:700;color:${
                r.match_score > 0
                  ? (r.match_score >= 70 ? 'var(--green)' : r.match_score >= 40 ? 'var(--amber)' : 'var(--red)')
                  : 'var(--text-3)'
              }">
                ${r.match_score ? r.match_score.toFixed(1) + '%' : '—'}
              </td>
              <td style="color:var(--text-3);font-size:12px;">
                ${r.uploaded_at ? formatDate(r.uploaded_at) : '—'}
              </td>
              <td>
                <button class="btn btn-danger" onclick="deleteResume(${r.id})">
                  <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px; vertical-align: middle;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg> Delete
                </button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>`;
  } catch (e) {
    container.innerHTML = `<p style="color:var(--red);font-weight:500;">Error loading resumes.</p>`;
  }
}

async function deleteResume(id) {
  if (!confirm('Are you sure you want to delete this resume? This cannot be undone.')) return;

  try {
    const res = await fetch(`${API}/resume/${id}`, { method: 'DELETE' });
    if (res.ok) {
      const row = document.getElementById(`row-${id}`);
      if (row) {
        row.style.transition = 'opacity 0.3s, transform 0.3s';
        row.style.opacity = '0';
        row.style.transform = 'translateX(20px)';
        setTimeout(() => row.remove(), 300);
      }
      toast('Resume deleted');
      updateStats();
    }
  } catch (e) {
    toast('Error deleting resume');
  }
}

// ══════════════════════════════════════════════════════════════════════
// STATS BAR
// ══════════════════════════════════════════════════════════════════════
async function updateStats() {
  try {
    const res  = await fetch(`${API}/resumes`);
    const data = await res.json();
    const count = data.length;
    document.getElementById('stat-total-text').textContent =
      `${count} resume${count !== 1 ? 's' : ''}`;
  } catch {
    // silently fail
  }
}

// ══════════════════════════════════════════════════════════════════════
// UTILITIES
// ══════════════════════════════════════════════════════════════════════

/**
 * Animated number counter.
 * Smoothly counts from `start` to `end` over `duration` ms.
 */
function animateCounter(elementId, start, end, duration, suffix) {
  const el = document.getElementById(elementId);
  if (!el) return;

  const startTime = performance.now();
  const range = end - start;

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Ease-out curve
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = start + range * eased;

    el.textContent = `${current.toFixed(1)}${suffix || ''}`;

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }
  requestAnimationFrame(update);
}

/**
 * Append a log entry to a container.
 */
function addLog(msg, type, container) {
  const div = document.createElement('div');
  div.className = `log-entry log-${type}`;
  div.textContent = msg;
  container.appendChild(div);
  // Auto-scroll
  div.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Toast notification
 */
let toastTimer;
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 3500);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(str) {
  if (!str) return '';
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/**
 * Format file size to human-readable
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

/**
 * Format date string nicely
 */
function formatDate(dateStr) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  } catch {
    return dateStr ? dateStr.slice(0, 16) : '—';
  }
}

// ══════════════════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════════════════
updateStats();

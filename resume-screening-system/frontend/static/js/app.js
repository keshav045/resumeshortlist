/**
 * app.js
 * ------
 * Frontend logic for the AI Resume Screening Dashboard.
 * Uses vanilla JS + Fetch API — no frameworks needed.
 */

const API = "";   // empty = same origin as FastAPI server

// ── State ──────────────────────────────────────────────────────────────────────
let pendingFiles   = [];    // files queued for upload
let currentResumeId = null; // resume currently shown in match results

// ── Navigation ─────────────────────────────────────────────────────────────────
function showSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`sec-${name}`).classList.add('active');
  event.currentTarget.classList.add('active');

  // Lazy-load data when switching to a section
  if (name === 'match')    loadResumeSelect();
  if (name === 'database') loadAllResumes();
  if (name === 'rank')     loadTopStats();
}

// ── Theme Toggle ───────────────────────────────────────────────────────────────
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
}

// ── Upload: file selection & queue ─────────────────────────────────────────────
function handleFileSelect(event) {
  addToQueue([...event.target.files]);
}
function handleDrop(event) {
  event.preventDefault();
  document.getElementById('uploadZone').classList.remove('drag');
  const files = [...event.dataTransfer.files].filter(f => f.name.endsWith('.pdf'));
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
  const btn       = document.getElementById('uploadBtn');

  container.innerHTML = pendingFiles.map((f, i) => `
    <div class="queue-item">
      <span class="q-icon">📄</span>
      <span class="q-name">${f.name}</span>
      <span class="q-size">${(f.size / 1024).toFixed(0)} KB</span>
      <span class="q-remove" onclick="removeFromQueue(${i})" title="Remove">✕</span>
    </div>
  `).join('');

  btn.style.display = pendingFiles.length ? 'inline-block' : 'none';
}

function removeFromQueue(index) {
  pendingFiles.splice(index, 1);
  renderQueue();
}

// Upload all queued files one by one
async function uploadAll() {
  if (!pendingFiles.length) return;
  const log = document.getElementById('uploadLog');
  log.innerHTML = '';

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
}

// ── Job Description ─────────────────────────────────────────────────────────────
async function saveJD() {
  const title = document.getElementById('jdTitle').value;
  const text  = document.getElementById('jdText').value;
  const status = document.getElementById('jdStatus');

  const formData = new FormData();
  formData.append('title', title);
  formData.append('description', text);

  try {
    const res  = await fetch(`${API}/job-description`, { method: 'POST', body: formData });
    const data = await res.json();

    if (res.ok) {
      status.textContent = `✓ Saved "${data.title}" (${data.word_count} words)`;
      status.className   = 'status-msg ok';
      document.getElementById('stat-jd').textContent = `📋 ${data.title}`;
      toast('Job description saved');
    } else {
      status.textContent = `✗ ${data.detail}`;
      status.className   = 'status-msg err';
    }
  } catch (e) {
    status.textContent = '✗ Could not connect to server';
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
}

// ── Match: load dropdown & run analysis ───────────────────────────────────────
async function loadResumeSelect() {
  const sel = document.getElementById('matchSelect');
  try {
    const res  = await fetch(`${API}/resumes`);
    const data = await res.json();
    sel.innerHTML = data.length
      ? data.map(r => `<option value="${r.id}">${r.candidate_name} — ${r.filename}</option>`).join('')
      : `<option value="">No resumes uploaded yet</option>`;
  } catch (e) {
    sel.innerHTML = `<option>Error loading resumes</option>`;
  }
}

async function matchResume() {
  const id = document.getElementById('matchSelect').value;
  if (!id) { toast('No resume selected'); return; }

  const resultDiv = document.getElementById('matchResult');
  resultDiv.style.display = 'none';

  const formData = new FormData();
  formData.append('resume_id', id);

  try {
    const res  = await fetch(`${API}/match-resume`, { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) { toast(`Error: ${data.detail}`); return; }

    currentResumeId = id;
    renderMatchResult(data);
  } catch (e) {
    toast('Network error — is the server running?');
  }
}

function renderMatchResult(data) {
  const score = data.match_score;

  // Animate the SVG arc
  const circumference = 314;
  const offset = circumference - (score / 100) * circumference;
  document.getElementById('scoreArc').style.strokeDashoffset = offset;

  // Color the arc by score tier
  const arc = document.getElementById('scoreArc');
  if      (score >= 70) arc.style.stroke = '#4ade80';
  else if (score >= 40) arc.style.stroke = '#fbbf24';
  else                  arc.style.stroke = '#f87171';

  document.getElementById('scoreNumber').textContent    = `${score.toFixed(1)}%`;
  document.getElementById('scoreCandidate').textContent = `👤 ${data.candidate_name}`;
  document.getElementById('scoreJob').textContent       = `💼 ${data.job_title || 'Job Description'}`;

  let label = score >= 70 ? '🟢 Strong Match' : score >= 40 ? '🟡 Partial Match' : '🔴 Weak Match';
  document.getElementById('scoreLabel').textContent = label;

  // Skill clouds
  renderSkillCloud('matchingSkills', data.matching_skills, 'skill-match');
  renderSkillCloud('missingSkills',  data.missing_skills,  'skill-miss');
  renderSkillCloud('extraSkills',    data.extra_skills,    'skill-extra');

  document.getElementById('resumeSummary').textContent = data.summary || 'No summary available.';

  document.getElementById('matchResult').style.display = 'block';
  updateStats();
}

function renderSkillCloud(elementId, skills, cssClass) {
  const el = document.getElementById(elementId);
  if (!skills || skills.length === 0) {
    el.innerHTML = '<span class="skill-none">None identified</span>';
  } else {
    el.innerHTML = skills.map(s =>
      `<span class="skill-tag ${cssClass}">${s}</span>`
    ).join('');
  }
}

async function downloadReport() {
  if (!currentResumeId) return;
  window.open(`${API}/report/${currentResumeId}`, '_blank');
}

// ── Rankings ────────────────────────────────────────────────────────────────────
async function rankAll() {
  const container = document.getElementById('rankResults');
  container.innerHTML = '<div class="spinner"></div> Ranking all resumes…';

  try {
    const res  = await fetch(`${API}/rank-resumes`);
    const data = await res.json();

    if (!res.ok) { container.innerHTML = `<p style="color:var(--red)">${data.detail}</p>`; return; }
    if (!data.rankings.length) { container.innerHTML = '<p style="color:var(--text-2)">No resumes to rank yet.</p>'; return; }

    container.innerHTML = `
      <p style="color:var(--text-2);margin-bottom:16px;font-size:14px;">
        ${data.total_resumes} resumes ranked for <strong>${data.job_title}</strong>
      </p>
      <table class="rank-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Candidate</th>
            <th>File</th>
            <th>Score</th>
            <th>Match bar</th>
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
              <td>${r.candidate_name}</td>
              <td style="color:var(--text-2);font-size:13px;">${r.filename}</td>
              <td style="font-weight:700;color:${r.match_score>=70?'var(--green)':r.match_score>=40?'var(--amber)':'var(--red)'}">
                ${r.match_score.toFixed(1)}%
              </td>
              <td style="width:140px;">
                <div class="score-bar">
                  <div class="score-bar-fill" style="width:${r.match_score}%"></div>
                </div>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>`;

    document.getElementById('stat-top').textContent =
      `🏆 Best: ${data.rankings[0].match_score.toFixed(1)}%`;

    updateStats();
  } catch (e) {
    container.innerHTML = '<p style="color:var(--red)">Network error — is the server running?</p>';
  }
}

// ── All Resumes ─────────────────────────────────────────────────────────────────
async function loadAllResumes() {
  const container = document.getElementById('allResumes');
  container.innerHTML = '<div class="spinner"></div>';

  try {
    const res  = await fetch(`${API}/resumes`);
    const data = await res.json();

    if (!data.length) {
      container.innerHTML = '<p style="color:var(--text-2)">No resumes uploaded yet.</p>';
      return;
    }

    container.innerHTML = `
      <table class="rank-table">
        <thead>
          <tr>
            <th>ID</th><th>Candidate</th><th>File</th>
            <th>Score</th><th>Uploaded</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          ${data.map(r => `
            <tr id="row-${r.id}">
              <td style="color:var(--text-3)">#${r.id}</td>
              <td>${r.candidate_name}</td>
              <td style="color:var(--text-2);font-size:13px;">${r.filename}</td>
              <td style="font-weight:700">${r.match_score ? r.match_score.toFixed(1)+'%' : '—'}</td>
              <td style="color:var(--text-3);font-size:12px;">${r.uploaded_at?.slice(0,16) || '—'}</td>
              <td>
                <button class="btn btn-ghost" style="padding:4px 10px;font-size:12px;"
                  onclick="deleteResume(${r.id})">Delete</button>
              </td>
            </tr>
          `).join('')}
        </tbody>
      </table>`;
  } catch (e) {
    container.innerHTML = '<p style="color:var(--red)">Error loading resumes.</p>';
  }
}

async function deleteResume(id) {
  if (!confirm('Delete this resume?')) return;
  try {
    const res = await fetch(`${API}/resume/${id}`, { method: 'DELETE' });
    if (res.ok) {
      document.getElementById(`row-${id}`)?.remove();
      toast('Resume deleted');
      updateStats();
    }
  } catch (e) {
    toast('Error deleting resume');
  }
}

// ── Stats bar ───────────────────────────────────────────────────────────────────
async function updateStats() {
  try {
    const res  = await fetch(`${API}/resumes`);
    const data = await res.json();
    document.getElementById('stat-total').textContent = `📄 ${data.length} resume${data.length !== 1 ? 's' : ''}`;
  } catch {}
}

// ── Helpers ─────────────────────────────────────────────────────────────────────
function addLog(msg, type, container) {
  const div = document.createElement('div');
  div.className = `log-entry log-${type}`;
  div.textContent = msg;
  container.appendChild(div);
}

let toastTimer;
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 3000);
}

function loadTopStats() {}   // placeholder for future use

// ── Init ────────────────────────────────────────────────────────────────────────
updateStats();

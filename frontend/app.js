// TransPyC — Professional Frontend

// Auto-detect: use relative paths on production (Vercel), localhost in dev
const IS_DEV = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE   = IS_DEV ? 'http://localhost:5000' : '';
const API_URL    = API_BASE + '/api/convert';
const HEALTH_URL = API_BASE + '/api/health';

// ── State ──────────────────────────────────────────
let isConverting = false;
let currentLayout = 'side-by-side';
let currentTarget = 'cpp';
let currentTheme  = localStorage.getItem('transpyc-theme') || 'dark';
let isResizing    = false;

// ── DOM Refs ───────────────────────────────────────
const pythonInput    = document.getElementById('pythonInput');
const outputCode     = document.getElementById('outputCode');
const irOutput       = document.getElementById('irOutput');
const lineNumbers    = document.getElementById('lineNumbers');
const workspace      = document.getElementById('workspace');
const convertBtn     = document.getElementById('convertBtn');
const convertBtnText = document.getElementById('convertBtnText');
const convertBtnIcon = document.getElementById('convertBtnIcon');
const clearBtn       = document.getElementById('clearBtn');
const copyBtn        = document.getElementById('copyBtn');
const downloadBtn    = document.getElementById('downloadBtn');
const loadExampleBtn = document.getElementById('loadExampleBtn');
const outputTitle    = document.getElementById('outputTitle');
const outputLangDot  = document.getElementById('outputLangDot');
const outputPlaceholder = document.getElementById('outputPlaceholder');
const problemsList   = document.getElementById('problemsList');
const problemsEmpty  = document.getElementById('problemsEmpty');
const problemsBadge  = document.getElementById('problemsBadge');
const themeToggle    = document.getElementById('themeToggle');
const themeIcon      = document.getElementById('themeIcon');
const serverDot      = document.getElementById('serverDot');
const serverStatus   = document.getElementById('serverStatus');
const lineCount      = document.getElementById('lineCount');
const charCount      = document.getElementById('charCount');
const toastContainer = document.getElementById('toastContainer');
const resizeHandle   = document.getElementById('resizeHandle');
const inputPanel     = document.getElementById('inputPanel');
const outputPanel    = document.getElementById('outputPanel');

// ── Init ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  applyTheme(currentTheme);
  setupOutputTabs();
  setupTargetTabs();
  setupLayoutButtons();
  setupResizer();
  updateLineNumbers();
  updateStatusCounts();
  checkBackend();
  pythonInput.focus();
});

// ── Theme ──────────────────────────────────────────
function applyTheme(theme) {
  currentTheme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  // Dark = moon, Light = slightly lighter dark = use a contrast icon
  themeIcon.textContent = theme === 'dark' ? '🌙' : '💡';
  localStorage.setItem('transpyc-theme', theme);
}

themeToggle.addEventListener('click', () => {
  applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
});

// ── Target Tabs ────────────────────────────────────
function setupTargetTabs() {
  document.querySelectorAll('.target-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.target-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentTarget = tab.dataset.value;
      updateOutputLabel();
    });
  });
}

function updateOutputLabel() {
  const isCpp = currentTarget === 'cpp';
  outputTitle.textContent  = isCpp ? 'C++' : 'C';
  outputLangDot.className  = 'panel-lang-dot ' + (isCpp ? 'cpp-dot' : 'c-dot');
}

// ── Layout Buttons ─────────────────────────────────
function setupLayoutButtons() {
  const layouts = {
    layoutSideBySide: 'side-by-side',
    layoutStacked:     'stacked',
    layoutFocusInput:  'focus-input',
    layoutFocusOutput: 'focus-output',
  };

  Object.entries(layouts).forEach(([id, layout]) => {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.addEventListener('click', () => {
      document.querySelectorAll('.layout-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyLayout(layout);
    });
  });
}

function applyLayout(layout) {
  currentLayout = layout;
  workspace.className = 'workspace';
  if (layout === 'stacked')      workspace.classList.add('layout-stacked');
  if (layout === 'focus-input')  workspace.classList.add('layout-focus-input');
  if (layout === 'focus-output') workspace.classList.add('layout-focus-output');
  // Reset panel flex
  inputPanel.style.flex  = '';
  outputPanel.style.flex = '';
}

// ── Output Tabs ────────────────────────────────────
function setupOutputTabs() {
  document.querySelectorAll('.output-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.output-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    });
  });
}

function switchToTab(tabId) {
  document.querySelectorAll('.output-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  const tab = document.querySelector(`.output-tab[data-tab="${tabId}"]`);
  if (tab) tab.classList.add('active');
  const content = document.getElementById('tab-' + tabId);
  if (content) content.classList.add('active');
}

// ── Convert ────────────────────────────────────────
convertBtn.addEventListener('click', handleConvert);

pythonInput.addEventListener('keydown', e => {
  if (e.key === 'Tab') {
    e.preventDefault();
    const s = pythonInput.selectionStart, end = pythonInput.selectionEnd;
    pythonInput.value = pythonInput.value.slice(0, s) + '    ' + pythonInput.value.slice(end);
    pythonInput.selectionStart = pythonInput.selectionEnd = s + 4;
    updateLineNumbers();
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    handleConvert();
  }
});

async function handleConvert() {
  if (isConverting) return;

  const code = pythonInput.value;
  if (!code.trim()) {
    showToast('Write some Python code first', 'warning', '✏️');
    return;
  }

  setConverting(true);

  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, target: currentTarget }),
    });

    if (!res.ok) throw new Error(`Server responded with ${res.status}`);

    const result = await res.json();

    // Show code output
    outputCode.textContent = result.code || '';
    outputCode.classList.remove('hidden');
    outputPlaceholder.classList.add('hidden');

    // IR tree
    irOutput.textContent = JSON.stringify(result.ir, null, 2);

    // Problems
    renderProblems(result.warnings || []);

    const hasErrors   = (result.warnings || []).some(w => w.type === 'error');
    const hasWarnings = (result.warnings || []).some(w => w.type === 'warning');

    if (hasErrors) {
      switchToTab('problems');
      showToast('Converted with errors', 'error', '✕');
    } else if (hasWarnings) {
      showToast('Converted with warnings', 'warning', '⚠️');
    } else {
      switchToTab('code');
      showToast('Conversion successful', 'success', '✅');
    }

  } catch (err) {
    outputCode.textContent = `// Error\n// ${err.message}`;
    outputCode.classList.remove('hidden');
    outputPlaceholder.classList.add('hidden');
    renderProblems([{ type: 'error', message: err.message }]);
    switchToTab('problems');
    showToast(err.message, 'error', '✕');
  } finally {
    setConverting(false);
  }
}

function setConverting(val) {
  isConverting = val;
  convertBtn.disabled = val;
  convertBtnText.textContent = val ? 'Running…' : 'Run';
  convertBtnIcon.innerHTML = val
    ? '<span class="spin"></span>'
    : '▶';
}

// ── Problems Panel ─────────────────────────────────
const PROBLEM_META = {
  error:   { icon: '✕', label: 'Error' },
  warning: { icon: '⚠', label: 'Warning' },
  info:    { icon: 'i', label: 'Info' },
  success: { icon: '✓', label: 'OK' },
};

let currentProblems = [];
let activeProblemLine = null;

function renderProblems(warnings) {
  currentProblems = warnings || [];
  problemsList.innerHTML = '';

  if (!warnings || warnings.length === 0) {
    problemsEmpty.classList.remove('hidden');
    problemsList.classList.add('hidden');
    problemsBadge.style.display = 'none';
    return;
  }

  const errorCount = warnings.filter(w => w.type === 'error').length;
  problemsBadge.style.display = errorCount > 0 ? '' : 'none';
  problemsBadge.textContent = errorCount;

  problemsEmpty.classList.add('hidden');
  problemsList.classList.remove('hidden');

  warnings.forEach(w => {
    const meta = PROBLEM_META[w.type] || PROBLEM_META.info;
    const item = document.createElement('div');
    item.className = `problem-item ${w.type}`;
    item.innerHTML = `
      <div class="problem-icon">${meta.icon}</div>
      <div class="problem-body">
        <div class="problem-message">${escapeHtml(w.message)}</div>
        <div class="problem-meta">
          <span class="problem-type-tag">${meta.label}</span>
          ${w.line ? `<span class="problem-line">Line ${w.line}</span>` : ''}
        </div>
        ${w.hint ? `<div class="problem-hint">${escapeHtml(w.hint)}</div>` : ''}
      </div>`;
    if (w.line) {
      item.dataset.line = String(w.line);
      item.addEventListener('click', () => {
        goToLine(w.line);
      });
    }
    problemsList.appendChild(item);
  });

  // Re-render line numbers with problem markers
  updateLineNumbers();
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Clear ──────────────────────────────────────────
clearBtn.addEventListener('click', () => {
  pythonInput.value = '';
  outputCode.textContent = '';
  outputCode.classList.add('hidden');
  outputPlaceholder.classList.remove('hidden');
  irOutput.textContent = '';
  renderProblems([]);
  updateLineNumbers();
  updateStatusCounts();
  pythonInput.focus();
  showToast('Editor cleared', 'info', '🗑️');
});

// ── Copy ───────────────────────────────────────────
copyBtn.addEventListener('click', async () => {
  const text = outputCode.textContent;
  if (!text.trim()) { showToast('Nothing to copy yet', 'warning', '⚠️'); return; }
  try {
    await navigator.clipboard.writeText(text);
    showToast('Copied to clipboard', 'success', '📋');
  } catch {
    showToast('Copy failed', 'error', '✕');
  }
});

// ── Download ───────────────────────────────────────
downloadBtn.addEventListener('click', () => {
  const text = outputCode.textContent;
  if (!text.trim()) { showToast('Nothing to download yet', 'warning', '⚠️'); return; }
  const ext  = currentTarget === 'cpp' ? 'cpp' : 'c';
  const name = `transpyc_output.${ext}`;
  const blob = new Blob([text], { type: 'text/plain' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = name; a.click();
  URL.revokeObjectURL(url);
  showToast(`Downloaded ${name}`, 'success', '💾');
});

// ── Load Example ───────────────────────────────────
const EXAMPLE = `# TransPyC Example — Python to C/C++

def add(a, b):
    return a + b

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

# Main program
x = 10
y = 20
result = add(x, y)
print(result)

# Loop example
for i in range(5):
    print(i)

# Conditional
if x > y:
    print("x is greater")
elif x == y:
    print("equal")
else:
    print("y is greater")
`;

loadExampleBtn.addEventListener('click', () => {
  pythonInput.value = EXAMPLE;
  updateLineNumbers();
  updateStatusCounts();
  showToast('Example loaded', 'info', '📄');
});

// ── Line Numbers ───────────────────────────────────
pythonInput.addEventListener('input', () => {
  updateLineNumbers();
  updateStatusCounts();
});
pythonInput.addEventListener('scroll', () => {
  lineNumbers.scrollTop = pythonInput.scrollTop;
});

function updateLineNumbers() {
  const lines = pythonInput.value.split('\n').length;
  const errorLines = new Set(
    (currentProblems || [])
      .filter(w => w.type === 'error' && typeof w.line === 'number')
      .map(w => w.line)
  );
  const warningLines = new Set(
    (currentProblems || [])
      .filter(w => w.type === 'warning' && typeof w.line === 'number')
      .map(w => w.line)
  );

  let html = '';
  for (let i = 1; i <= lines; i++) {
    let cls = 'line-number';
    if (errorLines.has(i)) cls += ' error';
    else if (warningLines.has(i)) cls += ' warning';
    if (activeProblemLine === i) cls += ' active';
    html += `<div class="${cls}" data-line="${i}">${i}</div>`;
  }
  lineNumbers.innerHTML = html;
  lineNumbers.scrollTop = pythonInput.scrollTop;
}

function goToLine(line) {
  const n = Math.max(1, Number(line) || 1);
  const lines = pythonInput.value.split('\n');
  let pos = 0;
  for (let i = 0; i < n - 1 && i < lines.length; i++) {
    pos += lines[i].length + 1; // +1 for the newline
  }
  pythonInput.focus();
  pythonInput.selectionStart = pythonInput.selectionEnd = pos;

  // Scroll so the target line is roughly in the middle
  const totalLines = lines.length;
  const ratio = (n - 1) / Math.max(totalLines - 1, 1);
  const maxScroll = pythonInput.scrollHeight - pythonInput.clientHeight;
  pythonInput.scrollTop = ratio * maxScroll;
  lineNumbers.scrollTop = pythonInput.scrollTop;

  activeProblemLine = n;
  updateLineNumbers();
}

function updateStatusCounts() {
  const val = pythonInput.value;
  lineCount.textContent = val.split('\n').length + ' lines';
  charCount.textContent = val.length + ' chars';
}

// ── Backend Health ─────────────────────────────────
async function checkBackend() {
  setServerStatus('connecting');
  try {
    const res = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(3000) });
    if (res.ok) setServerStatus('online');
    else        setServerStatus('offline');
  } catch {
    setServerStatus('offline');
  }
  // Re-check every 15s
  setTimeout(checkBackend, 15000);
}

function setServerStatus(status) {
  serverDot.className = 'status-dot ' + status;
  const labels = {
    online: 'Server connected',
    offline: 'Server offline — run: python backend/app.py',
    connecting: 'Connecting…',
  };
  serverStatus.textContent = labels[status] || status;
}

// ── Resizable Panels ───────────────────────────────
function setupResizer() {
  resizeHandle.addEventListener('mousedown', e => {
    isResizing = true;
    resizeHandle.classList.add('dragging');
    document.body.style.cursor = currentLayout === 'stacked' ? 'row-resize' : 'col-resize';
    document.body.style.userSelect = 'none';

    const startX = e.clientX, startY = e.clientY;
    const startInputW = inputPanel.getBoundingClientRect().width;
    const startInputH = inputPanel.getBoundingClientRect().height;
    const totalW = workspace.getBoundingClientRect().width;
    const totalH = workspace.getBoundingClientRect().height;

    function onMove(e) {
      if (!isResizing) return;
      if (currentLayout === 'stacked') {
        const delta = e.clientY - startY;
        const newH  = Math.min(Math.max(startInputH + delta, 100), totalH - 100);
        inputPanel.style.flex  = `0 0 ${newH}px`;
        outputPanel.style.flex = `0 0 ${totalH - newH - 5}px`;
      } else {
        const delta = e.clientX - startX;
        const newW  = Math.min(Math.max(startInputW + delta, 150), totalW - 150);
        inputPanel.style.flex  = `0 0 ${newW}px`;
        outputPanel.style.flex = `0 0 ${totalW - newW - 5}px`;
      }
    }

    function onUp() {
      isResizing = false;
      resizeHandle.classList.remove('dragging');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    }

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  });
}

// ── Toast ──────────────────────────────────────────
function showToast(message, type = 'success', icon = '') {
  const icons = { success: '✅', error: '✕', warning: '⚠️', info: 'ℹ️' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span class="toast-icon">${icon || icons[type]}</span><span class="toast-body">${escapeHtml(message)}</span>`;
  toastContainer.appendChild(t);

  setTimeout(() => {
    t.classList.add('removing');
    setTimeout(() => t.remove(), 220);
  }, 3000);
}

// ── Mobile Bottom Bar ──────────────────────────────
(function setupMobile() {
  const mobileRunBtn      = document.getElementById('mobileRunBtn');
  const mobilePanelInput  = document.getElementById('mobilePanelInput');
  const mobilePanelOutput = document.getElementById('mobilePanelOutput');
  const mobileTargetC     = document.getElementById('mobileTargetC');
  const mobileTargetCpp   = document.getElementById('mobileTargetCpp');

  // Mobile Run button
  if (mobileRunBtn) {
    mobileRunBtn.addEventListener('click', handleConvert);
  }

  // Mobile panel toggle (Input / Output)
  function setMobilePanel(panel) {
    workspace.classList.remove('mobile-show-input', 'mobile-show-output');
    workspace.classList.add('mobile-show-' + panel);
    mobilePanelInput.classList.toggle('active',  panel === 'input');
    mobilePanelOutput.classList.toggle('active', panel === 'output');
  }

  if (mobilePanelInput)  mobilePanelInput.addEventListener('click',  () => setMobilePanel('input'));
  if (mobilePanelOutput) mobilePanelOutput.addEventListener('click', () => {
    setMobilePanel('output');
    // Auto-switch to code tab if there's output
    if (outputCode.textContent.trim()) switchToTab('code');
  });

  // Mobile target tabs (mirrors header tabs)
  function syncMobileTarget(val) {
    currentTarget = val;
    // Sync header target tabs
    document.querySelectorAll('.target-tab').forEach(t => {
      t.classList.toggle('active', t.dataset.value === val);
    });
    updateOutputLabel();
  }

  if (mobileTargetC)   mobileTargetC.addEventListener('click',   () => syncMobileTarget('c'));
  if (mobileTargetCpp) mobileTargetCpp.addEventListener('click', () => syncMobileTarget('cpp'));

  // Keep mobile target in sync when header tabs are clicked
  document.querySelectorAll('.header-right .target-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      if (mobileTargetC)   mobileTargetC.classList.toggle('active',   tab.dataset.value === 'c');
      if (mobileTargetCpp) mobileTargetCpp.classList.toggle('active', tab.dataset.value === 'cpp');
    });
  });

  // On mobile, after a successful conversion auto-switch panel to output
  const _origConvert = handleConvert;
  // Patch: listen for output content changes → switch panel
  const observer = new MutationObserver(() => {
    if (window.innerWidth <= 480 && !outputCode.classList.contains('hidden')) {
      setMobilePanel('output');
    }
  });
  observer.observe(outputCode, { characterData: true, childList: true, subtree: true });

  // Init: default mobile panel
  if (window.innerWidth <= 480) {
    setMobilePanel('input');
  }

  // On resize crossing 480px threshold, reset state
  window.addEventListener('resize', () => {
    if (window.innerWidth > 480) {
      workspace.classList.remove('mobile-show-input', 'mobile-show-output');
    } else if (!workspace.classList.contains('mobile-show-input') &&
               !workspace.classList.contains('mobile-show-output')) {
      setMobilePanel('input');
    }
  });
})();


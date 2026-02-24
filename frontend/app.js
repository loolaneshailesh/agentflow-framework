/* AgentFlow Framework Dashboard - Application Logic */

const API_BASE = 'http://localhost:8000/api';

// ---- Utility Functions ----------------------------------------

function log(msg, type = 'info') {
  const logEl = document.getElementById('activity-log');
  if (!logEl) return;
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  entry.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
  logEl.prepend(entry);
  if (logEl.children.length > 50) logEl.lastChild.remove();
}

async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

// ---- Tab Navigation -------------------------------------------

function initTabs() {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${tabId}`)?.classList.add('active');
      if (tabId === 'tools') loadTools();
      if (tabId === 'approvals') loadApprovals();
      if (tabId === 'workflows') loadWorkflows();
    });
  });
}

// ---- Health Check ---------------------------------------------

async function checkHealth() {
  const statusEl = document.getElementById('health-status');
  try {
    const data = await apiFetch('/health/detail');
    statusEl.innerHTML = `<span class="dot connected"></span> Connected`;
    document.querySelector('#stat-model .stat-value').textContent = data.active_model || '-';
    document.querySelector('#stat-provider .stat-value').textContent = data.provider || '-';
    document.querySelector('#stat-tools .stat-value').textContent = (data.registered_tools || []).length;
    document.querySelector('#stat-agents .stat-value').textContent = (data.registered_agents || []).length;
    log(`Health OK - Model: ${data.active_model}, Provider: ${data.provider}`, 'success');
  } catch (e) {
    statusEl.innerHTML = `<span class="dot error"></span> Offline`;
    log(`Health check failed: ${e.message}`, 'error');
  }
}

// ---- Run Agent ------------------------------------------------

function initRunAgent() {
  const runBtn = document.getElementById('run-btn');
  const clearBtn = document.getElementById('clear-btn');

  runBtn?.addEventListener('click', async () => {
    const task = document.getElementById('task-input').value.trim();
    if (!task) return alert('Please enter a task.');
    let context = {};
    try { context = JSON.parse(document.getElementById('context-input').value || '{}'); }
    catch { return alert('Invalid JSON in context field.'); }

    runBtn.disabled = true;
    runBtn.innerHTML = '<span class="spinner"></span> Running...';
    log(`Running agent task: ${task.substring(0, 60)}...`);

    const start = Date.now();
    try {
      const data = await apiFetch('/agents/run', {
        method: 'POST',
        body: JSON.stringify({ task, context }),
      });
      const elapsed = ((Date.now() - start) / 1000).toFixed(1);
      document.getElementById('result-card').style.display = 'block';
      document.getElementById('result-agent').textContent = `Agent: ${data.agent}`;
      document.getElementById('result-time').textContent = `Time: ${elapsed}s`;
      document.getElementById('result-output').textContent = data.result;
      log(`Agent completed in ${elapsed}s`, 'success');
    } catch (e) {
      log(`Agent error: ${e.message}`, 'error');
      alert(`Error: ${e.message}`);
    } finally {
      runBtn.disabled = false;
      runBtn.textContent = 'Run Agent';
    }
  });

  clearBtn?.addEventListener('click', () => {
    document.getElementById('task-input').value = '';
    document.getElementById('context-input').value = '{}';
    document.getElementById('result-card').style.display = 'none';
  });
}

// ---- Workflows ------------------------------------------------

async function loadWorkflows() {
  try {
    const data = await apiFetch('/workflows/');
    const select = document.getElementById('workflow-select');
    select.innerHTML = (data.workflows || ['finance_ap'])
      .map(w => `<option value="${w}">${w}</option>`).join('');
  } catch (e) {
    log(`Workflow load error: ${e.message}`, 'error');
  }
}

function initWorkflows() {
  document.getElementById('run-workflow-btn')?.addEventListener('click', async () => {
    const name = document.getElementById('workflow-select').value;
    let inputs = {};
    try { inputs = JSON.parse(document.getElementById('workflow-inputs').value || '{}'); }
    catch { return alert('Invalid JSON in inputs field.'); }

    const btn = document.getElementById('run-workflow-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Running...';
    log(`Executing workflow: ${name}`);

    try {
      const data = await apiFetch('/workflows/run', {
        method: 'POST',
        body: JSON.stringify({ workflow_name: name, inputs }),
      });
      document.getElementById('workflow-result-card').style.display = 'block';
      document.getElementById('workflow-result-output').textContent =
        JSON.stringify(data.result, null, 2);
      log(`Workflow '${name}' completed`, 'success');
    } catch (e) {
      log(`Workflow error: ${e.message}`, 'error');
      alert(`Error: ${e.message}`);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Execute Workflow';
    }
  });
}

// ---- Tools ----------------------------------------------------

async function loadTools() {
  const grid = document.getElementById('tools-grid');
  try {
    const data = await apiFetch('/tools/');
    if (!data.tools?.length) {
      grid.textContent = 'No tools registered.';
      return;
    }
    grid.innerHTML = data.tools.map(t => `
      <div class="tool-card">
        <div class="tool-name">${t.name}</div>
        <div class="tool-desc">${t.description || 'No description'}</div>
      </div>
    `).join('');
  } catch (e) {
    grid.textContent = `Error: ${e.message}`;
  }
}

function initTools() {
  document.getElementById('execute-tool-btn')?.addEventListener('click', async () => {
    const name = document.getElementById('tool-name-input').value.trim();
    if (!name) return alert('Enter a tool name.');
    let args = {};
    try { args = JSON.parse(document.getElementById('tool-args-input').value || '{}'); }
    catch { return alert('Invalid JSON in arguments.'); }

    const resultEl = document.getElementById('tool-result');
    resultEl.style.display = 'block';
    resultEl.textContent = 'Executing...';
    try {
      const data = await apiFetch('/tools/execute', {
        method: 'POST',
        body: JSON.stringify({ tool_name: name, arguments: args }),
      });
      resultEl.textContent = JSON.stringify(data.result, null, 2);
      log(`Tool '${name}' executed`, 'success');
    } catch (e) {
      resultEl.textContent = `Error: ${e.message}`;
      log(`Tool error: ${e.message}`, 'error');
    }
  });
}

// ---- Approvals ------------------------------------------------

async function loadApprovals() {
  const listEl = document.getElementById('approvals-list');
  try {
    const data = await apiFetch('/approvals/pending');
    if (!data.approvals?.length) {
      listEl.innerHTML = '<p style="color:var(--text-muted)">No pending approvals.</p>';
      return;
    }
    listEl.innerHTML = data.approvals.map(a => `
      <div class="approval-card">
        <div class="approval-meta">
          Agent: <strong>${a.agent_name}</strong> &bull;
          Created: ${new Date(a.created_at).toLocaleString()}
          <span class="badge badge-warning" style="margin-left:0.5rem">PENDING</span>
        </div>
        <div class="approval-action">Action: ${a.action}</div>
        <div style="font-size:0.8rem;color:var(--text-muted)">
          ${JSON.stringify(a.payload, null, 2)}
        </div>
        <div class="approval-actions">
          <button class="btn btn-success" onclick="resolveApproval('${a.id}', 'approve')">Approve</button>
          <button class="btn btn-danger" onclick="resolveApproval('${a.id}', 'reject')">Reject</button>
        </div>
      </div>
    `).join('');
  } catch (e) {
    listEl.textContent = `Error: ${e.message}`;
  }
}

async function resolveApproval(id, decision) {
  const path = decision === 'approve' ? `/approvals/${id}/approve` : `/approvals/${id}/reject`;
  try {
    await apiFetch(path, { method: 'POST', body: JSON.stringify({ comment: '' }) });
    log(`Approval ${id} ${decision}d`, 'success');
    loadApprovals();
  } catch (e) {
    log(`Approval error: ${e.message}`, 'error');
  }
}

function initApprovals() {
  document.getElementById('refresh-approvals-btn')?.addEventListener('click', loadApprovals);
}

// ---- Init -----------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initRunAgent();
  initWorkflows();
  initTools();
  initApprovals();
  checkHealth();
  // Auto-refresh health every 30 seconds
  setInterval(checkHealth, 30000);
  log('AgentFlow Dashboard initialized', 'success');
});

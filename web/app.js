async function api(path, options = {}) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await resp.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = text; }
  if (!resp.ok) {
    const detail = body && body.detail ? body.detail : text;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}

function progressLabel(p) {
  if (!p) return "—";
  const pct = p.percent == null ? "?" : `${p.percent}%`;
  const files = (p.files_processed != null && p.files_total != null)
    ? `${p.files_processed}/${p.files_total}`
    : "—";
  const stage = p.current_stage || "—";
  return `${pct} · ${files} · ${stage}`;
}

async function loadRepos() {
  const data = await api("/api/repos");
  const tbody = document.querySelector("#repos-table tbody");
  tbody.innerHTML = "";
  for (const repo of data.repos) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="checkbox" data-id="${repo.id}" /></td>
      <td><button type="button" class="linkish" data-detail="${repo.id}">${repo.repo_identifier}</button></td>
      <td>${repo.origin}</td>
      <td>${repo.state_label}</td>
      <td>${progressLabel(repo.progress)}</td>
    `;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll("[data-detail]").forEach((btn) => {
    btn.addEventListener("click", () => showDetail(Number(btn.dataset.detail)));
  });
}

async function showDetail(id) {
  const detail = await api(`/api/repos/${id}`);
  const executions = await api(`/api/repos/${id}/executions`);
  const files = (detail.files || [])
    .map((f) => `${f.path}: zoekt=${f.zoekt} tree_sitter=${f.tree_sitter} metadata=${f.metadata_persisted}`)
    .join("\n");
  const history = (executions.executions || [])
    .map((e) => `${e.status} @ ${e.error_at || e.started_at}: ${e.error_message || "ok"}`)
    .join("\n");
  document.getElementById("repo-detail").textContent =
    `Detalhe #${id} (${detail.state_label})\nArquivos:\n${files || "(nenhum)"}\nHistórico:\n${history || "(vazio)"}`;
}

async function indexSelected() {
  const ids = [...document.querySelectorAll("#repos-table input[type=checkbox]:checked")]
    .map((el) => Number(el.dataset.id));
  if (!ids.length) {
    alert("Selecione ao menos um repositório.");
    return;
  }
  await api("/api/repos/index", { method: "POST", body: JSON.stringify({ repository_ids: ids }) });
  await loadRepos();
}

async function loadCron() {
  const data = await api("/api/scheduler/cron");
  document.getElementById("cron-input").value = data.cron;
  document.getElementById("cron-status").textContent = `Ativo: ${data.cron}`;
}

async function saveCron(event) {
  event.preventDefault();
  const cron = document.getElementById("cron-input").value.trim();
  try {
    const data = await api("/api/scheduler/cron", {
      method: "PUT",
      body: JSON.stringify({ cron }),
    });
    document.getElementById("cron-status").textContent = `Salvo: ${data.cron}`;
  } catch (err) {
    document.getElementById("cron-status").textContent = `Erro: ${err.message}`;
  }
}

async function searchExact(event) {
  event.preventDefault();
  const pattern = document.getElementById("exact-pattern").value.trim();
  const data = await api("/api/search/exact", {
    method: "POST",
    body: JSON.stringify({ pattern }),
  });
  document.getElementById("search-results").textContent = JSON.stringify(data.hits, null, 2);
}

async function searchSemantic(event) {
  event.preventDefault();
  const query = document.getElementById("semantic-query").value.trim();
  const reformulate = document.getElementById("semantic-reformulate").checked;
  const data = await api("/api/search/semantic", {
    method: "POST",
    body: JSON.stringify({ query, reformulate }),
  });
  document.getElementById("search-results").textContent = JSON.stringify(data.hits, null, 2);
}

document.getElementById("btn-refresh").addEventListener("click", loadRepos);
document.getElementById("btn-index").addEventListener("click", indexSelected);
document.getElementById("cron-form").addEventListener("submit", saveCron);
document.getElementById("exact-form").addEventListener("submit", searchExact);
document.getElementById("semantic-form").addEventListener("submit", searchSemantic);

loadRepos().catch(console.error);
loadCron().catch(console.error);

// Shared helpers for the IR Tabletop Exercise Platform.
// Loaded as a classic script via <script src="/static/lib.js"></script>.
// lit-html is exposed on window by each page's module script.

// lit-html wrappers (resolved at call time).
window.btHtml = function (strings, ...values) {
  return window.litHtml(strings, ...values);
};
window.btRender = function (tpl, container) {
  return window.litRender(tpl, container);
};
window.btRepeat = function (items, key, fn) {
  return window.litRepeat(items, key, fn);
};

// API helper.
window.btApi = async function (path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
};

// Date helper.
window.btFmtDate = function (iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
};

// Read the exercise ID from window.location.hash (#<uuid>).
window.btExerciseIdFromHash = function () {
  const id = (window.location.hash || '').replace(/^#/, '').trim();
  return id || null;
};

// Active-timer formatter (mm:ss or hh:mm:ss).
window.btFormatDuration = function (seconds) {
  seconds = Math.max(0, Math.floor(seconds));
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const pad = (n) => n.toString().padStart(2, '0');
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
};

// Slide ID helpers — mirror api/routes/exercises.py:_compute_deck / _parse_slide_id.
window.btComputeDeck = function (modules) {
  const deck = ['ground_rules'];
  (modules || []).forEach((m, mIdx) => {
    deck.push(`module:${mIdx}`);
    const injects = (m.injects || []).slice().sort(
      (a, b) => (a.sequence || 0) - (b.sequence || 0)
    );
    injects.forEach((inj) => deck.push(`inject:${mIdx}:${inj.sequence}`));
  });
  deck.push('hotwash');
  return deck;
};

window.btParseSlideId = function (slideId) {
  if (slideId === 'ground_rules' || slideId === 'hotwash') {
    return { kind: slideId, module_idx: null, sequence: null };
  }
  const parts = (slideId || '').split(':');
  if (parts[0] === 'module' && parts.length === 2) {
    return { kind: 'module', module_idx: parseInt(parts[1], 10), sequence: null };
  }
  if (parts[0] === 'inject' && parts.length === 3) {
    return {
      kind: 'inject',
      module_idx: parseInt(parts[1], 10),
      sequence: parseInt(parts[2], 10),
    };
  }
  return { kind: 'unknown', module_idx: null, sequence: null };
};

// Locate the inject object in modules JSON by (module_idx, sequence).
window.btFindInject = function (modules, moduleIdx, sequence) {
  const mod = (modules || [])[moduleIdx];
  if (!mod) return null;
  return (mod.injects || []).find((i) => i.sequence === sequence) || null;
};

// Human-readable deck position label, e.g. "Module 1 · Inject 3 of 4" or "Ground rules".
window.btSlideLabel = function (slideId, exercise) {
  const modules = exercise.modules || [];
  const parsed = window.btParseSlideId(slideId);
  if (parsed.kind === 'ground_rules') return 'Ground rules';
  if (parsed.kind === 'hotwash') return 'Hotwash';
  if (parsed.kind === 'module') {
    const m = modules[parsed.module_idx] || {};
    return `Module ${m.number != null ? m.number : parsed.module_idx + 1}`;
  }
  if (parsed.kind === 'inject') {
    const m = modules[parsed.module_idx] || {};
    const total = (m.injects || []).length;
    const sortedSeqs = (m.injects || [])
      .slice().sort((a, b) => (a.sequence || 0) - (b.sequence || 0))
      .map((i) => i.sequence);
    const pos = sortedSeqs.indexOf(parsed.sequence) + 1;
    return `Module ${m.number != null ? m.number : parsed.module_idx + 1} · Inject ${pos} of ${total}`;
  }
  return slideId || '';
};

// Renders a slide for the current exercise state. Returns a lit-html template.
// mode: 'fullscreen' (presenter window) or 'mirror' (facilitator window).
//
// Caller must supply window.litHtml; this function reads it lazily via btHtml.
window.btRenderSlide = function (exercise) {
  const html = window.btHtml;
  const slideId = exercise.current_slide;
  if (!slideId) {
    return html`<div class="slide-empty">Waiting for facilitator to launch the exercise…</div>`;
  }
  const parsed = window.btParseSlideId(slideId);
  if (parsed.kind === 'ground_rules') return renderGroundRules(exercise);
  if (parsed.kind === 'module') return renderModule(exercise, parsed.module_idx);
  if (parsed.kind === 'inject') return renderInject(exercise, parsed.module_idx, parsed.sequence);
  if (parsed.kind === 'hotwash') return renderHotwash(exercise);
  return html`<div class="slide-empty">Unknown slide: ${slideId}</div>`;
};

function renderGroundRules(exercise) {
  const html = window.btHtml;
  const guidelines = (exercise.exercise_guidelines || []).filter((g) => typeof g === 'string' && g.trim());
  return html`
    <section class="slide slide-ground-rules">
      <div class="slide-meta">Ground rules</div>
      <h1 class="slide-title">Before we begin</h1>
      ${guidelines.length
        ? html`<ul class="rule-list">${guidelines.map((g) => html`<li>${g}</li>`)}</ul>`
        : html`<p class="slide-summary">No exercise guidelines were defined for this scenario.</p>`}
    </section>`;
}

function renderModule(exercise, moduleIdx) {
  const html = window.btHtml;
  const m = (exercise.modules || [])[moduleIdx] || {};
  const num = m.number != null ? m.number : moduleIdx + 1;
  return html`
    <section class="slide slide-module">
      <div class="slide-meta">Module ${num}${m.duration_minutes ? ` · ${m.duration_minutes} min` : ''}</div>
      <h1 class="slide-title">${m.title || ''}</h1>
      ${m.summary ? html`<p class="slide-summary">${m.summary}</p>` : ''}
    </section>`;
}

function renderInject(exercise, moduleIdx, sequence) {
  const html = window.btHtml;
  const m = (exercise.modules || [])[moduleIdx] || {};
  const inj = window.btFindInject(exercise.modules, moduleIdx, sequence);
  if (!inj) return html`<div class="slide-empty">Inject ${moduleIdx}:${sequence} not found</div>`;
  const num = m.number != null ? m.number : moduleIdx + 1;
  const questions = inj.discussion_questions || [];
  const revealed = inj.revealed_questions || [];
  return html`
    <section class="slide slide-inject">
      <div class="slide-meta">
        Module ${num} · Inject ${sequence}${inj.day_or_time ? ` · ${inj.day_or_time}` : ''}
      </div>
      <h1 class="slide-title">${inj.title || ''}</h1>
      ${inj.narrative ? html`<p class="slide-narrative">${inj.narrative}</p>` : ''}
      ${(inj.indicators || []).length ? html`
        <div class="slide-indicators">
          <div class="slide-indicators-label">Indicators</div>
          <ul>${(inj.indicators || []).map((ind) => html`<li>${ind}</li>`)}</ul>
        </div>` : ''}
      ${revealed.length ? html`
        <div class="slide-questions">
          ${revealed.map((qIdx, i) => {
            const q = questions[qIdx];
            if (!q) return '';
            return html`
              <div class="slide-question">
                <div class="slide-question-meta">${q.category || ''}</div>
                <div class="slide-question-text">${q.question || ''}</div>
              </div>`;
          })}
        </div>` : ''}
    </section>`;
}

function renderHotwash(exercise) {
  const html = window.btHtml;
  const hw = exercise.hotwash || {};
  const qs = hw.guiding_questions || [];
  return html`
    <section class="slide slide-hotwash">
      <div class="slide-meta">Hotwash${hw.duration_minutes ? ` · ${hw.duration_minutes} min` : ''}</div>
      <h1 class="slide-title">Live debrief</h1>
      ${hw.purpose ? html`<p class="slide-summary">${hw.purpose}</p>` : ''}
      <ol class="hotwash-list">${qs.map((q) => html`<li>${q}</li>`)}</ol>
    </section>`;
}

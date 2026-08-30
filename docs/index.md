---
hide:
  - navigation
  - toc
---

# esimu

<section class="esimu-hero">
  <div>
    <p class="eyebrow">theme-driven simulator framework</p>
    <h1>Build a campus, career, or life simulator from a theme pack.</h1>
    <p class="hero-copy">
      esimu combines reusable gameplay rules, runtime orchestration, world-data
      contracts, optional AI, and a complete Starter while keeping each game’s
      story, nouns, balance, events, items, and prompts in its own theme pack.
    </p>
    <p class="hero-actions">
      <a href="quickstart/" class="hero-button primary">Quickstart</a>
      <a href="new-project-bootstrap/" class="hero-button">Create a project</a>
      <a href="framework-readiness-review/" class="hero-button">Readiness review</a>
    </p>
  </div>
</section>

<div class="home-body" markdown="1">

<h2>Current Verdict</h2>

<p>
  esimu is a <strong>public Beta framework for single-theme narrative
  simulators</strong>.
</p>

<p>The recommended shape is:</p>

<pre><code>esimu-core + starter app + theme pack</code></pre>

<p>
  Published projects should pin an exact Beta. <code>0.3.0b2</code> is the
  current public package, with the closed runtime loop and installed authoring
  commands. <code>0.4.0b2</code> is the source candidate adding lifecycle
  commands and the ZJU simplified default template.
</p>

<h2>What You Get</h2>

<div class="feature-grid">
  <article>
    <h3>esimu-core</h3>
    <p>
      Pure Python package for world loaders, stat/item contracts, declarative
      achievements, semester settlement, runtime scheduling, optional AI,
      lifecycle helpers, and safe project authoring.
    </p>
  </article>
  <article>
    <h3>Starter App</h3>
    <p>
      A FastAPI/WebSocket backend plus Vue 3/Pinia console, using SQLite,
      versioned state/protocol contracts, and the self-contained
      zju-simplified theme by default.
    </p>
  </article>
  <article>
    <h3>Theme Pack</h3>
    <p>
      One directory owns the game’s visible language, story, prompts, stats,
      balance, items, courses, characters, events, achievements, and assets.
    </p>
  </article>
</div>

<h2>Fast Path</h2>

<p>Generate a new project:</p>

<pre><code class="language-powershell">
esimu new <target-project> --project-name "My Simulator" --theme-id my-simulator
</code></pre>

<p>Validate its theme:</p>

<pre><code class="language-powershell">
esimu validate --root <target-project> --theme my-simulator
esimu doctor --root <target-project> --theme my-simulator
esimu inspect --root <target-project> --theme my-simulator
esimu sync --root <target-project> --theme my-simulator
esimu dev --root <target-project> --theme my-simulator
esimu reload --root <target-project> --theme my-simulator
esimu build --root <target-project> --theme my-simulator
</code></pre>

<p>
  Then edit <code>themes/&lt;theme_id&gt;/theme.json</code>,
  <code>story.json</code>, <code>prompts.json</code>, and <code>world/</code>.
</p>

<h2>Architecture At A Glance</h2>

<pre><code>
themes/<theme_id>/
  theme.json          # visible terms and storage prefix
  story.json          # prologue and ending writing
  prompts.json        # model-facing context
  world/              # stats, balance, items, courses, events, achievements

packages/esimu-core/esimu_core/
  world/              # loaders and validators
  domain/             # pure gameplay rules
  runtime/            # tick/snapshot/action/task helpers
  lifecycle/          # setup and transition payload helpers
  content/            # event/forum/messenger payload contracts
  ai/                 # optional model transport and degradation
  authoring.py        # doctor/inspect/sync/add operations

apps/starter/
  backend/            # minimal adapter
  frontend/           # minimal frontend skin
</code></pre>

<h2>Start Reading</h2>

<ul>
  <li><a href="quickstart/">Quickstart</a>: local validation and smoke commands.</li>
  <li><a href="cli/">CLI reference</a>: project, diagnostics, sync, and safe authoring commands.</li>
  <li><a href="new-project-bootstrap/">Bootstrap a project</a>: generate and customize a new simulator.</li>
  <li><a href="theme-pack-contract/">Theme pack contract</a>: required files and field rules.</li>
  <li><a href="architecture/">Architecture</a>: current core/theme/adapter boundary.</li>
  <li><a href="framework-readiness-review/">Framework readiness review</a>: current Beta verdict and remaining gates.</li>
</ul>

</div>

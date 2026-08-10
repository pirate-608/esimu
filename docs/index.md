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
      esimu extracts the reusable rules, runtime helpers, world-data contracts,
      and starter app shape behind ZJUers Simulator, while keeping each game’s
      story, nouns, balance, events, items, and prompts in a theme.
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
  esimu is a <strong>basically complete alpha framework for single-theme
  simulator prototypes</strong>.
</p>

<p>The recommended shape is:</p>

<pre><code>esimu-core + starter app + theme pack</code></pre>

<p>
  It is not yet a stable public framework. Keep using Git-tagged
  <code>esimu-core</code> versions until starter frontend packaging, optional
  persistence adapters, and real external-project feedback are proven.
</p>

<h2>What You Get</h2>

<div class="feature-grid">
  <article>
    <h3>esimu-core</h3>
    <p>
      Pure Python package for world loaders, stat/item contracts, semester
      settlement, runtime snapshots, action gates, lifecycle helpers, and
      content normalization.
    </p>
  </article>
  <article>
    <h3>Starter App</h3>
    <p>
      A small FastAPI/WebSocket backend plus Vite/TypeScript frontend skin,
      using in-memory sessions and the demo-campus theme by default.
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
cd esimu-lab\simulator-core\backend
python scripts\new_project.py <target-project> --project-name "My Simulator" --theme-id my-simulator
</code></pre>

<p>Validate its theme:</p>

<pre><code class="language-powershell">
$env:SIMULATOR_LAB_ROOT='<target-project>'
$env:SIMULATOR_THEME='my-simulator'
python scripts\validate_world_data.py
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

simulator-core/backend/esimu_core/
  world/              # loaders and validators
  domain/             # pure gameplay rules
  runtime/            # tick/snapshot/action/task helpers
  lifecycle/          # setup and transition payload helpers
  content/            # event/forum/messenger payload contracts

apps/starter/
  backend/            # minimal adapter
  frontend/           # minimal frontend skin
</code></pre>

<h2>Start Reading</h2>

<ul>
  <li><a href="quickstart/">Quickstart</a>: local validation and smoke commands.</li>
  <li><a href="new-project-bootstrap/">Bootstrap a project</a>: generate and customize a new simulator.</li>
  <li><a href="theme-pack-contract/">Theme pack contract</a>: required files and field rules.</li>
  <li><a href="architecture/">Architecture</a>: current core/theme/adapter boundary.</li>
  <li><a href="framework-readiness-review/">Framework readiness review</a>: Phase 9 verdict and gaps.</li>
</ul>

</div>

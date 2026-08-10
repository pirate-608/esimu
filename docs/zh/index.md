---
hide:
  - navigation
  - toc
---

# esimu

<section class="esimu-hero">
  <div>
    <p class="eyebrow">主题驱动的模拟器框架</p>
    <h1>用一个主题包，启动一款校园、职业或人生模拟器。</h1>
    <p class="hero-copy">
      esimu 从 ZJUers Simulator 中抽取可复用的规则、运行时辅助、世界数据契约
      和 starter 应用形态；每个游戏自己的故事、名词、数值、事件、道具和 prompt
      都留在主题包里。
    </p>
    <p class="hero-actions">
      <a href="quickstart/" class="hero-button primary">快速开始</a>
      <a href="new-project-bootstrap/" class="hero-button">创建项目</a>
      <a href="framework-readiness-review/" class="hero-button">就绪审查</a>
    </p>
  </div>
</section>

<div class="home-body">

<h2>当前结论</h2>

<p>
  esimu 已经可以作为<strong>基本完整的 alpha 框架</strong>，用于创建单主题模拟器原型。
</p>

<p>推荐形态是：</p>

<pre><code>esimu-core + starter app + theme pack</code></pre>

<p>
  它还不是稳定公共框架。现阶段建议继续使用 Git tag 固定
  <code>esimu-core</code> 版本，等 starter 前端依赖策略、可选持久化适配器和真实外部项目反馈成熟后，
  再考虑更正式的发布渠道。
</p>

<h2>你会得到什么</h2>

<div class="feature-grid">
  <article>
    <h3>esimu-core</h3>
    <p>
      Python 核心包，负责世界数据加载、属性/道具契约、学期结算、运行时快照、
      action gate、生命周期辅助和内容标准化。
    </p>
  </article>
  <article>
    <h3>Starter App</h3>
    <p>
      一个很小的 FastAPI/WebSocket 后端与 Vite/TypeScript 前端皮肤，默认使用
      demo-campus 主题，并以内存状态跑通最小游戏循环。
    </p>
  </article>
  <article>
    <h3>Theme Pack</h3>
    <p>
      一个目录承载游戏可见语言、故事、prompt、属性、平衡、道具、课程、角色、
      事件、成就和资源。
    </p>
  </article>
</div>

<h2>最快路径</h2>

<p>生成一个新项目：</p>

<pre><code class="language-powershell">
cd esimu-lab\simulator-core\backend
python scripts\new_project.py <target-project> --project-name "My Simulator" --theme-id my-simulator
</code></pre>

<p>验证生成的主题：</p>

<pre><code class="language-powershell">
$env:SIMULATOR_LAB_ROOT='<target-project>'
$env:SIMULATOR_THEME='my-simulator'
python scripts\validate_world_data.py
</code></pre>

<p>
  然后编辑 <code>themes/&lt;theme_id&gt;/theme.json</code>、
  <code>story.json</code>、<code>prompts.json</code> 和 <code>world/</code>。
</p>

<h2>架构一眼看懂</h2>

<pre><code>
themes/&lt;theme_id&gt;/
  theme.json          # 可见名词和浏览器存储前缀
  story.json          # 序章与结局文案
  prompts.json        # 面向模型的上下文
  world/              # 属性、平衡、道具、课程、事件、成就

simulator-core/backend/esimu_core/
  world/              # 加载器与校验器
  domain/             # 纯游戏规则
  runtime/            # tick、快照、action、后台任务辅助
  lifecycle/          # 开局与状态转换辅助
  content/            # 事件、论坛、私信内容契约

apps/starter/
  backend/            # 最小适配器
  frontend/           # 最小前端皮肤
</code></pre>

<h2>继续阅读</h2>

<ul>
  <li><a href="quickstart/">快速开始</a>：本地验证与 smoke 命令。</li>
  <li><a href="new-project-bootstrap/">创建新项目</a>：生成并定制一个模拟器。</li>
  <li><a href="theme-pack-contract/">主题包契约</a>：必需文件和字段规则。</li>
  <li><a href="architecture/">架构</a>：当前 core/theme/adapter 边界。</li>
  <li><a href="framework-readiness-review/">框架就绪审查</a>：Phase 9 结论和剩余缺口。</li>
</ul>

</div>

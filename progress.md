# PaperSplitter 2.0 — 项目进度文档

> 用途：当打开一个新对话时，让 AI 快速了解项目的架构、已完成的工作和关键设计决策。

## 1. 项目概览

PaperSplitter 是一个试卷管理系统，支持 PDF 试卷解析、题目提取、AI 分类打标、LaTeX 公式渲染。

**前端（正在重构）**：Vue 3 + Vite + TypeScript + Element Plus（SPA）
**后端（稳定）**：Flask + MySQL + Jinja2 模板（旧）
**离线管线**：PyMuPDF + Google GenAI + OpenAI（PDF→图片→分类→入库）

### 1.1 项目目录结构

```
PaperSplitter2.0/
├── frontend/                    # Vue 3 前端（重构中）
│   ├── src/
│   │   ├── api/                 # API 封装层（axios）
│   │   │   ├── request.ts       # Axios 实例 + 拦截器
│   │   │   ├── syllabus.ts      # Syllabus API
│   │   │   ├── topic.ts         # Topic 详情 API
│   │   │   └── search.ts        # 搜索 API
│   │   ├── components/          # 可复用组件
│   │   │   ├── AppTopNav.vue    # 顶部导航栏
│   │   │   ├── TocSidebar.vue   # TOC 侧边栏
│   │   │   ├── TopicCard.vue    # 话题卡片
│   │   │   ├── QuestionCard.vue # 题目卡片
│   │   │   └── EmptyState.vue   # 空状态占位
│   │   ├── composables/         # 组合式函数
│   │   │   └── useMathJax.ts    # MathJax LaTeX 公式渲染
│   │   ├── layouts/
│   │   │   └── DefaultLayout.vue # 布局外壳（含 keep-alive）
│   │   ├── router/
│   │   │   └── index.ts         # 4 条路由
│   │   ├── types/
│   │   │   └── index.ts         # TS 类型定义
│   │   ├── views/
│   │   │   ├── SyllabusView.vue  # 主页：Syllabus 列表
│   │   │   ├── topic/
│   │   │   │   └── TopicDetail.vue  # 话题详情页
│   │   │   ├── search/
│   │   │   │   └── SearchResult.vue # 搜索结果页
│   │   │   └── error/
│   │   │       └── NotFound.vue     # 404 页面
│   │   ├── App.vue             # 根组件
│   │   ├── main.ts             # 入口
│   │   └── style.css           # 全局样式
│   ├── index.html
│   └── vite.config.ts
├── backend/
│   ├── webapp/                  # Flask Web 应用
│   │   ├── server/
│   │   │   └── app.py          # Flask 路由 + JSON API
│   │   ├── database/
│   │   │   ├── database.py     # MySQL 数据库访问层
│   │   │   └── db_config.py    # 数据库连接配置
│   │   ├── templates/          # Jinja2 模板（旧）
│   │   └── static/             # 静态资源（旧）
│   └── offline/                # 离线数据管线
└── progress.md                 # 本文件
```

### 1.2 路由设计

| 路径 | 组件 | 说明 |
|------|------|------|
| `/` | SyllabusView | 主页，显示大纲列表（keep-alive 缓存） |
| `/topic/:topicId` | TopicDetail | 话题详情 + 题目列表（不缓存） |
| `/search` | SearchResult | 搜索结果页 |
| `/:pathMatch(.*)*` | NotFound | 404 兜底 |

路由配置见：[router/index.ts](file:///d:/Python%20Projects/PaperSplitter2.0/frontend/src/router/index.ts)

### 1.3 后端 API 设计

全部 JSON API 以 `/api/` 开头，统一返回结构 `{ code: 0, data: ..., message: "" }`。

| 端点 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/api/topics` | GET | `has_questions` (可选) | 扁平 syllabus 列表 |
| `/api/topics/grouped` | GET | `has_questions` (可选) | 按前缀分组 |
| `/api/topics/<topic_id>` | GET | — | 话题详情 + 全部题目 |
| `/api/search` | GET | `q` | 关键词搜索 |
| `/api/question_images/<path>` | GET | — | 题目图片服务 |

---

## 2. 本次对话修改记录

### 2.1 MathJax LaTeX 公式渲染修复

**涉及文件**：
- [useMathJax.ts](file:///d:/Python%20Projects/PaperSplitter2.0/frontend/src/composables/useMathJax.ts) — 组合式函数
- [TopicDetail.vue](file:///d:/Python%20Projects/PaperSplitter2.0/frontend/src/views/topic/TopicDetail.vue) — 修复调用时序
- [index.html](file:///d:/Python%20Projects/PaperSplitter2.0/frontend/index.html) — 恢复原始 async 加载

**问题**：TopicDetail 页面的 LaTeX 公式不渲染，无报错。
**根因**：`<el-skeleton>` 在 `loading=true` 时用 `v-if` 隐藏 default slot 内容 → 公式不在 DOM 中 → MathJax 扫描不到。时序是 `loading=false` 在 `renderMath()` 之后才执行。

**修复**：
1. `useMathJax.ts`：使用 MathJax 3 内置的 `startup.promise` 确保启动就绪，不再用轮询或自定义事件。
2. `TopicDetail.vue`：将 `loading.value = false` 移到 `renderMath()` **之前**，先让内容显示到 DOM 中，再触发 MathJax 排版。

**关键代码时序**（TopicDetail.vue `onMounted`）：
```typescript
detail.value = data
loading.value = false    // 先关闭骨架屏，让内容进入 DOM
await renderMath()       // 再扫描 DOM 中 LaTeX 公式
```

### 2.2 "Contain Questions Only" 筛选功能

**涉及文件**：
- 前端：[SyllabusView.vue](file:///d:/Python%20Projects/PaperSplitter2.0/frontend/src/views/SyllabusView.vue)
- 前端 API：[syllabus.ts](file:///d:/Python%20Projects/PaperSplitter2.0/frontend/src/api/syllabus.ts)
- 后端路由：[app.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/webapp/server/app.py)
- 后端数据库：[database.py](file:///d:/Python%20Projects/PaperSplitter2.0/backend/webapp/database/database.py)

**功能**：Syllabus 页面添加 `<el-switch>` 开关，开启后只显示 questions 表中有真题的 topic。

**实现**：
- 后端：`get_all_topics(has_questions_only=True)` 使用 `SELECT DISTINCT s.* FROM syllabus s INNER JOIN questions q ON s.topic_id = q.topic_id`
- 前端：`hasQuestionsOnly` ref 绑定 switch，change 事件重新调 `getGroupedSyllabus(hasQuestionsOnly.value)`

### 2.3 页面状态保留（keep-alive 缓存）

**涉及文件**：
- [DefaultLayout.vue](file:///d:/Python%20Projects/PaperSplitter2.0/frontend/src/layouts/DefaultLayout.vue) — 外层包裹 keep-alive
- [SyllabusView.vue](file:///d:/Python%20Projects/PaperSplitter2.0/frontend/src/views/SyllabusView.vue) — keep-alive 生命周期适配

**功能**：通过面包屑导航返回 Syllabus 页面时，保留筛选状态、滚动位置和已加载的数据。

**实现**：
- `DefaultLayout.vue`：`<router-view v-slot>` + `<keep-alive :include="['SyllabusView']">`
- 仅缓存 `SyllabusView`，`TopicDetail` 不缓存（每次重新获取数据）
- `SyllabusView.vue` 添加：
  - `defineOptions({ name: 'SyllabusView' })` — 显式声明组件名，确保 include 匹配
  - `onDeactivated` → 保存 `window.scrollY` 到 `savedScrollTop`
  - `onActivated` → `nextTick` 后 `window.scrollTo()` 恢复位置 + `renderMath()` 重渲染

**注意**：keep-alive 的 `include` 匹配是**大小写敏感**的，必须用 `'SyllabusView'`（PascalCase）而非 `'syllabus'`。

---

## 3. 关键设计决策

### 3.1 为什么 SyllabusView 用 keep-alive 而 TopicDetail 不用？

- **SyllabusView**：用户频繁通过面包屑导航返回，每次重新请求数据 + 重置滚动位置体验差。缓存后 `hasQuestionsOnly` 等 ref 状态自动保留。
- **TopicDetail**：每个 topic 的数据不同，需要每次进入重新加载。不缓存确保数据新鲜度。

### 3.2 MathJax 渲染为什么用 startup.promise 而不是轮询/事件？

MathJax 3 的启动是异步的（`tex-svg.js` 用 `async` 加载），`script.onload` 只能保证脚本下载完毕，不能保证 MathJax 内部初始化完成。`MathJax.startup.promise` 是官方提供的启动完成信号，是最可靠的方式。

### 3.3 为什么 "Contain Questions Only" 用 INNER JOIN 而不是 WHERE IN？

```sql
-- 方案 A（用户提出）：SELECT DISTINCT topic_id FROM questions → WHERE IN
-- 方案 B（采用）：SELECT DISTINCT s.* FROM syllabus s INNER JOIN questions q ON s.topic_id = q.topic_id
```
INNER JOIN 一次查询完成，不需要先查 question 表拼列表再查 syllabus 表，数据库层面的 JOIN 优化也更高效。

### 3.4 为什么 MySQL 使用 dictionary=True 的 cursor？

与原有 SQLite 版的 `row_factory = sqlite3.Row` 等价，所有查询结果直接返回字典（列名 → 值），前端和后端代码都按字典键名访问数据，语义清晰。

---

## 4. 待办/可继续的方向

- [ ] **TocSidebar 同步激活**：当 SyllabusView 被 keep-alive 恢复时，TocSidebar 是否同步更新高亮
- [ ] **搜索结果页 MathJax**：SearchResult.vue 是否也需要调用 `renderMath()`
- [ ] **性能优化**：大数据量下 Syllabus 列表的懒加载/虚拟滚动
- [ ] **部署**：Nginx 配置，前端 build 产物 serve 策略

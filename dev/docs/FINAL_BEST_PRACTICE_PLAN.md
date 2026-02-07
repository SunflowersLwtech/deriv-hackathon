# TradeIQ 最终最佳实践实施计划

- 文档路径: `/Users/sunfl/Documents/study/deriv hackathon/dev/docs/FINAL_BEST_PRACTICE_PLAN.md`
- 适用代码库: `/Users/sunfl/Documents/study/deriv hackathon`
- 版本: v1.0
- 日期: 2026-02-07

## 1. 目标与范围

本计划用于落地完整 TradeIQ 系统，覆盖：
1. Django 后端智能代理（DeepSeek function calling、市场工具、行为教练、Bluesky 内容）。
2. Next.js 14 前端（Dashboard、Market、Behavior、Content、聊天面板）。
3. Supabase Auth Google 登录（前后端联动）。

严格约束：
1. 仅使用 DeepSeek API（只有不得已才使用 OpenRouter）。
2. 使用 conda 环境 `tradeiq`。
3. 统一从项目根目录 `.env` 读取配置。
4. Supabase Google Provider 已在控制台配置，代码只做接入。

## 2. 当前基线与关键差距

当前仓库存在可复用基础，但未形成可演示闭环。主要差距：
1. 前端目录缺失，Phase 6/7 未启动。
2. 多个关键 API 未实现（`market/brief`、`market/ask`、`market/price`、`chat/ask`、`content/generate`、`demo/seed`、`demo/wow-moment`）。
3. demo fixtures 中 overtrading/loss-chasing/healthy 无 trade 数据，行为检测链路无法触发。
4. DeepSeek 路由与工具契约未完全对齐目标接口。
5. Supabase JWT 鉴权中间件与受保护权限未落地。
6. `DATABASE_URL` 当前格式错误导致回退 sqlite，容易造成“假成功”。

## 3. 执行原则（最佳实践）

1. 先打通最小闭环，再扩展体验层。
2. 接口先行：先固定 API contract，再写前后端。
3. 强约束命名：工具函数名、URL、JSON 字段严格按计划统一。
4. 所有外部 API（DeepSeek/Deriv/News/Finnhub/Bluesky）必须有超时、重试、降级。
5. 不把 secrets 写死到代码；`.env` 只本地使用，禁止提交。
6. 每个 phase 必须有可重复验证命令与明确 DoD（Definition of Done）。
7. 不修改你标记的禁改文件；若与目标冲突，先记录冲突并做最小变更决策。

## 4. 冲突与决策（先对齐）

### 4.1 已识别冲突

1. 你要求“不要修改 `tradeiq/settings.py`”，但 Supabase JWT 中间件与 DRF 权限默认要接入 settings。
2. 你要求“不要修改 behavior/”，但目标工具命名需要 `generate_behavioral_nudge`（当前为 `generate_behavioral_nudge_with_ai`）。

### 4.2 建议决策

1. `tradeiq/settings.py` 允许最小必要变更（仅新增 middleware/REST auth 配置，不改其他行为）。
2. behavior 逻辑保持不动，在 `agents/tools_registry.py` 做适配层（别名映射）满足工具命名契约。

## 5. 分阶段实施计划（推荐顺序）

## Phase A: 稳定化与安全前置（半天）

目标：避免后续联调“假绿”。

任务：
1. 修复 `.env` 中 `DATABASE_URL` 为有效 Supabase URI（密码 URL encode）。
2. 同步依赖：`backend/requirements.txt` 与 `scripts/environment.yml` 都补齐 `finnhub-python`、`websockets`、`textblob`。
3. 统一读取根目录 `.env`（脚本和服务一致）。
4. 清理硬编码凭据（特别是 `scripts/deriv_test.py`）。
5. 补 `.gitignore` 防止 `__pycache__`、临时文件污染。

DoD：
1. `conda activate tradeiq && cd backend && python manage.py check` 无错误且不再出现 DB parse fallback。
2. `python scripts/verify_env.py` 通过。
3. 仓库无新增敏感信息泄漏。

## Phase 0: Infrastructure（0.5 天）

目标：完成基础设施落地。

任务：
1. 更新 `backend/requirements.txt`（五个包）。
2. 创建 `market_insights` Supabase 表（结构对齐 `market/models.py`）。
3. 在 `tradeiq` 环境安装依赖并验证。

DoD：
1. `market_insights` 表存在，字段与 Django model 一致。
2. `pip install -r backend/requirements.txt` 成功。
3. `python manage.py showmigrations`、`python manage.py check` 均通过。

## Phase 1: Agent Core（1 天）

目标：构建统一 AI 路由大脑。

任务：
1. `agents/llm_client.py`
   - `get_client()` 单例。
   - `chat_completion()` 通用封装。
   - `chat_completion_with_tools()` 完整工具循环（可多轮 tool calls）。
   - 指数退避重试和错误分类。
2. `agents/prompts.py`
   - 写入完整 `MASTER_COMPLIANCE_RULES`。
   - 补齐 `SYSTEM_PROMPT_MARKET/BEHAVIOR/CONTENT/ROUTER`。
3. `agents/tools_registry.py`
   - 定义 9 个工具（名字严格一致）。
   - `TOOL_DISPATCH_MAP` 与真实函数绑定。
4. `agents/router.py`
   - `route_query(query, user_id=None, conversation_history=None)`。
   - 集成合规检查与免责声明拼接。
   - 新增 `generate_market_brief(instruments)`。

DoD：
1. 输入任意 market/behavior/content 问题都能走统一路由。
2. tool call 支持多轮直到最终文本。
3. 输出不含预测/喊单语句，且带免责声明。

## Phase 2: Market Analysis Tools（1 天）

目标：提供真实市场分析能力。

任务：
1. `market/tools.py`
   - `fetch_price_data(instrument, timeframe)` 对接 Deriv WS（含 symbol map）。
   - `search_news(instrument, hours)` 聚合 NewsAPI + Finnhub。
   - `analyze_technicals(instrument)` 纯 Python 实现 SMA20/50、RSI、趋势。
   - `get_sentiment(instrument)` 用 TextBlob 聚合新闻情绪。
2. `market/views.py`
   - `MarketBriefView`。
   - `AskAnalystView`。
   - `LivePriceView`。
3. `market/urls.py`
   - 增加 `brief/`、`ask/`、`price/`。

DoD：
1. 三个 market API 都可返回结构化 JSON。
2. Deriv 不可用时有可解释降级返回（不是 500 崩溃）。
3. 技术指标计算结果可重复、可单测。

## Phase 3: Content Generation Tools（0.5-1 天）

目标：完成 Bluesky 内容生产闭环。

任务：
1. `content/tools.py`
   - `generate_social_content`。
   - `format_bluesky_post`（300 字符内，强制免责声明）。
   - `compose_bluesky_thread`（3-5 帖）。
   - `apply_persona_voice`。
2. `content/personas.py`
   - 完整 persona 配置：`system_prompt`、`voice_config`、`example_posts`、`banned_phrases`。
3. `content/views.py`
   - 增加 `GenerateContentView`。
4. `content/urls.py`
   - 增加 `generate/`。

DoD：
1. 输入 insight 可产出 post/thread。
2. 超长文本自动裁剪且保留合规尾注。
3. persona 切换后风格明显且不破合规规则。

## Phase 4: WebSocket Chat Integration（0.5 天）

目标：聊天端到端联通。

任务：
1. `chat/consumers.py`
   - 每连接维护 conversation history。
   - 使用 `asyncio.to_thread()` 调 `route_query()`。
   - 支持 normal reply + behavioral nudge。
2. 新建 `chat/views.py`、`chat/urls.py`
   - `POST /api/chat/ask/` 作为 REST fallback。
3. `tradeiq/urls.py`
   - include `api/chat/`。
4. 群组隔离
   - 不使用全局固定 group，按 user/session 隔离，避免跨用户消息泄漏。

DoD：
1. WS 与 REST 都能返回 AI 结果。
2. behavior nudge 仅到目标用户连接。

## Phase 5: Demo System（0.5 天）

目标：演示场景一键可复现。

任务：
1. 完善 fixtures：
   - `demo_overtrading.json` 至少 18 笔 trade。
   - `demo_loss_chasing.json` 至少 6 笔递增仓位。
   - `demo_healthy_session.json` 至少 6 笔健康样本。
2. 新建 `demo_all_in_one.json`（demo user + 3 personas）。
3. `demo/views.py`
   - `SeedDemoDataView`。
   - `WowMomentView`。
4. `demo/urls.py`
   - 增 `seed/`、`wow-moment/`。

DoD：
1. seed 后可直接运行完整演示链路。
2. wow-moment 一次调用返回 market + behavior + content 联合结果。

## Phase 6: Supabase Auth（Google Sign-In）（1 天）

目标：统一认证链路。

任务（前端）：
1. 安装 `@supabase/supabase-js`、`@supabase/ssr`。
2. 新建 `src/lib/supabase/client.ts`、`server.ts`、`middleware.ts`。
3. 新建 `/login`、`/auth/callback`、全局 `middleware.ts`。
4. 导航栏增加 sign-out。

任务（后端）：
1. 新建 `tradeiq/middleware/supabase_auth.py`。
2. 验证 `Authorization: Bearer <jwt>`，映射/自动创建 `users` 表记录。
3. 为受保护接口启用权限控制。

DoD：
1. 未登录访问受保护页面会跳转 `/login`。
2. Google 登录后可访问前后端受保护接口。
3. JWT 无效时后端返回 401。

## Phase 7: Frontend Next.js（nof1.ai 风格）（1.5-2 天）

目标：构建可演示前端体验。

任务：(完全复刻https://nof1.ai/的前端包括色彩,元素,任何视觉效果,交互可以自然一些)
1. 初始化 Next.js 14 + Tailwind + ESLint + TS。
2. 新建 API/WebSocket 客户端：`src/lib/api.ts`、`src/lib/websocket.ts`。
3. 搭建基础壳：Sidebar、TickerBar、ChatPanel、DisclaimerBadge、DataCard、AppShell。
4. 页面实现：
   - `/` Dashboard
   - `/market`
   - `/behavior`
   - `/content`
5. 完成暗色高密度视觉与响应式。

DoD：
1. 四页面均可加载并拉取后端数据。
2. 聊天面板可发送/接收。
3. 内容工作台可生成并预览 Bluesky 内容。

## Phase 8: 联调、质量门禁与彩排（0.5-1 天）

目标：保证 Demo Day 稳定。

任务：
1. 全链路回归：market -> behavior -> content。
2. 异常注入：DeepSeek 超时、Deriv 断连、News API 限流。
3. 加缓存和超时兜底，控制 P95 响应时间。
4. 固化 demo 脚本（口播 + API 触发顺序 + fallback 话术）。

DoD：
1. 关键流程 3 次连跑无中断。
2. 任一外部 API 故障不导致整体 500。

## 6. 里程碑与建议排期

1. Day 1: Phase A + 0 + 1。
2. Day 2: Phase 2 + 3 + 4。
3. Day 3: Phase 5 + 6。
4. Day 4: Phase 7 + 8 + Demo 彩排。

## 7. 验收命令清单（最终）

```bash
# Backend
cd backend
python manage.py runserver

curl -X POST http://localhost:8000/api/demo/seed/
curl -X POST http://localhost:8000/api/demo/load-scenario/ -H "Content-Type: application/json" -d '{"scenario":"revenge_trading"}'
curl -X POST http://localhost:8000/api/market/ask/ -H "Content-Type: application/json" -d '{"question":"What is happening with EUR/USD?"}'
curl -X POST http://localhost:8000/api/chat/ask/ -H "Content-Type: application/json" -d '{"message":"Why did EUR/USD spike?"}'
curl -X POST http://localhost:8000/api/content/generate/ -H "Content-Type: application/json" -d '{"insight":"EUR/USD dropped 1.2%","platform":"bluesky_post"}'
curl -X POST http://localhost:8000/api/demo/wow-moment/ -H "Content-Type: application/json" -d '{"user_id":"aaaaaaaa-0000-4000-8000-000000000001","instrument":"EUR/USD"}'

# Frontend
cd ../frontend
npm run dev
```

## 8. 质量门禁（必须同时满足）

1. 功能门禁：上述验收命令全部成功。
2. 合规门禁：输出不含预测/喊单语句，免责声明全覆盖。
3. 安全门禁：代码库无硬编码密钥，JWT 无效请求均拒绝。
4. 性能门禁：关键 API 在常规网络下可接受（建议 P95 < 3s，外部 API 异常时有降级）。
5. 可演示门禁：Wow flow 一次触发成功。

## 9. 风险与回滚策略

1. DeepSeek 超时/失败。
   - 策略：重试 + 降级模板 + 缓存上一条可用分析。
2. Deriv WS 不稳定。
   - 策略：断线重连 + 最近价格缓存 + 明确“数据暂不可用”状态。
3. NewsAPI/Finnhub 限流。
   - 策略：双源聚合 + 去重 + 失败部分可空。
4. Supabase Auth 回调失败。
   - 策略：独立 callback 诊断日志 + 登录重试入口。
5. Demo 现场网络波动。
   - 策略：预置 mock fallback 和缓存数据。

## 10. 文件级执行清单（最终）

新增：
1. `backend/chat/views.py`
2. `backend/chat/urls.py`
3. `backend/fixtures/demo_all_in_one.json`
4. `backend/tradeiq/middleware/supabase_auth.py`
5. `frontend/` 整体目录与文件

修改：
1. `backend/requirements.txt`
2. `backend/agents/prompts.py`
3. `backend/agents/tools_registry.py`
4. `backend/agents/router.py`
5. `backend/market/tools.py`
6. `backend/market/views.py`
7. `backend/market/urls.py`
8. `backend/content/tools.py`
9. `backend/content/personas.py`
10. `backend/content/views.py`
11. `backend/content/urls.py`
12. `backend/chat/consumers.py`
13. `backend/demo/views.py`
14. `backend/demo/urls.py`
15. `backend/tradeiq/urls.py`
16. `backend/fixtures/demo_overtrading.json`
17. `backend/fixtures/demo_loss_chasing.json`
18. `backend/fixtures/demo_healthy_session.json`

保持不动（按你要求）：
1. `backend/behavior/` 全部
2. `backend/content/models.py`
3. `backend/content/bluesky.py`
4. `backend/market/models.py`
5. `backend/agents/compliance.py`
6. 所有 migrations
7. `backend/fixtures/demo_revenge_trading.json`
8. `backend/fixtures/demo_personas.json`

## 11. 最终演示关键流（唯一主线）

Market event -> AI explains -> Detects user pattern -> Nudge appears -> Content generated -> Published to Bluesky

该主线是 Demo 成功的唯一高优先级验收路径，所有任务以保证这条链路稳定为第一目标。

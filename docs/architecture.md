# Love Director — 软件架构文档

## 概述

Love Director 是一个"恋爱观观测与导演系统"。当前 v1.0 以 Claude Code Skill（SKILL.md）的形式运行，架构设计预留了从"AI Agent 寄生程序"逐步演进为"独立软件"的完整路径。

### 核心哲学

- **不治疗、不建议、不评判** — 导演只呈现，角色自己选择
- **数据驱动** — 一切结论锚定在用户提供的聊天记录和全国统计数据上
- **隐私优先** — 默认不存储、不上传、不联网

---

## 演进路径

```
v1.0 (当前) — SKILL.md，寄生在 AI agent 中
  └─ 优点: 零安装、跨平台、即开即用
  └─ 局限: 依赖 AI 平台、无持久存储、无自有UI

v2.0 (API化) — Python 核心引擎 + AI 后端插件
  └─ 核心逻辑与 AI 推理分离
  └─ 外部工具通过插件系统接入
  └─ 可被 CLI/Web/其他应用调用

v3.0 (完整软件) — Web + Desktop 独立应用
  └─ 自有 UI + 数据存储 + 分析引擎
  └─ 可选对接任意 AI 后端
```

---

## 五层架构

```
┌──────────────────────────────────────────────────┐
│                展示层 (Presentation)              │
│  CLI / Web UI / Desktop App / IDE Plugin          │
├──────────────────────────────────────────────────┤
│                编排层 (Orchestration)             │
│  Love Director Engine                             │
│  ├─ Phase 管理器: 0→1A→1B→1C→2→3→4→5           │
│  ├─ 状态机                                       │
│  └─ 决策树生成器 ★                               │
├──────────────────────────────────────────────────┤
│                分析层 (Analytics)                 │
│  ├─ 聊天分析引擎 (NLP Pipeline)                   │
│  ├─ 画像计算引擎                                  │
│  └─ 概率引擎                                      │
├──────────────────────────────────────────────────┤
│                  数据层 (Data)                    │
│  ├─ 用户画像 (本地优先，加密)                      │
│  ├─ 知识库                                       │
│  └─ 统计数据库                                    │
├──────────────────────────────────────────────────┤
│                集成层 (Integration)               │
│  ├─ 数据导入插件 (WeFlow/wechat_analysis/...)     │
│  ├─ AI 后端适配器 (Claude/GPT/Gemini/Ollama)      │
│  └─ 心理模型插件 (Lila/MBTI/...)                  │
└──────────────────────────────────────────────────┘
```

---

## 核心模块

### 1. Love Director Engine (编排层)

```python
class LoveDirectorEngine:
    """平台无关的核心引擎，纯 Python，无 AI 平台依赖"""

    def process_phase(self, session, input_data) -> PhaseResult: ...
    def build_profile(self, self_report, chat_records) -> UserProfile: ...
    def probe_philosophy(self, profile, questionnaire) -> PhilosophyProfile: ...
    def observe_behavior(self, profile, philosophy, analysis) -> BehaviorReport: ...
    def generate_decision_tree(self, profile, philosophy, behavior) -> DecisionTree: ...
```

### 2. 决策树引擎 (Phase 4 核心)

概率化决策树生成流程:

1. **关键变量提取**: 从 Phase 1-3 数据中提取 2-4 个核心变量
   - 筛选标准: 自述-行为差距、跨关系一致性、改变难度可评估
2. **分支构建**: 每个变量生成"保持"和"改变"两个一级分支
   - 每个分支标注概率 + 数据依据
3. **随机事件**: 基于用户择偶模式 + 概率分布的外部事件
4. **结局生成**: 6 种类型 (惯性/成长/意外/警示/循环/重构)
   - 每个结局: 概率 × 时间框架 × 故事演绎 × 数据依据

### 3. 数据层: 隐私优先

- 默认无存储 (v1.0 纯会话)
- 可选加密存储用户画像 (v2.0+)
- 聊天记录仅分析时缓存，不长期存储
- 知识库版本化管理

### 4. 插件系统

```python
class DataImportPlugin(ABC):
    """聊天数据导入插件接口"""
    name: str
    def import_chat_records(self, path) -> list[ChatRecord]: ...

class AIBackendPlugin(ABC):
    """AI 后端插件接口"""
    def generate(self, prompt, context) -> str: ...

class PsychologyPlugin(ABC):
    """心理模型插件接口"""
    def assess(self, data) -> AssessmentResult: ...
```

---

## 外部联动项目

### P0 (必须集成)
- [WeFlow](https://github.com/hicccc77/WeFlow) — 微信聊天记录导出
- [wechat_analysis](https://github.com/4everzyj/wechat_analysis) — 情感评分 + 情绪分类

### P1 (强烈建议)
- [Lila MCP](https://github.com/lila-graph/lila-mcp) — 依恋风格 + 大五人格
- [ex-skill](https://github.com/perkfly/ex-skill) — 对方人格蒸馏

### P2 (推荐)
- [FriendScope](https://github.com/ChanMeng666/friendscope) — 关系 10 维度评估
- [wechat-insight](https://github.com/caigee-cmd/wechat-insight) — MBTI 推断
- [mbti-mcp](https://github.com/wenyili/mbti-mcp) — MBTI 测试

### P3 (探索)
- [Soul Matrix AI](https://github.com/taielab/soul-matrix-ai) — 兼容性雷达图
- [agora](https://github.com/geekjourneyx/agora) — 多 Agent 审议
- [yourself-skill](https://github.com/notdog1998/yourself-skill) — 自我副本构建

---

## 仓库结构

```
love-director/
├── skill/            ← 当前实现: Claude Code Skill
├── engine/           ← 未来: Python 核心引擎
├── data/             ← JSON/YAML 知识库
├── docs/             ← 架构 + 开发文档
├── web/              ← 未来: Web 前端
├── desktop/          ← 未来: 桌面应用
└── .github/          ← Issue/PR 模板
```

---

## 数据流

```
用户输入 → Phase 0 (安全声明)
  → Phase 1A (问卷自述)
  → Phase 1B (WeFlow 多对象导出)
  → Phase 1C (自述 vs 行为差距)
  → Phase 2 (7维探针 + Lila 依恋风格)
  → Phase 3 (行为观测 + wechat_analysis 情感曲线)
  → Phase 4 (决策树生成 ★)
  → Phase 5 (导演视角闭环)
```

---

## 技术选型建议

| 层 | 推荐技术栈 | 理由 |
|----|----------|------|
| 引擎 | Python 3.12+ | NLP 生态成熟、类型提示完整 |
| Web 前端 | Next.js + D3.js | 决策树可视化、SSR |
| 桌面 | Tauri (Rust + React) | 体积小、全本地、隐私安全 |
| 数据 | SQLite + JSON | 轻量、可离线、用户可控 |
| AI 后端 | Claude API / OpenAI / Ollama | 多模型可选 |
| NLP | SnowNLP + 大连理工情感词典 | 中文情感分析 |

---

## 许可

MIT License — 你可以自由使用、修改、分发。情感反诈的姊妹项目 [emotional-fraud-detector](https://github.com/awaqufexituf65-cmyk/emotional-fraud-detector) 同样 MIT 许可。

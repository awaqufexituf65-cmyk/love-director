# Love Director Engine — Python 核心计算引擎

## 这不是套壳 AI

Love Director Engine 是一个**独立于 AI 平台的 Python 计算引擎**。它做 AI 不能做的事：数学计算、NLP 分析、决策树构建、概率赋值。

## 架构

```
engine/
├── cli.py                          ← CLI 入口: love-director analyze --chats *.txt
├── src/
│   ├── director.py                  ← 主编排器: 绑定所有模块
│   ├── phases/
│   │   ├── phase_manager.py         ← Phase 状态机 (0→1→2→3→4→5)
│   │   └── decision_tree.py         ← ★ 决策树生成器 (变量提取→分支→结局)
│   ├── analysis/
│   │   ├── probability_engine.py    ← 概率引擎 (贝叶斯条件概率)
│   │   ├── profile_engine.py        ← 画像引擎 (自述 vs 行为差距)
│   │   └── chat_analyzer.py         ← NLP 管道 (情感评分/冲突检测/话题分析)
│   ├── data/
│   │   └── store.py                 ← 隐私优先本地存储
│   └── plugins/
│       ├── base.py                  ← 插件接口
│       └── data_import/             ← WeFlow/手动 适配器
```

## 安装

```bash
cd engine
pip install -r requirements.txt  # snownlp, jieba
```

## 使用

```bash
# 分析聊天记录 → 生成决策树
python -m engine.cli analyze --chats chat1.txt chat2.txt chat3.txt \
  --age 28 --city "上海" --parents "和睦" --relationships 3

# 从 JSON 生成画像
python -m engine.cli profile --self-report profile.json
```

## 输出示例

```
🎬 Love Director — 开始分析
Phase 1A: 画像采集完成
Phase 1B: 分析了 3 段关系
  - 伴侣相似度: 0.72 (高一致性 — 你在重复同一模板)
  - 冲突回避指数: 0.68 (显著回避模式)
Phase 1C: 差距分析发现 3 个盲区
  ⚠️ 脆弱性评分: 0.65 (偏高)

Phase 4: 🌳 生成决策树...
  - 关键变量: 3 个
  - 变量: conflict_handling, mate_selection_filter, security_attachment
  - 验证: ✅ 通过

🔀 冲突应对方式 (gap: 0.80, consistency: 0.85)
  ├─ 保持回避 — ~78%
     ├─ 🎲 遇到安全型伴侣 — ~20%
        🍂 被温柔地接住 [🌱 growth] — ~12%
        🍂 他还是离开了 [🍂 inertia] — ~8%
     ├─ 🎲 遇到焦虑型伴侣 — ~15%
        ...

🎥 导演视角: 你是你自己的导演。
```

## 依赖

- Python 3.10+
- `snownlp` (中文情感分析)
- `jieba` (中文分词，可选)

## 限制

- 不调用外部 AI API — 纯本地计算
- 中文情感词典为简化内置版，完整版需手动下载大连理工词典
- 依恋风格评估需 Lila MCP 外部服务

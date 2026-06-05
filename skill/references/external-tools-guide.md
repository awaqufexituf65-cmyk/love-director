# 外部工具联动指南

Love Director 可以与以下开源工具联动，从"纯 AI 推理"升级为"硬数据分析 + 科学模型"。

## 分层策略

| 层级 | 引导语气 | 用户不装的后果 |
|------|---------|-------------|
| 🔴 P0 | "强烈建议安装" | 行为层缺少数据支撑，分析置信度显著下降 |
| 🟠 P1 | "推荐安装" | 缺少科学模型维度，用问卷自评替代 |
| 🟡 P2 | "可选进阶" | 不影响核心流程，锦上添花 |

---

## 🔴 P0: 数据管道

### WeFlow — 微信聊天记录导出
- 仓库: https://github.com/hicccc77/WeFlow
- 前提: 微信桌面版 4.0+
- 用途: 导出与多个对象的完整聊天记录
- 详细教程: 见 `references/weflow-guide.md`

### wechat_analysis — 情感分析
- 仓库: https://github.com/4everzyj/wechat_analysis
- 用途: 对导出的聊天记录生成情感评分时间曲线 + 情绪分类热力图
- 安装: `git clone` + `pip install -r requirements.txt`
- 使用: 将 WeFlow 导出的 TXT 放入指定目录 → 运行脚本 → 获得图表
- 产出: 情感评分曲线图（看懂关系温度变化）、情绪热力图（愤怒/悲伤/恐惧/惊讶/喜悦分布）

---

## 🟠 P1: 深度模型

### Lila MCP — 依恋风格评估
- 仓库: https://github.com/lila-graph/lila-mcp
- 用途: 科学评估依恋风格（安全型/焦虑型/回避型/混乱型）+ 大五人格
- 配置: 在 Claude Code 中添加 MCP Server
- 替代: 若不安装，用 Phase 2 问卷自评替代（精度较低）

### ex-skill — 对方人格蒸馏
- 仓库: https://github.com/perkfly/ex-skill
- 用途: 从聊天记录中蒸馏出对方的人格结构（5-6层标签）
- 注意: 仅对用户主动提供的、用户自己参与的聊天记录进行分析
- 产出: 对方的人格 SKILL.md → 输入 Love Director Phase 4 演绎

---

## 🟡 P2: 增强层

### FriendScope — 关系评估框架
- 仓库: https://github.com/ChanMeng666/friendscope
- 用途: 10维度关系科学评估（信任/沟通/情感支持/冲突解决/边界...）
- 参考其框架作为 Phase 3 行为观测的维度参考

### wechat-insight — MBTI 推断
- 仓库: https://github.com/caigee-cmd/wechat-insight
- 用途: 从聊天风格推断 MBTI + 社交关系网络图

### mbti-mcp — MBTI 测试
- 仓库: https://github.com/wenyili/mbti-mcp
- 用途: 28题/48题 MBTI 测试（可选，MBTI 科学性有争议）

---
title: 商机洞察专家
name: 商机洞察专家
version: 2.0.0
description: >
  CRM商机洞察引擎。基于FABM客户数据库，通过五维评分模型自动识别最有可能采购CRM的客户， 并给出可执行的跟进建议。每个推荐附带领域专家级的理由说明。

  v2.0更新：融合量子蜂群线索开发六步工作流，形成完整的"发现→开发→转化"Pipeline

  五维评分：行业吸引力(25%) + 企业规模(25%) + 数字化需求(20%) + 触达基础(15%) + 区域优先级(15%)

  三大Pipeline模式： - discover: 商机洞察（谁可能买？为什么？） - develop: 线索开发（怎么联系？发什么？） - full:
  全流程（从上一步直接到下一步）
agent_created: true
agent_tags:
  - 商机
  - 线索开发
  - CRM销售
  - 客户洞察
  - 价值营销
  - 量子蜂群
  - 六步工作流
trigger_keywords:
  - 谁可能买CRM
  - 商机洞察
  - 找出潜在客户
  - 机会客户
  - 高意向客户
  - CRM需求
  - 怎么联系
  - 发什么邮件
  - 关键人是谁
  - 价值主张
  - 营销邮件
  - 制造业商机
  - 汽配商机
  - 杭州商机
  - 本周跟进谁
  - 今天联系谁
  - 给我客户名单
methodology_references:
  - 五维CRM采购意向评分模型（行业·规模·需求·基础·区域）
  - S/A/B/C/D 四级商机等级（>=8.5/>=7.5/>=6.5/>=5.5/<5.5）
  - Fit × Intent × Engagement 乘法评分（替代传统加法评分）
  - 9种AI预测模型模式（企业画像/意图信号/行为衰减/相似拓展/复合/转化预测/账户聚合/负面信号/重评）
  - 200+信号维度（扩展自5维→企业画像/意图/行为/技术栈/人事/财务/负面等）
  - 连续学习回路（月度自动重评分+成交数据反馈权重调整）
  - 负面信号降权机制（营收下滑/无跟进/长期沉默自动扣分）
  - 线索开发六步工作流（客户认知→需求分析→关键人排序→价值主张→邮件→行动）
  - 决策角色模型（EB/T-CB/T-AB/UB/EK）
  - 价值主张生成（按角色KPI定制化匹配）
  - 营销邮件模板（量子蜂群标准化模板）
  - FABM客户数据库（457家浙江企业）
  - 行业CRM需求指数（10行业·1-10分）
  - 决策链行业模板（制造/汽配）
knowledge_sources:
  - alliance.db（FABM客户数据库·457家客户）
  - 量子蜂群·线索开发六步工作流
  - 行业KnowHow知识库
scripts:
  - opportunity_scorer.py: 商机洞察+线索开发全流程引擎（v2.0，Phase 1+2+3）
compiled_methodology:
  file: /Users/sunsun/.workbuddy/methodology/methodology_knowledge_base.json
  version: 2.0.0
  nodes:
    - models.crm_opportunity_scorer: 五维CRM商机评分（5条规则+权重）
    - models.lead_development_pipeline: 线索开发六步工作流（6步+8条规则）
    - models.fabm_customer_scoring: FABM客户评分（五维+分数解释）
    - models.quality_scoring: 输出质量评分标准（五维度+阈值）
    - models.error_patterns: 错误模式+纠正规则（4个）
    - models.semantic_query_templates: 语义查询模板（4个）
disable: true
---

# 商机洞察专家 v2.0（融合线索开发）

## 定位

**从"谁可能买"一直到"怎么联系"，一站式搞定。**

```
v1.0: 谁可能买CRM？→ 排名+理由
    ↓
v2.0: 谁可能买？→ 有什么需求？→ 找谁谈？→ 怎么说？→ 发什么邮件？
```

融合量子蜂群 Section 04「线索开发六步工作流」后，商机洞察专家形成了完整的 **"发现→开发→转化"三阶段Pipeline**。

---

## 方法论编译引擎接入（执行前必读·硬性规则）

> ⚠️ **核心原则**：五维评分模型、线索开发六步工作流等确定性规则已编译为
> `/Users/sunsun/.workbuddy/methodology/methodology_knowledge_base.json`（v2.0）。
> **执行任何评分/开发任务前，必须先读取该JSON对应节点，禁止在Prompt中重新"理解"规则。**

### 读取节点映射

| 任务 | JSON节点 | 说明 |
|:-----|:-------|:-----|
| Phase 1：商机五维评分 | `models.crm_opportunity_scorer` | 5条规则+权重，直接按rules评分 |
| Phase 2：线索开发六步 | `models.lead_development_pipeline` | 6步+8条规则+4个转化信号 |
| FABM客户评分 | `models.fabm_customer_scoring` | 五维+分数解释 |
| 输出质量自查 | `models.quality_scoring` | 五维度逐项打分，按阈值决定交付 |
| 错误检查 | `models.error_patterns` | 4个错误模式，输出前自动检查 |
| 语义查询解析 | `models.semantic_query_templates` | 4个自然语言→SQL映射模板 |

### 执行规程（3条·必遵守）

```
规程1：评分任务（Phase 1）
  1. 读取 JSON → models.crm_opportunity_scorer
  2. 对每条规则（rules数组），按 condition 判断 → 给分
  3. 加权计算总分（按 weight 字段）
  4. 输出时引用 rule.id（如"R001:客户匹配度90分"）
  5. 禁止：在输出中重新描述五维模型（"客户匹配度25%..."）

规程2：线索开发任务（Phase 2/3）
  1. 读取 JSON → models.lead_development_pipeline
  2. 按 steps 数组顺序执行（step=1 → step=2 → ...）
  3. 每步检查 completion_criteria 是否满足，否则不进入下一步
  4. 执行中检查是否违反 rules（如L001:每一步必须有明确输出）
  5. 检查 conversion_signals：满足任一信号 → 立即创建商机

规程3：质量自查（每次重大输出）
  1. 读取 JSON → models.quality_scoring
  2. 五维度逐项打分（1-10分）
  3. 计算加权总分 = Σ(dimension.score × dimension.weight)
  4. 总分 >= 8.5 → ✅ 交付
     6.0 <= 总分 < 8.5 → ⚠️ 修正后再交付
     总分 < 6.0 → 🔴 不交付，重做
```

> ⚠️ **迭代规则**：每次修改评分逻辑/权重/规则，必须同步更新两个地方：
> 1. `methodology_knowledge_base.json`（编译版·确定性规则）
> 2. 本文件 `methodology_references`（描述版·非确定性说明）
> 两者不一致 → 以JSON为准

---

## 使用方式

### 模式1：discover — 商机洞察（Phase 1）

```
> 谁可能买CRM？
> 制造业商机有哪些？
> 杭州的高意向客户？

输出：评分排名 + 五维理由 + 推荐行动
```

### 模式2：develop — 线索开发（Phase 2+3）

```
> 帮我开发吉利汽车的线索
> 怎么联系万向钱潮？
> 给福耀玻璃写一封营销邮件

输出：需求分析 + 决策链 + 关键人价值主张 + 可直接发送的邮件
```

### 模式3：全流程（Phase 1→2→3）

```
> 制造业谁可能买？帮我开发第一个客户
> 杭州TOP3客户，各写一封邮件

输出：先出洞察排名 → 对排名第一执行完整开发流程
```

## Pipeline详解

### Phase 1：商机洞察（建——找谁）

| 维度 | 权重 | 判断逻辑 |
|:-----|:----:|:---------|
| 行业吸引力 | 25% | 汽配10>制造9>电子9>科技8 |
| 企业规模 | 25% | 100亿+10分 / 10亿→8分 |
| 数字化需求 | 20% | 行业+规模+分层综合 |
| 触达基础 | 15% | A层10分 > B层7分 |
| 区域优先级 | 15% | 杭甬10 > 温9 |

输出：**评分排名 + 每条理由（为什么是这个分）**

### Phase 2：线索开发（怎么打）

融合量子蜂群六步工作流：

```
Step 1: 客户认知
  → 你是谁？客户是谁？
  
Step 2: 需求分析
  → 基于业务场景识别3-5个潜在商机
  → 按紧迫度+预算排序

Step 3: 关键人排序
  → 决策角色识别（EB/T-CB/T-AB/UB/EK）
  → 影响力评估（1-10分）
  → 输出：接触地图

Step 4: 价值主张
  → 每个关键人的KPI对应价值点
  → 每个价值点附量化数据
  → 输出：差异化价值主张卡

Step 5: 营销邮件
  → 基于量子蜂群Section 04模板
  → 包含：身份介绍+痛点共鸣+量化案例+邀约理由

Step 6: 下一步动作
  → 明确邀约理由
  → 设置跟进提醒
```

### Phase 3：执行输出

```
📧 可直接发送的邮件草稿

邮件主题：[行业]数字化转型的新思路——基于浙江同行的实践

尊敬的[客户][角色]：

我是纷享销客浙江渠道的石磊...

我们已经为浙江[行业]企业实现了：
✓ 销售效率提升30%
✓ 客户转化率提升20%

[基于角色KPI的定制价值主张]

想约您15分钟交流...
```

## 完整输出示例

```
🔍 浙江吉利汽车有限公司 深度洞察
   行业: 汽车零部件 | 城市: 宁波 | 分层: A
   商机评分: 10.0分 (S级·绝对优先)
   预估预算: 50-100万

📋 推荐需求 (TOP4):
  1. 供应商关系管理(SRM)
  2. 售后质量追溯系统
  3. 销售过程管理
  4. 客户门户

👥 决策链 (4人):
  EB 总经理/董事长 → 关注: 客户关系+供应链 | 影响力: 10/10
  UB 销售/市场总监 → 关注: 客户管理效率 | 影响力: 9/10
  T-CB 信息化负责人 → 关注: 系统对接与数据 | 影响力: 8/10
  EK 财务总监 → 关注: 投资回报周期 | 影响力: 7/10

📧 推荐首封邮件:
[可直接复制的完整邮件草稿]
```

## 快速命令

```bash
# Phase 1: 商机洞察（全量）
cd ~/.workbuddy/skills/商机洞察专家/scripts
python3 opportunity_scorer.py discover
python3 opportunity_scorer.py discover 制造业
python3 opportunity_scorer.py discover 汽车零部件 宁波

# Phase 2+3: 线索开发（单个客户）
python3 opportunity_scorer.py develop 吉利汽车
python3 opportunity_scorer.py develop 万向钱潮
python3 opportunity_scorer.py develop 福耀玻璃
```

## 版本日志

| 版本 | 日期 | 变更 |
|:----:|:----:|:-----|
| v2.0 | 2026-06-19 | 融合量子蜂群线索开发六步工作流，新增develop模式+邮件生成 |
| v3.0 | 2026-06-19 | **方法论升级**：AAA复合评分框架(Fit×Intent×Engagement) + 9种预测模型 + 200+信号维度 + 负面信号检测 + 连续学习回路 |
| v1.0 | 2026-06-19 | 初始版本，五维商机洞察评分引擎 |

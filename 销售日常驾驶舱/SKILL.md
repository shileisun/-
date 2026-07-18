---
title: 销售日常驾驶舱
name: sales-daily-dashboard
version: 1
description: |
  [原名：销售日常驾驶舱]
  每日上午10:00自动生成销售驾驶舱报告，连接纷享销客CRM获取客户/商机/销售任务数据，结合量子蜂群FABM客户数据库，生成今日任务、跟进提醒、绩效诊断、本周计划的完整驾驶舱。触发词：今日任务、销售驾驶舱、每日报告、今天做什么、本周计划。
agent_created: true
agent_tags:
  - 销售
  - 驾驶舱
  - 每日任务
  - CRM
  - 量子蜂群
trigger_keywords:
  - 今日任务
  - 销售驾驶舱
  - 每日报告
  - 今天做什么
  - 本周计划
  - 每日工作
  - 跟进提醒
  - 销售日常
  - 每日驾驶舱
knowledge_sources:
  - 量子蜂群 v12.0 销售日常驾驶舱模块
  - FABM客户数据库（2,982家浙江企业）
  - 纷享销客CRM对象模型（Account/Lead/Opportunity/Task）
disable: true
---

# 销售日常驾驶舱 Skill v1.0

## 能力

通过连接纷享销客CRM + FABM客户数据库，在每日上午10:00自动生成结构化驾驶舱报告。驾驶舱包含以下板块：

| 板块 | 内容 | 数据来源 |
|:---|:-----|:---------|
| **① 今日任务** | 待跟进A/B层客户、待处理商机、待办事项 | CRM TaskObj + FABM分层 |
| **② 跟进提醒** | 30天未跟进客户预警、今日联系人推荐 | CRM AccountObj + FABM |
| **③ 绩效诊断** | 本月业绩进度、拜访量/商机转化/签约对比 | CRM NewOpportunityObj + 计划对比 |
| **④ 下周计划** | AI预生成的下周重点工作 | CRM历史数据 + 量子蜂群推理 |

## 触发词

- "今日任务" / "今天做什么" → 立即生成今日驾驶舱
- "本周计划" → 自动生成周计划
- 也可以作为自动化Skill，每天10:00按时执行

## 工作流程

### Step 1：查询CRM获取数据

用 **QueryRecordsBySQL** 或 **GetObjectDescribe** 从CRM获取以下数据：

```sql
-- 1. 今日待办事项（TaskObj）
SELECT id, name, task_date, priority, status, related_account_name
FROM TaskObj
WHERE task_date = '今天' AND status = 'open'
ORDER BY priority DESC

-- 2. 30天未跟进客户（AccountObj）
SELECT id, name, industry, last_contact_date, owner_name
FROM AccountObj
WHERE DATEDIFF(day, last_contact_date, GETDATE()) > 30
  AND owner_name = '当前用户'
ORDER BY last_contact_date ASC

-- 3. 在途商机（NewOpportunityObj 商机2.0）
-- 注意：sales_status 使用API值，"1"=进行中
SELECT name, amount, sales_stage, probability, account_id
FROM NewOpportunityObj
WHERE sales_status = '1'
ORDER BY amount DESC
```

### Step 2：合并FABM客户数据

从量子蜂群的FABM客户数据库读取分层数据，与CRM数据合并：
- **A层客户**（838家）：标记为重点经营
- **B层客户**（921家）：标记为积极跟进
- **C层客户**（827家）：标记为持续触达
- **D层客户**（396家）：标记为保持联系

### Step 3：AI推理生成驾驶舱

基于以上数据，结合量子蜂群推理链，生成结构化的驾驶舱文本：

```
输入：CRM查询结果 + FABM分层数据 + 本月计划
  ↓
事实提取：X个待办 + Y个预警客户 + Z个在途商机
  ↓
优先级排序：按客户等级+商机金额+紧急度排序
  ↓
话术生成：每个待办自动生成触达话术
  ↓
绩效诊断：当前进度 vs 计划目标，根因分析
  ↓
输出：结构化驾驶舱报告
```

### Step 4：输出格式

生成的驾驶舱报告包含清晰的板块，示例输出格式如下：

```
━━ 上午好，[姓名]！今天是 [YYYY年M月D日 星期X] ━━

📋 今日任务
  ✓ 跟进[客户名]（A层）→ 已生成触达话术
  ✓ 处理[商机名]（P1）→ 建议今天完成[动作]
  ⚠ 预警：[客户名] 30天未跟进
  💡 建议：[客户名] 昨天[事件]，适合跟进

📊 绩效诊断
  本月进度：[X]%（目标[Y]%，欠[Z]%）
  拜访量：[X]次（目标[Y]次）
  商机转化：[X]个（目标[Y]个）
  改进建议：[个性化建议]

📈 本周计划（AI预生成）
  1. [任务1]
  2. [任务2]
  3. [任务3]
```

## 数据源说明

### 信源1：纷享销客CRM（通过crm-mcp连接）

| 对象 | API名称 | 关键字段 | 用途 |
|:----|:-------|:---------|:----|
| 客户 | AccountObj | id, name, owner, last_followed_time, field_7i6jf__c(未跟进天数) | 客户跟进状态 |
| 商机 | NewOpportunityObj | name, amount, sales_stage, probability, account_id, owner, close_date, record_type, field_sKyt1__c(商机预定级), field_6iOwJ__c(预测ARR), field_2S4lu__c(预测总金额) | 在途商机管理 |
| 任务 | TaskObj | id, name, dead_line, status, owner | 今日待办 |
| 联系人 | ContactObj | id, name, account_name, phone, email | 联系推荐 |
| 日程 | EventObj | id, subject, start_time, end_time, related_account | 今日日程 |
| 销售记录 | SalesforceObj | id, name, amount, close_date, stage | 绩效统计 |

### 信源2：FABM客户数据库（本地量子蜂群）

| 数据 | 路径 | 用途 |
|:----|:-----|:----|
| FABM客户数据 | ~/.workbuddy/memory/客户数据_FABM.json | 分层/行业/区域过滤 |
| 客户分层配置 | ~/.workbuddy/memory/客户数据配置.json | 分层策略映射 |

## 查询模板

### 今日待办查询

```
GetObjectDescribe(objectApiName="TaskObj")  → 获取字段
QueryRecordsBySQL(sql="SELECT id, name, task_date, priority, status, related_account_name FROM TaskObj WHERE task_date = '2026-06-16' AND status = 'open' ORDER BY priority DESC")
```

### 预警客户查询

```
GetObjectDescribe(objectApiName="AccountObj") → 获取last_contact_date字段
QueryRecordsByTemplate(
  objectApiName="AccountObj",
  queryMode="RECORD",
  selectFields=["id","name","industry","last_contact_date"],
  searchTemplateQuery={
    "limit": 20,
    "filters": [
      {"field_name": "last_contact_date", "operator": "LT", "field_values": ["30天前的日期"]},
      {"field_name": "owner_name", "operator": "EQ", "field_values": ["当前用户"]}
    ],
    "orders": [{"fieldName": "last_contact_date", "isAsc": true}]
  }
)
```

### 绩效统计查询（NewOpportunityObj 商机2.0）

注意：`sales_status` 用API值，"1"=进行中，"2"=赢单

```
QueryRecordsByTemplate(
  objectApiName="NewOpportunityObj",
  queryMode="AGGREGATE",
  aggregationType="SUM",
  metricFieldApiName="amount",
  searchTemplateQuery={
    "limit": 1,
    "filters": [
      {"field_name": "sales_status", "operator": "EQ", "field_values": ["2"]},
      {"field_name": "close_date", "operator": "BETWEEN", "field_values": ["当月第一天", "当月最后一天"]}
    ]
  }
)
```

### 在途商机查询模板

```
-- 全量在途商机（进行中），按金额降序
QueryRecordsByTemplate(
  objectApiName="NewOpportunityObj",
  queryMode="RECORD",
  selectFields=["name","amount","sales_stage","probability","account_id","owner","close_date","record_type","field_sKyt1__c","field_6iOwJ__c","field_2S4lu__c","partner_id"],
  searchTemplateQuery={
    "limit": 20,
    "orders": [{"fieldName": "amount", "isAsc": false}],
    "filters": [
      {"field_name": "sales_status", "operator": "EQ", "field_values": ["1"]}
    ]
  },
  needCount=true
)
```

## 自动化配置参考

需要配合WorkBuddy自动化使用，配置如下：

- **名称**：销售日常驾驶舱·每日推送
- **Schedule**：每天上午10:00
- **RRULE**：FREQ=DAILY;BYHOUR=10;BYMINUTE=0
- **Prompt**：执行「销售日常驾驶舱」Skill，连接纷享销客CRM，查询今日任务、预警客户、在途商机，结合FABM客户分层数据，生成今日销售驾驶舱报告
- **ConnectorIds**：crm-mcp（纷享销客CRM连接器）

## 注意事项

1. 执行前确认crm-mcp连接器已启用（connected状态）
2. 如CRM查询返回空结果，使用FABM本地数据作为降级方案
3. 绩效诊断需要用户事先在CRM中设置本月销售目标
4. 客户跟进话术基于量子蜂群信任拜访专家方法论自动生成
5. AI生成的每日任务建议仅为参考，最终执行需用户确认
6. **⚠️ 在途商机必须从 `NewOpportunityObj`（商机2.0）获取，`OpportunityObj`（商机1.0）已废弃**
7. **⚠️ `sales_status` 字段的查询值必须用API值：`"1"`=进行中，`"2"`=赢单，不是显示名"进行中"/"赢单"**
8. `TaskObj` 的截止日期字段是 `dead_line` 而非 `task_date`，且暂无 `priority` 字段
9. `AccountObj` 的未跟进天数计算字段为 `field_7i6jf__c`

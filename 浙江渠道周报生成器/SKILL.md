---
name: 浙江渠道周报生成器
version: 1.0.0
description: |
  纷享销客浙江渠道团队工作周报自动生成器。
  每周日定时执行，自动生成本周渠道工作周报（WORD格式）。
  报告涵盖：Q2经营数据仪表盘、核心在途商机观测、上周计划回顾、
  本周主要工作、风险预警与资源诉求、伙伴经营健康度、下周计划、
  案例复盘与心得共8个板块。
trigger_keywords:
  - 周报
  - 渠道周报
  - 浙江周报
  - 生成周报
  - 渠道工作周报
  - 周报生成
agent_created: true
alliance:
  version: "5.0"
  department: 经营司
  role: 周报生成
  pipeline_phase: -1
  upstream: []
  downstream: []
  color: "#48bb78"
disable: true
---

# 浙江渠道周报生成器

## 角色定位

纷享销客浙江渠道团队专属的周报自动化生成工具，基于 CRM 数据和团队输入自动输出专业格式的 WORD 周报文档。

## 触发条件

- 用户要求生成/更新浙江渠道工作周报
- 用户说"周报"、"生成周报"、"渠道周报"
- 定时自动化：每周日 21:30 自动触发

## 执行流程

### 步骤1：确认周期信息

- 确认当前周次编号（如第21周）
- 确认报告周期（周一至周日）
- 确认报告日期

### 步骤2：收集本周数据

需要从用户处收集以下信息（或基于对话历史/CRM数据填充）：

#### A. Q2 经营数据
- 业绩目标/完成/完成率/差距
- ARR 目标/完成/完成率/差距
- 在途商机金额（50%+赢率）

#### B. 核心在途商机
- 商机名称、FCO、阶段、赢率、预计成交时间、业绩/ARR、归属伙伴
- 感孝项目群追踪

#### C. 上周计划回顾
- 逐项列出计划、完成状态、完成率、未完成原因

#### D. 本周主要工作
- **孙石磊**：生态开源活动、新伙伴引入、伙伴业务支持
- **孙晓辰**：商机跟进与拜访、商机漏盘、能力建设
- **李大伟**：项目支持、感孝项目群、其他

#### E. 风险预警与资源诉求
- 风险清单（级别/项目/卡点/资源/Deadline）
- 资源诉求汇总

#### F. 伙伴经营健康度
- 8个伙伴的完成率、商机储备、活跃度、本周动作、风险信号

#### G. 下周计划
- 三人各自下周计划

#### H. 案例复盘与心得
- 3-4个本周实战心得/方法论文框

### 步骤3：生成 WORD 文件

使用模板脚本生成：

```bash
cd /Users/sunsun/WorkBuddy/Claw && python3 zj_channel_weekly_report_template.py
```

模板脚本位置：`/Users/sunsun/WorkBuddy/Claw/zj_channel_weekly_report_template.py`

### 步骤4：交付

输出文件路径示例：
`/Users/sunsun/WorkBuddy/Claw/Zhejiang_Channel_Weekly_Report_2026_W21.docx`

## 数据来源

### 重要：在途商机取商机2.0（NewOpportunityObj）

❌ 旧数据源 `OpportunityObj`（商机1.0）已废弃，**不要再使用**。
✅ 在途商机全部从 `NewOpportunityObj`（商机2.0）获取。

### CRM 对象与字段映射

| CRM对象 | API名称 | 关键字段 | 说明 |
|:--------|:--------|:---------|:-----|
| 商机2.0 | `NewOpportunityObj` | `name`, `amount`, `sales_stage`, `probability`, `close_date`, `account_id`, `owner`, `record_type`, `field_sKyt1__c`, `field_6iOwJ__c`, `field_2S4lu__c`, `partner_id`, `sales_status` | 在途商机主表 |
| 客户 | `AccountObj` | `id`, `name`, `owner`, `last_followed_time`, `field_7i6jf__c` | 客户跟进状态 |
| 任务 | `TaskObj` | `id`, `name`, `dead_line`, `status`, `owner` | 待办事项 |
| 销售记录 | `SalesRecordObj` | `id`, `name`, `amount`, `close_date`, `stage` | 绩效统计 |

### 商机2.0 关键字段详解

| 字段 | API名 | 类型 | 说明 |
|:-----|:------|:----|:------|
| 商机名称 | `name` | text | - |
| 商机金额 | `amount` | currency | 签约总金额（含一次性费用+产品费） |
| 商机阶段 | `sales_stage` | select_one | API值如 `4Kwp4Jng9`, 对应显示值如"初步接洽" |
| 阶段赢率 | `probability` | percentile | 0-100的值 |
| 预计签约日期 | `close_date` | date | - |
| 客户名称 | `account_id` | object_reference | 关联 AccountObj |
| 负责人 | `owner` | employee | 关联系统用户 |
| 业务类型 | `record_type` | record_type | 选项：新购商机/增购商机/续费商机/新购商机（代理商）等 |
| 商机预定级 | `field_sKyt1__c` | select_one | 选项：SVIP/VIP/重要/标准/小微，API值：option1/01zg0tS95/mdCJmn1Lo/9338l3x5O |
| 预测成交ARR | `field_6iOwJ__c` | currency | - |
| 预测成交总金额 | `field_2S4lu__c` | currency | - |
| 合作伙伴 | `partner_id` | object_reference | 关联 PartnerObj |
| 阶段状态 | `sales_status` | select_one | **API值："1"=进行中，"2"=赢单，"3"=输单，"4"=无效** |
| 商机层级 | `new_opportunity_path` | tree_path | 商机2.0子父层级关系 |
| 上级商机 | `parent_id` | object_reference | 关联上级 NewOpportunityObj |

### 查询模板（必读）

**⚠️ `sales_status` 字段必须使用API值（"1"/"2"/"3"/"4"），不是显示值（"进行中"/"赢单"）**

```sql
-- 在途商机（进行中），按金额降序
-- sales_status='1' 表示"进行中"
QueryRecordsByTemplate(
  objectApiName="NewOpportunityObj",
  queryMode="RECORD",
  selectFields=["name","amount","sales_stage","probability","account_id","owner","close_date","record_type","field_sKyt1__c","field_6iOwJ__c","field_2S4lu__c","partner_id","sales_status"],
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

```sql
-- 指定负责人的在途商机（如孙晓辰，owner_id=11233）
QueryRecordsByTemplate(
  objectApiName="NewOpportunityObj",
  queryMode="RECORD",
  selectFields=["name","amount","sales_stage","probability","account_id","owner","close_date","record_type","field_sKyt1__c","field_6iOwJ__c","field_2S4lu__c","partner_id"],
  searchTemplateQuery={
    "limit": 20,
    "orders": [{"fieldName": "amount", "isAsc": false}],
    "filters": [
      {"field_name": "owner", "operator": "EQ", "field_values": ["11233"]},
      {"field_name": "sales_status", "operator": "EQ", "field_values": ["1"]}
    ]
  },
  needCount=true
)
```

### 数据结构字段说明

获取字段描述：

```python
GetObjectDescribe(objectApiName="NewOpportunityObj", simpleDescribe=True)  → 获取所有字段
```

1. **纷享销客 CRM 系统**（MCP接口）：
   - 商机对象 (NewOpportunityObj) ← **商机2.0，必用**
   - 客户对象 (AccountObj)
   - 销售记录对象 (SalesRecordObj)

2. **团队人工输入**：周会讨论内容、拜访纪要、策略共识

## 报告结构（8大板块）

| 板块 | 内容 |
|------|------|
| 一、Q2经营数据仪表盘 | 季度核心指标 + 经营健康度诊断 |
| 二、核心在途商机观测 | 商机红黄绿灯 + 感孝项目群 |
| 三、上周计划回顾 | 逐项对照 + 完成率 |
| 四、本周主要工作 | 三人分头工作详细记录 |
| 五、风险预警与资源诉求 | 风险清单 + 资源诉求 |
| 六、伙伴经营健康度 | 8伙伴六维看板 |
| 七、下周计划 | 三人下周计划 |
| 八、案例复盘与心得 | 实战心得 + 团队策略共识 |

## 关键人员

- 孙石磊（团队负责人）
- 孙晓辰 Richard（渠道经理）
- 李大伟（浙分渠道经理）

## 关键伙伴

宁波青谷、联动智慧、感孝、杭州智享、纵享、启德、慧生纪元（新）、蜗石智能（新）

## 注意事项

- 模板脚本中的 `REPORT_DATA` 字典包含上周默认数据，生成新周报时需要更新为本周实际数据
- 所有中文内容直接使用中文字面量，避免 unicode 转义编码导致截断问题
- 字符串中包含引号时使用 `\u201c`（左）和 `\u201d`（右）中文引号，或用单引号包裹
- Python 3.9 环境，f-string 中不能包含反斜杠

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
伙伴业务诊断Agent v3.0 - 诊断引擎
来源：《伙伴盈利手册3.0》+ 经盈工作坊第一期
v3.0 新增：综合判断与评价 / 业务策略与方法建议 / 暖心寄语
用法：
  python3 diagnose_partner.py --input /path/to/meeting_notes.txt
  python3 diagnose_partner.py --json '{"revenue": 200, "team_size": 5, ...}'
"""

import sys
import json
import os
import re
import argparse
from datetime import datetime

# ── 4阶段判定标准（经盈工作坊版）─────────────────────────────────
STAGE_STANDARDS = [
    {"stage": 1, "name": "初创启动期", "revenue_max": 300, "team_max": 5,
     "arr_max": 200, "clients_max": 30, "years": "0-3年", "color": "🔴",
     "features": [
         "老板亲自跑单，几乎没有稳定团队",
         "签单靠关系和机会，无可复制打法",
         "交付全靠老板，没有成型的交付体系",
         "每月现金流紧张，账期管理混乱",
         "尚未聚焦行业，什么客户都接"
     ]},
    {"stage": 2, "name": "规模发展期", "revenue_min": 300, "revenue_max": 1000,
     "team_min": 5, "team_max": 15, "arr_max": 800, "clients_min": 30, "clients_max": 80,
     "years": "3-5年", "color": "🟠",
     "features": [
         "有初始销售团队，但打法尚未统一",
         "新签在增长，但续费率低于70%",
         "老板仍深陷日常，团队还不能独立跑",
         "有了行业方向，但不够聚焦",
         "能算清当前账，未来账算不明白"
     ]},
    {"stage": 3, "name": "专业经营期", "revenue_min": 1000, "revenue_max": 3000,
     "team_min": 15, "team_max": 50, "arr_min": 1000, "clients_min": 80, "clients_max": 200,
     "years": "5年以上", "color": "🟢",
     "features": [
         "有专职销售、交付、客成分工",
         "续费率稳定在75%以上",
         "聚焦1-2个细分行业，有标杆客户",
         "有周例会、月复盘等经营管理机制",
         "能算清三层账，利润稳定但增长放缓"
     ]},
    {"stage": 4, "name": "战略共赢期", "revenue_min": 3000,
     "team_min": 50, "arr_min": 2000, "clients_min": 200,
     "years": "—", "color": "🟣",
     "features": [
         "老板抽身做战略，核心管理层独立运营",
         "在目标行业有品牌影响力",
         "续费率≥90%，客户主动转介绍",
         "方法论可输出，具备生态整合能力",
         "参与厂商战略共建，有行业话语权"
     ]},
]

# ── 健康度指标标准（4阶段版）─────────────────────────────────
HEALTH_BENCHMARK = {
    1: {"revenue": (None, 300), "gross_margin": (30, None), "cash_months": (3, None),
        "roi": (1.5, None), "monthly_leads": (5, 10), "conversion": (30, 40),
        "avg_arr": (2, 5), "sales_cycle": (None, 3), "total_clients": (10, 30),
        "renewal": (60, None), "upsell": (None, 5), "team_size": (1, 5),
        "per_head_revenue": (30, None), "turnover": (None, 30)},
    2: {"revenue": (300, 1000), "gross_margin": (32, None), "cash_months": (6, None),
        "roi": (1.8, None), "monthly_leads": (10, 20), "conversion": (30, 35),
        "avg_arr": (3, 8), "sales_cycle": (None, 3), "total_clients": (30, 80),
        "renewal": (65, None), "upsell": (5, 15), "team_size": (5, 15),
        "per_head_revenue": (35, None), "turnover": (None, 25)},
    3: {"revenue": (1000, 3000), "gross_margin": (40, None), "cash_months": (12, None),
        "roi": (2.5, None), "monthly_leads": (30, 50), "conversion": (35, 40),
        "avg_arr": (10, 30), "sales_cycle": (2, 3), "total_clients": (80, 200),
        "renewal": (75, None), "upsell": (25, 40), "team_size": (15, 50),
        "per_head_revenue": (45, None), "turnover": (None, 15)},
    4: {"revenue": (3000, None), "gross_margin": (45, None), "cash_months": (24, None),
        "roi": (3.0, None), "monthly_leads": (50, None), "conversion": (40, None),
        "avg_arr": (20, None), "sales_cycle": (None, 2), "total_clients": (200, None),
        "renewal": (90, None), "upsell": (40, None), "team_size": (50, None),
        "per_head_revenue": (50, None), "turnover": (None, 10)},
}

# ── 六度业务模型检查项 ────────────────────────────────────────
SIX_MODELS = [
    {"key": "fabm_prospecting", "name": "FABM开源", "check": "是否有ABM精准名单和定向触达机制？"},
    {"key": "eco_prospecting", "name": "生态开源", "check": "是否锁定金蝶/用友/MES核心管道？"},
    {"key": "sales_power", "name": "销售力", "check": "是否有标准销售SOP？赢单率是否达标？"},
    {"key": "marketing_events", "name": "市场活动", "check": "是否定期举办打单会/沙龙（月1-2场）？"},
    {"key": "industry", "name": "行业化3.0", "check": "是否有聚焦1-3个行业？是否有行业样板？"},
    {"key": "retention", "name": "存量经营", "check": "是否有CSM团队？续约率是否达标？"},
]

# ── 五力诊断（25题版，经盈工作坊工具①）─────────────────────
FIVE_POWERS = [
    {"key": "strategy", "name": "战略力", "emoji": "🧭",
     "questions": [
         "我能清晰说出公司未来3年的战略方向，且团队都知道",
         "我已明确聚焦的行业/客户画像，不再见单就做",
         "我知道自己的核心竞争优势是什么，且在持续强化",
         "我能判断哪些机会要抓、哪些机会要放弃",
         "公司的资源（人/财/时间）分配与战略方向一致",
     ]},
    {"key": "finance", "name": "算账力", "emoji": "🧮",
     "questions": [
         "我能说出公司每月的盈亏平衡点是多少",
         "我清楚每一单的毛利率，并有底线标准",
         "我有完整的续费追踪机制，每月知道续费率",
         "我能按人/团队核算每个人的产出贡献",
         "我的财务数据是实时可见的，不靠月底对账",
     ]},
    {"key": "organization", "name": "组织力", "emoji": "⚙️",
     "questions": [
         "公司有清晰的岗位职责和考核标准，不靠老板盯",
         "公司有能独立带团队的干部，不是所有事都靠我",
         "公司的核心业务流程有文档/SOP，新人可以上手",
         "团队有明确的激励机制，优秀员工愿意留下",
         "公司文化是可感知的，员工行为与文化一致",
     ]},
    {"key": "execution", "name": "执行力", "emoji": "🚀",
     "questions": [
         "公司有明确的季度/月度目标，且全员知晓",
         "重要任务都有负责人、时间节点和完成标准",
         "我每周有固定的业务回顾会，跟进执行进度",
         "年初定的计划，到年底执行完成率超过70%",
         "团队遇到困难时有问题上报机制，不是靠等老板发现",
     ]},
    {"key": "review", "name": "复盘力", "emoji": "🔄",
     "questions": [
         "公司有固定的月度/季度复盘机制，不只开庆功会",
         "我能说出近一年内公司从失败案例中改进的3件事",
         "公司有沉淀经验的机制（案例库、SOP更新等）",
         "我鼓励团队汇报问题，不会因为汇报坏消息而被批评",
         "同样的问题在我们公司不会犯第二次",
     ]},
]

# ── 五力评级（经盈工作坊工具①）───────────────────────────────
FIVE_POWER_RATING = [
    (100, 125, "🏆 强健型", "维持优势，重点打磨最短板那一力"),
    (75, 99, "💪 成长型", "找到最低分那一力，制定专项改进计划"),
    (50, 74, "⚠️ 发展型", "排优先级，从最影响生存的那一力开始"),
    (0, 49, "🆘 救火型", "先聚焦活下来，战略力和算账力是底线"),
]

# ── TOP5共性问题（经盈工作坊工具③）───────────────────────────
TOP5_ISSUES = [
    {"id": 1, "name": "老板转身赤字", "desc": "老板是最大的销售，走不出去", "priority": "P0", "level": "🔴"},
    {"id": 2, "name": "开源体系缺失", "desc": "没有可复制的获客打法", "priority": "P0", "level": "🔴"},
    {"id": 3, "name": "打法不可复制", "desc": "靠关系、靠人脉，没有体系", "priority": "P1", "level": "🟡"},
    {"id": 4, "name": "资金账目迷茫", "desc": "不清楚自己赚多少、亏多少", "priority": "P1", "level": "🟡"},
    {"id": 5, "name": "行业聚焦不清", "desc": "什么单都接，没有主赛道", "priority": "P1", "level": "🟡"},
]

# ── 赋能重心8选3（经盈工作坊工具③）───────────────────────────
ENABLEMENT_OPTIONS = [
    "战略聚焦辅导", "算账能力培训", "组织体系搭建", "执行机制设计",
    "价值销售培训", "干部力培育", "经营会升级", "复盘机制建立",
]

# ── v3.0 综合判断与评价生成器 ────────────────────────────────
def generate_comprehensive_assessment(data, stage, is_virtual, health_results, health_grade, coverage):
    """生成综合判断与评价（v3.0核心板块）"""
    assessment = {}

    # 一句话评价
    stage_name = stage["name"]
    owner_name = data.get("owner_name", "伙伴负责人")
    years = data.get("years", 0)
    revenue = data.get("revenue", 0)
    team_size = data.get("team_size", 0)
    arr = data.get("arr", 0)
    danger_count = len(health_results["danger"])
    warning_count = len(health_results["warning"])

    assessments_one_line = []
    if years >= 10:
        assessments_one_line.append(f"深耕{stage_name}赛道超过{years}年的长期主义者")
    elif years >= 5:
        assessments_one_line.append(f"稳健走过{years}年的行业深耕者")
    if arr >= 500:
        assessments_one_line.append("手握可观的存量资产")
    if team_size >= 15:
        assessments_one_line.append("具备规模化交付的团队底座")
    if revenue >= 1000:
        assessments_one_line.append("已经跨过千万营收门槛")
    if not assessments_one_line:
        assessments_one_line.append(f"正处在{stage_name}的关键成长期")

    assessment["one_line"] = "、".join(assessments_one_line[:3]) + "——当下最需要做的是'结构调整'，而非'从头再来'。"

    # 核心竞争力
    competencies = []
    impl_count = data.get("impl_count", 0) or 0
    if impl_count >= 10:
        competencies.append({
            "name": "强大的交付能力",
            "desc": f"{impl_count}人的实施团队是同行难以企及的规模，意味着能承接复杂项目、能交付大客户、能在当地建立服务口碑",
            "value": "🌟🌟🌟 核⼼壁垒"
        })
    if arr >= 400:
        competencies.append({
            "name": "可观的存量资产",
            "desc": f"{arr}万+ARR是过去多年交付质量最好的证明——客户愿意续费，就是对公司最大的信任票",
            "value": "🌟🌟🌟 核心资产"
        })
    if years >= 10:
        competencies.append({
            "name": "深厚的本地根基",
            "desc": f"深耕宁波市场{years}年，有头部客户、有区域口碑、有行业人脉——这是新人无法短期复制的护城河",
            "value": "🌟🌟 信任资产"
        })
    if data.get("head_clients") or data.get("total_clients", 0) >= 80:
        competencies.append({
            "name": "头部客户背书",
            "desc": "已成交头部客户，意味着产品能力、服务能力已经通过高标准检验，这是最好的'销售话术'",
            "value": "🌟🌟 品牌资产"
        })
    # 至少保证3项
    while len(competencies) < 3:
        candidates = [
            {"name": "行业经验积累", "desc": "已有的客户服务经验是最大的无形资产", "value": "⭐ 基础资产"},
            {"name": "团队战斗力", "desc": "现有团队是公司最宝贵的财富，每个人都是多年磨合的结果", "value": "⭐ 基础资产"},
            {"name": "客户信任基础", "desc": "每个续约客户都是对公司价值的认可，比任何广告都有说服力", "value": "⭐ 基础资产"},
        ]
        for c in candidates:
            if c["name"] not in [x["name"] for x in competencies]:
                competencies.append(c)
                break
    assessment["competencies"] = competencies[:4]

    # 结构性改善课题
    issues = []
    sales_count = data.get("sales_count", 0) or (team_size - impl_count)
    if impl_count > 0 and sales_count > 0 and impl_count / max(sales_count, 1) >= 3:
        ratio = impl_count // max(sales_count, 1)
        issues.append({
            "name": "销售交付结构失衡",
            "urgency": "P0",
            "logic": f"销售{sales_count}人 vs 实施{impl_count}人（1:{ratio}），每名销售背后扛{ratio}个实施的人效压力，新签产能严重不足——这不是人的问题，是结构的问题"
        })
    renewal = data.get("renewal", 100)
    if data.get("has_csm") is False or renewal < 70:
        issues.append({
            "name": "存量经营空白",
            "urgency": "P0",
            "logic": f"存量{arr}万+ARR无人主动经营，续约率{renewal}%靠交付质量自然维系。一旦竞品渗透或关键人变动，流失风险会被放大"
        })
    if danger_count >= 2:
        issues.append({
            "name": "健康度红灯指标需紧急处理",
            "urgency": "P0",
            "logic": f"{danger_count}项危险指标集中在获客和续约环节，反映的是体系能力缺口，不是执行力问题——建体系比盯人更有效"
        })
    if warning_count >= 3:
        issues.append({
            "name": "经营精细度不足",
            "urgency": "P1",
            "logic": "多项指标处于预警带，说明'能活下来'但'活得不够精细'，需要从凭经验管理转向看数据管理"
        })
    if not data.get("has_weekly_meeting"):
        issues.append({
            "name": "经营节奏尚未建立",
            "urgency": "P1",
            "logic": "缺少固定周会和月度经营会机制，管理靠'人盯人'而非'制度管人'——团队越大越需要节奏感"
        })
    assessment["issues"] = issues[:4]

    # 综合评分卡
    coverage_count = sum(1 for _, s, _ in coverage if "✅" in s)
    profit_pattern, _, profit_level = check_profit_pattern(data)
    assessment["scorecard"] = {
        "health_grade": health_grade,
        "coverage": f"{coverage_count}/6",
        "profit": profit_pattern,
        "profit_level": profit_level,
    }

    return assessment


# ── v3.0 业务策略与方法建议生成器 ─────────────────────────────
def generate_business_strategies(data, stage, health_results, coverage):
    """生成贴合实际的业务策略与方法建议"""
    strategies = {}

    stage_num = stage["stage"]
    revenue = data.get("revenue", 0)
    team_size = data.get("team_size", 0)
    arr = data.get("arr", 0)
    sales_count = data.get("sales_count", 0) or 3
    impl_count = data.get("impl_count", 0) or 0
    monthly_leads = data.get("monthly_leads", 15)
    conversion = data.get("conversion", 25)
    renewal = data.get("renewal", 60)
    upsell = data.get("upsell", 10)
    per_head = data.get("per_head_revenue", 55)

    # 7.1 开源获客策略
    prospecting = []
    if stage_num <= 2:
        prospecting.append({
            "action": "建立「电话+微信+社群+线下」四阶递进获客体系",
            "how": [
                f"每日每人50通电话，以加微信为第一目标（接通率4%→日均2个微信，月度60个新联系人）",
                "锁定宁波本地3-5个行业社群（制造业HR群/CIO群等），每周输出1篇专业内容（案例/趋势/干货），建立专业形象",
                "每月办1场小型线下沙龙（15-20人），用已成交头部客户做背书，会后48小时内完成回访"
            ],
            "owner": f"销售负责人（从{impl_count}人实施团队中选拔1人售前转岗协助开源）",
            "kpi": f"月新增商机从{monthly_leads}个→25-30个（3个月内），新增商机中30%来自存量转介绍"
        })
    else:
        prospecting.append({
            "action": "激活存量转介绍 + 生态渠道双引擎",
            "how": [
                "TOP20客户逐一拜访，主动邀请转介绍（每客户目标介绍2个同行业潜在客户，以案例分享为名义邀约）",
                "与宁波本地金蝶/用友/SAP代理商建立正式合作管道，每月交换3-5条商机，建立'谁推荐谁跟'的分润机制",
                "每季度做1次已成交客户成功案例包装（图文+视频），用于销售物料、朋友圈传播和市场活动"
            ],
            "owner": "老板亲自（TOP客户拜访）+ 销售负责人（渠道管理）",
            "kpi": "存量转介绍贡献30%新商机 + 生态渠道贡献20%新商机（6个月内达成）"
        })
    strategies["prospecting"] = prospecting

    # 7.2 销售能力建设
    sales = []
    target_ratio = 35
    if stage_num <= 3:
        sales.append({
            "action": "建立标准化销售SOP + 销售团队有序扩编",
            "how": [
                "梳理CRM行业标准销售5步法：线索→商机→方案→报价→签约，每步有标准动作、话术、输出物模板",
                f"销售团队从{sales_count}人扩到{sales_count+2}人分两步行：先招1人跑通SOP（第1-2月），SOP验证后再招第2人（第3月）",
                "建立周度商机复盘会（每周一30分钟）：每个商机三问——SSO是否清晰？下周行动承诺是什么？需要什么资源？",
                "销售新人培训压缩到2周：第1周学产品+SOP+sales playbook，第2周跟老销售跑3个真实客户"
            ],
            "owner": "老板（第1-2月亲自带+制定SOP）→ 销售负责人（第3月起独立运营）",
            "kpi": f"商机转化率从{conversion:.0f}%→{target_ratio}%（6个月内），新人3个月内出首单"
        })
    strategies["sales"] = sales

    # 7.3 客户经营深化
    retention = []
    if not data.get("has_csm") or renewal < 75:
        retention.append({
            "action": "从0到1建立客户成功体系——让500万存量从'自然维系'变成'主动经营'",
            "how": [
                f"从{impl_count}人实施团队选拔2人转岗CSM（选沟通力强、有客户意识的实施顾问，不是淘汰下来的人）",
                "建立客户分层经营机制：A类（ARR>10万/年）季度拜访+定制服务报告，B类（3-10万）半年拜访+产品使用培训，C类（<3万）年度回访+线上社群运营",
                "每季度一次客户健康度评估：使用频率/关键人变动/竞品接触/新需求/满意度，打分红黄绿。红灯客户当月必须出行动方案",
                "建立增购触发器：用户数使用率>80%→推扩容，单一模块用满1年→推关联模块，行业政策变化→推合规升级"
            ],
            "owner": "从实施团队选拔1名负责人（给正式title和激励），老板直接管前3个月",
            "kpi": f"续约率从{renewal:.0f}%→75%（12个月内），增购率从{upsell:.0f}%→20%+（12个月内），客户健康度红灯数逐月下降"
        })
    strategies["retention"] = retention

    # 7.4 组织效能优化
    org = []
    if impl_count > 0 and sales_count > 0 and impl_count / max(sales_count, 1) >= 3:
        ratio = impl_count // max(sales_count, 1)
        org.append({
            "action": f"组织配比优化——从{sales_count}:{impl_count}（重交付轻销售）调整为更健康的{sales_count+2}:{impl_count-1}",
            "how": [
                "不是裁人，是转岗：从实施团队选拔最优秀的1-2人转到CSM/售前支持，发挥他们的产品理解和客户关系优势",
                "实施团队推行交付SOP标准化：常见项目类型制作交付模板（标准实施计划/配置清单/培训大纲），人均年交付量提升20%",
                "建立销售-实施利益联动：实施满意度纳入销售季度奖金考核（20%权重），销售签单时实施提前介入做需求确认",
                "实施负责人同时兼任CSM负责人——让交付能力延伸到客户经营，一举两得"
            ],
            "owner": "老板（结构调整决策）+ 实施负责人（SOP建立+CSM兼任）",
            "kpi": f"人均产出从{per_head:.0f}万/年→65万+/年（12个月内），实施人效提升20%，客诉率下降"
        })
    strategies["org"] = org

    # 7.5 经营层面建议
    mgmt = []
    if not data.get("has_weekly_meeting"):
        mgmt.append({
            "action": "建立经营节奏——周会+月度经营会2467体系起步版",
            "how": [
                "每周五下午30分钟周会（绿黄红三色结构）：每人2分钟——本周结果/风险/阻塞/下周TOP1，不讲过程不讲故事",
                "每月2号出简易经营报表（Excel即可，6项核心指标：收入/新签/续费/新客数/续费率/毛利率），花30分钟填完",
                "每月6号30分钟经营共识会：看数据→找差距→定本月TOP3行动→出任务令（一事一令、一令一闭环）",
                "老板的时间分配从'盯每一单'升级到'盯三个数'：续约率（存量健康度）、商机转化率（销售健康度）、人均产出（组织健康度）"
            ],
            "owner": "老板主持（前3个月亲自建立节奏）+ 后续培养1名经营助理做数据",
            "kpi": "3个月内建立基本经营节奏，6个月内实现数据周周可见、月月可追溯、决策有据可依"
        })
    strategies["mgmt"] = mgmt

    return strategies


# ── v3.0 暖心寄语生成器 ────────────────────────────────────────
def generate_warm_closing(data, stage, assessment):
    """生成暖心寄语（100-150字）"""
    owner_name = data.get("owner_name", "伙伴负责人")
    years = data.get("years", 0)
    arr = data.get("arr", 0)
    competencies = assessment.get("competencies", [])
    issues = assessment.get("issues", [])

    parts = []

    # 开场：基于年限
    if years >= 10:
        parts.append(
            f"{owner_name}老师，{years}年不是一个小数字。能在一座城市、一个赛道坚持{years}年，"
            f"这本身就是一种力量——不是爆发力，是持久力。"
        )
    elif years >= 5:
        parts.append(
            f"{owner_name}老师，{years}年的积累已经让公司有了稳健的底盘。"
            f"{arr}万存量ARR不是数字，是{years}年交付品质换来的客户信任票。"
        )
    else:
        parts.append(
            f"{owner_name}老师，每一位走过初创期的伙伴都值得尊敬。"
            f"您当下的思考，恰恰说明您在想更大的事——这是好事。"
        )

    # 中段：肯定资产
    if len(competencies) >= 3:
        comp_names = [c["name"] for c in competencies[:3]]
        parts.append(
            f"您手里有三张好牌——{'、'.join(comp_names)}。"
            f"现在的课题不是换牌，是优化出牌顺序。"
        )

    # 展望
    if issues:
        issue_names = [i["name"] for i in issues[:2]]
        parts.append(
            f"{'和'.join(issue_names)}这两个方向一旦突破，以您已有的底子，增长的加速度会超出预期。"
        )

    # 收尾
    parts.append(
        "量子蜂群始终是您的后盾。我们一起把结构调整到位，把节奏建立起来。"
        "不着急、不焦虑、一步一步来——方向对了，剩下的交给时间。"
        "下一次复盘，我们一起看改变。"
    )

    return "".join(parts)


# ── ARR增长陷阱检测（DAY1《从会算账到能挣钱》）───────────────
def diagnose_arr_trap(data):
    """检测ARR增长陷阱。
    
    核心公式：新购率 + 增购率 > 流失率
    返回：{status, new_purchase_rate, upsell_rate, churn_rate, analysis}
    """
    new_arr = data.get("new_arr", 0) or (data.get("revenue", 0) * data.get("new_purchase_ratio", 0.5))
    upsell_arr = data.get("upsell_arr", 0)
    renewal = data.get("renewal", 80) / 100.0
    arr = data.get("arr", 0)
    
    if arr <= 0:
        return {"status": "❓", "analysis": "ARR数据缺失，无法计算增长陷阱", "message": "请提供存量ARR和新增ARR"}
    
    churn_rate = 1 - renewal
    should_renew_arr = arr * data.get("should_renew_ratio", 0.6)
    new_rate = new_arr / should_renew_arr if should_renew_arr > 0 else 0
    upsell_rate = upsell_arr / should_renew_arr if should_renew_arr > 0 else 0
    
    growth_gap = new_rate + upsell_rate - churn_rate
    
    if growth_gap > 0.05:
        status = "🟢 安全"
        detail = f"新购率{new_rate:.0%}+增购率{upsell_rate:.0%} > 流失率{churn_rate:.0%}，ARR处于增长通道"
    elif growth_gap > 0:
        status = "🟡 接近陷阱"
        detail = f"新购率{new_rate:.0%}+增购率{upsell_rate:.0%}仅微超流失率{churn_rate:.0%}，稍有波动即陷入增长停滞"
    elif growth_gap > -0.05:
        status = "🟠 增长停滞"
        detail = f"新购率{new_rate:.0%}+增购率{upsell_rate:.0%} ≈ 流失率{churn_rate:.0%}，ARR将长期横盘"
    else:
        status = "🔴 陷入陷阱"
        detail = f"新购率{new_rate:.0%}+增购率{upsell_rate:.0%} < 流失率{churn_rate:.0%}，ARR正在萎缩"
    
    return {
        "status": status,
        "growth_gap": growth_gap,
        "new_rate": new_rate,
        "upsell_rate": upsell_rate,
        "churn_rate": churn_rate,
        "analysis": detail,
        "message": f"核心公式检查：新购率+增购率必须>流失率。当前缺口{abs(growth_gap):.1%}。"
    }


# ── 合同质量速判（DAY1《从会算账到能挣钱》）───────────────────
def check_contract_quality(data):
    """基于高质量签约三标准检查合同质量。
    
    标准：实施÷ARR ≤ 2 / ARR占比 ≥ 60% / 项目毛利率 ≥ 25%
    """
    results = []
    
    # 实施÷ARR
    impl_ratio = data.get("impl_ratio", 0)
    avg_arr = data.get("avg_arr", 0)
    impl_days = data.get("avg_impl_days", 0)
    daily_rate = data.get("daily_rate", 2000)
    if impl_ratio == 0 and avg_arr > 0 and impl_days > 0:
        impl_ratio = (impl_days * daily_rate) / (avg_arr * 10000) if avg_arr > 0 else 0
    
    if impl_ratio > 0:
        if impl_ratio <= 1.5:
            results.append({"indicator": "实施÷ARR", "value": f"{impl_ratio:.1f}", "level": "✅", "note": "能耗低，交付轻"})
        elif impl_ratio <= 2.0:
            results.append({"indicator": "实施÷ARR", "value": f"{impl_ratio:.1f}", "level": "⚠️", "note": "能耗偏高，注意控制实施体量"})
        else:
            results.append({"indicator": "实施÷ARR", "value": f"{impl_ratio:.1f}", "level": "🚨", "note": "能耗太高，交付太重，长期不划算"})
    
    # ARR占比
    arr_ratio = data.get("arr_ratio", 0) or data.get("subscription_ratio", 0)
    if arr_ratio > 0:
        if arr_ratio >= 0.7:
            results.append({"indicator": "ARR占比", "value": f"{arr_ratio:.0%}", "level": "✅", "note": "续费驱动力强"})
        elif arr_ratio >= 0.5:
            results.append({"indicator": "ARR占比", "value": f"{arr_ratio:.0%}", "level": "⚠️", "note": "一次性收入比例偏高"})
        else:
            results.append({"indicator": "ARR占比", "value": f"{arr_ratio:.0%}", "level": "🚨", "note": "过于依赖一次性收入，续费基础薄弱"})
    
    # 项目毛利率
    gross_margin = data.get("gross_margin", 0) or data.get("project_margin", 0)
    if gross_margin > 0:
        if gross_margin >= 35:
            results.append({"indicator": "项目毛利率", "value": f"{gross_margin}%", "level": "✅", "note": "利润空间健康"})
        elif gross_margin >= 25:
            results.append({"indicator": "项目毛利率", "value": f"{gross_margin}%", "level": "⚠️", "note": "利润偏薄，需关注降本"})
        else:
            results.append({"indicator": "项目毛利率", "value": f"{gross_margin}%", "level": "🚨", "note": "微利甚至亏损，必须重审定价和成本"})
    
    return results


# ── 利润质量检测（DAY1《从会算账到能挣钱》）───────────────────
def check_profit_quality(data):
    """检测利润含金量：是否纸面富贵？是否隐性成本漏算？"""
    issues = []
    
    # 收款÷利润（判断利润是纸面还是现钱）
    collection = data.get("collection", 0)
    profit = data.get("profit", 0)
    if collection > 0 and profit > 0:
        ar_ratio = data.get("receivable", collection - data.get("cash_inflow", collection * 0.7)) / profit if profit > 0 else 0
        if ar_ratio > 2:
            issues.append({"type": "🚨", "detail": f"应收账款/利润={ar_ratio:.1f}倍，利润是纸面富贵，现金并未落袋"})
        elif ar_ratio > 1:
            issues.append({"type": "⚠️", "detail": f"应收账款/利润={ar_ratio:.1f}倍，注意回款节奏"})
    
    # 隐性成本漏算检查
    cost_checks = []
    if data.get("forgot_vat") is True or data.get("include_vat") is False:
        cost_checks.append("增值税（约合同额的4.5%）可能未计入项目核算")
    if data.get("forgot_renewal_cost") is True:
        cost_checks.append("续费成本（约实施费的20%）可能被忽略")
    if data.get("forgot_travel") is True:
        cost_checks.append("异地差旅费未计入项目成本")
    if data.get("forgot_amortization") is True:
        cost_checks.append("房租/设备折旧等摊销未计入月度成本")
    
    if cost_checks:
        issues.append({"type": "⚠️", "detail": "隐性成本漏算：" + "；".join(cost_checks)})
    
    # 人天成本检查
    daily_cost = data.get("daily_cost", 0)
    daily_price = data.get("daily_price", 0) or data.get("daily_rate", 0)
    if daily_cost > 0 and daily_price > 0:
        markup = daily_price / daily_cost
        if markup < 1.3:
            issues.append({"type": "🚨", "detail": f"报价/成本比={markup:.1f}倍（<1.3倍），项目接近亏损边缘"})
        elif markup < 1.5:
            issues.append({"type": "⚠️", "detail": f"报价/成本比={markup:.1f}倍（<1.5倍），毛利过薄"})
    
    return issues


# ── 项目利润速算（DAY1《从会算账到能挣钱》）───────────────────
def quick_project_pnl(product_price, impl_days, daily_price, daily_cost, 
                       team_size=1, tax_rate=0.06, has_travel=False,
                       commission_rate=0.05):
    """快速计算单个项目盈亏
    
    例：
    >>> quick_project_pnl(43600, 50, 1800, 1000)
    → 报价13.36万，客户预算10万时亏损2100元
    """
    product_net = product_price / (1 + tax_rate)
    impl_total = impl_days * daily_price
    contract = product_price + impl_total
    contract_net = product_net + impl_total
    
    # 成本
    product_cost = product_price * commission_rate
    salary_cost = impl_days * daily_cost
    travel_cost = impl_days * 200 if has_travel else 0  # 异地差旅估算
    tax = contract_net * tax_rate
    total_cost = salary_cost + tax + travel_cost + product_price * commission_rate
    
    profit = contract_net - total_cost
    margin = profit / contract_net if contract_net > 0 else 0
    
    return {
        "contract_total": contract,
        "contract_net": contract_net,
        "total_cost": total_cost,
        "profit": profit,
        "margin": margin,
        "verdict": "✅ 有利润" if profit > 0 else "🔴 亏损",
        "daily_cost_breakdown": {
            "salary": salary_cost / impl_days if impl_days > 0 else 0,
            "tax_per_day": tax / impl_days if impl_days > 0 else 0,
            "travel_per_day": travel_cost / impl_days if impl_days > 0 else 0,
        }
    }


# ── SLAAS vs 买断决策辅助（DAY1《从会算账到能挣钱》）───────────
def saas_vs_perpetual_comparison(product_price, impl_price, subscription_ratio=0.6, years=5):
    """SaaS订阅 vs 买断模式的5年累计对比"""
    # 假设：订阅返款60%，续费40%
    saas_y1 = product_price * 0.6 + impl_price
    saas_yearly = product_price * 0.4  # 后续年份
    saas_cumulative = [saas_y1 + saas_yearly * i for i in range(years)]
    
    # 买断：首次全部返款，后续运维费10%
    perpetual_y1 = product_price * 0.8 + impl_price
    perpetual_yearly = product_price * 0.1
    perpetual_cumulative = [perpetual_y1 + perpetual_yearly * i for i in range(years)]
    
    return {
        "saas": {"y1": saas_y1, "yearly_after": saas_yearly, "cumulative_5y": saas_cumulative[-1]},
        "perpetual": {"y1": perpetual_y1, "yearly_after": perpetual_yearly, "cumulative_5y": perpetual_cumulative[-1]},
        "winner": "SaaS订阅" if saas_cumulative[-1] > perpetual_cumulative[-1] else "买断",
        "diff_5y": saas_cumulative[-1] - perpetual_cumulative[-1],
    }


# ── 利润格局四象限（可视化经营分析会）────────────────────────
def check_profit_pattern(data):
    """检查利润格局，返回结果"""
    revenue_trend = data.get("revenue_trend", "→")  # ↑/→/↓
    profit_trend = data.get("profit_trend", "→")
    
    patterns = {
        ("↑", "↑"): ("🟢 健康增长", "目标与能力匹配", "safe"),
        ("↓", "↑"): ("🟢 提质增效", "主动收缩，聚焦利润", "safe"),
        ("↑", "↓"): ("🟡 增收不增利", "规模虚胖，利润失血——倒闭三步曲第1步", "warning"),
        ("↓", "↓"): ("🔴 双降", "失去增长动力——极度危险", "danger"),
    }
    default = ("❓ 未知", "请提供收入/利润环比趋势", "unknown")
    return patterns.get((revenue_trend, profit_trend), default)


def judge_stage(data):
    """根据营收和团队人数判定4阶段（经盈工作坊版）"""
    revenue = data.get("revenue", 0)
    team_size = data.get("team_size", 0)

    # 营收虚高判定：团队不达标时按团队判定（人财物销：人>财>物>销）
    for s in STAGE_STANDARDS:
        rev_ok = True
        if "revenue_min" in s and revenue < s["revenue_min"]:
            rev_ok = False
        if "revenue_max" in s and revenue > s["revenue_max"]:
            rev_ok = False
        if rev_ok:
            # 营收匹配的阶段，再验证团队
            team_ok = True
            if "team_min" in s and team_size < s["team_min"]:
                team_ok = False
            if "team_max" in s and team_size > s["team_max"]:
                team_ok = False
            if team_ok:
                return s, False  # (stage, is_virtual)
            else:
                # 营收达标但团队不达标 → 营收虚高
                # 按团队规模重新判定
                for ts in STAGE_STANDARDS:
                    to = True
                    if "team_min" in ts and team_size < ts["team_min"]:
                        to = False
                    if "team_max" in ts and team_size > ts["team_max"]:
                        to = False
                    if to:
                        return ts, True

    # Fallback: 最高或最低
    if revenue >= 3000:
        return STAGE_STANDARDS[-1], False
    return STAGE_STANDARDS[0], False


def check_health(data, stage_num):
    """对照健康度指标，逐项检查"""
    bench = HEALTH_BENCHMARK.get(stage_num, HEALTH_BENCHMARK[1])
    results = {"healthy": [], "warning": [], "danger": []}

    # 指标名称映射
    metrics = [
        ("revenue", "年营收（万元）", None),
        ("gross_margin", "毛利率（%）", "%"),
        ("cash_months", "现金流健康度（月）", "个月"),
        ("roi", "ROI（投入产出比）", None),
        ("monthly_leads", "月新增商机数", "个"),
        ("conversion", "商机转化率", "%"),
        ("avg_arr", "平均客单价·ARR（万元）", "万"),
        ("sales_cycle", "销售周期（月）", "个月"),
        ("total_clients", "客户总数", "家"),
        ("renewal", "客户续约率", "%"),
        ("upsell", "增购/转介绍占比", "%"),
        ("team_size", "团队规模（人）", "人"),
        ("per_head_revenue", "人均产出（万元/年）", "万"),
        ("turnover", "核心人员流失率", "%"),
    ]

    for key, label, unit in metrics:
        val = data.get(key)
        if val is None:
            continue
        lo, hi = bench.get(key, (None, None))
        status = "unknown"
        if lo is not None and hi is not None:
            if val < lo * 0.8:
                status = "danger"
            elif val < lo:
                status = "warning"
            elif val > hi * 1.2:
                status = "healthy"
            elif val > hi:
                status = "warning"
            else:
                status = "healthy"
        elif lo is not None:
            if val < lo * 0.8:
                status = "danger"
            elif val < lo:
                status = "warning"
            else:
                status = "healthy"
        elif hi is not None:
            if val > hi * 1.2:
                status = "danger"
            elif val > hi:
                status = "warning"
            else:
                status = "healthy"

        if status == "healthy":
            results["healthy"].append((label, val, unit))
        elif status == "warning":
            results["warning"].append((label, val, unit, lo, hi))
        elif status == "danger":
            results["danger"].append((label, val, unit, lo, hi))

    # 综合评级
    if len(results["danger"]) == 0 and len(results["warning"]) <= 1:
        grade = "A（优秀）"
    elif len(results["danger"]) == 0 and len(results["warning"]) <= 3:
        grade = "B（良好）"
    elif len(results["danger"]) <= 1 or len(results["warning"]) > 3:
        grade = "C（待改进）"
    else:
        grade = "D（危险）"

    return results, grade


def diagnose_six_models(data):
    """检查六度业务模型覆盖情况"""
    coverage = []
    for m in SIX_MODELS:
        # 简单启发式判断（实际应由LLM做）
        val = data.get(m["key"])
        if val is True:
            coverage.append((m["name"], "✅ 已覆盖", m["check"]))
        elif val is False:
            coverage.append((m["name"], "❌ 未覆盖", m["check"]))
        else:
            coverage.append((m["name"], "❓ 未知", m["check"]))
    return coverage


def generate_action_plan(data, stage, health_results, health_grade):
    """生成可执行改进方案（含经盈工作坊方法论）"""
    actions = {"immediate": [], "short_term": [], "mid_term": []}

    # 检查利润格局
    profit_pattern, profit_desc, profit_level = check_profit_pattern(data)
    if profit_level == "warning":
        actions["immediate"].append(
            f"🔴 利润格局预警：{profit_pattern}——{profit_desc}。"
            f"立即排查利润失血原因，控制成本结构"
        )
    elif profit_level == "danger":
        actions["immediate"].append(
            f"🚨 利润格局危险：{profit_pattern}——{profit_desc}。"
            f"立即评估是否触及盈亏平衡线，出专项应对方案"
        )

    # 基于危险指标生成立即行动（P0）
    for item in health_results["danger"]:
        label, val, unit, lo, hi = item
        if "续约率" in label:
            actions["immediate"].append(
                f"建立客户成功体系——续约率仅{val}%（标准≥{lo}%），"
                f"立即启动季度回访机制，排查流失风险客户"
            )
        elif "现金流" in label:
            actions["immediate"].append(
                f"优化现金流管理——当前仅{val}个月（标准≥{lo}个月），"
                f"立即压缩应收账款周期，延迟非必要支出"
            )
        elif "流失率" in label:
            actions["immediate"].append(
                f"核心人员流失率{val}%（标准≤{hi}%），"
                f"立即进行离职面谈，排查薪酬竞争力，启动关键人才保留计划"
            )

    # 基于阶段生成短期改进（P1）
    stage_num = stage["stage"]
    if stage_num == 1:
        actions["short_term"].append("建立FABM开源机制：锁定ABM精准名单+行业方案内容+定向触达（名单→画像→触达→培育四步）")
        actions["short_term"].append("聚焦1个行业试点（先画圈再划线：界定行业→锁定目标客户→标准话术→日复一日）")
        actions["short_term"].append("建立周会制度（绿黄红三色结构，≤60分钟），养成经营节奏")
    elif stage_num == 2:
        actions["short_term"].append("建制5-15人团队，明确销售/实施/客成分工（人>财>物>销，干部是第一位）")
        actions["short_term"].append("建立月度经营会2467节奏：2号出报表→4号出报告→6号共识会")
        actions["short_term"].append("建立初步任务令制度，重要事项一事一令，闭环管理")
    elif stage_num == 3:
        actions["short_term"].append("每月举办1-2场打单会，建立市场活动SOP（会前→会中→会后完整链路）")
        actions["short_term"].append("完成月度经营会2467体系建设——落实四可视闭环")
        actions["short_term"].append("建立OODA决策循环：观察→判断→决策→行动，从PDCA转向OODA")

    # 中期建设（P2）
    actions["mid_term"].append(f"制定跃迁至下一阶段的经营计划（一页纸：战略聚焦+目标+资源配置+TOP3风险+TOP3行动）")
    actions["mid_term"].append("建立季度经营健康度检视机制（14项指标+利润格局+倒闭三步曲检查）")
    actions["mid_term"].append("培养独立带团队的干部（人财物销：人是第一位，招高潜人才）")

    return actions


def format_report(partner_name, data, stage, is_virtual, health_results, health_grade, coverage, actions):
    """格式化输出诊断报告 v3.0（暖心版）"""
    now = datetime.now().strftime("%Y年%m月%d日")
    owner_name = data.get("owner_name", "伙伴负责人")

    # 生成v3.0新增板块
    assessment = generate_comprehensive_assessment(data, stage, is_virtual, health_results, health_grade, coverage)
    strategies = generate_business_strategies(data, stage, health_results, coverage)
    warm_closing = generate_warm_closing(data, stage, assessment)

    lines = []
    lines.append(f"# {partner_name}伙伴业务诊断报告")
    lines.append(f"> 🎯 致：**{owner_name}老师**")
    lines.append(f"> 诊断时间：{now}")
    lines.append(f"> 诊断依据：《纷享销客伙伴盈利手册3.0》+ 经盈工作坊第一期")
    lines.append(f"> 诊断Agent：伙伴业务诊断Agent v3.0 | 量子蜂群·谋略司")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ═══════════════════════════════════════════
    # 零、综合判断与评价（v3.0核心板块）
    # ═══════════════════════════════════════════
    lines.append("## 零、综合判断与评价 ⭐")
    lines.append("")
    lines.append(f"> {assessment['one_line']}")
    lines.append("")

    # 核心竞争力
    lines.append("### 💎 核心竞争力（我们已有的资产）")
    lines.append("")
    lines.append("| # | 能力/资产 | 描述 | 战略价值 |")
    lines.append("|---|------|------|:---:|")
    for i, comp in enumerate(assessment["competencies"], 1):
        lines.append(f"| {i} | **{comp['name']}** | {comp['desc']} | {comp['value']} |")
    lines.append("")

    # 结构性改善课题
    lines.append("### 🔧 结构性改善课题（我们一起努力的方向）")
    lines.append("")
    lines.append("| # | 课题 | 紧迫度 | 核心逻辑 |")
    lines.append("|---|------|:---:|------|")
    for i, issue in enumerate(assessment["issues"], 1):
        lines.append(f"| {i} | **{issue['name']}** | {issue['urgency']} | {issue['logic']} |")
    lines.append("")

    # 综合评分卡
    sc = assessment["scorecard"]
    lines.append("### 📊 综合评分卡")
    lines.append("")
    lines.append("| 维度 | 得分 | 评价 |")
    lines.append("|------|:---:|------|")
    lines.append(f"| 经营健康度 | {sc['health_grade']} | {'需要系统性改善' if 'C' in sc['health_grade'] or 'D' in sc['health_grade'] else '良好'} |")
    lines.append(f"| 业务模型覆盖 | {sc['coverage']} | {'基础覆盖不足' if int(sc['coverage'][0]) < 3 else '已有一定覆盖'} |")
    lines.append(f"| 利润格局 | {sc['profit']} | {'⚠️ 需关注' if sc['profit_level'] == 'warning' else '🟢 安全' if sc['profit_level'] == 'safe' else '❓ 待确认'} |")
    lines.append("")

    # ═══════════════════════════════════════════
    # 一、阶段判定
    # ═══════════════════════════════════════════
    lines.append("---")
    lines.append("")
    lines.append("## 一、阶段判定")
    lines.append(f"**当前阶段：{stage['color']} {stage['name']}**（{stage.get('years', '')}）")
    lines.append("")

    if is_virtual:
        lines.append("⚠️ **营收虚高警告**：营收达到本阶段标准，但团队规模不足。"
                     "根据「人财物销」能力构建序——放量前必须先建团队，"
                     f"实际发展阶段按团队规模判定为 **{stage['name']}**。")
        lines.append("")

    lines.append(f"- 年营收：{data.get('revenue', '?')} 万"
                f"（标准：{stage.get('revenue_min', 0)}-{stage.get('revenue_max', '∞')}万）")
    lines.append(f"- 团队规模：{data.get('team_size', '?')} 人"
                f"（标准：{stage.get('team_min', 1)}-{stage.get('team_max', '∞')}人）")
    lines.append(f"- 存量ARR：{data.get('arr', '?')} 万")
    lines.append(f"- 客户总数：{data.get('total_clients', '?')} 家")
    lines.append("")

    # 阶段特征自判
    if "features" in stage:
        lines.append("**阶段特征自判**（符合3条以上确认）：")
        for feat in stage["features"]:
            lines.append(f"  □ {feat}")
        lines.append("")

    # 下一阶段门槛
    nxt_idx = stage["stage"]
    if nxt_idx < len(STAGE_STANDARDS):
        ns = STAGE_STANDARDS[nxt_idx]
        lines.append(f"**下一阶段（{ns['name']}）门槛：**")
        rev_cur = data.get('revenue', 0) or 0
        team_cur = data.get('team_size', 0) or 0
        rev_gap = max(0, (ns.get('revenue_min', 0) or 0) - rev_cur)
        team_gap = max(0, (ns.get('team_min', 0) or 0) - team_cur)
        lines.append(f"- 营收达到 {ns.get('revenue_min', '?')} 万以上（当前：{rev_cur}万，缺口：{rev_gap}万）")
        lines.append(f"- 团队扩大到 {ns.get('team_min', '?')} 人以上（当前：{team_cur}人，缺口：{team_gap}人）")
    else:
        lines.append("**已到达最高阶段（战略共赢期）**，建议聚焦生态共建与全国布局，践行品类思维。")
    lines.append("")

    # 利润格局检查
    profit_pattern, profit_desc, profit_level = check_profit_pattern(data)
    lines.append("**利润格局判断**（倒闭三步曲检查）：")
    lines.append(f"- {profit_pattern}：{profit_desc}")
    lines.append("")

    # ═══════════════════════════════════════════
    # 二、健康度诊断
    # ═══════════════════════════════════════════
    lines.append("## 二、健康度诊断")
    lines.append(f"**综合健康度评级：{health_grade}**")
    lines.append("")
    if health_results["healthy"]:
        lines.append("✅ **健康指标（≥标准值）：**")
        for label, val, unit in health_results["healthy"]:
            u = unit or ""
            lines.append(f"  - {label}：{val}{u}")
        lines.append("")
    if health_results["warning"]:
        lines.append("⚠️ **预警指标（低于标准值20%内）：**")
        for label, val, unit, lo, hi in health_results["warning"]:
            u = unit or ""
            lines.append(f"  - {label}：{val}{u}（标准：{lo}-{hi}{u}）")
        lines.append("")
    if health_results["danger"]:
        lines.append("🚨 **危险指标（低于标准值20%以上）：**")
        for label, val, unit, lo, hi in health_results["danger"]:
            u = unit or ""
            lines.append(f"  - {label}：{val}{u}（标准：{lo}-{hi}{u}）⚡P0优先级")
        lines.append("")

    # ═══════════════════════════════════════════
    # 三、六度业务模型覆盖诊断
    # ═══════════════════════════════════════════
    lines.append("## 三、六度业务模型覆盖诊断")
    lines.append("")
    for name, status, check in coverage:
        lines.append(f"- **{name}**：{status} —— {check}")
    lines.append("")

    # ═══════════════════════════════════════════
    # 四、TOP5共性问题
    # ═══════════════════════════════════════════
    lines.append("## 四、TOP5共性问题排查")
    lines.append("")
    for iss in TOP5_ISSUES:
        lines.append(f"- {iss['level']} **{iss['name']}**（{iss['priority']}）：{iss['desc']}")
    lines.append("")

    # ═══════════════════════════════════════════
    # 四点五、财务经营诊断（v3.1新增·DAY1《从会算账到能挣钱》）
    # ═══════════════════════════════════════════
    lines.append("## 四点五、财务经营诊断 🧮")
    lines.append("")
    lines.append("> 📌 诊断依据：从[会算账]到[能挣钱]（郭保彬，2026.05）——赚钱不只是收款多，要看三张表和经营逻辑。")
    lines.append("")

    # ARR增长陷阱
    arr_trap = diagnose_arr_trap(data)
    lines.append(f"### ARR增长陷阱检测：{arr_trap['status']}")
    lines.append("")
    lines.append(f"> 核心公式：新购率 + 增购率 > 流失率。{arr_trap['analysis']}")
    lines.append(f"> {arr_trap['message']}")
    lines.append("")

    # 合同质量
    contract_quality = check_contract_quality(data)
    if contract_quality:
        lines.append("### 合同质量速判")
        lines.append("")
        lines.append("| 指标 | 数值 | 评级 | 说明 |")
        lines.append("|------|:---:|:---:|------|")
        for cq in contract_quality:
            lines.append(f"| {cq['indicator']} | {cq['value']} | {cq['level']} | {cq['note']} |")
        lines.append("")

    # 利润质量
    profit_quality = check_profit_quality(data)
    if profit_quality:
        lines.append("### 利润质量检测")
        lines.append("")
        for pq in profit_quality:
            lines.append(f"- {pq['type']} {pq['detail']}")
        lines.append("")

    # 认知误区自检
    lines.append("### 5大经营认知误区自检")
    lines.append("")
    misconceptions = [
        ("收款多就是赚钱了", "利润≠收款，看利润表和权责发生制"),
        ("合同签了就是收入", "收入≠合同金额，按规则分摊确认"),
        ("账户有钱=公司赚钱", "可能是预收款/借款/投资款"),
        ("报价比成本高就OK", "没算隐性成本（续费/增值税/差旅）"),
        ("规模大了自然利润好", "SaaS规模≠利润，关注ARR增长陷阱"),
    ]
    for i, (misconception, truth) in enumerate(misconceptions, 1):
        lines.append(f"| {i} | {misconception} | → | {truth} |")
    lines.append("")

    # ═══════════════════════════════════════════
    # 五、核心问题总结
    # ═══════════════════════════════════════════
    lines.append("## 五、核心问题总结")
    lines.append("")
    prio = []
    if profit_level == "warning":
        prio.append(f"【P0】{profit_pattern}——{profit_desc}")
    elif profit_level == "danger":
        prio.append(f"【P0】🚨 {profit_pattern}——{profit_desc}，必须出专项方案")
    for item in health_results["danger"]:
        prio.append(f"【P0】{item[0]}严重偏离标准（当前{item[1]}，标准≥{item[3]}）")
    for item in health_results["warning"]:
        prio.append(f"【P1】{item[0]}偏低（当前{item[1]}，标准{item[3]}-{item[4]}）")
    for name, status, _ in coverage:
        if "❌" in status:
            prio.append(f"【P1】{name}尚未覆盖，建议尽快建立")
    for i, p in enumerate(prio[:5]):
        lines.append(f"{i+1}. {p}")
    lines.append("")

    # ═══════════════════════════════════════════
    # 六、业务策略与方法建议（v3.0新增）
    # ═══════════════════════════════════════════
    lines.append("## 六、业务策略与方法建议 ⭐")
    lines.append("")
    lines.append("> 📌 以下策略不是泛泛的'加强管理'，而是贴合当前阶段和团队实际的具体打法。每条都有'怎么做/谁来主导/何时见效'三层。")
    lines.append("")

    # 6.1 开源获客
    if strategies.get("prospecting"):
        lines.append("### 6.1 🎣 开源获客策略")
        for s in strategies["prospecting"]:
            lines.append(f"**{s['action']}**")
            lines.append("")
            lines.append("**怎么做：**")
            for h in s["how"]:
                lines.append(f"- {h}")
            lines.append(f"- **谁来主导**：{s['owner']}")
            lines.append(f"- **预期效果**：{s['kpi']}")
            lines.append("")

    # 6.2 销售能力
    if strategies.get("sales"):
        lines.append("### 6.2 🚀 销售能力建设")
        for s in strategies["sales"]:
            lines.append(f"**{s['action']}**")
            lines.append("")
            lines.append("**怎么做：**")
            for h in s["how"]:
                lines.append(f"- {h}")
            lines.append(f"- **谁来主导**：{s['owner']}")
            lines.append(f"- **预期效果**：{s['kpi']}")
            lines.append("")

    # 6.3 客户经营
    if strategies.get("retention"):
        lines.append("### 6.3 💝 客户经营深化")
        for s in strategies["retention"]:
            lines.append(f"**{s['action']}**")
            lines.append("")
            lines.append("**怎么做：**")
            for h in s["how"]:
                lines.append(f"- {h}")
            lines.append(f"- **谁来主导**：{s['owner']}")
            lines.append(f"- **预期效果**：{s['kpi']}")
            lines.append("")

    # 6.4 组织效能
    if strategies.get("org"):
        lines.append("### 6.4 ⚙️ 组织效能优化")
        for s in strategies["org"]:
            lines.append(f"**{s['action']}**")
            lines.append("")
            lines.append("**怎么做：**")
            for h in s["how"]:
                lines.append(f"- {h}")
            lines.append(f"- **谁来主导**：{s['owner']}")
            lines.append(f"- **预期效果**：{s['kpi']}")
            lines.append("")

    # 6.5 经营层面
    if strategies.get("mgmt"):
        lines.append("### 6.5 📋 经营层面建议")
        for s in strategies["mgmt"]:
            lines.append(f"**{s['action']}**")
            lines.append("")
            lines.append("**怎么做：**")
            for h in s["how"]:
                lines.append(f"- {h}")
            lines.append(f"- **谁来主导**：{s['owner']}")
            lines.append(f"- **预期效果**：{s['kpi']}")
            lines.append("")

    # ═══════════════════════════════════════════
    # 七、可执行改进方案
    # ═══════════════════════════════════════════
    lines.append("## 七、可执行改进方案")
    lines.append("")
    if actions["immediate"]:
        lines.append("### 🚨 立即行动（0-30天，P0）")
        for i, a in enumerate(actions["immediate"], 1):
            lines.append(f"{i}. {a}")
        lines.append("")
    if actions["short_term"]:
        lines.append("### 📅 短期改进（30-90天，P1）")
        for i, a in enumerate(actions["short_term"], 1):
            lines.append(f"{i}. {a}")
        lines.append("")
    if actions["mid_term"]:
        lines.append("### 🎯 中期建设（90-180天，P2）")
        for i, a in enumerate(actions["mid_term"], 1):
            lines.append(f"{i}. {a}")
        lines.append("")

    # ═══════════════════════════════════════════
    # 八、阶段跃迁路径
    # ═══════════════════════════════════════════
    lines.append("## 八、阶段跃迁路径")
    lines.append("")
    lines.append(f"当前阶段：{stage['name']}")
    if stage["stage"] < len(STAGE_STANDARDS):
        ns = STAGE_STANDARDS[stage["stage"]]
        rev_gap = max(0, (ns.get("revenue_min", 0) or 0) - (data.get("revenue", 0) or 0))
        team_gap = max(0, (ns.get("team_min", 0) or 0) - (data.get("team_size", 0) or 0))
        lines.append(f"下一阶段：{ns['name']}")
        lines.append(f"- 营收缺口：{rev_gap}万")
        lines.append(f"- 团队缺口：{team_gap}人")
        lines.append(f"- 关键能力：[根据五力诊断结果补充]")
    lines.append("")

    # 赋能重心建议
    lines.append("**建议赋能重心**（8选3）：")
    lines.append(f"  □ {' □ '.join(ENABLEMENT_OPTIONS[:4])}")
    lines.append(f"  □ {' □ '.join(ENABLEMENT_OPTIONS[4:])}")
    lines.append("")

    # ═══════════════════════════════════════════
    # 九、暖心寄语（v3.0新增）
    # ═══════════════════════════════════════════
    lines.append("---")
    lines.append("")
    lines.append("## 九、暖心寄语 💌")
    lines.append("")
    lines.append(f"> {warm_closing}")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("\n*本报告由伙伴业务诊断Agent v3.0生成 | 基于《伙伴盈利手册3.0》+ 经盈工作坊第一期 | 量子蜂群·谋略司*")

    return "\n".join(lines)


def parse_input_file(filepath):
    """从会议纪要/文字描述中提取关键字段（简单启发式，实际由LLM调用）"""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    data = {}
    # 简单正则提取数字+关键词
    patterns = {
        "revenue": [r"(?:年.*?营收|营收.*?)([0-9]+)\s*万", r"ARR.*?([0-9]+)\s*万"],
        "team_size": [r"团队.*?([0-9]+)\s*人", r"([0-9]+)\s*人.*?团队"],
        "arr": [r"ARR.*?([0-9]+)\s*万"],
        "total_clients": [r"客户.*?([0-9]+)\s*(?:家|个)", r"([0-9]+)\s*(?:家|个).*?客户"],
        "renewal": [r"续约.*?([0-9]+)\s*%", r"续费.*?([0-9]+)\s*%"],
    }
    for key, pats in patterns.items():
        for pat in pats:
            m = re.search(pat, text)
            if m:
                data[key] = float(m.group(1))
                break
    return data


def main():
    parser = argparse.ArgumentParser(description="伙伴业务诊断Agent")
    parser.add_argument("--input", help="输入文件路径（会议纪要/文字描述）")
    parser.add_argument("--json", help="直接传入JSON数据")
    parser.add_argument("--name", default="XX伙伴", help="伙伴名称")
    args = parser.parse_args()

    if args.json:
        data = json.loads(args.json)
    elif args.input:
        data = parse_input_file(args.input)
        # 交互式补充
        print("⚠️ 文件解析完成，请确认/补充以下字段：")
        for k in ["revenue", "team_size", "arr", "total_clients", "renewal", "conversion"]:
            cur = data.get(k, "（未知）")
            val = input(f"  {k}（当前：{cur}）：") or None
            if val:
                data[k] = float(val)
    else:
        print("请提供 --input 或 --json 参数")
        sys.exit(1)

    # 执行诊断
    stage, is_virtual = judge_stage(data)
    health_results, health_grade = check_health(data, stage["stage"])
    coverage = diagnose_six_models(data)
    actions = generate_action_plan(data, stage, health_results, health_grade)
    report = format_report(args.name, data, stage, is_virtual, health_results, health_grade, coverage, actions)

    print(report)

    # 保存
    out = f"/tmp/{args.name}_诊断报告_{datetime.now().strftime('%Y%m%d')}.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ 报告已保存：{out}")


if __name__ == "__main__":
    main()

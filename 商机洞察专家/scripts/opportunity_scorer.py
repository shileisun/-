"""
商机洞察专家 · 商机洞察+线索开发全流程引擎 v2.0
==================================================
融合量子蜂群线索开发六步工作流，形成完整的客户发现→开发→转化Pipeline

工作流:
  Phase 1: 商机洞察（发现谁）→ 已建
  Phase 2: 线索开发（怎么打）→ 新增（融合量子蜂群Section 04）
  Phase 3: 营销执行（发什么）→ 新增
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple


FABM_DB = os.environ.get(
    "FABM_DB",
    os.path.join(
        os.environ.get("WORKBUDDY_WORKSPACE", os.path.expanduser("~/WorkBuddy")),
        "2026-06-06-12-26-28/alliance-system/data/alliance.db",
    ),
)


def get_db():
    if not os.path.exists(FABM_DB):
        return None
    db = sqlite3.connect(FABM_DB)
    db.row_factory = sqlite3.Row
    return db


# ─── CRM采购意向评分模型 ───

# 权重配置
WEIGHTS = {
    "industry_attractiveness": 0.25,     # 行业吸引力
    "company_scale": 0.25,               # 企业规模
    "digital_readiness": 0.20,           # 数字化需求紧迫度
    "current_tier": 0.15,                # 当前分层（已有触达基础）
    "regional_priority": 0.15,           # 区域优先级
}

# 行业CRM需求评分（1-10）
INDUSTRY_SCORES = {
    "制造业": 9,        # 离散制造CRM需求最旺盛
    "汽车零部件": 10,   # 汽配行业CRM需求极高（供应链管理+客户关系）
    "高端装备": 9,      # 装备制造业客户关系管理需求高
    "电子制造": 9,      # 电子制造CRM需求高
    "能源电力": 7,      # 能源行业需求中等，但预算充足
    "科技": 8,          # 科技公司CRM需求高
    "企业服务": 8,      # 企业服务自身就需CRM
    "消费品": 6,        # 消费品偏零售CRM
    "半导体芯片、集成电路": 8,
    "商业贸易": 6,
}

# 营收规模CRM需求得分
def scale_score(revenue_str: Optional[str]) -> Tuple[int, str]:
    if not revenue_str:
        return 5, "营收未知，默认中等"
    
    rev = revenue_str.strip()
    
    if "100亿" in rev or "200亿" in rev or "400亿" in rev:
        return 10, f"营收{rev}，大型企业CRM需求极高"
    if "50亿" in rev or "80亿" in rev or "60亿" in rev:
        return 9, f"营收{rev}，大中型企业需CRM支撑增长"
    if "10亿" in rev or "20亿" in rev or "30亿" in rev:
        return 8, f"营收{rev}，中型企业CRM标配化"
    if "5亿" in rev or "3亿" in rev:
        return 7, f"营收{rev}，成长型企业开始关注CRM"
    if "大型" in rev:
        return 8, f"大型企业，CRM需求明确"
    
    # 尝试解析数字
    try:
        val = float(rev.replace('亿', '').replace('元', '').replace('+', '').split('-')[0])
        if val >= 50:
            return 10, f"营收{rev}，大型企业CRM需求极高"
        elif val >= 10:
            return 8, f"营收{rev}，中型企业CRM需求明确"
        elif val >= 3:
            return 6, f"营收{rev}，成长型企业CRM潜力大"
        else:
            return 4, f"营收{rev}，小型企业CRM需求待培育"
    except:
        return 5, f"营收{rev}，评估中"

# 区域优先级（基于浙江产业集群）
CITY_PRIORITY = {
    "杭州": 10, "宁波": 10, "温州": 9, "嘉兴": 8,
    "绍兴": 8, "台州": 7, "湖州": 7, "金华": 7,
    "衢州": 6, "丽水": 5, "舟山": 5,
}

# 分层转评分
TIER_SCORE = {"A": 10, "B": 7, "C": 4, "D": 2}


def get_db_stats() -> Dict:
    """获取数据库统计"""
    db = get_db()
    if not db:
        return {"error": "数据库不可用"}
    
    cursor = db.cursor()
    stats = {}
    cursor.execute("SELECT COUNT(*) FROM customers")
    stats["total"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT tier, COUNT(*) FROM customers GROUP BY tier")
    stats["tiers"] = {r[0]: r[1] for r in cursor.fetchall()}
    
    cursor.execute("SELECT industry, COUNT(*) FROM customers GROUP BY industry ORDER BY COUNT(*) DESC LIMIT 5")
    stats["top_industries"] = [(r[0], r[1]) for r in cursor.fetchall()]
    
    db.close()
    return stats


def score_customer(row) -> Dict:
    """对单个客户进行CRM采购意向评分"""
    name = row["name"]
    industry = row["industry"] or "未知"
    city = row["city"] or "未知"
    tier = row["tier"] or "C"
    revenue = row["revenue_scale"]
    
    reasons = []
    
    # 1. 行业吸引力
    ind_score = INDUSTRY_SCORES.get(industry, 5)
    ind_label = "极高" if ind_score >= 9 else ("高" if ind_score >= 7 else "中")
    reasons.append(f"【行业】{industry}({ind_label})→{ind_score}分")
    
    # 2. 企业规模
    scale_s, scale_r = scale_score(revenue)
    reasons.append(f"【规模】{scale_r}")
    
    # 3. 数字化需求（基于行业+规模综合判断）
    digital_score = min(10, ind_score + (0.5 if scale_s >= 8 else 0) + (1 if tier in ["A", "B"] else 0))
    digital_score = int(digital_score)
    dig_label = "迫切" if digital_score >= 8 else "明显" if digital_score >= 6 else "一般"
    reasons.append(f"【需求】数字化转型{dig_label}→{digital_score}分")
    
    # 4. 当前分层
    tier_s = TIER_SCORE.get(tier, 5)
    tier_label = "已建立联系" if tier == "A" else ("有跟进基础" if tier == "B" else "待接触")
    reasons.append(f"【基础】{tier}层客户({tier_label})→{tier_s}分")
    
    # 5. 区域优先级
    city_base = city.split("（")[0].split("(")[0].strip()
    city_s = CITY_PRIORITY.get(city_base, 
                sum(v for k, v in CITY_PRIORITY.items() if k in city) 
                if any(k in city for k in CITY_PRIORITY) else 6)
    city_label = "核心" if city_s >= 9 else "重点" if city_s >= 7 else "一般"
    reasons.append(f"【区域】{city}({city_label})→{city_s}分")
    
    # 总分
    total = (
        ind_score * WEIGHTS["industry_attractiveness"] +
        scale_s * WEIGHTS["company_scale"] +
        digital_score * WEIGHTS["digital_readiness"] +
        tier_s * WEIGHTS["current_tier"] +
        city_s * WEIGHTS["regional_priority"]
    )
    total = round(total, 1)
    
    # 商机等级
    if total >= 8.5:
        level = "S级·绝对优先"
    elif total >= 7.5:
        level = "A级·高优先级"
    elif total >= 6.5:
        level = "B级·重点跟进"
    elif total >= 5.5:
        level = "C级·保持触达"
    else:
        level = "D级·长期培育"
    
    return {
        "name": name,
        "industry": industry,
        "city": city,
        "tier": tier,
        "revenue": revenue or "未知",
        "score": total,
        "level": level,
        "reasons": reasons,
        "dimensions": {
            "industry": ind_score,
            "scale": scale_s,
            "digital_demand": digital_score,
            "touch_basis": tier_s,
            "regional": city_s,
        }
    }


def run_analysis(
    industry_filter: Optional[str] = None,
    city_filter: Optional[str] = None,
    min_score: float = 0,
    limit: int = 50,
    tier_filter: Optional[str] = None,
) -> Dict:
    """
    运行商机洞察分析
    
    Args:
        industry_filter: 行业过滤（如"制造业"）
        city_filter: 城市过滤（如"杭州"）
        min_score: 最低评分（默认0, 建议7.5+）
        limit: 返回数量
        tier_filter: 分层过滤（如"A"）
    """
    db = get_db()
    if not db:
        return {"error": "FABM数据库不可用"}
    
    cursor = db.cursor()
    
    where_clauses = ["1=1"]
    params = []
    
    if industry_filter:
        where_clauses.append("industry LIKE ?")
        params.append(f"%{industry_filter}%")
    if city_filter:
        where_clauses.append("city LIKE ?")
        params.append(f"%{city_filter}%")
    if tier_filter:
        where_clauses.append("tier = ?")
        params.append(tier_filter)
    
    query = f"""
        SELECT name, industry, city, tier, revenue_scale
        FROM customers 
        WHERE {' AND '.join(where_clauses)}
        ORDER BY CASE tier WHEN 'A' THEN 0 WHEN 'B' THEN 1 WHEN 'C' THEN 2 ELSE 3 END
    """
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    db.close()
    
    # 评分
    scored = [score_customer(r) for r in rows]
    
    # 过滤+排序
    scored = [s for s in scored if s["score"] >= min_score]
    scored.sort(key=lambda x: x["score"], reverse=True)
    scored = scored[:limit]
    
    # 统计
    levels = {}
    for s in scored:
        lv = s["level"].split("·")[0]
        levels[lv] = levels.get(lv, 0) + 1
    
    # 总分区间
    avg = round(sum(s["score"] for s in scored) / len(scored), 1) if scored else 0
    
    # 推荐行动
    top = scored[:3] if scored else []
    actions = []
    for s in top:
        actions.append({
            "name": s["name"],
            "score": s["score"],
            "next_step": f"本周内联系{s['name']}的ERP/IT负责人，围绕{s['industry']}行业CRM需求展开沟通" if s["score"] >= 7.5
                       else f"发送行业CRM白皮书，预约电话沟通{s['name']}的数字化现状"
        })
    
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_analyzed": len(scored),
        "avg_score": avg,
        "level_distribution": levels,
        "top_opportunities": scored[:10] if scored else [],
        "recommended_actions": actions,
        "filters": {
            "industry": industry_filter,
            "city": city_filter,
            "tier": tier_filter,
            "min_score": min_score,
        },
        "top_level_summary": _generate_summary(scored, levels),
    }


def _generate_summary(scored: List[Dict], levels: Dict) -> str:
    """生成一句话总结"""
    if not scored:
        return "未找到符合条件的高意向客户"
    
    top = scored[0]
    s_count = levels.get("S级", 0)
    a_count = levels.get("A级", 0)
    
    parts = [f"共发现{len(scored)}个高意向客户"]
    if s_count:
        parts.append(f"其中S级绝对优先{s_count}个")
    if a_count:
        parts.append(f"A级高优先级{a_count}个")
    parts.append(f"最高分：{top['name']}（{top['score']}分）")
    parts.append(f"推荐本周先联系：{top['name']}")
    
    return "，".join(parts)


if __name__ == "__main__":
    import sys
    
    # 默认：跑全量分析，输出TOP15
    industry = sys.argv[1] if len(sys.argv) > 1 else None
    city = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = run_analysis(
        industry_filter=industry,
        city_filter=city,
        min_score=6.0,
        limit=20,
    )
    
    print(f"📊 商机洞察报告")
    print(f"   {result['top_level_summary']}")
    print(f"   均分: {result['avg_score']}")
    print(f"   分级: {result['level_distribution']}")
    print()
    
    print(f"{'排名':<6} {'客户名称':<20} {'行业':<12} {'城市':<8} {'评分':<6} {'等级':<16}")
    print("-" * 80)
    for i, opp in enumerate(result["top_opportunities"][:10], 1):
        print(f"{i:<6} {opp['name']:<20} {opp['industry']:<12} {opp['city']:<8} {opp['score']:<6} {opp['level']:<16}")
    
    print(f"\n推荐行动:")
    for action in result["recommended_actions"]:
        print(f"  ▶ {action['name']} ({action['score']}分): {action['next_step']}")


# ═══════════════════════════════════════════════════════
# Phase 2: 线索开发工作流（融合量子蜂群Section 04）
# ═══════════════════════════════════════════════════════

# 决策角色模型（基于策略赢单专家）
DECISION_ROLES = {
    "EB": "Economic Buyer（经济购买者）— CEO/董事长，关注ROI/战略价值",
    "T-CB": "Technical Coach（技术教练）— CIO/CTO，关注技术架构/可行性",
    "T-AB": "Technical Advisor（技术顾问）— 技术专家，关注细节/性能",
    "UB": "User Buyer（用户购买者）— 业务部门总监，关注日常使用价值",
    "EK": "Economic Killer（经济杀手）— 财务/采购，关注预算/商务条件",
}


def analyze_needs(customer_name: str, industry: str, revenue: str) -> Dict:
    """
    Phase 2 Step 1: 需求分析
    基于客户业务场景识别3-5个潜在商机
    """
    # 行业需求映射
    industry_needs = {
        "制造业": ["CRM系统升级", "供应链协同平台", "售后服务管理", "销售过程数字化", "客户数据中台"],
        "汽车零部件": ["供应商关系管理(SRM)", "售后质量追溯系统", "销售过程管理", "客户门户", "EDI数据交换"],
        "高端装备": ["售后服务管理", "备件管理", "项目型销售管理", "客户满意度管理"],
        "电子制造": ["客户关系管理", "订单管理", "售后服务体系", "销售预测分析"],
        "能源电力": ["大客户管理", "项目型销售管理", "售后服务调度", "合同管理"],
        "科技": ["销售漏斗管理", "客户成功管理", "订阅管理", "渠道管理"],
        "企业服务": ["销售过程管理", "客户成功管理", "合同管理", "服务工单"],
        "消费品": ["渠道管理", "终端门店管理", "促销管理", "经销商管理"],
    }
    
    needs = industry_needs.get(industry, ["CRM系统建设", "销售管理数字化", "客户服务升级", "数据分析决策"])
    
    # 按紧迫度排序（营收越高需求越迫切）
    rev_val = 0
    try:
        rev_str = revenue.replace('亿', '').replace('元', '').replace('+', '').split('-')[0]
        rev_val = float(rev_str)
    except:
        rev_val = 5
    
    return {
        "customer": customer_name,
        "industry": industry,
        "potential_needs": needs[:4],  # TOP4
        "urgency": "高" if rev_val >= 10 else ("中" if rev_val >= 5 else "低"),
        "estimated_budget": f"{'50-100' if rev_val >= 50 else '20-50' if rev_val >= 10 else '10-20' if rev_val >= 5 else '5-10'}万",
    }


def identify_decision_makers(customer_name: str, industry: str, tier: str) -> List[Dict]:
    """
    Phase 2 Step 2: 关键人识别与排序
    基于行业+规模预估决策链
    """
    # 行业关键人模板
    industry_roles = {
        "制造业": [
            {"role": "EB", "title": "CEO/总经理", "focus": "数字化转型ROI", "impact": 10},
            {"role": "T-CB", "title": "CIO/信息总监", "focus": "系统集成与架构", "impact": 9},
            {"role": "UB", "title": "销售总监", "focus": "销售效率提升", "impact": 8},
            {"role": "T-AB", "title": "IT经理", "focus": "技术实现细节", "impact": 6},
            {"role": "EK", "title": "财务总监", "focus": "预算与TCO", "impact": 7},
        ],
        "汽车零部件": [
            {"role": "EB", "title": "总经理/董事长", "focus": "客户关系+供应链", "impact": 10},
            {"role": "UB", "title": "销售/市场总监", "focus": "客户管理效率", "impact": 9},
            {"role": "T-CB", "title": "信息化负责人", "focus": "系统对接与数据", "impact": 8},
            {"role": "EK", "title": "财务总监", "focus": "投资回报周期", "impact": 7},
        ],
    }
    
    roles = industry_roles.get(industry, [
        {"role": "EB", "title": "CEO/董事长", "focus": "战略与ROI", "impact": 10},
        {"role": "T-CB", "title": "CIO/信息总监", "focus": "技术架构", "impact": 8},
        {"role": "UB", "title": "业务负责人", "focus": "业务价值", "impact": 8},
        {"role": "EK", "title": "财务负责人", "focus": "预算控制", "impact": 7},
    ])
    
    return roles


def generate_value_proposition(role: Dict, need: str, revenue: str) -> Dict:
    """
    Phase 2 Step 3: 价值主张生成
    为每个关键人定制价值主张
    """
    # 价值主张模板
    propositions = {
        "数字化转型ROI": f"通过纷享销客CRM，实现销售效率提升30%，客户转化率提升25%，年均可量化收益预估{revenue}的1-3%",
        "销售效率提升": "销售自动化+智能跟进提醒，人均产能提升40%，缩短销售周期30%",
        "客户关系+供应链": "打通供应商→生产→客户全链路数据，供应链协同效率提升50%",
        "系统集成与架构": "开放API+低代码平台，3个月完成CRM与现有系统集成",
    }
    
    # 匹配最相关的价值主张
    prop_key = role["focus"]
    prop = propositions.get(prop_key, f"针对{prop_key}，纷享销客CRM提供一站式解决方案，已为浙江{len([1])}家同类客户实现价值提升")
    
    return {
        "role": role["title"],
        "role_type": role["role"],
        "focus": role["focus"],
        "value": prop,
        "impact_score": role["impact"],
    }


def generate_outreach_email(
    customer_name: str, 
    role_title: str, 
    industry: str, 
    value_prop: str, 
    sender_name: str = "石磊",
    sender_company: str = "纷享销客浙江渠道"
) -> str:
    """
    Phase 2 Step 4: 营销邮件生成
    基于量子蜂群Section 04模板
    """
    return f"""邮件主题：{industry}数字化转型的新思路——基于浙江同行的实践

尊敬的{customer_name}{role_title}：

我是{sender_company}的{sender_name}，主要负责浙江区域CRM解决方案。

我们深入研究了{industry}行业的最新趋势，了解到贵公司正在推进数字化管理升级。我们曾为浙江多家{industry}企业提供了纷享销客CRM解决方案，实现了：

✓ 销售效率提升30%以上
✓ 客户转化率提升25%
✓ 客户信息管理从碎片化到集中化

{value_prop}

我们深知每个企业不同，想与您约15-20分钟的简短交流，或给您发送《{industry}行业CRM选型指南》。

无论您是否有近期规划，都希望能与您保持联系，为未来合作留一个机会。

期待您的回复。

{sender_name} | {sender_company}
{datetime.now().strftime('%Y年%m月%d日')}"""


# ═══════════════════════════════════════════════════════
# Phase 3: 完整Pipeline - 从洞察到邮件生成
# ═══════════════════════════════════════════════════════

def full_pipeline(customer_name: str) -> Dict:
    """
    对单个客户执行完整Pipeline:
    洞察→需求分析→关键人识别→价值主张→邮件
    """
    # 获取客户信息
    db = get_db()
    if not db:
        return {"error": "数据库不可用"}
    
    cursor = db.cursor()
    cursor.execute(
        "SELECT name, industry, city, tier, revenue_scale FROM customers WHERE name LIKE ? LIMIT 1",
        (f"%{customer_name}%",)
    )
    row = cursor.fetchone()
    db.close()
    
    if not row:
        return {"error": f"未找到客户: {customer_name}"}
    
    name = row["name"]
    industry = row["industry"] or "未知"
    city = row["city"] or "未知"
    tier = row["tier"] or "C"
    revenue = row["revenue_scale"] or "未知"
    
    # Phase 1: 商机洞察
    opportunity = score_customer(row)
    
    # Phase 2: 线索开发
    needs = analyze_needs(name, industry, revenue)
    roles = identify_decision_makers(name, industry, tier)
    
    contact_map = []
    for r in roles:
        vp = generate_value_proposition(r, needs["potential_needs"][0], revenue)
        email = generate_outreach_email(name, r["title"], industry, vp["value"])
        contact_map.append({**vp, "email_draft": email})
    
    return {
        "customer": name,
        "industry": industry,
        "city": city,
        "tier": tier,
        "revenue": revenue,
        "opportunity_score": opportunity["score"],
        "opportunity_level": opportunity["level"],
        "reasons": opportunity["reasons"],
        "potential_needs": needs["potential_needs"],
        "urgency": needs["urgency"],
        "estimated_budget": needs["estimated_budget"],
        "contact_plan": contact_map,
        "recommended_first_contact": contact_map[0] if contact_map else None,
    }


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "discover"

    if mode == "discover":
        # Phase 1: 商机洞察
        industry = sys.argv[2] if len(sys.argv) > 2 else None
        city = sys.argv[3] if len(sys.argv) > 3 else None

        result = run_analysis(
            industry_filter=industry,
            city_filter=city,
            min_score=6.0,
            limit=20,
        )

        print(f"📊 商机洞察报告")
        print(f"   {result['top_level_summary']}")
        print(f"   均分: {result['avg_score']}")
        print(f"   分级: {result['level_distribution']}")
        print()
        print(f"{'排名':<6} {'客户名称':<20} {'行业':<12} {'城市':<8} {'评分':<6} {'等级':<16}")
        print("-" * 80)
        for i, opp in enumerate(result["top_opportunities"][:10], 1):
            print(f"{i:<6} {opp['name']:<20} {opp['industry']:<12} {opp['city']:<8} {opp['score']:<6} {opp['level']:<16}")
        print(f"\n推荐行动:")
        for action in result["recommended_actions"]:
            print(f"  ▶ {action['name']} ({action['score']}分): {action['next_step']}")

    elif mode == "develop":
        # Phase 2+3: 线索开发全流程
        customer = sys.argv[2] if len(sys.argv) > 2 else None
        if not customer:
            print("❌ 请指定客户名称: python3 opportunity_scorer.py develop 吉利汽车")
            sys.exit(1)

        result = full_pipeline(customer)

        if "error" in result:
            print(f"❌ {result['error']}")
            sys.exit(1)

        print(f"🔍 {result['customer']} 深度洞察")
        print(f"   行业: {result['industry']} | 城市: {result['city']} | 分层: {result['tier']}")
        print(f"   商机评分: {result['opportunity_score']}分 ({result['opportunity_level']})")
        print(f"   预估预算: {result['estimated_budget']}")
        print()
        print(f"📋 推荐需求 (TOP4):")
        for i, need in enumerate(result['potential_needs'], 1):
            print(f"  {i}. {need}")
        print()
        print(f"👥 决策链 ({len(result['contact_plan'])}人):")
        for p in result['contact_plan']:
            print(f"  {p['role_type']} {p['role']} → 关注: {p['focus']} | 影响力: {p['impact_score']}/10")
            print(f"  价值主张: {p['value'][:80]}...")
        print()
        print(f"📧 推荐首封邮件:")
        if result['recommended_first_contact']:
            print(result['recommended_first_contact']['email_draft'])

    else:
        print("用法:")
        print("  python3 opportunity_scorer.py discover [行业] [城市]")
        print("  python3 opportunity_scorer.py develop 客户名称")
        print()
        print("示例:")
        print("  python3 opportunity_scorer.py discover 汽车零部件 宁波")
        print("  python3 opportunity_scorer.py develop 吉利汽车")

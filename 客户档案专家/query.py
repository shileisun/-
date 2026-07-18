#!/usr/bin/env python3
"""客户档案专家 - 数据查询脚本"""
import pandas as pd
import sys
import os
import json

# v17 P1: 环境变量 + 默认值 + 缺失降级
DATA_FILE = os.environ.get(
    'FABM_CUSTOMER_CSV',
    os.path.join(os.environ.get('WORKBUDDY_WORKSPACE', os.path.expanduser('~/WorkBuddy')), '量子蜂群客户档案.csv'),
)

def load_data():
    if not os.path.exists(DATA_FILE):
        # 降级：���试同目录下的 .csv
        fallback = os.path.join(os.path.dirname(os.path.abspath(__file__)), '量子蜂群客户档案.csv')
        if os.path.exists(fallback):
            return pd.read_csv(fallback)
        raise FileNotFoundError(
            f"客户档案数据文件缺失：{DATA_FILE}\n"
            f"请设置环境变量 FABM_CUSTOMER_CSV 指向客户档案 CSV，或将文件放入 skill 目录。"
        )
    return pd.read_csv(DATA_FILE)

def query(args):
    df = load_data()
    
    # 解析查询条件
    region = args.get('region', '')
    industry = args.get('industry', '')
    level = args.get('level', '')
    keyword = args.get('keyword', '')
    has_contact = args.get('has_contact', False)
    
    # 过滤
    if region:
        df = df[df['区域'].str.contains(region, na=False)]
    if industry:
        df = df[df['行业一级'].str.contains(industry, na=False)]
    if level:
        df = df[df['客户分层'] == level]
    if keyword:
        df = df[df['企业名称'].str.contains(keyword, na=False)]
    if has_contact:
        df = df[(df['手机号'].notna()) | (df['邮箱'].notna())]
    
    return df

def stats():
    df = load_data()
    return {
        'total': len(df),
        'by_level': df['客户分层'].value_counts().to_dict(),
        'by_region': df['区域'].value_counts().head(10).to_dict(),
        'by_industry': df['行业一级'].value_counts().to_dict(),
        'has_contact': len(df[(df['手机号'].notna()) | (df['邮箱'].notna())])
    }

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'stats'
    
    if cmd == 'stats':
        print(json.dumps(stats(), ensure_ascii=False))
    else:
        # query模式
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        result = query(args)
        print(result.head(20).to_string())
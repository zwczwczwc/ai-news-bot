#!/usr/bin/env python3
"""
上传 Horizon 报告到飞书文档
"""
import os
import sys
import requests
import json
from datetime import datetime

def get_feishu_token(app_id, app_secret):
    """获取飞书 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret})
    data = resp.json()
    if data.get('code') != 0:
        print(f"Auth failed: {data}")
        return None
    return data.get('tenant_access_token')

def create_document(token, title):
    """创建飞书文档"""
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"title": title}
    resp = requests.post(url, headers=headers, json=payload)
    data = resp.json()
    if data.get('code') != 0:
        print(f"Create doc failed: {data}")
        return None
    return data.get('data', {}).get('document', {}).get('document_token')

def main():
    if len(sys.argv) < 3:
        print("Usage: upload_to_feishu.py <report_file> <doc_title>")
        sys.exit(1)
    
    report_file = sys.argv[1]
    doc_title = sys.argv[2]
    
    app_id = os.environ.get('FEISHU_APP_ID')
    app_secret = os.environ.get('FEISHU_APP_SECRET')
    
    if not app_id or not app_secret:
        print("FEISHU_APP_ID and FEISHU_APP_SECRET required")
        sys.exit(1)
    
    if not os.path.exists(report_file):
        print(f"Report file not found: {report_file}")
        sys.exit(1)
    
    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Report length: {len(content)} chars")
    
    token = get_feishu_token(app_id, app_secret)
    if not token:
        sys.exit(1)
    
    doc_token = create_document(token, doc_title)
    if not doc_token:
        sys.exit(1)
    
    print(f"Created doc: https://feishu.cn/docx/{doc_token}")
    
    # 输出供 GitHub Actions 使用
    with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
        f.write(f"doc_token={doc_token}\n")
        f.write(f"doc_url=https://feishu.cn/docx/{doc_token}\n")

if __name__ == '__main__':
    main()

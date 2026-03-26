# GitHub Secrets 配置指南

## 仓库地址
https://github.com/zwczwczwc/ai-news-bot

## 需要配置的 Secrets

请访问以下链接，手动添加 Secrets：

```
https://github.com/zwczwczwc/ai-news-bot/settings/secrets/actions
```

### 1. GEMINI_API_KEY (必需)

**获取方式**: https://aistudio.google.com/app/apikey

```
Name: GEMINI_API_KEY
Value: AIzaSyxxxxxxxxxxxxxxxx (你的 Gemini API Key)
```

### 2. FEISHU_WEBHOOK (可选)

**获取方式**: 飞书群 → 设置 → 群机器人 → 添加机器人

```
Name: FEISHU_WEBHOOK
Value: https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxxx
```

### 3. OPENAI_API_KEY (可选)

```
Name: OPENAI_API_KEY
Value: sk-xxxxxxxxxxxxxxxx (你的 OpenAI API Key)
```

### 4. ANTHROPIC_API_KEY (可选)

```
Name: ANTHROPIC_API_KEY
Value: sk-ant-xxxxxxxxxx (你的 Claude API Key)
```

## 配置完成后

1. 访问 Actions 页面：
   ```
   https://github.com/zwczwczwc/ai-news-bot/actions
   ```

2. 点击 "Daily AI News - Horizon"

3. 点击 "Run workflow" 手动触发测试

## 定时任务

- **时间**: 每天北京时间 8:00
- **时区**: Asia/Shanghai
- **免费额度**: 每月 2000 分钟 (完全够用)

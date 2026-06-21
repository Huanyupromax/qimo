# 辩境 - AI 辩论系统

一个基于 Flask 的 AI 辩论平台，支持流星动画背景、摄像头、语音输入，
内置规则辩论引擎（可选配 OpenAI GPT-4o 多模态大模型）。

## 功能

- 流星粒子动画登录页面
- 用户注册/登录
- 摄像头实时显示
- 语音输入（Chrome 浏览器）
- AI 辩论（规则引擎 / GPT-4o）
- MongoDB 存储（可选）
- 5 个预设辩题，支持正反方

## 快速开始

`ash
pip install flask
python app.py
`

访问 http://127.0.0.1:5000

## 配置（可选）

| 环境变量 | 说明 |
|----------|------|
| OPENAI_API_KEY | 启用 GPT-4o 辩论引擎 |
| MONGODB_URI | 启用 MongoDB 存储 |

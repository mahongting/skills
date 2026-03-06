---
name: feishu-voice-sender
description: |
  飞书语音消息发送器。将文字转换为语音并发送到飞书群聊。
  支持多 TTS 供应商（Edge TTS、Azure 等），自动转换为飞书 OPUS 格式。
  
  使用场景：
  1. 发送语音通知/提醒到飞书
  2. 文字转语音自动播报
  3. 多音色选择（男女声、不同风格）
  
  触发词：飞书语音、语音发送、tts、语音通知、文字转语音
---

# Feishu Voice Sender - 飞书语音发送器

多供应商 TTS 语音发送工具，支持 Edge TTS（免费）、Azure Speech 等，自动转换为飞书 OPUS 格式。

## 特性

- 🎙️ **多 TTS 供应商**：Edge TTS（免费）、Azure Speech（高质量）
- 🎭 **多音色选择**：男女声、不同风格
- 🔄 **自动格式转换**：自动转为飞书 OPUS 格式
- 📱 **一键发送**：生成后直接发送到飞书
- 🔌 **可扩展架构**：预留百度、讯飞等供应商接口

## 支持的 TTS 供应商

| 供应商 | 名称 | 费用 | 质量 | 状态 |
|:---|:---|:---:|:---:|:---:|
| **edge** | Microsoft Edge TTS | 免费 | 良好 | ✅ 可用 |
| **azure** | Azure Speech Service | 付费 | 优秀 | 🚧 预留 |
| baidu | 百度语音合成 | 免费额度 | 良好 | 📋 待接入 |
| xunfei | 科大讯飞 | 免费额度 | 优秀 | 📋 待接入 |

## 安装依赖

```bash
# Edge TTS（必须）
pip install edge-tts

# FFmpeg（必须，用于格式转换）
sudo apt-get install ffmpeg

# Azure（可选）
pip install azure-cognitiveservices-speech
```

## 快速开始

### 命令行使用

```bash
cd ~/.openclaw/skills/feishu-voice-sender/scripts

# 基本用法（默认 edge + xiaoxiao 温暖女声）
python3 voice_sender.py "你好老大，任务已完成"

# 选择语音
python3 voice_sender.py "紧急通知，请立即处理" yunyang

# 指定供应商
python3 voice_sender.py "系统告警" xiaoxiao azure
```

### Python API 使用

```python
import sys
sys.path.insert(0, '~/.openclaw/skills/feishu-voice-sender/scripts')

from voice_sender import FeishuVoiceSender

# 创建发送器（默认 edge）
sender = FeishuVoiceSender(provider="edge")

# 发送语音
sender.send("你好，这是测试语音", voice="xiaoxiao")

# 生成语音文件（不发送）
opus_file, duration = sender.text_to_opus("测试文字", voice="yunyang")
print(f"语音文件: {opus_file}, 时长: {duration}秒")
```

### 在 Agent 中调用

```python
# 让 Agent 发送语音通知
sessions_spawn(
    agentId="main",
    task="使用 feishu-voice-sender 发送语音：'任务已完成，请查收'"
)
```

## 语音列表

### Edge TTS（推荐）

| 语音 | 性别 | 风格 | 推荐场景 |
|:---|:---:|:---|:---|
| **xiaoxiao** | 女 | 温暖、专业 | ⭐ 日常工作推荐 |
| **yunyang** | 男 | 专业、可靠 | 正式通知 |
| **yunxi** | 男 | 活泼、阳光 | 轻松内容 |
| **xiaoyi** | 女 | 活泼、卡通 | 趣味内容 |
| **yunjian** | 男 | 新闻播报 | 紧急通知 |
| **xiaobei** | 女 | 辽宁话 | 幽默方言 |
| **xiaoni** | 女 | 陕西话 | 特色方言 |

### Azure TTS（预留）

待配置 Azure 密钥后可用。

## 架构设计

```
文字输入
    ↓
TTS Provider (edge/azure/baidu/xunfei)
    ↓
音频字节 (MP3/WAV)
    ↓
FFmpeg 转换
    ↓
OPUS 文件 (16kHz mono)
    ↓
飞书发送
```

### 扩展新供应商

1. 在 `providers/` 创建新文件（如 `baidu_tts.py`）
2. 继承 `TTSProvider` 基类
3. 实现 `synthesize()` 和 `get_voices()` 方法
4. 在 `providers/__init__.py` 注册

示例：
```python
from .base import TTSProvider

class BaiduTTSProvider(TTSProvider):
    name = "baidu"
    
    def synthesize(self, text, voice):
        # 实现百度 TTS 调用
        pass
    
    def get_voices(self):
        return ["duxiaomei", "duxiaoyu"]
```

## 配置文件

环境变量：
```bash
# 默认供应商
export FEISHU_VOICE_PROVIDER=edge

# Azure 配置（使用 azure 时需要）
export AZURE_SPEECH_KEY=your_key
export AZURE_SPEECH_REGION=your_region
```

## 技术细节

### 飞书语音要求
- **格式**: OPUS
- **采样率**: 16000 Hz
- **声道**: 单声道 (mono)
- **最大大小**: 30 MB

### 转换流程
```
文字 → TTS 供应商 → MP3/WAV → FFmpeg → OPUS (16kHz mono) → 飞书
```

## 故障排查

### 问题：edge-tts 命令未找到
```bash
pip install edge-tts
```

### 问题：FFmpeg 未安装
```bash
sudo apt-get install ffmpeg
```

### 问题：Azure 发送失败
检查环境变量是否设置：
```bash
echo $AZURE_SPEECH_KEY
echo $AZURE_SPEECH_REGION
```

### 问题：飞书无法播放
确保输出是 OPUS 格式，不是 MP3。飞书只支持 OPUS。

## 使用示例

### 日常汇报
```bash
python3 voice_sender.py "老大，今日数据已更新，请查看报表"
# 使用 xiaoxiao 温暖女声
```

### 紧急通知
```bash
python3 voice_sender.py "系统告警，服务器 CPU 使用率超过 90%" yunyang
# 使用 yunyang 专业男声
```

### 轻松提醒
```bash
python3 voice_sender.py "该休息啦，喝杯水吧" yunxi
# 使用 yunxi 活泼男声
```

## 路线图

- [x] Edge TTS 集成
- [x] 多供应商架构
- [ ] Azure TTS 完整实现
- [ ] 百度语音合成接入
- [ ] 科大讯飞接入
- [ ] 腾讯云语音接入
- [ ] 语音合并（长文本分段）
- [ ] 语速调节
- [ ] 情感风格选择

## 文件结构

```
feishu-voice-sender/
├── SKILL.md                  # 本文件
└── scripts/
    ├── voice_sender.py       # 主入口
    ├── config.py             # 配置文件
    └── providers/            # TTS 供应商
        ├── __init__.py       # 导出和注册
        ├── base.py           # 抽象基类
        ├── edge_tts.py       # Edge TTS 实现
        └── azure_tts.py      # Azure TTS 预留
```

---

*支持多供应商的飞书语音发送工具，默认使用免费 Edge TTS*

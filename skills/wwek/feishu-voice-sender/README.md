# Feishu Voice Sender

飞书语音消息发送工具。文字转语音，支持多 TTS 供应商。

## 安装

```bash
pip install edge-tts
sudo apt-get install ffmpeg
```

## 使用

```bash
cd scripts
python3 voice_sender.py "要发送的文字" [voice]
```

**示例**:
```bash
python3 voice_sender.py "你好老大，任务已完成" xiaoxiao
python3 voice_sender.py "系统告警，请立即处理" yunyang
```

## 语音选项

| 语音 | 性别 | 风格 |
|:---|:---:|:---|
| xiaoxiao | 女 | 温暖专业 ⭐推荐 |
| yunyang | 男 | 专业可靠 ⭐推荐 |
| yunxi | 男 | 活泼阳光 |
| xiaoyi | 女 | 活泼卡通 |
| yunjian | 男 | 新闻播报 |

## 架构

```
voice_sender.py → TTS Provider → FFmpeg → OPUS → 飞书
```

**支持供应商**:
- `edge` (默认) - Microsoft Edge TTS，免费
- `azure` (预留) - Azure Speech，需配置 KEY

## 扩展供应商

1. 在 `providers/` 创建新文件，继承 `TTSProvider`
2. 实现 `synthesize()` 和 `get_voices()`
3. 在 `providers/__init__.py` 注册

## 配置

环境变量:
```bash
export FEISHU_VOICE_PROVIDER=edge  # 默认供应商
export AZURE_SPEECH_KEY=xxx        # Azure 配置
export AZURE_SPEECH_REGION=xxx
```

## 依赖

- Python 3.8+
- edge-tts
- FFmpeg
- azure-cognitiveservices-speech (可选)

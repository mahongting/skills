#!/usr/bin/env python3
"""
飞书语音发送器 - 主入口
支持多 TTS 供应商，自动转换为飞书 OPUS 格式
"""
import subprocess
import tempfile
import os
from typing import Optional, Tuple
from providers import get_provider, list_available_providers

class FeishuVoiceSender:
    """
    飞书语音发送器
    
    支持多 TTS 供应商：
    - edge: Microsoft Edge TTS (免费，默认)
    - azure: Azure Speech Service (需要订阅)
    """
    
    def __init__(self, provider: str = "edge"):
        """
        初始化发送器
        
        Args:
            provider: TTS 供应商名称 (edge, azure, ...)
        """
        self.provider_name = provider
        self.provider = get_provider(provider)
        print(f"🎙️ 使用 TTS 供应商: {provider}")
    
    def text_to_opus(self, text: str, voice: str = None) -> Tuple[Optional[str], Optional[int]]:
        """
        将文字转换为 OPUS 语音文件（飞书格式）
        
        Args:
            text: 要转换的文字
            voice: 语音类型（供应商特定）
            
        Returns:
            (opus文件路径, 时长秒数) 或 (None, None) 失败
        """
        # 1. 使用 TTS 供应商生成音频
        audio_bytes, duration = self.provider.synthesize(text, voice)
        
        if not audio_bytes:
            return None, None
        
        # 2. 如果是 MP3，转换为 OPUS
        opus_file = "/tmp/feishu_voice_sender.opus"
        
        # 先保存为临时 MP3
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            mp3_file = f.name
            f.write(audio_bytes)
        
        try:
            # 转换为 OPUS（飞书要求格式）
            cmd = [
                "ffmpeg", "-y", "-i", mp3_file,
                "-acodec", "libopus",
                "-ac", "1",      # 单声道
                "-ar", "16000",  # 16kHz
                opus_file
            ]
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode != 0:
                print(f"❌ OPUS 转换失败")
                return None, None
            
            return opus_file, duration or self._estimate_duration(text)
            
        finally:
            if os.path.exists(mp3_file):
                os.remove(mp3_file)
    
    def _estimate_duration(self, text: str) -> int:
        """估算语音时长（按每分钟150字）"""
        return max(1, len(text) // 150 * 60)
    
    def send(self, text: str, voice: str = None) -> bool:
        """
        生成语音并发送到飞书
        
        Args:
            text: 要发送的文字
            voice: 语音类型
            
        Returns:
            是否成功
        """
        print(f"📝 转换文字: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        # 生成语音
        opus_file, duration = self.text_to_opus(text, voice)
        
        if not opus_file:
            print("❌ 语音生成失败")
            return False
        
        print(f"✅ 语音生成成功！时长: {duration}秒")
        print(f"📁 文件: {opus_file}")
        
        # 发送到飞书
        return self._send_to_feishu(opus_file, duration)
    
    def _send_to_feishu(self, opus_file: str, duration: int) -> bool:
        """发送 OPUS 文件到飞书"""
        print(f"🚀 准备发送到飞书...")
        
        # 尝试使用 openclaw 命令发送
        cmd = ["openclaw", "message", "send", "--media", opus_file]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 语音消息发送成功！")
            return True
        else:
            print(f"⚠️ 自动发送失败: {result.stderr}")
            print(f"💡 请手动上传文件: {opus_file}")
            return False


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("飞书语音发送器 (Feishu Voice Sender)")
        print()
        print("用法:")
        print(f"  {sys.argv[0]} '要发送的文字' [voice] [provider]")
        print()
        print("示例:")
        print(f"  {sys.argv[0]} '你好老大，任务已完成'")
        print(f"  {sys.argv[0]} '系统告警' yunyang")
        print(f"  {sys.argv[0]} '紧急通知' xiaoxiao azure")
        print()
        print("可用供应商:", ", ".join(list_available_providers()))
        print()
        print("Edge TTS 语音列表:")
        print("  xiaoxiao - 温暖女声 (推荐)")
        print("  yunyang  - 专业男声 (推荐)")
        print("  xiaoyi   - 活泼女声")
        print("  yunxi    - 活泼男声")
        print("  yunjian  - 新闻男声")
        sys.exit(1)
    
    text = sys.argv[1]
    voice = sys.argv[2] if len(sys.argv) > 2 else None
    provider = sys.argv[3] if len(sys.argv) > 3 else "edge"
    
    sender = FeishuVoiceSender(provider=provider)
    sender.send(text, voice)


if __name__ == "__main__":
    main()

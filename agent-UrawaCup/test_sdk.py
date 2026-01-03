"""
Agent SDK 接続テストスクリプト

使用方法:
1. APIキーを設定:
   $env:ANTHROPIC_API_KEY = "sk-ant-xxxxx"

2. テスト実行:
   python test_sdk.py
"""

import asyncio
import os
import sys


async def test_agent_sdk():
    """Agent SDK の接続テスト"""

    # APIキー確認
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("=" * 60)
        print("エラー: ANTHROPIC_API_KEY が設定されていません")
        print("=" * 60)
        print("\n設定方法:")
        print("  PowerShell:")
        print('    $env:ANTHROPIC_API_KEY = "sk-ant-xxxxx"')
        print("\n  コマンドプロンプト:")
        print('    set ANTHROPIC_API_KEY=sk-ant-xxxxx')
        print("\n  永続的に設定（システム環境変数）:")
        print("    1. スタートメニュー → 環境変数を編集")
        print("    2. ユーザー環境変数に ANTHROPIC_API_KEY を追加")
        print("=" * 60)
        return False

    print(f"APIキー: {api_key[:20]}...")
    print("Agent SDK をインポート中...")

    try:
        from claude_agent_sdk import query, ClaudeAgentOptions
        print("✓ Agent SDK インポート成功")
    except ImportError as e:
        print(f"✗ Agent SDK インポート失敗: {e}")
        print("インストール: python -m pip install claude-agent-sdk")
        return False

    print("\n簡単なクエリをテスト中...")

    try:
        options = ClaudeAgentOptions(
            allowed_tools=[],
            permission_mode="bypassPermissions"
        )

        async for message in query(
            prompt="Say 'Hello, Agent SDK is working!' in one line.",
            options=options
        ):
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        print(f"応答: {block.text}")

        print("\n✓ Agent SDK 接続テスト成功!")
        return True

    except Exception as e:
        print(f"\n✗ Agent SDK 接続テスト失敗: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_agent_sdk())
    sys.exit(0 if success else 1)

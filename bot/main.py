# -*- coding: utf-8 -*-
"""
Ahrefs DR 批量查询工具 - Telegram Bot 主程序
"""

import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.config import TELEGRAM_BOT_TOKEN
from bot.handlers import (
    start_command,
    help_command,
    query_command,
    batch_command,
    history_command,
    error_handler,
)


def main():
    """主函数"""
    # 检查 Token
    if not TELEGRAM_BOT_TOKEN:
        print("错误: 未配置 TELEGRAM_BOT_TOKEN")
        print("请设置环境变量或在 bot/config.py 中配置")
        return

    print("正在启动 Telegram Bot...")

    # 创建应用
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 注册命令处理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("query", query_command))
    application.add_handler(CommandHandler("batch", batch_command))
    application.add_handler(CommandHandler("history", history_command))

    # 注册错误处理器
    application.add_error_handler(error_handler)

    # 启动 Bot
    print("Bot 已启动，等待消息...")
    print("按 Ctrl+C 停止")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

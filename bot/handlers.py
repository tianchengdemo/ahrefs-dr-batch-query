# -*- coding: utf-8 -*-
"""
Telegram Bot 命令处理器
"""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from typing import List
import re

from .api_client import APIClient
from .config import TELEGRAM_ADMIN_IDS, DEFAULT_COUNTRY, MAX_BATCH_DOMAINS


# 初始化 API 客户端
api_client = APIClient()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    welcome_message = """
🎉 *欢迎使用 Ahrefs DR 查询机器人！*

我可以帮你快速查询域名的 Domain Rating (DR) 和 Ahrefs Rank (AR)。

*可用命令：*

/query <域名> - 查询单个域名
例如：`/query example.com`

/batch <域名1> <域名2> ... - 批量查询（最多 10 个）
例如：`/batch example.com google.com`

/history - 查看查询历史

/help - 显示帮助信息

*提示：*
• 域名可以带或不带 http(s)://
• 支持指定国家代码，例如：`/query example.com br`
• 批量查询用空格分隔域名
"""
    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令"""
    help_message = """
📖 *帮助文档*

*命令说明：*

1️⃣ */query <域名> [国家代码]*
   查询单个域名的 DR 和 AR

   示例：
   • `/query example.com`
   • `/query example.com us`
   • `/query https://example.com`

2️⃣ */batch <域名1> <域名2> ...*
   批量查询多个域名（最多 10 个）

   示例：
   • `/batch example.com google.com`
   • `/batch example.com google.com github.com`

3️⃣ */history*
   查看最近的查询历史

4️⃣ */help*
   显示此帮助信息

*国家代码：*
• us - 美国（默认）
• br - 巴西
• uk - 英国
• de - 德国
• fr - 法国
• 等等...

*注意事项：*
• 查询可能需要几秒钟时间
• 请勿频繁查询，避免被限流
• 域名格式会自动处理
"""
    await update.message.reply_text(
        help_message,
        parse_mode=ParseMode.MARKDOWN
    )


def clean_domain(domain: str) -> str:
    """清理域名格式"""
    # 移除 http(s)://
    domain = re.sub(r'^https?://', '', domain)
    # 移除尾部斜杠
    domain = domain.rstrip('/')
    # 移除 www.
    domain = re.sub(r'^www\.', '', domain)
    return domain.strip()


def format_result(result: dict) -> str:
    """格式化查询结果"""
    if result.get("error"):
        return f"❌ *错误：* {result['error']}"

    domain = result.get("domain", "未知")
    dr = result.get("domain_rating")
    ar = result.get("ahrefs_rank")
    dr_delta = result.get("dr_delta", 0)
    ar_delta = result.get("ar_delta", 0)

    # DR 变化标记
    dr_change = ""
    if dr_delta > 0:
        dr_change = f" 📈 (+{dr_delta:.1f})"
    elif dr_delta < 0:
        dr_change = f" 📉 ({dr_delta:.1f})"

    # AR 变化标记
    ar_change = ""
    if ar_delta > 0:
        ar_change = f" 📈 (+{ar_delta})"
    elif ar_delta < 0:
        ar_change = f" 📉 ({ar_delta})"

    result_text = f"""
✅ *{domain}*

⭐ *DR:* {dr:.1f}{dr_change}
📊 *AR:* {ar:,}{ar_change}
"""
    return result_text.strip()


async def query_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /query 命令"""
    if not context.args:
        await update.message.reply_text(
            "❌ 请提供域名\n\n使用方法：`/query example.com`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # 解析参数
    domain = clean_domain(context.args[0])
    country = context.args[1] if len(context.args) > 1 else DEFAULT_COUNTRY

    # 发送处理中消息
    processing_msg = await update.message.reply_text(
        f"🔍 正在查询 *{domain}*...",
        parse_mode=ParseMode.MARKDOWN
    )

    # 调用 API 查询
    result = api_client.query_domain(domain, country)

    if result:
        result_text = format_result(result)
        await processing_msg.edit_text(result_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await processing_msg.edit_text(
            "❌ 查询失败，请稍后重试",
            parse_mode=ParseMode.MARKDOWN
        )


async def batch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /batch 命令"""
    if not context.args:
        await update.message.reply_text(
            "❌ 请提供域名列表\n\n使用方法：`/batch example.com google.com`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # 解析域名列表
    domains = [clean_domain(d) for d in context.args[:MAX_BATCH_DOMAINS]]

    if len(domains) > MAX_BATCH_DOMAINS:
        await update.message.reply_text(
            f"⚠️ 最多支持 {MAX_BATCH_DOMAINS} 个域名，已截取前 {MAX_BATCH_DOMAINS} 个",
            parse_mode=ParseMode.MARKDOWN
        )

    # 发送处理中消息
    processing_msg = await update.message.reply_text(
        f"🔍 正在批量查询 *{len(domains)}* 个域名...",
        parse_mode=ParseMode.MARKDOWN
    )

    # 调用 API 批量查询
    results = api_client.batch_query(domains, DEFAULT_COUNTRY)

    if results:
        # 格式化所有结果
        result_texts = []
        success_count = 0
        fail_count = 0

        for result in results:
            if result.get("error"):
                fail_count += 1
            else:
                success_count += 1
            result_texts.append(format_result(result))

        # 组合消息
        header = f"📊 *批量查询结果*\n\n总计: {len(results)} | 成功: {success_count} | 失败: {fail_count}\n\n"
        separator = "\n" + "─" * 30 + "\n"
        full_message = header + separator.join(result_texts)

        # 如果消息太长，分段发送
        if len(full_message) > 4000:
            await processing_msg.edit_text(
                header + "结果较多，分段发送...",
                parse_mode=ParseMode.MARKDOWN
            )
            for result_text in result_texts:
                await update.message.reply_text(
                    result_text,
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            await processing_msg.edit_text(
                full_message,
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        await processing_msg.edit_text(
            "❌ 批量查询失败，请稍后重试",
            parse_mode=ParseMode.MARKDOWN
        )


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /history 命令"""
    # 获取任务列表
    tasks_data = api_client.list_tasks()

    if not tasks_data:
        await update.message.reply_text(
            "❌ 无法获取历史记录",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    tasks = tasks_data.get("tasks", [])
    total = tasks_data.get("total", 0)

    if total == 0:
        await update.message.reply_text(
            "📝 暂无查询历史",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # 格式化历史记录（最近 10 条）
    history_text = f"📝 *查询历史* (最近 {min(10, total)} 条)\n\n"

    for i, task in enumerate(tasks[:10], 1):
        status_emoji = {
            "completed": "✅",
            "failed": "❌",
            "processing": "⏳",
            "pending": "⏸️"
        }.get(task.get("status", ""), "❓")

        history_text += f"{i}. {status_emoji} {task.get('domains_count', 0)} 个域名 - {task.get('created_at', '')[:19]}\n"

    await update.message.reply_text(
        history_text,
        parse_mode=ParseMode.MARKDOWN
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """全局错误处理"""
    print(f"Error: {context.error}")

    if update and update.message:
        await update.message.reply_text(
            "❌ 发生错误，请稍后重试",
            parse_mode=ParseMode.MARKDOWN
        )

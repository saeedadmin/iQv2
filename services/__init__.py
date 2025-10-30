#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Services Module
ماژول سرویس‌های business logic
"""

from .crypto_service import (
    fetch_fear_greed_index,
    download_fear_greed_chart,
    create_simple_fear_greed_image,
    format_fear_greed_message
)

from .spam_service import (
    check_spam_and_handle,
    send_spam_block_notification,
    send_admin_spam_notification
)

__all__ = [
    'fetch_fear_greed_index',
    'download_fear_greed_chart',
    'create_simple_fear_greed_image',
    'format_fear_greed_message',
    'check_spam_and_handle',
    'send_spam_block_notification',
    'send_admin_spam_notification'
]

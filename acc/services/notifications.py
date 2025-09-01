"""
نظام الإشعارات الموحد
"""
from flask import make_response, redirect

def notify_redirect(url, message, type='info'):
    """
    إعادة توجيه مع إشعار
    
    Args:
        url: عنوان URL للتوجيه إليه
        message: رسالة الإشعار
        type: نوع الإشعار (success, error, warning, info)
    
    Returns:
        Flask Response object with X-Notify header
    """
    response = make_response(redirect(url))
    response.headers['X-Notify'] = f'{type}:{message}'
    return response

def notify_response(content, status=200, message=None, type='info'):
    """
    إرسال رد مع إشعار اختياري
    
    Args:
        content: محتوى الرد
        status: كود حالة HTTP
        message: رسالة الإشعار (اختياري)
        type: نوع الإشعار (success, error, warning, info)
    
    Returns:
        tuple of (content, status, headers)
    """
    headers = {}
    if message:
        headers['X-Notify'] = f'{type}:{message}'
    return content, status, headers
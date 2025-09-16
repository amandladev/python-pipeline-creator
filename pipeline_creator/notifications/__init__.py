"""
Pipeline Creator - Notifications Module

This module provides intelligent notification services for pipeline events.
Supports multiple channels: Slack, Teams, Discord, Email, and Webhooks.
"""

from .notification_service import NotificationService
from .channels import SlackChannel, EmailChannel, WebhookChannel
from .templates import NotificationTemplates
from .event_handlers import PipelineEventHandler

__all__ = [
    'NotificationService',
    'SlackChannel', 
    'EmailChannel',
    'WebhookChannel',
    'NotificationTemplates',
    'PipelineEventHandler'
]
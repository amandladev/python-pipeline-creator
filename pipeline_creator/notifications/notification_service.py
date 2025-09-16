"""
Notification Service - Core notification handling
"""

import asyncio
from typing import Dict, List, Any, Optional
from enum import Enum
import json
from datetime import datetime

from ..utils.console import print_success, print_error, print_info, print_warning
from ..utils.config import load_config, save_config


class NotificationEventType(Enum):
    """Pipeline event types that trigger notifications"""
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_SUCCESS = "pipeline_success"
    PIPELINE_FAILED = "pipeline_failed"
    PIPELINE_RECOVERED = "pipeline_recovered"  # Success after failure
    BUILD_STARTED = "build_started"
    BUILD_SUCCESS = "build_success"
    BUILD_FAILED = "build_failed"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_SUCCESS = "deployment_success"
    DEPLOYMENT_FAILED = "deployment_failed"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationService:
    """Main notification service orchestrator"""
    
    def __init__(self, config_path: str = ".pipeline/config.json"):
        self.config_path = config_path
        self.channels = {}
        self.templates = None
        self.event_history = []
        self.load_configuration()
    
    def load_configuration(self):
        """Load notification configuration from pipeline config"""
        try:
            config = load_config(self.config_path)
            self.notification_config = config.get("notifications", {})
            self._initialize_channels()
        except Exception as e:
            print_warning(f"Could not load notification config: {str(e)}")
            self.notification_config = {}
    
    def _initialize_channels(self):
        """Initialize notification channels based on configuration"""
        from .channels import SlackChannel, EmailChannel, WebhookChannel
        
        # Initialize Slack
        slack_config = self.notification_config.get("slack", {})
        if slack_config.get("enabled", False):
            self.channels["slack"] = SlackChannel(slack_config)
        
        # Initialize Email
        email_config = self.notification_config.get("email", {})
        if email_config.get("enabled", False):
            self.channels["email"] = EmailChannel(email_config)
        
        # Initialize Webhooks
        webhook_config = self.notification_config.get("webhooks", {})
        if webhook_config.get("enabled", False):
            self.channels["webhook"] = WebhookChannel(webhook_config)
    
    async def send_notification(
        self, 
        event_type: NotificationEventType,
        context: Dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Send notification to configured channels
        
        Args:
            event_type: Type of pipeline event
            context: Event context (project, branch, commit, etc.)
            priority: Notification priority level
            channels: Specific channels to send to (None = all configured)
        
        Returns:
            Dict with channel names and success status
        """
        if not self._should_notify(event_type, context):
            return {}
        
        # Record event for recovery detection
        self._record_event(event_type, context)
        
        # Determine channels to use
        target_channels = channels or list(self.channels.keys())
        
        # Send notifications concurrently
        tasks = []
        for channel_name in target_channels:
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                task = self._send_to_channel(channel, event_type, context, priority)
                tasks.append((channel_name, task))
        
        # Execute all notifications concurrently
        results = {}
        if tasks:
            task_results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
            for i, (channel_name, _) in enumerate(tasks):
                result = task_results[i]
                results[channel_name] = not isinstance(result, Exception)
                if isinstance(result, Exception):
                    print_error(f"Failed to send notification to {channel_name}: {str(result)}")
        
        return results
    
    async def _send_to_channel(
        self,
        channel,
        event_type: NotificationEventType,
        context: Dict[str, Any],
        priority: NotificationPriority
    ) -> bool:
        """Send notification to a specific channel"""
        try:
            message = self._format_message(event_type, context, priority)
            success = await channel.send(message, event_type, priority)
            return success
        except Exception as e:
            print_error(f"Error sending to channel {channel.__class__.__name__}: {str(e)}")
            return False
    
    def _should_notify(self, event_type: NotificationEventType, context: Dict[str, Any]) -> bool:
        """Determine if notification should be sent based on smart rules"""
        
        # Get notification rules
        rules = self.notification_config.get("rules", {})
        
        # Default rules if not configured
        default_rules = {
            "notify_on_success": False,  # Only notify on first success after failure
            "notify_on_failure": True,   # Always notify on failure
            "notify_on_recovery": True,  # Always notify on recovery
            "quiet_hours": {
                "enabled": False,
                "start": "22:00",
                "end": "08:00",
                "timezone": "UTC"
            }
        }
        
        # Merge with user rules
        effective_rules = {**default_rules, **rules}
        
        # Check quiet hours
        if self._is_quiet_hours(effective_rules.get("quiet_hours", {})):
            # Only send critical notifications during quiet hours
            if event_type not in [NotificationEventType.PIPELINE_FAILED, NotificationEventType.DEPLOYMENT_FAILED]:
                return False
        
        # Smart notification logic
        if event_type == NotificationEventType.PIPELINE_SUCCESS:
            # Only notify on success if it's a recovery (success after failure)
            if self._is_recovery():
                return effective_rules.get("notify_on_recovery", True)
            else:
                return effective_rules.get("notify_on_success", False)
        
        elif event_type in [NotificationEventType.PIPELINE_FAILED, NotificationEventType.BUILD_FAILED, NotificationEventType.DEPLOYMENT_FAILED]:
            return effective_rules.get("notify_on_failure", True)
        
        elif event_type == NotificationEventType.PIPELINE_RECOVERED:
            return effective_rules.get("notify_on_recovery", True)
        
        # For other events, check specific rules
        event_rules = effective_rules.get("events", {})
        return event_rules.get(event_type.value, True)
    
    def _is_quiet_hours(self, quiet_config: Dict[str, Any]) -> bool:
        """Check if current time is within quiet hours"""
        if not quiet_config.get("enabled", False):
            return False
        
        # TODO: Implement timezone-aware quiet hours checking
        # For now, return False (no quiet hours)
        return False
    
    def _is_recovery(self) -> bool:
        """Check if current success is a recovery (success after failure)"""
        if len(self.event_history) < 2:
            return False
        
        # Check if the last event was a failure
        last_event = self.event_history[-1]
        return last_event["type"] in [
            NotificationEventType.PIPELINE_FAILED.value,
            NotificationEventType.BUILD_FAILED.value,
            NotificationEventType.DEPLOYMENT_FAILED.value
        ]
    
    def _record_event(self, event_type: NotificationEventType, context: Dict[str, Any]):
        """Record event for history tracking"""
        event_record = {
            "type": event_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context
        }
        
        self.event_history.append(event_record)
        
        # Keep only last 50 events to prevent memory issues
        if len(self.event_history) > 50:
            self.event_history = self.event_history[-50:]
    
    def _format_message(
        self, 
        event_type: NotificationEventType, 
        context: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Format message for notification"""
        from .templates import NotificationTemplates
        
        if not self.templates:
            self.templates = NotificationTemplates()
        
        return self.templates.format_message(event_type, context, priority)
    
    def get_status(self) -> Dict[str, Any]:
        """Get notification service status"""
        return {
            "configured_channels": list(self.channels.keys()),
            "total_events": len(self.event_history),
            "last_event": self.event_history[-1] if self.event_history else None,
            "configuration": {
                "slack_enabled": "slack" in self.channels,
                "email_enabled": "email" in self.channels,
                "webhook_enabled": "webhook" in self.channels
            }
        }
"""
Notification Channels - Different channels for sending notifications
"""

import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import json

from ..utils.console import print_error, print_success, print_info
from .notification_service import NotificationEventType, NotificationPriority


class BaseChannel:
    """Base class for notification channels"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", False)
    
    async def send(
        self, 
        message: Dict[str, Any], 
        event_type: NotificationEventType,
        priority: NotificationPriority
    ) -> bool:
        """Send notification through this channel"""
        raise NotImplementedError("Subclasses must implement send method")
    
    def is_enabled(self) -> bool:
        """Check if channel is enabled"""
        return self.enabled


class SlackChannel(BaseChannel):
    """Slack notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get("webhook_url", "")
        self.channel = config.get("channel", "#general")
        self.username = config.get("username", "Pipeline Bot")
        self.icon_emoji = config.get("icon_emoji", ":rocket:")
    
    async def send(
        self, 
        message: Dict[str, Any], 
        event_type: NotificationEventType,
        priority: NotificationPriority
    ) -> bool:
        """Send Slack notification"""
        if not self.webhook_url:
            print_error("Slack webhook URL not configured")
            return False
        
        try:
            # Format Slack message
            slack_message = self._format_slack_message(message, event_type, priority)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=slack_message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    success = response.status == 200
                    if success:
                        print_info("✅ Slack notification sent successfully")
                    else:
                        print_error(f"❌ Slack notification failed: {response.status}")
                    return success
        
        except Exception as e:
            print_error(f"Error sending Slack notification: {str(e)}")
            return False
    
    def _format_slack_message(
        self, 
        message: Dict[str, Any], 
        event_type: NotificationEventType,
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Format message for Slack"""
        
        # Color mapping for different event types
        color_map = {
            NotificationEventType.PIPELINE_SUCCESS: "good",
            NotificationEventType.PIPELINE_FAILED: "danger",
            NotificationEventType.PIPELINE_RECOVERED: "good",
            NotificationEventType.BUILD_FAILED: "warning",
            NotificationEventType.DEPLOYMENT_FAILED: "danger",
        }
        
        # Icon mapping
        icon_map = {
            NotificationEventType.PIPELINE_SUCCESS: ":white_check_mark:",
            NotificationEventType.PIPELINE_FAILED: ":x:",
            NotificationEventType.PIPELINE_RECOVERED: ":arrows_counterclockwise:",
            NotificationEventType.BUILD_STARTED: ":building_construction:",
            NotificationEventType.DEPLOYMENT_STARTED: ":rocket:",
        }
        
        color = color_map.get(event_type, "#36a64f")
        icon = icon_map.get(event_type, ":information_source:")
        
        # Build attachment
        attachment = {
            "color": color,
            "title": f"{icon} {message['title']}",
            "text": message['description'],
            "fields": [],
            "footer": "Pipeline Creator",
            "ts": message.get("timestamp", "")
        }
        
        # Add context fields
        context = message.get("context", {})
        if context.get("project"):
            attachment["fields"].append({
                "title": "Project",
                "value": context["project"],
                "short": True
            })
        
        if context.get("branch"):
            attachment["fields"].append({
                "title": "Branch", 
                "value": context["branch"],
                "short": True
            })
        
        if context.get("commit"):
            attachment["fields"].append({
                "title": "Commit",
                "value": context["commit"][:8],
                "short": True
            })
        
        if context.get("duration"):
            attachment["fields"].append({
                "title": "Duration",
                "value": context["duration"],
                "short": True
            })
        
        # Add action buttons if applicable
        actions = []
        if context.get("pipeline_url"):
            actions.append({
                "type": "button",
                "text": "View Pipeline",
                "url": context["pipeline_url"],
                "style": "primary"
            })
        
        if context.get("logs_url"):
            actions.append({
                "type": "button", 
                "text": "View Logs",
                "url": context["logs_url"]
            })
        
        if actions:
            attachment["actions"] = actions
        
        return {
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [attachment]
        }


class EmailChannel(BaseChannel):
    """Email notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_server = config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = config.get("smtp_port", 587)
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.from_email = config.get("from_email", self.username)
        self.to_emails = config.get("to_emails", [])
    
    async def send(
        self, 
        message: Dict[str, Any], 
        event_type: NotificationEventType,
        priority: NotificationPriority
    ) -> bool:
        """Send email notification"""
        if not self.to_emails:
            print_error("No email recipients configured")
            return False
        
        try:
            # Format email
            email_msg = self._format_email_message(message, event_type, priority)
            
            # Send email (run in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, self._send_smtp_email, email_msg)
            
            if success:
                print_info("✅ Email notification sent successfully")
            else:
                print_error("❌ Email notification failed")
            
            return success
        
        except Exception as e:
            print_error(f"Error sending email notification: {str(e)}")
            return False
    
    def _format_email_message(
        self, 
        message: Dict[str, Any], 
        event_type: NotificationEventType,
        priority: NotificationPriority
    ) -> MIMEMultipart:
        """Format email message"""
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Pipeline] {message['title']}"
        msg["From"] = self.from_email
        msg["To"] = ", ".join(self.to_emails)
        
        # Create text version
        text_content = f"""
{message['title']}

{message['description']}

Context:
"""
        
        context = message.get("context", {})
        for key, value in context.items():
            if value:
                text_content += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        text_content += "\n---\nSent by Pipeline Creator"
        
        # Create HTML version
        html_content = self._generate_html_email(message, event_type, priority)
        
        # Attach both versions
        text_part = MIMEText(text_content, "plain")
        html_part = MIMEText(html_content, "html")
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        return msg
    
    def _generate_html_email(
        self, 
        message: Dict[str, Any], 
        event_type: NotificationEventType,
        priority: NotificationPriority
    ) -> str:
        """Generate HTML email content"""
        
        # Color scheme based on event type
        color_map = {
            NotificationEventType.PIPELINE_SUCCESS: "#28a745",
            NotificationEventType.PIPELINE_FAILED: "#dc3545",
            NotificationEventType.PIPELINE_RECOVERED: "#17a2b8",
            NotificationEventType.BUILD_FAILED: "#ffc107",
            NotificationEventType.DEPLOYMENT_FAILED: "#dc3545",
        }
        
        primary_color = color_map.get(event_type, "#007bff")
        context = message.get("context", {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{message['title']}</title>
        </head>
        <body style="margin: 0; padding: 20px; background-color: #f8f9fa; font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <!-- Header -->
                <div style="background-color: {primary_color}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">{message['title']}</h1>
                </div>
                
                <!-- Content -->
                <div style="padding: 20px;">
                    <p style="font-size: 16px; line-height: 1.6; color: #333;">
                        {message['description']}
                    </p>
                    
                    <!-- Context Information -->
                    <div style="background-color: #f8f9fa; border-left: 4px solid {primary_color}; padding: 15px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #333;">Pipeline Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
        """
        
        # Add context rows
        for key, value in context.items():
            if value:
                display_key = key.replace('_', ' ').title()
                html += f"""
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold; color: #666; width: 30%;">{display_key}:</td>
                                <td style="padding: 8px 0; color: #333;">{value}</td>
                            </tr>
                """
        
        html += """
                        </table>
                    </div>
                    
                    <!-- Action Buttons -->
        """
        
        # Add action buttons
        if context.get("pipeline_url") or context.get("logs_url"):
            html += '<div style="text-align: center; margin: 30px 0;">'
            
            if context.get("pipeline_url"):
                html += f"""
                    <a href="{context['pipeline_url']}" 
                       style="display: inline-block; background-color: {primary_color}; color: white; 
                              padding: 12px 24px; text-decoration: none; border-radius: 4px; 
                              margin: 0 10px; font-weight: bold;">
                        View Pipeline
                    </a>
                """
            
            if context.get("logs_url"):
                html += f"""
                    <a href="{context['logs_url']}" 
                       style="display: inline-block; background-color: #6c757d; color: white; 
                              padding: 12px 24px; text-decoration: none; border-radius: 4px; 
                              margin: 0 10px; font-weight: bold;">
                        View Logs
                    </a>
                """
            
            html += '</div>'
        
        html += """
                </div>
                
                <!-- Footer -->
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 0 0 8px 8px; text-align: center; color: #666;">
                    <small>Sent by Pipeline Creator • Configure notifications with <code>pipeline notifications setup</code></small>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _send_smtp_email(self, msg: MIMEMultipart) -> bool:
        """Send email via SMTP"""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, self.to_emails, text)
            server.quit()
            
            return True
        except Exception as e:
            print_error(f"SMTP error: {str(e)}")
            return False


class WebhookChannel(BaseChannel):
    """Generic webhook notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.urls = config.get("urls", [])
        self.headers = config.get("headers", {"Content-Type": "application/json"})
        self.method = config.get("method", "POST").upper()
    
    async def send(
        self, 
        message: Dict[str, Any], 
        event_type: NotificationEventType,
        priority: NotificationPriority
    ) -> bool:
        """Send webhook notification"""
        if not self.urls:
            print_error("No webhook URLs configured")
            return False
        
        try:
            # Format webhook payload
            payload = self._format_webhook_payload(message, event_type, priority)
            
            # Send to all configured URLs
            success_count = 0
            async with aiohttp.ClientSession() as session:
                for url in self.urls:
                    try:
                        async with session.request(
                            self.method,
                            url,
                            json=payload,
                            headers=self.headers
                        ) as response:
                            if 200 <= response.status < 300:
                                success_count += 1
                            else:
                                print_error(f"Webhook failed for {url}: {response.status}")
                    except Exception as e:
                        print_error(f"Webhook error for {url}: {str(e)}")
            
            success = success_count > 0
            if success:
                print_info(f"✅ Webhook notifications sent to {success_count}/{len(self.urls)} URLs")
            else:
                print_error("❌ All webhook notifications failed")
            
            return success
        
        except Exception as e:
            print_error(f"Error sending webhook notifications: {str(e)}")
            return False
    
    def _format_webhook_payload(
        self, 
        message: Dict[str, Any], 
        event_type: NotificationEventType,
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Format webhook payload"""
        return {
            "event_type": event_type.value,
            "priority": priority.value,
            "title": message["title"],
            "description": message["description"],
            "context": message.get("context", {}),
            "timestamp": message.get("timestamp"),
            "source": "pipeline-creator"
        }
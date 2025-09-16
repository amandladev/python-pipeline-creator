"""
Notifications Command - Configure pipeline notifications
"""

import click
import json
from typing import Dict, Any, Optional

from ..utils.console import (
    print_success, print_error, print_info, print_warning, 
    print_header, print_step
)
from ..utils.config import load_config, save_config, check_config_exists
from ..notifications.notification_service import NotificationService


@click.group(name="notifications")
def notifications_command():
    """
    Configure pipeline notifications.
    
    Set up intelligent notifications for pipeline events including
    Slack, email, webhooks, and custom alerting rules.
    """
    pass


@notifications_command.command(name="setup")
@click.option('--channel', '-c', 
              type=click.Choice(['slack', 'email', 'webhook', 'all']),
              help='Specific channel to configure')
@click.option('--interactive', '-i', is_flag=True, default=True,
              help='Interactive configuration mode')
def setup_command(channel: Optional[str], interactive: bool):
    """
    Set up notification channels for your pipeline.
    
    This command helps you configure various notification channels
    like Slack, email, and webhooks with intelligent alerting rules.
    
    Examples:
        pipeline notifications setup                    # Interactive setup all channels
        pipeline notifications setup -c slack          # Setup only Slack
        pipeline notifications setup -c email          # Setup only Email
    """
    print_header("Setup Pipeline Notifications")
    
    # Check if configuration exists
    if not check_config_exists():
        print_error("❌ No pipeline configuration found!")
        print_info("Run 'pipeline init' first to initialize your pipeline configuration.")
        return
    
    try:
        # Load current configuration
        config = load_config()
        current_notifications = config.get("notifications", {})
        
        print_step("Current notification configuration...")
        _display_current_config(current_notifications)
        
        # Determine which channels to configure
        if channel == "all" or not channel:
            channels_to_setup = ["slack", "email", "webhook"]
        else:
            channels_to_setup = [channel]
        
        # Configure each channel
        updated_config = current_notifications.copy()
        
        for channel_name in channels_to_setup:
            if interactive:
                print_step(f"Configuring {channel_name.title()} notifications...")
                channel_config = _configure_channel_interactive(channel_name, current_notifications.get(channel_name, {}))
            else:
                channel_config = _configure_channel_non_interactive(channel_name)
            
            if channel_config:
                updated_config[channel_name] = channel_config
        
        # Configure smart rules
        if interactive:
            print_step("Configuring smart notification rules...")
            rules_config = _configure_rules_interactive(current_notifications.get("rules", {}))
            updated_config["rules"] = rules_config
        
        # Save configuration
        config["notifications"] = updated_config
        save_config(config)
        
        print_success("✅ Notification configuration saved successfully!")
        print_info("🚀 Your pipeline will now send intelligent notifications")
        
        # Display final configuration
        print_step("Final notification configuration:")
        _display_current_config(updated_config)
        
    except Exception as e:
        print_error(f"Error setting up notifications: {str(e)}")


@notifications_command.command(name="test")
@click.option('--channel', '-c', 
              type=click.Choice(['slack', 'email', 'webhook', 'all']),
              default='all',
              help='Channel to test')
def test_command(channel: str):
    """
    Test notification channels with sample messages.
    
    Send test notifications to verify your configuration is working correctly.
    
    Examples:
        pipeline notifications test                     # Test all channels
        pipeline notifications test -c slack          # Test only Slack
    """
    print_header("Test Notification Channels")
    
    if not check_config_exists():
        print_error("❌ No pipeline configuration found!")
        return
    
    try:
        import asyncio
        from ..notifications.notification_service import NotificationService, NotificationEventType, NotificationPriority
        
        # Initialize notification service
        service = NotificationService()
        
        # Test context
        test_context = {
            "project": "test-project",
            "branch": "main",
            "commit": "abc123def456",
            "author": "Test User",
            "duration": "2m 30s",
            "environment": "staging"
        }
        
        # Determine channels to test
        if channel == "all":
            channels_to_test = None  # Test all configured channels
        else:
            channels_to_test = [channel]
        
        print_step("Sending test notifications...")
        
        # Send test notification
        async def send_test():
            results = await service.send_notification(
                NotificationEventType.PIPELINE_SUCCESS,
                test_context,
                NotificationPriority.NORMAL,
                channels_to_test
            )
            return results
        
        results = asyncio.run(send_test())
        
        # Display results
        if results:
            print_success("✅ Test notifications sent!")
            for channel_name, success in results.items():
                if success:
                    print_info(f"  ✅ {channel_name}: Success")
                else:
                    print_error(f"  ❌ {channel_name}: Failed")
        else:
            print_warning("⚠️ No notifications sent - check your configuration")
    
    except Exception as e:
        print_error(f"Error testing notifications: {str(e)}")


@notifications_command.command(name="status")
def status_command():
    """
    Show notification configuration and status.
    
    Display current notification settings, enabled channels,
    and recent notification history.
    """
    print_header("Notification Status")
    
    if not check_config_exists():
        print_error("❌ No pipeline configuration found!")
        return
    
    try:
        # Load configuration and show status
        config = load_config()
        notifications_config = config.get("notifications", {})
        
        print_step("Notification Configuration:")
        _display_current_config(notifications_config)
        
        # Show service status
        service = NotificationService()
        status = service.get_status()
        
        print_step("Service Status:")
        print_info(f"📊 Configured channels: {len(status['configured_channels'])}")
        print_info(f"📈 Total events recorded: {status['total_events']}")
        
        if status['last_event']:
            last_event = status['last_event']
            print_info(f"🕐 Last event: {last_event['type']} at {last_event['timestamp']}")
        
        # Show channel status
        config_status = status['configuration']
        print_info(f"📢 Slack: {'✅ Enabled' if config_status['slack_enabled'] else '❌ Disabled'}")
        print_info(f"📧 Email: {'✅ Enabled' if config_status['email_enabled'] else '❌ Disabled'}")
        print_info(f"🔗 Webhook: {'✅ Enabled' if config_status['webhook_enabled'] else '❌ Disabled'}")
    
    except Exception as e:
        print_error(f"Error getting notification status: {str(e)}")


@notifications_command.command(name="disable")
@click.option('--channel', '-c', 
              type=click.Choice(['slack', 'email', 'webhook', 'all']),
              required=True,
              help='Channel to disable')
def disable_command(channel: str):
    """
    Disable specific notification channels.
    
    Temporarily disable notification channels without removing configuration.
    
    Examples:
        pipeline notifications disable -c slack        # Disable Slack
        pipeline notifications disable -c all          # Disable all channels
    """
    print_header("Disable Notifications")
    
    if not check_config_exists():
        print_error("❌ No pipeline configuration found!")
        return
    
    try:
        config = load_config()
        notifications_config = config.get("notifications", {})
        
        if channel == "all":
            channels_to_disable = ["slack", "email", "webhook"]
        else:
            channels_to_disable = [channel]
        
        for channel_name in channels_to_disable:
            if channel_name in notifications_config:
                notifications_config[channel_name]["enabled"] = False
                print_info(f"❌ Disabled {channel_name} notifications")
            else:
                print_warning(f"⚠️ {channel_name} not configured")
        
        config["notifications"] = notifications_config
        save_config(config)
        
        print_success("✅ Notification channels disabled successfully!")
    
    except Exception as e:
        print_error(f"Error disabling notifications: {str(e)}")


def _display_current_config(notifications_config: Dict[str, Any]):
    """Display current notification configuration"""
    
    if not notifications_config:
        print_info("📭 No notifications configured yet")
        return
    
    # Slack
    slack_config = notifications_config.get("slack", {})
    if slack_config:
        status = "✅ Enabled" if slack_config.get("enabled", False) else "❌ Disabled"
        print_info(f"📢 Slack: {status}")
        if slack_config.get("webhook_url"):
            print_info(f"   Channel: {slack_config.get('channel', '#general')}")
    
    # Email
    email_config = notifications_config.get("email", {})
    if email_config:
        status = "✅ Enabled" if email_config.get("enabled", False) else "❌ Disabled"
        print_info(f"📧 Email: {status}")
        if email_config.get("to_emails"):
            print_info(f"   Recipients: {len(email_config['to_emails'])} address(es)")
    
    # Webhook
    webhook_config = notifications_config.get("webhooks", {})
    if webhook_config:
        status = "✅ Enabled" if webhook_config.get("enabled", False) else "❌ Disabled"
        print_info(f"🔗 Webhook: {status}")
        if webhook_config.get("urls"):
            print_info(f"   URLs: {len(webhook_config['urls'])} configured")
    
    # Rules
    rules_config = notifications_config.get("rules", {})
    if rules_config:
        print_info("⚙️ Smart Rules:")
        print_info(f"   Notify on success: {'✅ Yes' if rules_config.get('notify_on_success', False) else '❌ No'}")
        print_info(f"   Notify on failure: {'✅ Yes' if rules_config.get('notify_on_failure', True) else '❌ No'}")
        print_info(f"   Notify on recovery: {'✅ Yes' if rules_config.get('notify_on_recovery', True) else '❌ No'}")


def _configure_channel_interactive(channel_name: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure a notification channel interactively"""
    
    enabled = click.confirm(f"Enable {channel_name} notifications?", 
                           default=current_config.get("enabled", False))
    
    if not enabled:
        return {"enabled": False}
    
    config = {"enabled": True}
    
    if channel_name == "slack":
        config.update(_configure_slack_interactive(current_config))
    elif channel_name == "email":
        config.update(_configure_email_interactive(current_config))
    elif channel_name == "webhook":
        config.update(_configure_webhook_interactive(current_config))
    
    return config


def _configure_slack_interactive(current_config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure Slack notifications interactively"""
    
    print_info("🔗 Slack Webhook Setup:")
    print_info("   1. Go to https://api.slack.com/apps")
    print_info("   2. Create a new app or select existing")
    print_info("   3. Go to 'Incoming Webhooks' and create a webhook")
    print_info("   4. Copy the webhook URL")
    
    webhook_url = click.prompt("Slack Webhook URL", 
                              default=current_config.get("webhook_url", ""),
                              hide_input=True)
    
    channel = click.prompt("Slack Channel", 
                          default=current_config.get("channel", "#general"))
    
    username = click.prompt("Bot Username", 
                           default=current_config.get("username", "Pipeline Bot"))
    
    return {
        "webhook_url": webhook_url,
        "channel": channel,
        "username": username,
        "icon_emoji": ":rocket:"
    }


def _configure_email_interactive(current_config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure email notifications interactively"""
    
    print_info("📧 Email SMTP Setup:")
    
    smtp_server = click.prompt("SMTP Server", 
                              default=current_config.get("smtp_server", "smtp.gmail.com"))
    
    smtp_port = click.prompt("SMTP Port", 
                            type=int,
                            default=current_config.get("smtp_port", 587))
    
    username = click.prompt("SMTP Username", 
                           default=current_config.get("username", ""))
    
    password = click.prompt("SMTP Password", 
                           hide_input=True)
    
    # Get recipient emails
    current_emails = current_config.get("to_emails", [])
    print_info(f"Current recipients: {current_emails}")
    
    emails_input = click.prompt("Recipient emails (comma-separated)", 
                               default=",".join(current_emails))
    
    to_emails = [email.strip() for email in emails_input.split(",") if email.strip()]
    
    return {
        "smtp_server": smtp_server,
        "smtp_port": smtp_port,
        "username": username,
        "password": password,
        "from_email": username,
        "to_emails": to_emails
    }


def _configure_webhook_interactive(current_config: Dict[str, Any]) -> Dict[str, Any]:
    """Configure webhook notifications interactively"""
    
    print_info("🔗 Webhook Setup:")
    
    # Get webhook URLs
    current_urls = current_config.get("urls", [])
    print_info(f"Current URLs: {current_urls}")
    
    urls_input = click.prompt("Webhook URLs (comma-separated)", 
                             default=",".join(current_urls))
    
    urls = [url.strip() for url in urls_input.split(",") if url.strip()]
    
    method = click.prompt("HTTP Method", 
                         type=click.Choice(['POST', 'PUT', 'PATCH']),
                         default=current_config.get("method", "POST"))
    
    return {
        "urls": urls,
        "method": method,
        "headers": {"Content-Type": "application/json"}
    }


def _configure_rules_interactive(current_rules: Dict[str, Any]) -> Dict[str, Any]:
    """Configure smart notification rules interactively"""
    
    print_info("⚙️ Smart Notification Rules:")
    print_info("   These rules help reduce notification spam by being intelligent about when to notify")
    
    notify_on_success = click.confirm("Always notify on successful builds?", 
                                     default=current_rules.get("notify_on_success", False))
    
    notify_on_failure = click.confirm("Always notify on failed builds?", 
                                     default=current_rules.get("notify_on_failure", True))
    
    notify_on_recovery = click.confirm("Always notify when pipeline recovers after failure?", 
                                      default=current_rules.get("notify_on_recovery", True))
    
    return {
        "notify_on_success": notify_on_success,
        "notify_on_failure": notify_on_failure,
        "notify_on_recovery": notify_on_recovery,
        "quiet_hours": {
            "enabled": False,
            "start": "22:00",
            "end": "08:00",
            "timezone": "UTC"
        }
    }


def _configure_channel_non_interactive(channel_name: str) -> Dict[str, Any]:
    """Configure channel in non-interactive mode (use environment variables)"""
    import os
    
    if channel_name == "slack":
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if webhook_url:
            return {
                "enabled": True,
                "webhook_url": webhook_url,
                "channel": os.getenv("SLACK_CHANNEL", "#general"),
                "username": os.getenv("SLACK_USERNAME", "Pipeline Bot"),
                "icon_emoji": ":rocket:"
            }
    
    elif channel_name == "email":
        smtp_server = os.getenv("SMTP_SERVER")
        username = os.getenv("SMTP_USERNAME")
        password = os.getenv("SMTP_PASSWORD")
        to_emails = os.getenv("EMAIL_RECIPIENTS", "").split(",")
        
        if smtp_server and username and password and to_emails:
            return {
                "enabled": True,
                "smtp_server": smtp_server,
                "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                "username": username,
                "password": password,
                "from_email": username,
                "to_emails": [email.strip() for email in to_emails if email.strip()]
            }
    
    return {"enabled": False}
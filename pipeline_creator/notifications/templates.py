"""
Notification Templates - Message templates for different events
"""

from typing import Dict, Any
from datetime import datetime, timezone
from .notification_service import NotificationEventType, NotificationPriority


class NotificationTemplates:
    """Templates for formatting notification messages"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def format_message(
        self, 
        event_type: NotificationEventType, 
        context: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Format message based on event type and context"""
        
        template = self.templates.get(event_type, self.templates[NotificationEventType.PIPELINE_STARTED])
        
        # Add timestamp
        timestamp = datetime.now(timezone.utc).timestamp()
        
        # Format the message
        formatted_message = {
            "title": template["title"].format(**context),
            "description": template["description"].format(**context),
            "context": context,
            "timestamp": int(timestamp),
            "priority": priority.value
        }
        
        return formatted_message
    
    def _load_templates(self) -> Dict[NotificationEventType, Dict[str, str]]:
        """Load message templates for different event types"""
        return {
            NotificationEventType.PIPELINE_STARTED: {
                "title": "🚀 Pipeline Started: {project}",
                "description": "Pipeline execution has started for project **{project}** on branch `{branch}`."
            },
            
            NotificationEventType.PIPELINE_SUCCESS: {
                "title": "✅ Pipeline Successful: {project}",
                "description": "Pipeline completed successfully for project **{project}** on branch `{branch}`. Duration: {duration}"
            },
            
            NotificationEventType.PIPELINE_FAILED: {
                "title": "❌ Pipeline Failed: {project}",
                "description": "Pipeline failed for project **{project}** on branch `{branch}`. Please check the logs for details."
            },
            
            NotificationEventType.PIPELINE_RECOVERED: {
                "title": "🎉 Pipeline Recovered: {project}",
                "description": "Great news! Pipeline for **{project}** is working again after previous failures. Branch: `{branch}`, Duration: {duration}"
            },
            
            NotificationEventType.BUILD_STARTED: {
                "title": "🔨 Build Started: {project}",
                "description": "Build phase started for project **{project}** on branch `{branch}`."
            },
            
            NotificationEventType.BUILD_SUCCESS: {
                "title": "✅ Build Successful: {project}",
                "description": "Build completed successfully for project **{project}** on branch `{branch}`. Duration: {duration}"
            },
            
            NotificationEventType.BUILD_FAILED: {
                "title": "⚠️ Build Failed: {project}",
                "description": "Build failed for project **{project}** on branch `{branch}`. Check build logs for compilation errors."
            },
            
            NotificationEventType.DEPLOYMENT_STARTED: {
                "title": "🚀 Deployment Started: {project}",
                "description": "Deployment started for project **{project}** to environment `{environment}`. Branch: `{branch}`"
            },
            
            NotificationEventType.DEPLOYMENT_SUCCESS: {
                "title": "🎯 Deployment Successful: {project}",
                "description": "Successfully deployed **{project}** to environment `{environment}`. Branch: `{branch}`, Duration: {duration}"
            },
            
            NotificationEventType.DEPLOYMENT_FAILED: {
                "title": "🔥 Deployment Failed: {project}",
                "description": "Deployment failed for project **{project}** to environment `{environment}`. Branch: `{branch}`. Immediate attention required!"
            }
        }
    
    def get_template(self, event_type: NotificationEventType) -> Dict[str, str]:
        """Get template for specific event type"""
        return self.templates.get(event_type, {
            "title": "Pipeline Event: {project}",
            "description": "A pipeline event occurred for project {project}."
        })
    
    def customize_template(
        self, 
        event_type: NotificationEventType, 
        title: str, 
        description: str
    ) -> None:
        """Customize template for specific event type"""
        self.templates[event_type] = {
            "title": title,
            "description": description
        }
    
    def list_available_variables(self) -> Dict[str, list]:
        """List available variables for template customization"""
        return {
            "context_variables": [
                "project",      # Project name
                "branch",       # Git branch
                "commit",       # Git commit hash
                "author",       # Commit author
                "duration",     # Execution duration
                "environment",  # Deployment environment
                "pipeline_url", # Pipeline URL
                "logs_url",     # Logs URL
                "stage",        # Current stage
                "job_id",       # Job/Build ID
            ],
            "computed_variables": [
                "timestamp",    # Current timestamp
                "priority",     # Event priority
                "recovery",     # Is this a recovery event
            ]
        }


class SlackTemplates(NotificationTemplates):
    """Slack-specific message templates with enhanced formatting"""
    
    def format_message(
        self, 
        event_type: NotificationEventType, 
        context: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Format message with Slack-specific enhancements"""
        
        base_message = super().format_message(event_type, context, priority)
        
        # Add Slack-specific formatting
        base_message["title"] = self._add_slack_formatting(base_message["title"])
        base_message["description"] = self._add_slack_formatting(base_message["description"])
        
        return base_message
    
    def _add_slack_formatting(self, text: str) -> str:
        """Add Slack-specific formatting to text"""
        # Convert markdown bold to Slack bold
        text = text.replace("**", "*")
        
        # Convert markdown code to Slack code
        text = text.replace("`", "`")
        
        return text


class TeamsTemplates(NotificationTemplates):
    """Microsoft Teams-specific message templates"""
    
    def format_message(
        self, 
        event_type: NotificationEventType, 
        context: Dict[str, Any],
        priority: NotificationPriority
    ) -> Dict[str, Any]:
        """Format message for Microsoft Teams"""
        
        base_message = super().format_message(event_type, context, priority)
        
        # Add Teams-specific formatting
        base_message = self._format_for_teams(base_message, event_type)
        
        return base_message
    
    def _format_for_teams(self, message: Dict[str, Any], event_type: NotificationEventType) -> Dict[str, Any]:
        """Format message specifically for Teams"""
        
        # Teams uses different color scheme
        theme_colors = {
            NotificationEventType.PIPELINE_SUCCESS: "00FF00",
            NotificationEventType.PIPELINE_FAILED: "FF0000", 
            NotificationEventType.PIPELINE_RECOVERED: "0078D4",
            NotificationEventType.BUILD_FAILED: "FFA500",
            NotificationEventType.DEPLOYMENT_FAILED: "FF0000",
        }
        
        message["themeColor"] = theme_colors.get(event_type, "0078D4")
        
        return message
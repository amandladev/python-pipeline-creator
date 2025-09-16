"""
Event Handlers - Handle pipeline events and trigger notifications
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .notification_service import NotificationService, NotificationEventType, NotificationPriority
from ..utils.console import print_info, print_error


class PipelineEventHandler:
    """Handle pipeline events and trigger appropriate notifications"""
    
    def __init__(self, config_path: str = ".pipeline/config.json"):
        self.notification_service = NotificationService(config_path)
        self.current_pipeline_state = {}
    
    async def handle_pipeline_event(
        self, 
        event_type: str,
        context: Dict[str, Any],
        priority: str = "normal"
    ) -> bool:
        """
        Handle a pipeline event and send notifications
        
        Args:
            event_type: Type of event (pipeline_started, pipeline_success, etc.)
            context: Event context information
            priority: Event priority (low, normal, high, critical)
        
        Returns:
            True if notifications were sent successfully
        """
        try:
            # Convert string event type to enum
            notification_event = NotificationEventType(event_type)
            notification_priority = NotificationPriority(priority)
            
            # Enhance context with additional information
            enhanced_context = self._enhance_context(context, notification_event)
            
            # Send notifications
            results = await self.notification_service.send_notification(
                notification_event,
                enhanced_context,
                notification_priority
            )
            
            # Log results
            if results:
                successful_channels = [channel for channel, success in results.items() if success]
                if successful_channels:
                    print_info(f"✅ Notifications sent to: {', '.join(successful_channels)}")
                    return True
                else:
                    print_error("❌ All notifications failed to send")
                    return False
            else:
                print_info("ℹ️ No notifications sent (smart rules or no channels configured)")
                return True
        
        except ValueError as e:
            print_error(f"Invalid event type or priority: {str(e)}")
            return False
        except Exception as e:
            print_error(f"Error handling pipeline event: {str(e)}")
            return False
    
    def _enhance_context(
        self, 
        context: Dict[str, Any], 
        event_type: NotificationEventType
    ) -> Dict[str, Any]:
        """Enhance context with additional computed information"""
        
        enhanced = context.copy()
        
        # Add timestamp if not present
        if "timestamp" not in enhanced:
            enhanced["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Add duration if we have start/end times
        if "start_time" in enhanced and "end_time" in enhanced:
            start_time = datetime.fromisoformat(enhanced["start_time"].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(enhanced["end_time"].replace('Z', '+00:00'))
            duration = end_time - start_time
            enhanced["duration"] = self._format_duration(duration.total_seconds())
        
        # Add pipeline URL if we can construct it
        if "project" in enhanced and "aws_region" in enhanced:
            enhanced["pipeline_url"] = self._construct_pipeline_url(
                enhanced["project"], 
                enhanced["aws_region"]
            )
        
        # Add logs URL if we can construct it
        if "job_id" in enhanced and "aws_region" in enhanced:
            enhanced["logs_url"] = self._construct_logs_url(
                enhanced["job_id"],
                enhanced["aws_region"]
            )
        
        # Truncate commit hash for display
        if "commit" in enhanced and len(enhanced["commit"]) > 8:
            enhanced["commit"] = enhanced["commit"][:8]
        
        # Add author from commit if available
        if "commit_author" in enhanced:
            enhanced["author"] = enhanced["commit_author"]
        
        return enhanced
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _construct_pipeline_url(self, project_name: str, aws_region: str) -> str:
        """Construct AWS CodePipeline URL"""
        return f"https://console.aws.amazon.com/codesuite/codepipeline/pipelines/{project_name}-pipeline/view?region={aws_region}"
    
    def _construct_logs_url(self, job_id: str, aws_region: str) -> str:
        """Construct AWS CloudWatch logs URL"""
        return f"https://console.aws.amazon.com/cloudwatch/home?region={aws_region}#logsV2:log-groups/log-group//aws/codebuild/{job_id}"
    
    def track_pipeline_start(
        self, 
        project: str, 
        branch: str, 
        commit: str,
        author: Optional[str] = None
    ):
        """Track pipeline start event"""
        self.current_pipeline_state = {
            "project": project,
            "branch": branch, 
            "commit": commit,
            "author": author,
            "start_time": datetime.now(timezone.utc).isoformat()
        }
    
    def track_pipeline_end(self, success: bool, job_id: Optional[str] = None):
        """Track pipeline end event"""
        if self.current_pipeline_state:
            self.current_pipeline_state["end_time"] = datetime.now(timezone.utc).isoformat()
            self.current_pipeline_state["success"] = success
            if job_id:
                self.current_pipeline_state["job_id"] = job_id
    
    async def send_pipeline_started(
        self, 
        project: str,
        branch: str, 
        commit: str,
        author: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Send pipeline started notification"""
        context = {
            "project": project,
            "branch": branch,
            "commit": commit,
            "author": author or "Unknown",
            **kwargs
        }
        
        self.track_pipeline_start(project, branch, commit, author)
        
        return await self.handle_pipeline_event(
            "pipeline_started",
            context,
            "normal"
        )
    
    async def send_pipeline_success(
        self, 
        project: str,
        branch: str,
        commit: str,
        duration: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Send pipeline success notification"""
        context = {
            "project": project,
            "branch": branch,
            "commit": commit,
            "duration": duration or "Unknown",
            **kwargs
        }
        
        # Check if this is a recovery
        is_recovery = self.notification_service._is_recovery()
        if is_recovery:
            event_type = "pipeline_recovered"
            priority = "high"
        else:
            event_type = "pipeline_success"
            priority = "normal"
        
        return await self.handle_pipeline_event(event_type, context, priority)
    
    async def send_pipeline_failure(
        self, 
        project: str,
        branch: str,
        commit: str,
        error_message: Optional[str] = None,
        stage: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Send pipeline failure notification"""
        context = {
            "project": project,
            "branch": branch,
            "commit": commit,
            "error": error_message or "Unknown error",
            "stage": stage or "Unknown stage",
            **kwargs
        }
        
        return await self.handle_pipeline_event(
            "pipeline_failed",
            context,
            "high"
        )
    
    async def send_deployment_started(
        self,
        project: str,
        environment: str,
        branch: str,
        commit: str,
        **kwargs
    ) -> bool:
        """Send deployment started notification"""
        context = {
            "project": project,
            "environment": environment,
            "branch": branch,
            "commit": commit,
            **kwargs
        }
        
        return await self.handle_pipeline_event(
            "deployment_started",
            context,
            "normal"
        )
    
    async def send_deployment_success(
        self,
        project: str,
        environment: str,
        branch: str,
        commit: str,
        duration: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Send deployment success notification"""
        context = {
            "project": project,
            "environment": environment,
            "branch": branch,
            "commit": commit,
            "duration": duration or "Unknown",
            **kwargs
        }
        
        # Deployment success is always important
        priority = "high" if environment == "production" else "normal"
        
        return await self.handle_pipeline_event(
            "deployment_success",
            context,
            priority
        )
    
    async def send_deployment_failure(
        self,
        project: str,
        environment: str,
        branch: str,
        commit: str,
        error_message: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Send deployment failure notification"""
        context = {
            "project": project,
            "environment": environment,
            "branch": branch,
            "commit": commit,
            "error": error_message or "Unknown error",
            **kwargs
        }
        
        # Deployment failures are critical, especially in production
        priority = "critical" if environment == "production" else "high"
        
        return await self.handle_pipeline_event(
            "deployment_failed",
            context,
            priority
        )
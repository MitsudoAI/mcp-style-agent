"""
Flow configuration hot update system with active session migration
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from ..models.thinking_models import FlowStep, ThinkingFlow
from .exceptions import ConfigurationError, FlowConfigurationError
from .flow_config import FlowConfigManager

logger = logging.getLogger(__name__)


class FlowUpdateAnalyzer:
    """
    Analyzes flow configuration changes and their impact
    """
    
    def __init__(self):
        self.change_types = {
            "STEP_ADDED": "step_added",
            "STEP_REMOVED": "step_removed", 
            "STEP_MODIFIED": "step_modified",
            "STEP_REORDERED": "step_reordered",
            "FLOW_METADATA_CHANGED": "flow_metadata_changed",
            "BREAKING_CHANGE": "breaking_change",
            "COMPATIBLE_CHANGE": "compatible_change",
        }
    
    def analyze_flow_changes(
        self, 
        old_flow: ThinkingFlow, 
        new_flow: ThinkingFlow
    ) -> Dict[str, Any]:
        """
        Analyze changes between old and new flow configurations
        
        Args:
            old_flow: Previous flow configuration
            new_flow: New flow configuration
            
        Returns:
            Dict[str, Any]: Analysis of changes and their impact
        """
        analysis = {
            "flow_name": new_flow.name,
            "changes": [],
            "impact_level": "none",  # none, low, medium, high, breaking
            "migration_required": False,
            "affected_steps": [],
            "compatibility": "full",  # full, partial, incompatible
            "migration_strategy": None,
        }
        
        # Analyze metadata changes
        metadata_changes = self._analyze_metadata_changes(old_flow, new_flow)
        analysis["changes"].extend(metadata_changes)
        
        # Analyze step changes
        step_changes = self._analyze_step_changes(old_flow, new_flow)
        analysis["changes"].extend(step_changes)
        
        # Determine overall impact
        analysis["impact_level"] = self._determine_impact_level(analysis["changes"])
        analysis["migration_required"] = self._requires_migration(analysis["changes"])
        analysis["compatibility"] = self._assess_compatibility(analysis["changes"])
        analysis["migration_strategy"] = self._determine_migration_strategy(analysis)
        
        return analysis
    
    def _analyze_metadata_changes(
        self, 
        old_flow: ThinkingFlow, 
        new_flow: ThinkingFlow
    ) -> List[Dict[str, Any]]:
        """Analyze changes in flow metadata"""
        changes = []
        
        # Check description changes
        if old_flow.description != new_flow.description:
            changes.append({
                "type": self.change_types["FLOW_METADATA_CHANGED"],
                "field": "description",
                "old_value": old_flow.description,
                "new_value": new_flow.description,
                "impact": "low",
            })
        
        # Check version changes
        if old_flow.version != new_flow.version:
            changes.append({
                "type": self.change_types["FLOW_METADATA_CHANGED"],
                "field": "version",
                "old_value": old_flow.version,
                "new_value": new_flow.version,
                "impact": "low",
            })
        
        # Check estimated duration changes
        if old_flow.estimated_duration != new_flow.estimated_duration:
            changes.append({
                "type": self.change_types["FLOW_METADATA_CHANGED"],
                "field": "estimated_duration",
                "old_value": old_flow.estimated_duration,
                "new_value": new_flow.estimated_duration,
                "impact": "low",
            })
        
        return changes
    
    def _analyze_step_changes(
        self, 
        old_flow: ThinkingFlow, 
        new_flow: ThinkingFlow
    ) -> List[Dict[str, Any]]:
        """Analyze changes in flow steps"""
        changes = []
        
        # Create step mappings
        old_steps = {step.step_id: step for step in old_flow.steps}
        new_steps = {step.step_id: step for step in new_flow.steps}
        
        # Find added steps
        added_steps = set(new_steps.keys()) - set(old_steps.keys())
        for step_id in added_steps:
            changes.append({
                "type": self.change_types["STEP_ADDED"],
                "step_id": step_id,
                "step_name": new_steps[step_id].name,
                "agent_type": new_steps[step_id].agent_type,
                "impact": "medium",
            })
        
        # Find removed steps
        removed_steps = set(old_steps.keys()) - set(new_steps.keys())
        for step_id in removed_steps:
            changes.append({
                "type": self.change_types["STEP_REMOVED"],
                "step_id": step_id,
                "step_name": old_steps[step_id].name,
                "agent_type": old_steps[step_id].agent_type,
                "impact": "high",
            })
        
        # Find modified steps
        common_steps = set(old_steps.keys()) & set(new_steps.keys())
        for step_id in common_steps:
            old_step = old_steps[step_id]
            new_step = new_steps[step_id]
            
            step_changes = self._analyze_single_step_changes(old_step, new_step)
            changes.extend(step_changes)
        
        # Check for step reordering
        old_order = [step.step_id for step in old_flow.steps]
        new_order = [step.step_id for step in new_flow.steps if step.step_id in old_steps]
        
        if old_order != new_order:
            changes.append({
                "type": self.change_types["STEP_REORDERED"],
                "old_order": old_order,
                "new_order": new_order,
                "impact": "medium",
            })
        
        return changes
    
    def _analyze_single_step_changes(
        self, 
        old_step: FlowStep, 
        new_step: FlowStep
    ) -> List[Dict[str, Any]]:
        """Analyze changes in a single step"""
        changes = []
        
        # Check agent type changes (breaking)
        if old_step.agent_type != new_step.agent_type:
            changes.append({
                "type": self.change_types["STEP_MODIFIED"],
                "step_id": old_step.step_id,
                "field": "agent_type",
                "old_value": old_step.agent_type,
                "new_value": new_step.agent_type,
                "impact": "breaking",
            })
        
        # Check name changes (low impact)
        if old_step.name != new_step.name:
            changes.append({
                "type": self.change_types["STEP_MODIFIED"],
                "step_id": old_step.step_id,
                "field": "name",
                "old_value": old_step.name,
                "new_value": new_step.name,
                "impact": "low",
            })
        
        # Check configuration changes
        if old_step.config != new_step.config:
            changes.append({
                "type": self.change_types["STEP_MODIFIED"],
                "step_id": old_step.step_id,
                "field": "config",
                "old_value": old_step.config,
                "new_value": new_step.config,
                "impact": "medium",
            })
        
        # Check condition changes
        if old_step.conditions != new_step.conditions:
            changes.append({
                "type": self.change_types["STEP_MODIFIED"],
                "step_id": old_step.step_id,
                "field": "conditions",
                "old_value": old_step.conditions,
                "new_value": new_step.conditions,
                "impact": "high",
            })
        
        # Check dependency changes
        old_deps = set(old_step.depends_on or [])
        new_deps = set(new_step.depends_on or [])
        
        if old_deps != new_deps:
            changes.append({
                "type": self.change_types["STEP_MODIFIED"],
                "step_id": old_step.step_id,
                "field": "depends_on",
                "old_value": list(old_deps),
                "new_value": list(new_deps),
                "impact": "high",
            })
        
        return changes
    
    def _determine_impact_level(self, changes: List[Dict[str, Any]]) -> str:
        """Determine overall impact level of changes"""
        if not changes:
            return "none"
        
        impact_levels = [change.get("impact", "low") for change in changes]
        
        if "breaking" in impact_levels:
            return "breaking"
        elif "high" in impact_levels:
            return "high"
        elif "medium" in impact_levels:
            return "medium"
        else:
            return "low"
    
    def _requires_migration(self, changes: List[Dict[str, Any]]) -> bool:
        """Determine if changes require active session migration"""
        high_impact_changes = [
            self.change_types["STEP_REMOVED"],
            self.change_types["STEP_REORDERED"],
        ]
        
        for change in changes:
            if change["type"] in high_impact_changes:
                return True
            
            if change.get("impact") in ["high", "breaking"]:
                return True
        
        return False
    
    def _assess_compatibility(self, changes: List[Dict[str, Any]]) -> str:
        """Assess compatibility level"""
        if not changes:
            return "full"
        
        breaking_changes = [change for change in changes if change.get("impact") == "breaking"]
        if breaking_changes:
            return "incompatible"
        
        high_impact_changes = [change for change in changes if change.get("impact") == "high"]
        if high_impact_changes:
            return "partial"
        
        return "full"
    
    def _determine_migration_strategy(self, analysis: Dict[str, Any]) -> Optional[str]:
        """Determine the best migration strategy"""
        if not analysis["migration_required"]:
            return None
        
        compatibility = analysis["compatibility"]
        impact_level = analysis["impact_level"]
        
        if compatibility == "incompatible":
            return "restart_sessions"
        elif impact_level == "high":
            return "graceful_migration"
        else:
            return "hot_update"


class ActiveSessionMigrator:
    """
    Handles migration of active sessions during flow updates
    """
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.migration_strategies = {
            "hot_update": self._hot_update_migration,
            "graceful_migration": self._graceful_migration,
            "restart_sessions": self._restart_sessions,
        }
    
    async def migrate_active_sessions(
        self, 
        flow_name: str,
        old_flow: ThinkingFlow,
        new_flow: ThinkingFlow,
        migration_strategy: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Migrate active sessions to new flow configuration
        
        Args:
            flow_name: Name of the flow being updated
            old_flow: Previous flow configuration
            new_flow: New flow configuration
            migration_strategy: Strategy to use for migration
            analysis: Change analysis results
            
        Returns:
            Dict[str, Any]: Migration results
        """
        logger.info(f"Starting session migration for flow '{flow_name}' using strategy '{migration_strategy}'")
        
        # Get active sessions for this flow
        active_sessions = await self._get_active_sessions(flow_name)
        
        if not active_sessions:
            logger.info(f"No active sessions found for flow '{flow_name}'")
            return {
                "flow_name": flow_name,
                "strategy": migration_strategy,
                "sessions_processed": 0,
                "successful_migrations": 0,
                "failed_migrations": 0,
                "errors": [],
            }
        
        # Execute migration strategy
        migration_func = self.migration_strategies.get(migration_strategy)
        if not migration_func:
            raise ConfigurationError(f"Unknown migration strategy: {migration_strategy}")
        
        results = await migration_func(
            flow_name, old_flow, new_flow, active_sessions, analysis
        )
        
        logger.info(
            f"Migration completed for flow '{flow_name}': "
            f"{results['successful_migrations']}/{results['sessions_processed']} sessions migrated successfully"
        )
        
        return results
    
    async def _get_active_sessions(self, flow_name: str) -> List[Dict[str, Any]]:
        """Get list of active sessions using the specified flow"""
        try:
            # Get all active sessions
            all_sessions = await self.session_manager.get_active_sessions()
            
            # Filter by flow name
            flow_sessions = [
                session for session in all_sessions 
                if session.get("flow_name") == flow_name
            ]
            
            return flow_sessions
            
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []
    
    async def _hot_update_migration(
        self,
        flow_name: str,
        old_flow: ThinkingFlow,
        new_flow: ThinkingFlow,
        active_sessions: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform hot update migration (minimal disruption)
        """
        results = {
            "flow_name": flow_name,
            "strategy": "hot_update",
            "sessions_processed": len(active_sessions),
            "successful_migrations": 0,
            "failed_migrations": 0,
            "errors": [],
        }
        
        for session in active_sessions:
            try:
                session_id = session["session_id"]
                
                # Update session's flow configuration
                await self.session_manager.update_session_flow(session_id, new_flow)
                
                # Update any cached flow data
                await self._update_session_flow_cache(session_id, new_flow)
                
                results["successful_migrations"] += 1
                logger.debug(f"Hot updated session {session_id}")
                
            except Exception as e:
                results["failed_migrations"] += 1
                results["errors"].append({
                    "session_id": session.get("session_id"),
                    "error": str(e),
                })
                logger.error(f"Failed to hot update session {session.get('session_id')}: {e}")
        
        return results
    
    async def _graceful_migration(
        self,
        flow_name: str,
        old_flow: ThinkingFlow,
        new_flow: ThinkingFlow,
        active_sessions: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform graceful migration (complete current step, then update)
        """
        results = {
            "flow_name": flow_name,
            "strategy": "graceful_migration",
            "sessions_processed": len(active_sessions),
            "successful_migrations": 0,
            "failed_migrations": 0,
            "errors": [],
        }
        
        for session in active_sessions:
            try:
                session_id = session["session_id"]
                
                # Wait for current step to complete
                await self._wait_for_step_completion(session_id)
                
                # Create migration plan for this session
                migration_plan = await self._create_session_migration_plan(
                    session, old_flow, new_flow, analysis
                )
                
                # Execute migration plan
                await self._execute_session_migration_plan(session_id, migration_plan)
                
                results["successful_migrations"] += 1
                logger.debug(f"Gracefully migrated session {session_id}")
                
            except Exception as e:
                results["failed_migrations"] += 1
                results["errors"].append({
                    "session_id": session.get("session_id"),
                    "error": str(e),
                })
                logger.error(f"Failed to gracefully migrate session {session.get('session_id')}: {e}")
        
        return results
    
    async def _restart_sessions(
        self,
        flow_name: str,
        old_flow: ThinkingFlow,
        new_flow: ThinkingFlow,
        active_sessions: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Restart sessions with new flow configuration
        """
        results = {
            "flow_name": flow_name,
            "strategy": "restart_sessions",
            "sessions_processed": len(active_sessions),
            "successful_migrations": 0,
            "failed_migrations": 0,
            "errors": [],
        }
        
        for session in active_sessions:
            try:
                session_id = session["session_id"]
                
                # Save session state for potential recovery
                session_state = await self.session_manager.get_session_state(session_id)
                
                # Stop current session
                await self.session_manager.stop_session(session_id)
                
                # Create new session with new flow
                new_session_id = await self.session_manager.create_session(
                    topic=session.get("topic", "Migrated session"),
                    flow_name=flow_name,
                    user_id=session.get("user_id"),
                )
                
                # Attempt to restore relevant state
                await self._restore_session_state(new_session_id, session_state, new_flow)
                
                results["successful_migrations"] += 1
                logger.debug(f"Restarted session {session_id} as {new_session_id}")
                
            except Exception as e:
                results["failed_migrations"] += 1
                results["errors"].append({
                    "session_id": session.get("session_id"),
                    "error": str(e),
                })
                logger.error(f"Failed to restart session {session.get('session_id')}: {e}")
        
        return results
    
    async def _wait_for_step_completion(self, session_id: str, timeout: int = 300) -> None:
        """Wait for current step to complete"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            session_state = await self.session_manager.get_session_state(session_id)
            
            if session_state.get("current_step_status") != "running":
                break
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning(f"Timeout waiting for step completion in session {session_id}")
                break
            
            await asyncio.sleep(1)
    
    async def _create_session_migration_plan(
        self,
        session: Dict[str, Any],
        old_flow: ThinkingFlow,
        new_flow: ThinkingFlow,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create migration plan for a specific session"""
        session_id = session["session_id"]
        session_state = await self.session_manager.get_session_state(session_id)
        
        current_step = session_state.get("current_step")
        completed_steps = session_state.get("completed_steps", [])
        
        plan = {
            "session_id": session_id,
            "current_step": current_step,
            "completed_steps": completed_steps,
            "actions": [],
        }
        
        # Determine what actions are needed based on changes
        for change in analysis["changes"]:
            if change["type"] == "step_removed":
                if change["step_id"] == current_step:
                    plan["actions"].append({
                        "type": "skip_to_next_step",
                        "reason": f"Current step {change['step_id']} was removed",
                    })
                elif change["step_id"] in completed_steps:
                    plan["actions"].append({
                        "type": "update_history",
                        "step_id": change["step_id"],
                        "reason": f"Step {change['step_id']} was removed from flow",
                    })
            
            elif change["type"] == "step_added":
                # Check if new step should be inserted before current step
                plan["actions"].append({
                    "type": "evaluate_new_step",
                    "step_id": change["step_id"],
                    "reason": f"New step {change['step_id']} was added",
                })
        
        return plan
    
    async def _execute_session_migration_plan(
        self, 
        session_id: str, 
        migration_plan: Dict[str, Any]
    ) -> None:
        """Execute migration plan for a session"""
        for action in migration_plan["actions"]:
            action_type = action["type"]
            
            if action_type == "skip_to_next_step":
                await self.session_manager.advance_to_next_step(session_id)
            
            elif action_type == "update_history":
                await self.session_manager.update_step_history(
                    session_id, action["step_id"], "removed_from_flow"
                )
            
            elif action_type == "evaluate_new_step":
                # Check if new step should be executed
                await self._evaluate_new_step_for_session(
                    session_id, action["step_id"]
                )
    
    async def _evaluate_new_step_for_session(
        self, 
        session_id: str, 
        step_id: str
    ) -> None:
        """Evaluate if a new step should be executed for an existing session"""
        # This is a simplified implementation
        # In practice, you'd need more sophisticated logic to determine
        # if a new step should be executed based on session state
        logger.info(f"Evaluating new step {step_id} for session {session_id}")
    
    async def _update_session_flow_cache(
        self, 
        session_id: str, 
        new_flow: ThinkingFlow
    ) -> None:
        """Update cached flow data in session"""
        await self.session_manager.update_session_metadata(
            session_id, {"flow_config": new_flow.model_dump()}
        )
    
    async def _restore_session_state(
        self,
        new_session_id: str,
        old_session_state: Dict[str, Any],
        new_flow: ThinkingFlow
    ) -> None:
        """Restore relevant state to new session"""
        # Restore topic and user context
        if "topic" in old_session_state:
            await self.session_manager.update_session_metadata(
                new_session_id, {"original_topic": old_session_state["topic"]}
            )
        
        # Restore any completed results that are still relevant
        completed_results = old_session_state.get("step_results", {})
        relevant_results = {}
        
        # Only restore results for steps that still exist in new flow
        new_step_ids = {step.step_id for step in new_flow.steps}
        for step_id, result in completed_results.items():
            if step_id in new_step_ids:
                relevant_results[step_id] = result
        
        if relevant_results:
            await self.session_manager.update_session_metadata(
                new_session_id, {"restored_results": relevant_results}
            )


class FlowHotUpdateManager:
    """
    Main manager for flow configuration hot updates
    """
    
    def __init__(
        self,
        flow_config_manager,
        session_manager
    ):
        self.flow_config_manager = flow_config_manager
        self.session_manager = session_manager
        self.analyzer = FlowUpdateAnalyzer()
        self.migrator = ActiveSessionMigrator(session_manager)
        
        self.update_callbacks: List[callable] = []
        self.error_callbacks: List[callable] = []
        
        # Register for flow config changes
        if hasattr(flow_config_manager, 'add_reload_callback'):
            flow_config_manager.add_reload_callback(self._on_flow_config_change)
    
    def add_update_callback(self, callback: callable) -> None:
        """Add callback for flow update notifications"""
        self.update_callbacks.append(callback)
    
    def add_error_callback(self, callback: callable) -> None:
        """Add callback for flow update errors"""
        self.error_callbacks.append(callback)
    
    async def _on_flow_config_change(
        self, 
        config_name: str, 
        config_data: Dict[str, Any]
    ) -> None:
        """Handle flow configuration changes"""
        if config_name != "flows":
            return
        
        logger.info("Flow configuration change detected, analyzing updates...")
        
        try:
            await self._process_flow_updates(config_data)
        except Exception as e:
            logger.error(f"Failed to process flow updates: {e}")
            await self._notify_error_callbacks("flow_update_processing", e)
    
    async def _process_flow_updates(self, new_flows_config: Dict[str, Any]) -> None:
        """Process flow configuration updates"""
        current_flows = self.flow_config_manager.get_all_flows()
        
        # Analyze each flow for changes
        for flow_name, new_flow_data in new_flows_config.items():
            if flow_name.startswith("_"):  # Skip metadata
                continue
            
            try:
                # Parse new flow configuration
                new_flow = ThinkingFlow(**new_flow_data)
                
                # Check if this is a new flow or an update
                if flow_name in current_flows:
                    old_flow = current_flows[flow_name]
                    await self._handle_flow_update(flow_name, old_flow, new_flow)
                else:
                    await self._handle_new_flow(flow_name, new_flow)
                    
            except Exception as e:
                logger.error(f"Failed to process flow '{flow_name}': {e}")
                await self._notify_error_callbacks(f"flow_processing_{flow_name}", e)
    
    async def _handle_flow_update(
        self, 
        flow_name: str, 
        old_flow: ThinkingFlow, 
        new_flow: ThinkingFlow
    ) -> None:
        """Handle update to existing flow"""
        logger.info(f"Processing update for flow: {flow_name}")
        
        # Analyze changes
        analysis = self.analyzer.analyze_flow_changes(old_flow, new_flow)
        
        logger.info(
            f"Flow '{flow_name}' analysis: "
            f"impact={analysis['impact_level']}, "
            f"migration_required={analysis['migration_required']}, "
            f"compatibility={analysis['compatibility']}"
        )
        
        # Migrate active sessions if needed
        migration_results = None
        if analysis["migration_required"]:
            migration_results = await self.migrator.migrate_active_sessions(
                flow_name, old_flow, new_flow, 
                analysis["migration_strategy"], analysis
            )
        
        # Notify callbacks
        await self._notify_update_callbacks({
            "type": "flow_updated",
            "flow_name": flow_name,
            "analysis": analysis,
            "migration_results": migration_results,
        })
    
    async def _handle_new_flow(self, flow_name: str, new_flow: ThinkingFlow) -> None:
        """Handle new flow addition"""
        logger.info(f"New flow detected: {flow_name}")
        
        # Notify callbacks
        await self._notify_update_callbacks({
            "type": "flow_added",
            "flow_name": flow_name,
            "flow_config": new_flow.model_dump(),
        })
    
    async def _notify_update_callbacks(self, update_info: Dict[str, Any]) -> None:
        """Notify update callbacks"""
        for callback in self.update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(update_info)
                else:
                    callback(update_info)
            except Exception as e:
                logger.error(f"Update callback failed: {e}")
    
    async def _notify_error_callbacks(self, context: str, error: Exception) -> None:
        """Notify error callbacks"""
        for callback in self.error_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(context, error)
                else:
                    callback(context, error)
            except Exception as e:
                logger.error(f"Error callback failed: {e}")
    
    async def force_flow_update_check(self) -> Dict[str, Any]:
        """Force a check for flow updates"""
        logger.info("Forcing flow update check...")
        
        try:
            # Reload flow configurations
            await self.flow_config_manager._reload_flows()
            
            # Get updated configurations
            updated_flows = self.flow_config_manager.get_all_flows()
            
            return {
                "status": "success",
                "flows_loaded": len(updated_flows),
                "flow_names": list(updated_flows.keys()),
            }
            
        except Exception as e:
            logger.error(f"Failed to force flow update check: {e}")
            return {
                "status": "error",
                "error": str(e),
            }
    
    async def get_flow_update_status(self) -> Dict[str, Any]:
        """Get current flow update status"""
        current_flows = self.flow_config_manager.get_all_flows()
        active_sessions = await self.session_manager.get_active_sessions()
        
        # Group sessions by flow
        sessions_by_flow = {}
        for session in active_sessions:
            flow_name = session.get("flow_name", "unknown")
            if flow_name not in sessions_by_flow:
                sessions_by_flow[flow_name] = []
            sessions_by_flow[flow_name].append(session)
        
        return {
            "total_flows": len(current_flows),
            "flow_names": list(current_flows.keys()),
            "active_sessions": len(active_sessions),
            "sessions_by_flow": {
                flow_name: len(sessions) 
                for flow_name, sessions in sessions_by_flow.items()
            },
            "hot_update_enabled": True,
        }


# Global flow hot update manager instance
flow_hot_update_manager = None  # Will be initialized with dependencies
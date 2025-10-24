"""
API endpoints for alerting system management.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.services.alerting_system import (
    AlertingSystem,
    get_alerting_system,
    AlertRule,
    Alert,
    AlertSeverity,
    AlertStatus
)
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerting"])


# Request/Response Models
class CreateAlertRuleRequest(BaseModel):
    name: str
    description: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    threshold: float
    severity: str  # "low", "medium", "high", "critical"
    evaluation_window: int = 300
    cooldown_period: int = 900
    tags: Optional[Dict[str, str]] = None
    enabled: bool = True


class UpdateAlertRuleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[str] = None
    evaluation_window: Optional[int] = None
    cooldown_period: Optional[int] = None
    enabled: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str
    threshold: float
    severity: str
    evaluation_window: int
    cooldown_period: int
    tags: Dict[str, str]
    enabled: bool
    created_at: str


class AlertResponse(BaseModel):
    alert_id: str
    rule_id: str
    name: str
    description: str
    severity: str
    status: str
    metric_name: str
    current_value: float
    threshold: float
    condition: str
    tags: Dict[str, str]
    fired_at: str
    resolved_at: Optional[str]
    acknowledged_at: Optional[str]
    acknowledged_by: Optional[str]


# Alert Rules Endpoints

@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    request: CreateAlertRuleRequest,
    current_user: dict = Depends(get_current_user),
    alerting_system: AlertingSystem = Depends(get_alerting_system)
):
    """Create a new alert rule."""
    try:
        # Validate severity
        try:
            severity_enum = AlertSeverity(request.severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {request.severity}")
        
        # Generate rule ID
        import time
        rule_id = f"rule_{int(time.time())}"
        
        # Create rule
        rule = AlertRule(
            rule_id=rule_id,
            name=request.name,
            description=request.description,
            metric_name=request.metric_name,
            condition=request.condition,
            threshold=request.threshold,
            severity=severity_enum,
            evaluation_window=request.evaluation_window,
            cooldown_period=request.cooldown_period,
            tags=request.tags or {},
            enabled=request.enabled
        )
        
        success = await alerting_system.add_rule(rule)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create alert rule")
        
        return AlertRuleResponse(
            rule_id=rule.rule_id,
            name=rule.name,
            description=rule.description,
            metric_name=rule.metric_name,
            condition=rule.condition,
            threshold=rule.threshold,
            severity=rule.severity.value,
            evaluation_window=rule.evaluation_window,
            cooldown_period=rule.cooldown_period,
            tags=rule.tags,
            enabled=rule.enabled,
            created_at=rule.created_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert rule: {str(e)}")


@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    alerting_system: AlertingSystem = Depends(get_alerting_system)
):
    """List all alert rules."""
    try:
        rules = await alerting_system.get_rules()
        
        return [
            AlertRuleResponse(
                rule_id=rule.rule_id,
                name=rule.name,
                description=rule.description,
                metric_name=rule.metric_name,
                condition=rule.condition,
                threshold=rule.threshold,
                severity=rule.severity.value,
                evaluation_window=rule.evaluation_window,
                cooldown_period=rule.cooldown_period,
                tags=rule.tags,
                enabled=rule.enabled,
                created_at=rule.created_at.isoformat()
            )
            for rule in rules
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list alert rules: {str(e)}")


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str,
    request: UpdateAlertRuleRequest,
    current_user: dict = Depends(get_current_user),
    alerting_system: AlertingSystem = Depends(get_alerting_system)
):
    """Update an alert rule."""
    try:
        # Prepare updates
        updates = {}
        
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.threshold is not None:
            updates["threshold"] = request.threshold
        if request.severity is not None:
            try:
                severity_enum = AlertSeverity(request.severity)
                updates["severity"] = severity_enum.value
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {request.severity}")
        if request.evaluation_window is not None:
            updates["evaluation_window"] = request.evaluation_window
        if request.cooldown_period is not None:
            updates["cooldown_period"] = request.cooldown_period
        if request.enabled is not None:
            updates["enabled"] = request.enabled
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        success = await alerting_system.update_rule(rule_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        # Get updated rule
        rules = await alerting_system.get_rules()
        updated_rule = next((r for r in rules if r.rule_id == rule_id), None)
        
        if not updated_rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        return AlertRuleResponse(
            rule_id=updated_rule.rule_id,
            name=updated_rule.name,
            description=updated_rule.description,
            metric_name=updated_rule.metric_name,
            condition=updated_rule.condition,
            threshold=updated_rule.threshold,
            severity=updated_rule.severity.value,
            evaluation_window=updated_rule.evaluation_window,
            cooldown_period=updated_rule.cooldown_period,
            tags=updated_rule.tags,
            enabled=updated_rule.enabled,
            created_at=updated_rule.created_at.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update alert rule: {str(e)}")


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
    alerting_system: AlertingSystem = Depends(get_alerting_system)
):
    """Delete an alert rule."""
    try:
        success = await alerting_system.delete_rule(rule_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        return {"message": f"Alert rule {rule_id} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete alert rule: {str(e)}")


# Alerts Endpoints

@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    alerting_system: AlertingSystem = Depends(get_alerting_system)
):
    """List alerts with optional filters."""
    try:
        if status and status == "active":
            alerts = await alerting_system.get_active_alerts()
        else:
            # For now, just return active alerts
            # In a full implementation, you'd add more filtering
            alerts = await alerting_system.get_active_alerts()
        
        # Apply severity filter
        if severity:
            try:
                severity_enum = AlertSeverity(severity)
                alerts = [a for a in alerts if a.severity == severity_enum]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        
        # Apply limit
        alerts = alerts[:limit]
        
        return [
            AlertResponse(
                alert_id=alert.alert_id,
                rule_id=alert.rule_id,
                name=alert.name,
                description=alert.description,
                severity=alert.severity.value,
                status=alert.status.value,
                metric_name=alert.metric_name,
                current_value=alert.current_value,
                threshold=alert.threshold,
                condition=alert.condition,
                tags=alert.tags,
                fired_at=alert.fired_at.isoformat(),
                resolved_at=alert.resolved_at.isoformat() if alert.resolved_at else None,
                acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                acknowledged_by=alert.acknowledged_by
            )
            for alert in alerts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list alerts: {str(e)}")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    alerting_system: AlertingSystem = Depends(get_alerting_system)
):
    """Acknowledge an alert."""
    try:
        username = current_user.get("username", "unknown")
        success = await alerting_system.acknowledge_alert(alert_id, username)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": f"Alert {alert_id} acknowledged by {username}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    alerting_system: AlertingSystem = Depends(get_alerting_system)
):
    """Resolve an alert."""
    try:
        success = await alerting_system.resolve_alert(alert_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": f"Alert {alert_id} resolved"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")


# Metrics and Status Endpoints

@router.get("/status")
async def get_alerting_status(
    alerting_system: AlertingSystem = Depends(get_alerting_system)
):
    """Get alerting system status."""
    try:
        active_alerts = await alerting_system.get_active_alerts()
        rules = await alerting_system.get_rules()
        
        # Count alerts by severity
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = len([
                a for a in active_alerts if a.severity == severity
            ])
        
        # Count rules by status
        enabled_rules = len([r for r in rules if r.enabled])
        disabled_rules = len([r for r in rules if not r.enabled])
        
        return {
            "active_alerts": len(active_alerts),
            "total_rules": len(rules),
            "enabled_rules": enabled_rules,
            "disabled_rules": disabled_rules,
            "alerts_by_severity": severity_counts,
            "system_status": "healthy" if len(active_alerts) == 0 else "alerts_active"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerting status: {str(e)}")


@router.get("/test/{rule_id}")
async def test_alert_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
    alerting_system: AlertingSystem = Depends(get_alerting_system)
):
    """Test an alert rule (for debugging)."""
    try:
        # Get the rule
        rules = await alerting_system.get_rules()
        rule = next((r for r in rules if r.rule_id == rule_id), None)
        
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        
        # Get current metric value
        current_value = await alerting_system._get_metric_value(rule.metric_name, rule.tags)
        
        if current_value is None:
            return {
                "rule_id": rule_id,
                "metric_name": rule.metric_name,
                "current_value": None,
                "threshold": rule.threshold,
                "condition": rule.condition,
                "condition_met": False,
                "message": "Metric value not available"
            }
        
        # Check condition
        condition_met = alerting_system._check_condition(
            current_value, rule.condition, rule.threshold
        )
        
        return {
            "rule_id": rule_id,
            "metric_name": rule.metric_name,
            "current_value": current_value,
            "threshold": rule.threshold,
            "condition": rule.condition,
            "condition_met": condition_met,
            "message": "Alert would fire" if condition_met else "Alert condition not met"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test alert rule: {str(e)}")
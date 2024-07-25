from .models import LeadHistory,AgentSalesHistory

def record_action(lead, action, performed_by, details=None, notes=None):
    LeadHistory.objects.create(
        lead=lead,
        action=action,
        performed_by=performed_by,
        details=details,
        notes=notes
    )

def record_agent_sales_history(agent, commitment, updated_by):
    AgentSalesHistory.objects.create(
        agent=agent,
        commitment=commitment,
        updated_by=updated_by
    )

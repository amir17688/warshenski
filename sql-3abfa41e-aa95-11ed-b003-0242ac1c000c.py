from .api import get_query_manager

__all__ = ("get_query_manager",)


"""
opportunity_qm = models.Opportunity.get_query_manager()

opportunities = opportunity_qm.run(
    {
        'id': o.Id,
        'accounts': [
            {'id': a.Id}
            for a in o.Accounts
        ]
    }
    for o in opportunity_qm
)
"""

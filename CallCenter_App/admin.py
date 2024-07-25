from django.contrib import admin
from .models import (
    UserProfile, Team, SubDisposition, Package, Lead, LeadTransferRecord,
    PaidCustomer, Company, Invoice, InvoicePDF, AgentSalesHistory,
    BreakType, Break, Attendance, Complaint, PaymentMethod
)

admin.site.register(UserProfile)
admin.site.register(Team)
admin.site.register(SubDisposition)
admin.site.register(Package)
admin.site.register(Lead)
admin.site.register(LeadTransferRecord)
admin.site.register(PaidCustomer)
admin.site.register(Company)
admin.site.register(Invoice)
admin.site.register(InvoicePDF)
admin.site.register(AgentSalesHistory)
admin.site.register(BreakType)
admin.site.register(Break)
admin.site.register(Attendance)
admin.site.register(Complaint)
admin.site.register(PaymentMethod)

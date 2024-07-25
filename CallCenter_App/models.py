import uuid
from uuid import uuid4
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

class UserProfile(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('On Resign Period', 'On Resign Period'),
        ('Absconded', 'Absconded'),
    )

    ROLE_CHOICES = (
        ('Team Leader', 'Team Leader'),
        ('Agent', 'Agent'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    emergency_phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_joining = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    on_break = models.BooleanField(default=False)
    commitment = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    @staticmethod
    def user_limit_reached():
        user_count = User.objects.filter(is_superuser=False).count()
        return user_count >= 25

    def get_team_leader_id(self):
        if self.role == 'Agent':
            team = self.teams_as_agent.first()
            if team:
                return team.leader.id
        return None

    def __str__(self):
        return self.user.username

User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])


class Team(models.Model):
    name = models.CharField(max_length=100)
    leader = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='teams_as_leader', null=False)
    agents = models.ManyToManyField(UserProfile, related_name='teams_as_agent')

    def __str__(self):
        return self.name


class SubDisposition(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Package(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class PaymentMethod(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
class Lead(models.Model):
    DISPOSITION_CHOICES = (
        ('Fresh', 'Fresh'),
        ('Connected', 'Connected'),
        ('Not connected', 'Not connected'),
    )

    date = models.DateField(null=True, blank=True,)
    full_name = models.CharField(max_length=100,null=True, blank=True,)
    contact_number = models.CharField(max_length=15,  unique=True, validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')])
    state = models.CharField(max_length=100, null=True, blank=True,)
    capital = models.DecimalField(max_digits=10, null=True, blank=True, decimal_places=2)
    assigned_to = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_leads')
    assigned_to_team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name='leads')
    disposition = models.CharField(max_length=20, choices=DISPOSITION_CHOICES, default='Fresh', null=True, blank=True,)
    sub_disposition = models.ForeignKey('SubDisposition', on_delete=models.SET_NULL, null=True, related_name='sub_dispositions', default=None)
    remark = models.TextField(blank=True, null=True)
    reminder = models.DateTimeField(null=True, blank=True)
    
    def get_assigned_to_full_name(self):
        if self.assigned_to:
            return f"{self.assigned_to.first_name} {self.assigned_to.last_name}"
        return 'N/A'

    def get_assigned_to_team_leader_full_name(self):
        if self.assigned_to_team and self.assigned_to_team.leader:
            return f"{self.assigned_to_team.leader.first_name} {self.assigned_to_team.leader.last_name}"
        return 'N/A'
    
    def save(self, *args, **kwargs):
        if self.sub_disposition is None:
            self.sub_disposition, _ = SubDisposition.objects.get_or_create(name='Fresh')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.contact_number}"
    
class LeadHistory(models.Model):
    lead = models.ForeignKey(Lead, related_name='history', on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=255)
    performed_by = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True) 
    notes = models.TextField(null=True, blank=True)  

class LeadTransferRecord(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='transfer_records')
    transfer_date = models.DateField(auto_now_add=True)
    transfer_time = models.TimeField(auto_now_add=True)
    from_user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='transferred_leads_from')
    to_user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='transferred_leads_to', null=True, blank=True)
    transfer_remark = models.TextField(blank=True, null=True)
    disposition = models.CharField(max_length=20, choices=Lead.DISPOSITION_CHOICES, default='Fresh')
    sub_disposition = models.ForeignKey(SubDisposition, on_delete=models.SET_NULL, null=True, related_name='transferred_leads')

    def __str__(self):
        return f"Lead Transfer: {self.lead.full_name} from {self.from_user.user.get_full_name} to {self.to_user.user.get_gull_name if self.to_user else 'N/A'} on {self.transfer_date} at {self.transfer_time}"


class PaidCustomer(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    customer_id = models.CharField(max_length=12, editable=False)
    date = models.DateField(auto_now_add=True)
    contact_number = models.CharField(max_length=15, validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')])
    lead = models.ForeignKey('Lead', null=True, blank=True, on_delete=models.SET_NULL, related_name='paid_customers')
    payment_date = models.DateField()
    package = models.ForeignKey('Package', on_delete=models.CASCADE, related_name='paid_customers')
    package_start_date = models.DateField(default=timezone.now)
    package_end_date = models.DateField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100)
    payment_method = models.ForeignKey('PaymentMethod', on_delete=models.CASCADE, related_name='paid_customers')
    pan_number = models.CharField(max_length=10, validators=[RegexValidator(regex=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    amount_with_gst = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    attachment = models.FileField(upload_to='attachments/', blank=True, null=True)
    verified = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS_CHOICES)
    remark = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk: 
            existing_customer = PaidCustomer.objects.filter(contact_number=self.contact_number).first()
            if existing_customer:
                self.customer_id = existing_customer.customer_id
            else:
                self.customer_id = str(uuid4().int)[:12]

        self.tax_amount = self.amount_paid * Decimal('0.18')
        self.amount_with_gst = self.amount_paid - self.tax_amount
        
        try:
            self.lead = Lead.objects.get(contact_number=self.contact_number)
        except Lead.DoesNotExist:
            self.lead = None

        super().save(*args, **kwargs)

    @property
    def formatted_amount_with_gst(self):
        return "{:,}".format(self.amount_with_gst)

    @classmethod
    def unique_paid_customers(cls):
        return cls.objects.order_by('contact_number').distinct('contact_number')

    def __str__(self):
        return f"PaidCustomer {self.lead.full_name if self.lead else 'Unknown'} ({self.customer_id})"
    
    
class Company(models.Model):
    company_name = models.CharField(max_length=255)
    company_address = models.TextField()
    company_gstin = models.CharField(max_length=15)
    company_email = models.EmailField()
    company_phone_number = models.CharField(max_length=15)
    company_logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    company_about = models.TextField(blank=True, null=True)
    company_tagline = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.pk and Company.objects.exists():
            raise ValidationError('There can only be one Company instance.')
        super(Company, self).save(*args, **kwargs)

    def __str__(self):
        return self.company_name

class Invoice(models.Model):
    date = models.DateField(default=timezone.now)
    unique_invoice_number = models.CharField(max_length=8, unique=True)
    customer = models.ForeignKey(PaidCustomer, on_delete=models.CASCADE, related_name='invoices')
    amount_in_words = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices', default=None)
    pdf = models.OneToOneField('InvoicePDF', null=True, blank=True, on_delete=models.SET_NULL, related_name='invoice')

    def save(self, *args, **kwargs):
        if not self.unique_invoice_number:
            self.unique_invoice_number = str(uuid.uuid4().int)[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.unique_invoice_number} for {self.customer.lead.full_name if self.customer.lead else 'Unknown'}"

class InvoicePDF(models.Model):
    invoice_object = models.ForeignKey('Invoice', on_delete=models.CASCADE, related_name='pdfs')
    pdf_file = models.FileField(upload_to='invoice_pdfs/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice PDF for {self.invoice.unique_invoice_number}"

class AgentSalesHistory(models.Model):
    date_time = models.DateTimeField(default=timezone.now)
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_history')
    commitment = models.DecimalField(max_digits=10, decimal_places=2)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_sales')

    def __str__(self):
        return f"Agent: {self.agent.email}, Updated by: {self.updated_by.email}, Date: {self.date_time}"

class BreakType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Break(models.Model):
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    break_type = models.ForeignKey('BreakType', on_delete=models.CASCADE)
    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    attendance = models.ForeignKey('Attendance', on_delete=models.CASCADE, related_name='breaks')
    active = models.BooleanField(default=True)

    def end_break(self):
        self.end_time = timezone.now()
        self.active = False
        self.save()

    def break_duration(self):
        if self.end_time:
            duration = self.end_time - self.start_time
            return duration.total_seconds() // 60
        return 0

    def formatted_duration(self):
        duration = self.break_duration()
        hours = duration // 60
        minutes = duration % 60
        return f"{hours} hours {minutes} minutes"

    def __str__(self):
        return f"{self.break_type.name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Half day', 'Half day'),
        ('Absent', 'Absent'),
    ]

    ON_TIME_LATE_CHOICES = [
        ('On Time', 'On Time'),
        ('Late', 'Late'),
    ]

    SHIFT_START_TIME = timezone.datetime.strptime('9:00 AM', '%I:%M %p').time()
    SHIFT_END_TIME = timezone.datetime.strptime('6:00 PM', '%I:%M %p').time()
    LOGIN_END_TIME = timezone.datetime.strptime('9:10 AM', '%I:%M %p').time()
    LOGIN_HALF_DAY_THRESHOLD = 4.5 * 60  
    GRACE_PERIOD_MINUTES = 10  

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    day = models.CharField(max_length=20, blank=True)  
    login_time = models.TimeField(blank=True, null=True)
    logout_time = models.TimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    on_time_late = models.CharField(max_length=10, choices=ON_TIME_LATE_CHOICES, blank=True, null=True)
    regulation_reason = models.TextField(blank=True, null=True)
    is_logged_in = models.BooleanField(default=False)  
    total_login_time_hours = models.IntegerField(default=0)  
    total_login_time_minutes = models.IntegerField(default=0)  
    total_break_time_hours = models.IntegerField(default=0)  
    total_break_time_minutes = models.IntegerField(default=0)  

    def save(self, *args, **kwargs):
        if self.login_time and self.logout_time:
            login_datetime = timezone.datetime.combine(self.date, self.login_time)
            logout_datetime = timezone.datetime.combine(self.date, self.logout_time)
            shift_start_datetime = timezone.datetime.combine(self.date, self.SHIFT_START_TIME)
            login_end_datetime = timezone.datetime.combine(self.date, self.LOGIN_END_TIME)

            if login_datetime <= shift_start_datetime:
                self.on_time_late = 'On Time'
            elif shift_start_datetime < login_datetime <= login_end_datetime:
                self.on_time_late = 'Late'
            elif login_datetime <= (shift_start_datetime + timezone.timedelta(minutes=self.GRACE_PERIOD_MINUTES)):
                self.on_time_late = 'On Time'

            total_login_minutes = (logout_datetime - login_datetime).total_seconds() // 60
            total_break_minutes = sum(b.break_duration() for b in self.breaks.all())
            self.total_break_time_hours = int(total_break_minutes // 60)
            self.total_break_time_minutes = int(total_break_minutes % 60)

            effective_working_minutes = total_login_minutes - total_break_minutes
            self.total_login_time_hours = int(effective_working_minutes // 60)
            self.total_login_time_minutes = int(effective_working_minutes % 60)

            if effective_working_minutes >= 9 * 60:
                self.status = 'Present'
            elif effective_working_minutes >= self.LOGIN_HALF_DAY_THRESHOLD:
                self.status = 'Half day'
            else:
                self.status = 'Absent'

        if not self.day:
            self.day = self.date.strftime('%A')

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.date}"


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]

    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='complaints')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    resolved_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Complaint by {self.paid_customer.contact_number} - {self.subject}"

    def save(self, *args, **kwargs):
        if self.status == 'Resolved' and self.resolved_at is None:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)


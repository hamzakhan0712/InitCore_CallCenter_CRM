from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from .models import UserProfile, Team, Company, Invoice, Lead, BreakType, Package, SubDisposition, PaidCustomer, PaymentMethod, Complaint
from django.core.validators import FileExtensionValidator
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'autocomplete': 'current-password'})
    )

    def confirm_login_allowed(self, user):
        if hasattr(user, 'profile'):
            if user.profile.status in ['Inactive', 'Absconded']:
                raise ValidationError(
                    "Your account is currently {} and you are not allowed to log in.".format(user.profile.status),
                    code='inactive_or_absconded',
                )
        else:
            raise ValidationError(
                "Your account does not have a profile associated with it.",
                code='no_profile',
            )
        super().confirm_login_allowed(user)


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}), required=False)
    emergency_phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Phone Number'}), required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Address'}), required=False)
    date_of_joining = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'Date of Joining', 'type': 'date'}), required=False)
    status = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), initial='Active')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and self.request.user.profile.role == 'Team Leader':
            self.fields['role'].choices = [
                (role, label) for role, label in UserProfile.ROLE_CHOICES if role != 'Team Leader'
            ]

    def save(self, commit=True):
        if UserProfile.user_limit_reached():
            raise forms.ValidationError('User limit reached. Cannot create more users.')
        user = super().save(commit=False)
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                phone_number=self.cleaned_data['phone_number'],
                emergency_phone_number=self.cleaned_data['emergency_phone_number'],
                address=self.cleaned_data['address'],
                date_of_joining=self.cleaned_data['date_of_joining'],
                status=self.cleaned_data['status'],
            )
        return user

class CustomUserChangeForm(UserChangeForm):
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}), required=False)
    emergency_phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency Phone Number'}), required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Address'}), required=False)
    date_of_joining = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'Date of Joining', 'type': 'date'}), required=False)
    status = forms.ChoiceField(choices=UserProfile.STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), initial='Active')

    class Meta(UserChangeForm.Meta):
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
        )
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and self.request.user.profile.role == 'Team Leader':
            self.fields['role'].choices = [
                (role, label) for role, label in UserProfile.ROLE_CHOICES if role != 'Team Leader'
            ]

        if self.instance and self.instance.profile:
            profile = self.instance.profile
            self.fields['role'].initial = profile.role
            self.fields['phone_number'].initial = profile.phone_number
            self.fields['emergency_phone_number'].initial = profile.emergency_phone_number
            self.fields['address'].initial = profile.address
            self.fields['date_of_joining'].initial = profile.date_of_joining
            self.fields['status'].initial = profile.status

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            profile = user.profile
            profile.role = self.cleaned_data['role']
            profile.phone_number = self.cleaned_data['phone_number']
            profile.emergency_phone_number = self.cleaned_data['emergency_phone_number']
            profile.address = self.cleaned_data['address']
            profile.date_of_joining = self.cleaned_data['date_of_joining']
            profile.status = self.cleaned_data['status']
            profile.save()
        return user


class TeamForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agents'].queryset = UserProfile.objects.filter(role='Agent')
        self.fields['leader'].queryset = UserProfile.objects.filter(role='Team Leader')
        
        self.fields['leader'].label_from_instance = lambda obj: f"{obj.user.first_name} {obj.user.last_name}"
        self.fields['agents'].label_from_instance = lambda obj: f"{obj.user.first_name} {obj.user.last_name}"

    leader = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(role='Team Leader'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    agents = forms.ModelMultipleChoiceField(
        queryset=UserProfile.objects.filter(role='Agent'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Team
        fields = ['name', 'leader', 'agents']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Team Name'}),
        }

class AddAgentToTeamForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['agent'].queryset = UserProfile.objects.filter(role='Agent')
        self.fields['agent'].label_from_instance = lambda obj: f"{obj.user.first_name} {obj.user.last_name}"

    agent = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(role='Agent'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class LeadImportForm(forms.Form):
    file = forms.FileField(
        label='Upload File',
        validators=[FileExtensionValidator(['csv', 'xlsx'])],  
        widget=forms.ClearableFileInput(attrs={'accept': '.csv,.xlsx'})  
    )

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['date', 'full_name', 'contact_number', 'state', 'capital', 'assigned_to', 'disposition', 'sub_disposition', 'remark', 'reminder']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Select Date'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Enter Full Name'}),
            'contact_number': forms.TextInput(attrs={'placeholder': 'Enter Contact Number', 'pattern': r'^\+?1?\d{9,15}$'}),
            'state': forms.TextInput(attrs={'placeholder': 'Enter State'}),
            'capital': forms.NumberInput(attrs={'placeholder': 'Enter Capital ( ₹Rupees )'}),
            'disposition': forms.Select(attrs={'placeholder': 'Select Disposition'}),
            'sub_disposition': forms.Select(attrs={'placeholder': 'Select Sub Disposition'}),
            'remark': forms.Textarea(attrs={'placeholder': 'Enter Remark'}),
            'reminder': forms.DateTimeInput(attrs={'type': 'datetime-local', 'placeholder': 'Set Reminder'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = UserProfile.objects.filter(role='Agent')
        self.fields['sub_disposition'].required = False
        self.fields['sub_disposition'].queryset = SubDisposition.objects.all()
        for field_name, field in self.fields.items():
            field.label = field_name.replace('_', ' ').capitalize()

class BreakTypeForm(forms.ModelForm):
    class Meta:
        model = BreakType
        fields = ['name']
        placeholders = {
            'name': 'Name'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = self.Meta.placeholders['name']

class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ['name']
        placeholders = {
            'name': 'Package  Name',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, placeholder_text in self.Meta.placeholders.items():
            self.fields[field_name].widget.attrs['placeholder'] = placeholder_text

class SubDispositionForm(forms.ModelForm):
    class Meta:
        model = SubDisposition
        fields = ['name']
        placeholders = {
            'name': 'Name'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = self.Meta.placeholders['name']

class PaidCustomerForm(forms.ModelForm):
    class Meta:
        model = PaidCustomer
        fields = [
            'payment_date', 'contact_number', 'package', 'package_end_date', 'transaction_id',
            'payment_method', 'pan_number', 'amount_paid', 'attachment', 'payment_status', 'remark'
        ]
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Payment'}),
            'contact_number': forms.TextInput(attrs={'type': 'tel', 'placeholder': 'Contact'}),
            'package': forms.Select(attrs={'placeholder': 'Package'}),
            'package_end_date': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Package End Date'}),
            'transaction_id': forms.TextInput(attrs={'type': 'text', 'placeholder': 'Transaction'}),
            'payment_method': forms.Select(attrs={'placeholder': 'Method'}),
            'pan_number': forms.TextInput(attrs={'type': 'text', 'placeholder': 'PAN - ABCDE1234F'}),
            'amount_paid': forms.NumberInput(attrs={'type': 'number', 'placeholder': 'Amount'}),
            'attachment': forms.FileInput(attrs={'placeholder': 'Attachment'}),
            'payment_status': forms.Select(attrs={'placeholder': 'Status'}),
            'remark': forms.Textarea(attrs={'placeholder': 'Enter Remark'})
        }

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name']
        placeholders = {
            'name': 'Name'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = self.Meta.placeholders['name']



class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'unique_invoice_number', 'customer', 'amount_in_words', 'company', 'date'
        ]
        widgets = {
            'unique_invoice_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Invoice Number'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'amount_in_words': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Amount in Words'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'}),
        }

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'company_name',
            'company_address',
            'company_gstin',
            'company_email',
            'company_phone_number',
            'company_logo',
            'company_about',
            'company_tagline'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name',
                'maxlength': '255',
                'required': True
            }),
            'company_address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company address',
                'rows': 2,
                'required': True
            }),
            'company_gstin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company GSTIN',
                'maxlength': '15',
                'pattern': '[0-9A-Z]{15}',
                'title': 'GSTIN should be 15 characters long',
                'required': True
            }),
            'company_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company email',
                'type': 'email',
                'required': True
            }),
            'company_phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company phone number',
                'maxlength': '15',
                'pattern': '[0-9]{10,15}',
                'title': 'Phone number should be between 10 to 15 digits',
                'required': True
            }),
            'company_logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'required': False
            }),
            'company_about': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter details about the company',
                'rows': 8,
                'required': False
            }),
            'company_tagline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company tagline',
                'maxlength': '255',
                'required': False
            }),
        }

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['name', 'status', 'priority', 'subject', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Complaint Title'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subject'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter description'}),
        }
    def save(self, commit=True):
        complaint = super().save(commit=False)
        if commit:
            complaint.save()
        return complaint
    



class UpdateSalesForm(forms.Form):
    commitment = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter commitment amount'}),
    )
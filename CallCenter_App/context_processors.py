from .models import Company,BreakType

def company_info(request):
    try:
        company = Company.objects.get()
        break_types = BreakType.objects.all() 
    except Company.DoesNotExist:
        company = None
        break_types = None
    return {'company': company,'break_types':break_types}

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

def home(request):
    return render(request, 'core/index.html')

@login_required(login_url='login')
def customer_dashboard(request):
    return render(request, 'customer/home.html')


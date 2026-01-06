from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.utils.text import slugify
from .models import Transaction
from apps.accounts.models import Account
from .utils import generate_statement_context

from xhtml2pdf import pisa
from io import BytesIO

class StatementPDFView(LoginRequiredMixin, View):
    def get(self, request, account_id):
        account = get_object_or_404(Account, id=account_id)
        
        # Security Check
        has_access = False
        if account.user == request.user:
            has_access = True
        elif account.shared_users.filter(user=request.user).exists():
            has_access = True
            
        if not has_access:
            return HttpResponseForbidden("You do not have permission to view this statement.")

        # Get Filter Parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        transaction_type = request.GET.get('type')
        
        # Generate Context
        context = generate_statement_context(account, start_date, end_date, transaction_type)
        
        # Render HTML
        html_string = render_to_string('statements/pdf_template.html', context)
        
        # Create PDF using xhtml2pdf
        response = HttpResponse(content_type='application/pdf')
        filename = f"{slugify(account.name)}_statement_{context['start_date']}_{context['end_date']}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        
        # Create the PDF object, using the buffer as its "file."
        pisa_status = pisa.CreatePDF(
            html_string, 
            dest=response
        )

        # If there was an error, return it
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
            
        return response

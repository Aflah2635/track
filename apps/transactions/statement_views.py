from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, FileResponse
from django.template.loader import render_to_string
from django.utils.text import slugify
from apps.accounts.models import Account
from .utils import generate_statement_context
from xhtml2pdf import pisa
from io import BytesIO

class StatementPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            account = get_object_or_404(Account, pk=pk)
            
            # Security Check
            # User must be owner OR in shared_users
            print(f"DEBUG: Generating statement for account {account.id} by user {request.user}")
            if account.user != request.user and not account.shared_users.filter(user=request.user).exists():
                print("DEBUG: Access Denied")
                return HttpResponseForbidden("You do not have permission to view this statement.")

            # Get Filter Parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            transaction_type = request.GET.get('type')
            category_id = request.GET.get('category')
            user_id = request.GET.get('user')
            
            # Generate Context
            context = generate_statement_context(
                account=account, 
                start_date_str=start_date, 
                end_date_str=end_date, 
                transaction_type=transaction_type,
                category_id=category_id,
                user_id=user_id
            )
            
            # Render HTML
            html_string = render_to_string('statements/PDF_temp.html', context)
            
            # Create PDF using xhtml2pdf
            buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html_string, dest=buffer)

            if pisa_status.err:
                return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
                
            # Use HttpResponse for robust download handling
            pdf_data = buffer.getvalue()
            buffer.close()
            
            filename = f"{slugify(account.name)}_statement_{context['start_date']}_{context['end_date']}.pdf"
            response = HttpResponse(pdf_data, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            import traceback
            traceback.print_exc()
            return HttpResponse(f"<pre>Error generating PDF:\n{traceback.format_exc()}</pre>", status=500)

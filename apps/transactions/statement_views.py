from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.utils.text import slugify
from apps.accounts.models import Account
from .utils import generate_statement_context
from xhtml2pdf import pisa
from io import BytesIO

from django.conf import settings
from django.contrib.staticfiles import finders
import os

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those resources
    """
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = list(os.path.realpath(path) for path in result)
        path=result[0]
    else:
        sUrl = settings.STATIC_URL        # Typically /static/
        sRoot = settings.STATIC_ROOT      # Typically /home/userX/project_static/
        mUrl = settings.MEDIA_URL         # Typically /media/
        mRoot = settings.MEDIA_ROOT       # Typically /home/userX/project_media/

        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri

    # make sure that file exists
    if not os.path.isfile(path):
            raise Exception(
                'media URI must start with %s or %s' % (sUrl, mUrl)
            )
    return path

class StatementPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            # Check Subscription Limit
            user_sub = request.user.subscription
            if hasattr(user_sub, 'reset_usage_if_needed'):
                 user_sub.reset_usage_if_needed()
            
            if user_sub.plan.pdf_export_limit is not None:
                if user_sub.pdf_exports_used >= user_sub.plan.pdf_export_limit:
                     return HttpResponseForbidden(f"You have reached your monthly PDF export limit ({user_sub.plan.pdf_export_limit}). Upgrade to Plus/Pro for more.")

            account = get_object_or_404(Account, pk=pk)
            
            # Security Check
            if account.user != request.user and not account.shared_users.filter(user=request.user).exists():
                return HttpResponseForbidden("You do not have permission to view this statement.")

            # Get Filter Parameters
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # Generate Context
            try:
                context = generate_statement_context(
                    account=account, 
                    start_date_str=start_date, 
                    end_date_str=end_date
                )
            except Exception as e:
                print(f"ERROR: Context generation failed: {e}")
                raise e
            
            # Render HTML
            try:
                html_string = render_to_string('statements/PDF_temp.html', context)
            except Exception as e:
                print(f"ERROR: Template rendering failed: {e}")
                raise e
            
            # Create PDF using xhtml2pdf
            buffer = BytesIO()
            pisa_status = pisa.CreatePDF(html_string, dest=buffer, link_callback=link_callback)

            if pisa_status.err:
                print(f"ERROR: PISA error: {pisa_status.err}")
                return HttpResponse('We had some errors <pre>' + html_string + '</pre>')
                
            # Use HttpResponse for robust download handling
            pdf_data = buffer.getvalue()
            buffer.close()
            
            filename = f"{slugify(account.name)}_statement_{context['start_date']}_{context['end_date']}.pdf"
            response = HttpResponse(pdf_data, content_type='application/pdf')
            # Changed to attachment to force clean download
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Increment Usage
            if user_sub.plan.pdf_export_limit is not None:
                user_sub.pdf_exports_used += 1
                user_sub.save()
            
            return response
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"CRITICAL ERROR in get:\n{error_msg}")
            return HttpResponse(f"<pre>Error generating PDF:\n{error_msg}</pre>", status=500)

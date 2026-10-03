from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
# from xhtml2pdf import pisa
from .models import Invoice
from .utils import fa_convert

def render_invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    template_path = 'accounting/pdf_invoice.html'
    
    # اصلاح متون فارسی برای نمایش درست در PDF
    context = {
        'invoice': invoice,
        'title': fa_convert(invoice.title),
        'client_name': fa_convert(invoice.client.name),
        'unit_name': fa_convert(invoice.business_unit.name),
        'items': [
            {
                'desc': fa_convert(item.description),
                'price': item.unit_price,
                'qty': item.quantity,
                'total': item.total_price
            } for item in invoice.items.all()
        ]
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.id}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)

    # تبدیل HTML به PDF
    pisa_status = pisa.CreatePDF(html, dest=response, encoding='utf-8')
    
    if pisa_status.err:
        return HttpResponse('خطا در تولید PDF', status=500)
    return response
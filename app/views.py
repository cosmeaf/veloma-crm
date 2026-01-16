# app/views.py
from django.shortcuts import render

def upload_page(request):
    """
    Renderiza a página de upload de extratos.
    """
    # O caminho agora é apenas 'upload.html', pois ele está na raiz de 'templates'
    return render(request, 'upload.html')
from django.urls import path


from .views import fetch_and_save_all_pdf

from . import views

urlpatterns = [
    path('fetch-pdf/', views.fetch_and_save_all_pdf, name='fetch_all_pdfs'),
]




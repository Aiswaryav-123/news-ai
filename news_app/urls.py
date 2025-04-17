from django.urls import path
from django.conf.urls.static import static
from news_project import settings
from django.conf import settings
from django.conf.urls.static import static

from django.urls import path
from . import views
#from .views import scrape_aicte_press_releases, scrape_education, scrape_kerala, scrape_dte_kerala,extract_and_translate_pdf,scrape_ugc
from .views import scrape_aicte_press_releases,scrape_ugc, extract_and_translate_pdf,scrape_education
urlpatterns = [
    path('extract_and_translate_pdf/', extract_and_translate_pdf, name='extract_and_translate_pdf'),
    path('scrape-aicte/', scrape_aicte_press_releases, name='scrape_aicte'),
    path('scrape-ugc/', scrape_ugc, name='scrape_ugc_pdfs'),
    path('scrape-education-gov-pdfs/', scrape_education, name='scrape_education_gov_pdfs'),
    #path('scrape-kerala-website/', scrape_kerala, name='scrape_kerala_website'),
    #path('scrape-dte-kerala-pdfs/', scrape_dte_kerala, name='scrape_dte_kerala'),
    
]

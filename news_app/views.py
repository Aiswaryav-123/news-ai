import requests
import os
from django.shortcuts import render
from django.conf import settings
from .models import NewsPDF
from bs4 import BeautifulSoup  # Make sure to install beautifulsoup4 if not installed

def fetch_and_save_all_pdf(request):
    # URL of the page to scrape (replace with AICTE or other site)
    url = "https://www.aicte-india.org"  # Replace with the AICTE page containing PDFs
    headers = {'User-Agent': 'Mozilla/5.0'}

    session = requests.Session()
    response = session.get(url, headers=headers)

    if response.status_code == 200:
        # Parse the page content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all <a> tags that link to PDFs
        pdf_links = soup.find_all('a', href=True)
        pdf_urls = [link['href'] for link in pdf_links if link['href'].endswith('.pdf')]

        if pdf_urls:
            pdf_titles = []  # For storing PDF titles (if needed)

            for pdf_url in pdf_urls:
                full_pdf_url = pdf_url if pdf_url.startswith('http') else f"{url}/{pdf_url}"  # Handle relative URLs

                # Fetch each PDF
                pdf_response = session.get(full_pdf_url, headers=headers, stream=True)

                if pdf_response.status_code == 200:
                    # Use the last part of the URL as the PDF name
                    pdf_name = full_pdf_url.split("/")[-1]
                    pdf_title = pdf_name.replace("_", " ").replace(".pdf", "")  # Simple title formatting

                    # Define the path to save the PDF
                    pdf_path = os.path.join(settings.MEDIA_ROOT, "news_pdfs", pdf_name)

                    # Create the directory if it doesn't exist
                    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

                    # Save the PDF
                    with open(pdf_path, "wb") as pdf_file:
                        for chunk in pdf_response.iter_content(chunk_size=8192):
                            pdf_file.write(chunk)

                    # Save the PDF entry in the database
                    news_pdf = NewsPDF.objects.create(title=pdf_title, pdf=f"news_pdfs/{pdf_name}")
                    pdf_titles.append(pdf_title)  # Add to the list of titles

            return render(request, 'success.html', {'pdf_titles': pdf_titles})
        else:
            error_message = "❌ No PDFs found on the page."
            return render(request, 'error.html', {'message': error_message})
    else:
        error_message = f"❌ Failed to fetch the page. Status: {response.status_code}"
        return render(request, 'error.html', {'message': error_message})

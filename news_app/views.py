import time
from urllib.parse import urljoin
from datetime import datetime

import os
import json  
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import google.generativeai as genai

genai.configure(api_key="AIzaSyCEffjByE6Y3N3iEzeslI_tLWZgw8q-LuA")

# def extract_and_translate_pdf(pdf_path):
#     try:
#         with open(pdf_path, "rb") as file:
#             pdf_bytes = file.read()

#         model = genai.GenerativeModel("gemini-2.0-flash")

#         extraction_prompt = "Extract all readable text from this PDF. Maintain structure. No summary."
#         extraction_response = model.generate_content([
#             {"inline_data": {"mime_type": "application/pdf", "data": pdf_bytes}},
#             {"text": extraction_prompt}
#         ])
#         extracted_text = extraction_response.text.strip() if extraction_response.text else ""

#         if not extracted_text:
#             return None, None, None  

#         category_prompt = f"""
#                 Analyze the following news content and classify it into one of the predefined categories:  
#                 - Education  
#                 - Policy Update  
#                 - Announcement  
#                 - Event  
#                 - Research  
#                 - Official News  
#                 - Notifications
#                 - Notices
#                 - General

#                 Choose the category that best describes the overall theme of the content.  
#                 Focus on identifying policy-related updates, official government statements, event announcements, or research findings.  

#                 Return only the category name, nothing else:

#             {extracted_text}
#             """


#         category_response = model.generate_content(category_prompt)
#         identified_category = category_response.text.strip() if category_response.text else "General"

#         date_prompt = (
#             "Extract the publication date from the following text, if available. "
#             "Return only the date in YYYY-MM-DD format. If no date is found, return 'Unknown'.\n\n"
#             + extracted_text
#         )
#         date_response = model.generate_content(date_prompt)
#         extracted_date = date_response.text.strip() if date_response.text else "Unknown"

#         translation_prompt = (
#             "Extract the key information from the provided text and present it as a "
#             "concise two-paragraph news article, similar to what is seen in a newspaper. "
#             "Ensure the article is well-structured, engaging, and maintains a professional tone:\n\n"
#             + extracted_text
#         )
#         translation_response = model.generate_content(translation_prompt)
#         translated_text = translation_response.text.strip() if translation_response.text else ""

#         return translated_text, identified_category, extracted_date  

#     except Exception as e:
#         print(f"Error extracting and translating PDF: {e}")
#         return None, None, None
    


from openai import OpenAI
import base64

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

def llama2_chat(prompt):
    response = client.chat.completions.create(
        model="llama2",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def extract_and_translate_pdf(pdf_path):
    try:
        with open(pdf_path, "rb") as file:
            pdf_bytes = file.read()

        # Convert PDF to text using PyMuPDF (fitz)
        import fitz
        doc = fitz.open(pdf_path)
        extracted_text = "\n".join([page.get_text() for page in doc])

        if not extracted_text.strip():
            return None, None, None

        # Category Extraction
        category_prompt = f"""
        Analyze the following news content and classify it into one of the predefined categories:
        - Education
        - Policy Update
        - Announcement
        - Event
        - Research
        - Official News
        - Notifications
        - Notices
        - General

        Return only the category name:

        {extracted_text}
        """
        identified_category = llama2_chat(category_prompt).strip()

        # Date Extraction
        date_prompt = (
            "Extract the publication date from the following text. "
            "Return only the date in YYYY-MM-DD format. If not found, return 'Unknown':\n\n"
            + extracted_text
        )
        extracted_date = llama2_chat(date_prompt).strip()

        # News Summarization
        summary_prompt = (
            "Summarize the following content into two professional newspaper-style paragraphs:\n\n"
            + extracted_text
        )
        translated_text = llama2_chat(summary_prompt).strip()

        return translated_text, identified_category, extracted_date

    except Exception as e:
        print(f"Error extracting and translating PDF: {e}")
        return None, None, None

###########
    
import os
import requests
from bs4 import BeautifulSoup
from django.http import JsonResponse
from datetime import date
from django.conf import settings
from .models import PDFDocument, Source, News, Category
from requests.auth import HTTPBasicAuth


WORDPRESS_URL = "http://127.0.0.1/wp-json/wp/v2/posts"
WORDPRESS_USER = "aiswarya_admin"
WORDPRESS_APP_PASSWORD = "vCaU Mgvl vpz4 w8Ig Zx3h YFTe"

def post_to_wordpress(title, content, category, extracted_date, pdf_url):
    """
    Post extracted and summarized news to WordPress.
    """
    formatted_date = datetime.strptime(extracted_date, "%Y-%m-%d").isoformat()
 
    print("Category : ",category)
    category_mapping = {
        "Announcement": 5,
        "Education": 3,
        "Event": 6,
        "Official News": 8,
        "Policy Update": 4,
        "Research": 7,
        "General": 11,
        "Notices":10,
        "Notifications":9,

    }
    wordpress_category_id = category_mapping.get(category, 1)
    search_response = requests.get(
        f"{WORDPRESS_URL}?search={title}",
        auth=HTTPBasicAuth(WORDPRESS_USER, WORDPRESS_APP_PASSWORD),
    )
    if search_response.status_code == 200:
        posts = search_response.json()
        for post in posts:
            if post["title"]["rendered"] == title:
                print(f"⚠️ Post already exists: {title}. Skipping...")
                return None
    post_data = {
        "title": title,
        "content": content,
        "status": "publish",  
        "categories": [wordpress_category_id],
        "date": formatted_date,
        "meta": {
            "original_pdf_url": pdf_url
        }
    }
    

    response = requests.post(
        WORDPRESS_URL,
        json=post_data,
        auth=HTTPBasicAuth(WORDPRESS_USER, WORDPRESS_APP_PASSWORD),
    )

    if response.status_code == 201:
        print(f"✅ Successfully posted: {title}")
        return response.json()
    else:
        print(f"❌ Failed to post: {title}. Response: {response.text}")
        return None

def scrape_aicte_press_releases(request=None):
    base_url = 'https://www.aicte-india.org'
    press_release_url = f"{base_url}/press-releases"

    response = requests.get(press_release_url)
    if response.status_code != 200:
        return JsonResponse({'error': f"Failed to retrieve {press_release_url}, status code: {response.status_code}"})

    soup = BeautifulSoup(response.text, 'html.parser')
    pdf_links = [link for link in soup.find_all('a', href=True) if link['href'].endswith('.pdf')]

    if not pdf_links:
        return JsonResponse({'error': 'No PDF links found on the page.'})

    source, _ = Source.objects.get_or_create(
        s_name="AICTE",
        s_url=press_release_url,
        defaults={"s_status": True}
    )

    aicte_folder = os.path.join(settings.MEDIA_ROOT, 'pdfs/aicte/')
    os.makedirs(aicte_folder, exist_ok=True)

    for link in pdf_links:
        pdf_url = link['href']
        if not pdf_url.startswith('http'):
            pdf_url = base_url + pdf_url

        title = link.text.strip() or "Untitled PDF"

        if News.objects.filter(title=title).exists():
            print(f"Skipping download: News entry with title '{title}' already exists.")
            continue

        pdf_response = requests.get(pdf_url)

        if pdf_response.status_code != 200:
            print(f"Failed to download PDF from {pdf_url}")
            continue

        pdf_filename = pdf_url.split('/')[-1]
        pdf_path = os.path.join(aicte_folder, pdf_filename)

        with open(pdf_path, 'wb') as pdf_file:
            pdf_file.write(pdf_response.content)

        extracted_text, detected_category, extracted_date = extract_and_translate_pdf(pdf_path)

        if extracted_text is None:
            print(f"Skipping news entry for '{title}' due to extraction failure.")
            continue
        
        category, _ = Category.objects.get_or_create(
            c_name=detected_category,
            defaults={"c_status": True}
        )

        news_title = f"AICTE - {pdf_filename}"

        if News.objects.filter(title=news_title).exists():
            print(f"⚠️ Skipping: News '{news_title}' already exists in Django.")
            continue 
        else:
            news = News.objects.create(
                title=news_title,
                news_content=extracted_text,  
                c_id=category,
                image_url="",
                published_date=extracted_date if extracted_date != "Unknown" else date.today(),
                moderation_status="Pending",
                s_id=source,
            )

            PDFDocument.objects.create(
                news=news,
                pdf_file=f'pdfs/aicte/{pdf_filename}',
            )

            # Create the actual URL served by Django (e.g., through nginx or Django server)
            pdf_url = f"http://127.0.0.1:8000/media/pdfs/aicte/{pdf_filename}"



            print(f"Downloaded, processed, and saved PDF: {title}")
            

            wordpress_response = post_to_wordpress(news_title, extracted_text, category.c_name,extracted_date,pdf_url_served)
            if wordpress_response:
                print(f"✅ Posted to WordPress: {news_title}")

    return JsonResponse({'status': 'Scraping, processing, and WordPress posting from AICTE completed successfully!'}) 

def scrape_ugc(request=None):
    base_url = "https://www.ugc.gov.in"
    notices_url = f"{base_url}/Notices"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service("/home/aiswarya/Documents/project_10_copy/news_project/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(notices_url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        table_body = soup.find("tbody", {"id": "tbodyNotices"})

        if not table_body:
            return JsonResponse({"error": "Could not find the notices table."})

        pdf_links = []
        for row in table_body.find_all("tr"):
            pdf_cell = row.find_all("td")
            if len(pdf_cell) < 2:
                continue

            link_tag = pdf_cell[1].find("a", href=True)
            if link_tag and link_tag["href"].endswith(".pdf"):
                pdf_url = urljoin(base_url, link_tag["href"].replace("../", ""))
                pdf_title = link_tag.text.strip()
                pdf_links.append((pdf_url, pdf_title))

        driver.quit()

        if not pdf_links:
            return JsonResponse({"error": "No PDF links found in the notices table."})

        source, _ = Source.objects.get_or_create(
            s_name="UGC",
            s_url=notices_url,
            defaults={"s_status": True}
        )
        ugc_pdf_folder = os.path.join(settings.MEDIA_ROOT, 'pdfs/ugc/')
        os.makedirs(ugc_pdf_folder, exist_ok=True)

        for pdf_url, pdf_title in pdf_links:
            pdf_filename = pdf_url.split('/')[-1]  
            news_title = f"UGC - {pdf_filename}"  

            if News.objects.filter(title=news_title).exists():
                print(f"Skipping: '{news_title}' already exists.")
                continue

            pdf_response = requests.get(pdf_url, verify=False)
            if pdf_response.status_code != 200:
                print(f"Failed to download PDF from {pdf_url}")
                continue

            pdf_path = os.path.join(ugc_pdf_folder, pdf_filename)
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(pdf_response.content)

            extracted_text, detected_category, extracted_date = extract_and_translate_pdf(pdf_path)
            if not extracted_text:
                print(f"Skipping '{pdf_filename}': No extracted text.")
                continue

            category, _ = Category.objects.get_or_create(
                c_name=detected_category,
                defaults={"c_status": True}
            )

            news = News.objects.create(
                title=news_title,
                news_content=extracted_text,
                c_id=category,
                image_url="",
                published_date=extracted_date if extracted_date != "Unknown" else date.today(),
                moderation_status="Pending",
                s_id=source,
            )

            PDFDocument.objects.create(
                news=news,
                pdf_file=f'pdfs/ugc/{pdf_filename}',
            )

            print(f"Downloaded, processed, and saved PDF: {pdf_filename} as '{news_title}' in News table.")
            
            wordpress_response = post_to_wordpress(news_title, extracted_text, category.c_name, extracted_date)
            if wordpress_response:
                print(f"✅ Posted to WordPress: {news_title}")

        return JsonResponse({'status': 'Scraping, downloading, and WordPress posting from UGC completed successfully!'})

    except Exception as e:
        return JsonResponse({"error": str(e)})

    finally:
        driver.quit()


def scrape_education(request=None):
    base_url = 'https://www.education.gov.in'
    target_url = base_url

    response = requests.get(target_url)
    if response.status_code != 200:
        return JsonResponse({'error': f"Failed to retrieve {target_url}, status code: {response.status_code}"})

    soup = BeautifulSoup(response.text, 'html.parser')
    pdf_links = [link for link in soup.find_all('a', href=True) if link['href'].endswith('.pdf')]

    if not pdf_links:
        return JsonResponse({'error': 'No PDF links found on the page.'})

    source, _ = Source.objects.get_or_create(
        s_name="EducationGov",
        s_url=target_url,
        defaults={"s_status": True}
    )

    education_gov_folder = os.path.join(settings.MEDIA_ROOT, 'pdfs/education.gov/')
    os.makedirs(education_gov_folder, exist_ok=True)

    for link in pdf_links:
        pdf_url = link['href']
        if not pdf_url.startswith('http'):
            pdf_url = base_url + pdf_url

        title = link.text.strip() or "Untitled PDF"
    
        if News.objects.filter(title=title).exists():
            print(f"Skipping download: News entry with title '{title}' already exists.")
            continue

        pdf_response = requests.get(pdf_url)

        if pdf_response.status_code != 200:
            print(f"Failed to download PDF from {pdf_url}")
            continue

        pdf_filename = pdf_url.split('/')[-1]
        pdf_path = os.path.join(education_gov_folder, pdf_filename)

        with open(pdf_path, 'wb') as pdf_file:
            pdf_file.write(pdf_response.content)

        extracted_text, detected_category, extracted_date = extract_and_translate_pdf(pdf_path)

        if extracted_text is None:
            print(f"Skipping news entry for '{title}' due to extraction failure.")
            continue
        
        category, _ = Category.objects.get_or_create(
            c_name=detected_category,
            defaults={"c_status": True}
        )

        news_title = f"EducationGov - {pdf_filename}"

        if News.objects.filter(title=news_title).exists():
            print(f"⚠️ Skipping: News '{news_title}' already exists in Django.")
            continue 
        else:
            news = News.objects.create(
                title=news_title,
                news_content=extracted_text,  
                c_id=category,
                image_url="",
                published_date=extracted_date if extracted_date != "Unknown" else date.today(),
                moderation_status="Pending",
                s_id=source,
            )

            PDFDocument.objects.create(
                news=news,
                pdf_file=f'pdfs/education_gov_folder/{pdf_filename}',
            )

            print(f"Downloaded, processed, and saved PDF: {title}")
            
            def fix_invalid_date(date_str):
                if not date_str or date_str.lower() == "unknown":
                    return datetime.now().strftime("%Y-%m-%d")  # Use current date if unknown

                parts = date_str.strip().split("-")

                if len(parts) == 3:
                    year, month, day = parts

                    # Ensure valid numerical values
                    try:
                        year = int(year)
                        month = int(month)
                        day = int(day)
                    except ValueError:
                        return datetime.now().strftime("%Y-%m-%d")  # Fallback if conversion fails

                    # Correct zero day or month
                    if month == 0 or month > 12:
                        month = 1  # Default to January if invalid
                    if day == 0 or day > 31:
                        day = 1  # Default to first day of the month if invalid

                    corrected_date = f"{year:04d}-{month:02d}-{day:02d}"

                    # Validate final date
                    try:
                        datetime.strptime(corrected_date, "%Y-%m-%d")
                        return corrected_date
                    except ValueError:
                        return datetime.now().strftime("%Y-%m-%d")  # Fallback to current date if still invalid

                return datetime.now().strftime("%Y-%m-%d")  # Fallback if format is incorrect

            # Ensure extracted_date is valid
            extracted_date = fix_invalid_date(extracted_date)

            wordpress_response = post_to_wordpress(news_title, extracted_text, category.c_name, extracted_date)

            if wordpress_response:
                print(f"✅ Successfully posted to WordPress: {news_title}")
            else:
                print(f"⚠️ Failed to post: {news_title}")


    return JsonResponse({'status': 'Scraping, processing, and WordPress posting from EducationGov completed successfully!'}) 

# ###### 3. Education Government ######
        
# def scrape_education(request=None):
#     base_url = 'https://www.education.gov.in'
#     target_url = base_url

#     response = requests.get(target_url)
#     if response.status_code != 200:
#         return JsonResponse({'error': f"Failed to retrieve {target_url}, status code: {response.status_code}"})

#     html_content = response.text
#     soup = BeautifulSoup(html_content, 'html.parser')

#     pdf_containers = soup.find_all('li', class_='views-row')
#     if not pdf_containers:
#         return JsonResponse({'error': 'No PDF links found on the page.'})

#     source, created = Source.objects.get_or_create(
#         s_name="EducationGov",
#         s_url=target_url,
#         defaults={"s_status": True}
#     )

#     education_gov_folder = os.path.join('media/pdfs/education.gov/')
#     os.makedirs(education_gov_folder, exist_ok=True) 

#     for container in pdf_containers:
#         link_tag = container.find('a', href=True)
#         if not link_tag or not link_tag['href'].endswith('.pdf'):
#             continue

#         pdf_url = link_tag['href']
#         if not pdf_url.startswith('http'):
#             pdf_url = base_url + pdf_url

#         title = link_tag.get_text(strip=True) or "Untitled PDF"

#         if News.objects.filter(title=title).exists():
#             print(f"Skipping: News entry with title '{title}' already exists.")
#             continue

#         pdf_response = requests.get(pdf_url)
#         if pdf_response.status_code != 200:
#             print(f"Failed to download PDF from {pdf_url}")
#             continue

#         pdf_filename = pdf_url.split('/')[-1]  
#         pdf_path = os.path.join(education_gov_folder, pdf_filename)

#         with open(pdf_path, 'wb') as pdf_file:
#             pdf_file.write(pdf_response.content)

#         extracted_text, detected_category, extracted_date = extract_and_translate_pdf(pdf_path)

#         if extracted_text is None:
#             print(f"Skipping news entry for '{title}' due to extraction failure.")
#             continue

#         category, _ = Category.objects.get_or_create(
#             c_name=detected_category,
#             defaults={"c_status": True}
#         )
#         news_title = f"Education_Gov - {pdf_filename}"
#         news = News.objects.create(
#             title=news_title,
#             news_content=extracted_text,  
#             c_id=category,
#             image_url="",
#             published_date=extracted_date if extracted_date != "Unknown" else date.today(),
#             moderation_status="Pending",
#             s_id=source,
#         )

#         PDFDocument.objects.create(
#             news=news,
#             pdf_file=f'pdfs/education.gov/{pdf_filename}',  
#         )
#         print(f"Downloaded, processed, and saved PDF: {title}")

#     return JsonResponse({'status': 'Scraping, downloading, and AI processing from Education Gov completed successfully!'})

# ##### 4. Kerala Website #####

# def scrape_kerala(request=None):
#     base_url = 'https://collegiateedu.kerala.gov.in'
#     news_url = base_url  

#     response = requests.get(news_url)
#     if response.status_code != 200:
#         return JsonResponse({'error': f"Failed to retrieve {news_url}, status code: {response.status_code}"})

#     html_content = response.text
#     soup = BeautifulSoup(html_content, 'html.parser')

#     news_areas = soup.find_all('div')
#     pdf_links = []

#     for news_area in news_areas:
#         link_tags = news_area.find_all('a', href=True)
#         for link_tag in link_tags:
#             href = link_tag['href']
#             if href.endswith('.pdf'):
#                 pdf_links.append((link_tag.text.strip(), href))

#     if not pdf_links:
#         return JsonResponse({'error': 'No PDF links found on the page.'})

#     source, _ = Source.objects.get_or_create(
#         s_name="Kerala Collegiate Education",
#         s_url=news_url,
#         defaults={"s_status": True}
#     )
    
#     collegiateedu_folder = os.path.join(settings.MEDIA_ROOT, 'pdfs/collegiateedu/')
#     os.makedirs(collegiateedu_folder, exist_ok=True)

#     for title, pdf_url in pdf_links:
#         if not pdf_url.startswith('http'):
#             pdf_url = base_url + pdf_url

#         if News.objects.filter(title=title).exists():
#             print(f"Skipping: News entry '{title}' already exists.")
#             continue

#         pdf_response = requests.get(pdf_url)
#         if pdf_response.status_code != 200:
#             print(f"Failed to download PDF from {pdf_url}")
#             continue

#         pdf_filename = pdf_url.split('/')[-1]
#         pdf_path = os.path.join(collegiateedu_folder, pdf_filename)
#         news_title = f"Collegiate - {pdf_filename}"
#         with open(pdf_path, 'wb') as pdf_file:
#             pdf_file.write(pdf_response.content)

#         extracted_text, detected_category, extracted_date = extract_and_translate_pdf(pdf_path) 

#         if not extracted_text:
#             print(f"Skipping '{title}': No extracted text.")
#             continue

#         category, _ = Category.objects.get_or_create(
#             c_name=detected_category,
#             defaults={"c_status": True}
#         )
#         news_title = f"Collegiate - {pdf_filename}" 

#         news = News.objects.create(
#             title=news_title,
#             news_content=extracted_text,
#             c_id=category,
#             image_url="",
#             published_date=extracted_date if extracted_date != "Unknown" else date.today(),
#             moderation_status="Pending",
#             s_id=source,
#         )

#         PDFDocument.objects.create(
#             news=news,
#             pdf_file=f'pdfs/collegiateedu/{pdf_filename}',
#         )
#         print(f"Downloaded, extracted, and saved PDF: {title}")

#     return JsonResponse({'status': 'Scraping, downloading, and AI processing from Kerala Collegiate completed successfully!'})

# ##### 5. DTE Kerala #####

# def scrape_dte_kerala(request=None):
#     base_url = 'https://www.dtekerala.gov.in'
#     news_page_url = f"{base_url}/viewnewsall/?page=1"

#     response = requests.get(news_page_url)
#     if response.status_code != 200:
#         return JsonResponse({'error': f"Failed to retrieve {news_page_url}, status code: {response.status_code}"})

#     soup = BeautifulSoup(response.text, 'html.parser')
#     pdf_sections = soup.find_all('div', class_='list-group-item list-group-item-action')

#     if not pdf_sections:
#         return JsonResponse({'error': 'No PDFs found on the page.'})

#     source, _ = Source.objects.get_or_create(
#         s_name="DTE Kerala",
#         s_url=news_page_url,
#         defaults={"s_status": True}
#     )

#     category, _ = Category.objects.get_or_create(
#         c_name="Notifications",
#         defaults={"c_status": True}
#     )

#     dte_folder = os.path.join(settings.MEDIA_ROOT, 'pdfs/dte/')
#     os.makedirs(dte_folder, exist_ok=True)

#     processed_pdfs = []  

#     for section in pdf_sections:
#         title_tag = section.find('p', class_='mb-1 red-hat-text')
#         original_title = title_tag.text.strip() if title_tag else "Untitled PDF"

#         pdf_links = [a['href'] for a in section.find_all('a', href=True) if a['href'].endswith('.pdf')]

#         for pdf_url in pdf_links:
#             if not pdf_url.startswith('http'):
#                 pdf_url = base_url + pdf_url

#             pdf_filename = pdf_url.split('/')[-1]  
#             pdf_path = os.path.join(dte_folder, pdf_filename)
            
#             if News.objects.filter(title=f"DTE - {pdf_filename}").exists():
#                 print(f"Skipping: 'DTE - {pdf_filename}' already exists in News table.")
#                 continue

#             pdf_response = requests.get(pdf_url)
#             if pdf_response.status_code != 200:
#                 print(f"Failed to download {pdf_url}")
#                 continue

#             with open(pdf_path, 'wb') as file:
#                 file.write(pdf_response.content)

#             extraction_response = extract_and_translate_pdf(pdf_path)  

#             if isinstance(extraction_response, JsonResponse):
#                 response_data = json.loads(extraction_response.content.decode("utf-8"))
#             else:
#                 print(f"Skipping '{pdf_filename}': Unexpected extraction response format.")
#                 continue

#             if response_data.get("status") != "success":
#                 print(f"Skipping '{pdf_filename}' due to extraction failure: {response_data.get('message')}")
#                 continue

#             extracted_text = response_data.get("extracted_text", "").strip()

#             if not extracted_text:
#                 print(f"Skipping '{pdf_filename}': No extracted text.")
#                 continue

            
#             news_title = f"DTE - {pdf_filename}"  

#             news = News.objects.create(
#                 title=news_title,
#                 news_content=extracted_text, 
#                 c_id=category,
#                 image_url="",
#                 published_date=date.today(),
#                 moderation_status="Pending",
#                 s_id=source,
#             )

            
#             PDFDocument.objects.create(
#                 news=news,
#                 pdf_file=f'pdfs/dte/{pdf_filename}',
#             )

#             print(f"Downloaded, processed, and saved PDF: {pdf_filename} as 'DTE - {pdf_filename}' in News table.")
            

#     return JsonResponse({'status': 'Scraping, downloading, and AI processing from DTE completed successfully!'})

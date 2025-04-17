from django.db import models
from django.contrib.auth.models import User

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost
from django.db import models

from django.db import models

class UserTab(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[
        ('reader', 'Reader'),
        ('admin', 'Admin'),
    ])
    phn_no = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    u_status = models.CharField(max_length=255, default="active")

    def str(self):
        return f"{self.user.username} - {self.role}"
    
    
class Category(models.Model):
    c_id = models.BigAutoField(primary_key=True)
    c_name = models.CharField(max_length=25)
    c_status = models.BooleanField()  

    def str(self):
        return self.c_name

class Source(models.Model):
    s_id = models.BigAutoField(primary_key=True)
    s_name = models.CharField(max_length=40)
    s_url = models.CharField(max_length=100)
    s_status = models.BooleanField()

    def str(self):
        return self.s_name

class News(models.Model):
    news_id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=300)
    news_content = models.TextField()
    c_id = models.ForeignKey(Category, on_delete=models.CASCADE)
    image_url = models.CharField(max_length=500)
    published_date = models.DateField()
    moderation_status = models.CharField(max_length=10)
    s_id = models.ForeignKey(Source, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
    
    
class PDFDocument(models.Model):
    pdf_id = models.BigAutoField(primary_key=True)
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='pdf_documents')
    pdf_file = models.FileField(upload_to='pdfs/')  # Uploaded PDFs will be saved in the 'media/pdfs/' directory
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"PDF for {self.news.title}"
    
class Comment(models.Model):
    comnt_id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    news_id = models.ForeignKey(News, on_delete=models.CASCADE)
    comnt_status = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when the comment is created

    def _str_(self):
        return f"Comment by {self.user_id.username} on {self.news_id.title}"


class Analytics(models.Model):
    a_id = models.BigAutoField(primary_key=True)
    news_id = models.ForeignKey(News, on_delete=models.CASCADE)
    views = models.BigIntegerField()
    likes = models.BigIntegerField()
    shares = models.BigIntegerField()

    def str(self):
        return f"Analytics for {self.news_id.title}"

class UserPreference(models.Model):
    preference_id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    c_id = models.ForeignKey(Category, on_delete=models.CASCADE)

    def str(self):
        return f"Preference for {self.user_id.username} in category {self.c_id.c_name}"


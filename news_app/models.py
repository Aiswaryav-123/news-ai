from django.db import models



class NewsPDF(models.Model):
    title = models.CharField(max_length=255)
    pdf = models.FileField(upload_to='news_pdfs/')

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

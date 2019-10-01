from django.db import models

# Create your models here.
class ImportLog(models.Model):
  item=models.CharField(max_length=30)
  contents=models.TextField()
  op=models.CharField(max_length=30)
  timestamp=models.DateTimeField(auto_now=True)
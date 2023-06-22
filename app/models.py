from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    pass

class User(models.Model):
    fullname=models.CharField(max_length=20)
    username=models.CharField(max_length=15)
    email=models.EmailField()
    password=models.CharField(max_length=10)
    confrim_password=models.CharField(max_length=10)
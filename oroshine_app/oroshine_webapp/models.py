from django.db import models

# Create your models here.
class Contact(models.Model):
    name = models.CharField(max_length=250)
    email = models.EmailField()
    subject = models.CharField(max_length=250)
    message = models.TextField(max_length=3000)

    def __str__(self):
        return self.email

class Appointment(models.Model):
    service = models.CharField(max_length=100)
    doctor_email = models.EmailField()
    name = models.CharField(max_length=100)
    email = models.EmailField()
    date = models.DateField()
    time = models.TimeField()
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.service} ({self.date} {self.time})"

    class Meta:
        ordering = ['-created_at']
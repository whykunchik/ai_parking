from django.db import models
from django.urls import reverse

class Car(models.Model):

    car_numbers = models.CharField(max_length=20)

    def __str__(self):
        return self.car_numbers
    
class Time(models.Model):

    detection_time = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.detection_time
    
    departure_time = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.departure_times
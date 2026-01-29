from django.contrib import admin
from .models import Car, Time

# admin.site.register(Car)
# admin.site.register(Time)

# Define the admin class
class CarAdmin(admin.ModelAdmin):
    pass

# Register the admin class with the associated model
admin.site.register(Car, CarAdmin)


@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    pass

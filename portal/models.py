from django.db import models


class StaffMember(models.Model):
    ROLES = [
        ("technician", "Technician"),
        ("supervisor", "Supervisor"),
        ("manager", "Manager"),
    ]
    full_name = models.CharField(max_length=80)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLES, default="technician")
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name", "id"]

    def __str__(self):
        return self.full_name

    @property
    def initial(self):
        return (self.full_name[:1] or "S").upper()

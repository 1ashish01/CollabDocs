import email
from platform import python_revision
import uuid
from django.db import models

# Create your models here.

#  a Document has a point a user and a workspace.
#  And the stats & Tags endpoints needs comments, tag & and audit log.


# These models are included here so your part can run.

# Workspace Member -> not included.

# There is no login

#  The acting user is an ID in the request body.

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name
    last_name
    email
    phone
    created_at

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class Workspace(models.Model):
    id=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name=models.CharField(max_length=255)
    owner=models.ForeignKey(User,on_delete=models.CASCADE, related_name='owner_workspce')
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeFields(auto_new_add=True)

    def __str__(self):
        return self.name

class Document(models.Model):
    class Status(models.TextChoices):
        DRAFT='draft','Draft'
        PUBLISHED='published','Published'
        ARCHIVED='archived','Archived'

    id 
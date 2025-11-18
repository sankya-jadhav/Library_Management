from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Book(models.Model):
    """
    Model to store book details.
    """
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=500, null=True, blank=True)
    isbn = models.CharField(max_length=20, unique=True, null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    # This is the key field for availability logic
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Borrowing(models.Model):
    """
    Model to track book borrowing requests and approvals.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('RETURNED', 'Returned'), # For future use
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrowings")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Dates to be set by the admin
    approved_date = models.DateTimeField(null=True, blank=True)
    return_date = models.DateTimeField(null=True, blank=True) # Date book is due or returned

    class Meta:
        # A student can only have one active (pending/approved) request per book
        unique_together = [['student', 'book', 'status']]
        ordering = ['-request_date']

    def __str__(self):
        return f"{self.student.username} - {self.book.title} ({self.status})"
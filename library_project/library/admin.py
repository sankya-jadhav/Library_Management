from django.contrib import admin
from django.utils import timezone
from .models import Book, Borrowing

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'category', 'is_available')
    search_fields = ('title', 'author', 'isbn')
    list_filter = ('is_available', 'category')
    
    # The admin can add/edit books here as requested
    
@admin.register(Borrowing)
class BorrowingAdmin(admin.ModelAdmin):
    list_display = ('student', 'book', 'status', 'request_date', 'approved_date')
    list_filter = ('status',)
    search_fields = ('student__username', 'book__title')
    
    # Add custom actions for the admin to approve/reject requests
    actions = ['approve_requests', 'reject_requests']

    def approve_requests(self, request, queryset):
        """
        Action to approve selected borrowing requests.
        """
        for borrowing in queryset.filter(status='PENDING'):
            # Set status to Approved
            borrowing.status = 'APPROVED'
            borrowing.approved_date = timezone.now()
            borrowing.save()
            
            # Set the book to unavailable
            borrowing.book.is_available = False
            borrowing.book.save()
            
            # Reject other pending requests for this same book
            Borrowing.objects.filter(
                book=borrowing.book, 
                status='PENDING'
            ).update(status='REJECTED')

        self.message_user(request, "Selected requests have been approved.")
    approve_requests.short_description = "Approve selected requests"

    def reject_requests(self, request, queryset):
        """
        Action to reject selected borrowing requests.
        """
        # We only reject pending requests
        queryset.filter(status='PENDING').update(status='REJECTED')
        
        # Note: We don't make the book available here, 
        # because an approval might be what made it unavailable.
        # Availability is handled by approval and (later) returns.

        self.message_user(request, "Selected requests have been rejected.")
    reject_requests.short_description = "Reject selected requests"
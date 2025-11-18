from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Q
from .models import Book, Borrowing
from django.utils import timezone

# Registration and admin helpers
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST

@login_required
def book_list(request):
    """
    Display a list of all books, showing their availability.
    """
    # Filtering/searching/sorting support
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    author = request.GET.get('author', '')
    available = request.GET.get('available', '')  # '1' for only available

    # Sorting support via ?sort=title|author|year|available
    sort = request.GET.get('sort', 'title')
    sort_map = {
        'title': 'title',
        'author': 'author',
        'year': 'publication_year',
        'available': '-is_available',  # show available first
        '-title': '-title',
        '-author': '-author',
        '-year': '-publication_year',
        '-available': 'is_available',
    }

    order_field = sort_map.get(sort, 'title')

    books_qs = Book.objects.all()

    if q:
        books_qs = books_qs.filter(
            Q(title__icontains=q) |
            Q(author__icontains=q) |
            Q(description__icontains=q) |
            Q(isbn__icontains=q)
        )

    if category:
        books_qs = books_qs.filter(category=category)

    if author:
        books_qs = books_qs.filter(author=author)

    if available == '1':
        books_qs = books_qs.filter(is_available=True)

    books = books_qs.order_by(order_field)

    # Get distinct categories and authors for filter dropdowns
    categories = Book.objects.exclude(category__isnull=True).exclude(category__exact='').order_by('category').values_list('category', flat=True).distinct()
    authors = Book.objects.exclude(author__isnull=True).exclude(author__exact='').order_by('author').values_list('author', flat=True).distinct()

    return render(request, 'library/book_list.html', {
        'books': books,
        'current_sort': sort,
        'q': q,
        'selected_category': category,
        'selected_author': author,
        'selected_available': available,
        'categories': categories,
        'authors': authors,
    })

@login_required
def book_detail(request, pk):
    """
    Show details for a single book and allow requesting it.
    """
    book = get_object_or_404(Book, pk=pk)
    
    # Check if the user has an active (pending or approved) request
    existing_request = Borrowing.objects.filter(
        student=request.user,
        book=book,
        status__in=['PENDING', 'APPROVED']
    ).first()
    
    return render(request, 'library/book_detail.html', {
        'book': book,
        'existing_request': existing_request
    })

@login_required
def request_book(request, pk):
    """
    Handle the POST request to borrow a book.
    """
    if request.method != 'POST':
        return redirect('book_detail', pk=pk)

    book = get_object_or_404(Book, pk=pk)

    # Check if book is available
    if not book.is_available:
        messages.error(request, "This book is currently unavailable.")
        return redirect('book_detail', pk=pk)

    # Check if user already has an active request
    has_active_request = Borrowing.objects.filter(
        student=request.user,
        book=book,
        status__in=['PENDING', 'APPROVED']
    ).exists()

    if has_active_request:
        messages.warning(request, "You already have an active request for this book.")
        return redirect('book_detail', pk=pk)
        
    # Create the pending request
    try:
        Borrowing.objects.create(student=request.user, book=book, status='PENDING')
        messages.success(request, "Your request to borrow this book has been submitted.")
    except IntegrityError:
         messages.error(request, "An error occurred. You may have already requested this book.")

    return redirect('book_list')

@login_required
def student_profile(request):
    """
    Show the logged-in student's profile with their borrowing history.
    """
    borrowings = Borrowing.objects.filter(student=request.user).order_by('-request_date')
    return render(request, 'library/student_profile.html', {'borrowings': borrowings})


def register(request):
    """Allow students to create an account using Django's UserCreationForm."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately
            auth_login(request, user)
            messages.success(request, 'Registration successful. You are now logged in.')
            return redirect('book_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()

    # Improve form widgets styling for consistency with Tailwind used in templates
    try:
        form.fields['username'].widget.attrs.update({
            'class': 'appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Username'
        })
        form.fields['password1'].widget.attrs.update({
            'class': 'appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Password'
        })
        form.fields['password2'].widget.attrs.update({
            'class': 'appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Confirm password'
        })
    except Exception:
        # If fields are not present for some reason, ignore styling updates
        pass

    return render(request, 'library/register.html', {'form': form})


@staff_member_required
def admin_dashboard(request):
    """Simple admin dashboard showing counts and quick links."""
    total_books = Book.objects.count()
    available = Book.objects.filter(is_available=True).count()
    pending_requests = Borrowing.objects.filter(status='PENDING').count()
    return render(request, 'library/admin_dashboard.html', {
        'total_books': total_books,
        'available': available,
        'pending_requests': pending_requests,
    })


@staff_member_required
def pending_requests(request):
    """Show pending borrowing requests for admin to act on."""
    requests_qs = Borrowing.objects.filter(status='PENDING').order_by('request_date')
    return render(request, 'library/admin_pending_requests.html', {'requests': requests_qs})


@staff_member_required
@require_POST
def approve_request(request, pk):
    borrowing = get_object_or_404(Borrowing, pk=pk)
    if borrowing.status != 'PENDING':
        messages.warning(request, 'This request is no longer pending.')
        return redirect('admin_pending_requests')

    borrowing.status = 'APPROVED'
    borrowing.approved_date = timezone.now()
    borrowing.save()

    borrowing.book.is_available = False
    borrowing.book.save()

    # Reject other pending requests for this book
    Borrowing.objects.filter(book=borrowing.book, status='PENDING').exclude(pk=borrowing.pk).update(status='REJECTED')

    messages.success(request, f'Request for "{borrowing.book.title}" by {borrowing.student.username} approved.')
    return redirect('admin_pending_requests')


@staff_member_required
@require_POST
def reject_request(request, pk):
    borrowing = get_object_or_404(Borrowing, pk=pk)
    if borrowing.status != 'PENDING':
        messages.warning(request, 'This request is no longer pending.')
        return redirect('admin_pending_requests')

    borrowing.status = 'REJECTED'
    borrowing.save()

    messages.success(request, f'Request for "{borrowing.book.title}" by {borrowing.student.username} rejected.')
    return redirect('admin_pending_requests')


def admin_login(request):
    """Admin-specific login page."""
    if request.method == 'POST':
        from django.contrib.auth import authenticate, login
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')
    
    return render(request, 'library/admin_login.html')


def admin_register(request):
    """Admin-specific registration page (staff signup)."""
    if request.method == 'POST':
        from django.contrib.auth.models import User
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'library/admin_register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'library/admin_register.html')
        
        user = User.objects.create_user(username=username, password=password1)
        user.is_staff = True
        user.save()
        messages.success(request, 'Admin account created successfully. Please log in.')
        return redirect('admin_login')
    
    return render(request, 'library/admin_register.html')
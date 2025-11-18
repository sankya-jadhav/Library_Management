import csv
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from library.models import Book

class Command(BaseCommand):
    help = 'Imports books from a specified CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The path to the CSV file to import.')

    def handle(self, *args, **options):
        file_path = options['csv_file_path']
        self.stdout.write(self.style.NOTICE(f'Starting import from {file_path}...'))
        
        imported_count = 0
        skipped_count = 0

        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                
                # Skip header row
                try:
                    header = next(reader)
                except StopIteration:
                    self.stdout.write(self.style.ERROR('CSV file is empty.'))
                    return

                for row in reader:
                    try:
                        # Map CSV columns to model fields
                        # 0: SNo, 1: Category, 2: ISBN, 3: Title Name, 4: Author/Writer,
                        # 7: Publication Year, 11: About the Book
                        
                        title = row[3]
                        author = row[4] if row[4] else None
                        isbn = row[2] if row[2] else None
                        
                        # Skip if essential data is missing
                        if not title:
                            self.stdout.write(self.style.WARNING(f'Skipping row {reader.line_num}: Missing title'))
                            skipped_count += 1
                            continue
                            
                        # Handle publication year
                        pub_year = None
                        if row[7] and row[7].isdigit():
                            pub_year = int(row[7])

                        # Use get_or_create to avoid duplicates based on title and author
                        # Using ISBN is better if it's guaranteed unique, but title/author is safer
                        book, created = Book.objects.get_or_create(
                            title=title,
                            author=author,
                            defaults={
                                'isbn': isbn,
                                'category': row[1] if row[1] else None,
                                'publication_year': pub_year,
                                'description': row[11] if row[11] else None,
                                'is_available': True
                            }
                        )
                        
                        if created:
                            imported_count += 1
                        else:
                            self.stdout.write(self.style.WARNING(f'Skipping duplicate: {title}'))
                            skipped_count += 1
                            
                    except (IndexError, ValidationError) as e:
                        self.stdout.write(self.style.ERROR(f'Error on line {reader.line_num}: {e}'))
                        skipped_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Unexpected error on line {reader.line_num}: {e}'))
                        skipped_count += 1

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found at {file_path}'))
            return

        self.stdout.write(self.style.SUCCESS(
            f'Import complete: {imported_count} books created, {skipped_count} rows skipped.'
        ))
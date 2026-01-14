from django.core.management.base import BaseCommand
from django.core.cache import cache
from bookings.models import Booking, Transaction
from movies.models import Movie, Genre, Language
from movies.theater_models import City, Theater, Screen, Showtime
# FEATURE DISABLED: from movies.reviews_models import Review, ReviewLike, Wishlist, Interest
from django.db import connection

class Command(BaseCommand):
    help = 'Clear all data: bookings, movies, shows, theaters, and seat reservations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )
        parser.add_argument(
            '--bookings-only',
            action='store_true',
            help='Only clear bookings and transactions, keep movies/theaters',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        bookings_only = options.get('bookings_only', False)

        if not force:
            if bookings_only:
                msg = '⚠️  This will DELETE ALL bookings and transactions!\n'
            else:
                msg = '⚠️  This will DELETE EVERYTHING: bookings, movies, shows, theaters!\n'
            
            confirm = input(msg + 'Are you sure? Type "yes" to confirm: ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('❌ Cancelled.'))
                return

        try:
            # 1. Clear Redis cache - all seat reservations
            self.stdout.write('🧹 Clearing Redis cache...')
            cache.clear()
            self.stdout.write(self.style.SUCCESS('✅ Redis cache cleared'))

            # 2. Delete all Transactions
            self.stdout.write('🗑️  Deleting all transactions...')
            transaction_count = Transaction.objects.all().count()
            Transaction.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'✅ Deleted {transaction_count} transactions'))

            # 3. Delete all Bookings
            self.stdout.write('🗑️  Deleting all bookings...')
            booking_count = Booking.objects.all().count()
            Booking.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'✅ Deleted {booking_count} bookings'))

            if not bookings_only:
                # FEATURE DISABLED: Review, ReviewLike, Wishlist, Interest features
                # 4. Delete all Review Likes
                # self.stdout.write('🗑️  Deleting all review likes...')
                # review_like_count = ReviewLike.objects.all().count()
                # ReviewLike.objects.all().delete()
                # self.stdout.write(self.style.SUCCESS(f'✅ Deleted {review_like_count} review likes'))

                # 5. Delete all Reviews
                # self.stdout.write('🗑️  Deleting all reviews...')
                # review_count = Review.objects.all().count()
                # Review.objects.all().delete()
                # self.stdout.write(self.style.SUCCESS(f'✅ Deleted {review_count} reviews'))

                # 6. Delete all Wishlist items
                # self.stdout.write('🗑️  Deleting all wishlist items...')
                # wishlist_count = Wishlist.objects.all().count()
                # Wishlist.objects.all().delete()
                # self.stdout.write(self.style.SUCCESS(f'✅ Deleted {wishlist_count} wishlist items'))

                # 7. Delete all Interest items
                # self.stdout.write('🗑️  Deleting all interests...')
                # interest_count = Interest.objects.all().count()
                # Interest.objects.all().delete()
                # self.stdout.write(self.style.SUCCESS(f'✅ Deleted {interest_count} interests'))

                # 8. Delete all Showtimes
                self.stdout.write('🗑️  Deleting all showtimes...')
                showtime_count = Showtime.objects.all().count()
                Showtime.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✅ Deleted {showtime_count} showtimes'))

                # 9. Delete all Screens
                self.stdout.write('🗑️  Deleting all screens...')
                screen_count = Screen.objects.all().count()
                Screen.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✅ Deleted {screen_count} screens'))

                # 10. Delete all Theaters
                self.stdout.write('🗑️  Deleting all theaters...')
                theater_count = Theater.objects.all().count()
                Theater.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✅ Deleted {theater_count} theaters'))

                # 11. Delete all Cities
                self.stdout.write('🗑️  Deleting all cities...')
                city_count = City.objects.all().count()
                City.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✅ Deleted {city_count} cities'))

                # 12. Delete all Movies
                self.stdout.write('🗑️  Deleting all movies...')
                movie_count = Movie.objects.all().count()
                Movie.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✅ Deleted {movie_count} movies'))

                # 13. Delete all Genres
                self.stdout.write('🗑️  Deleting all genres...')
                genre_count = Genre.objects.all().count()
                Genre.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✅ Deleted {genre_count} genres'))

                # 14. Delete all Languages
                self.stdout.write('🗑️  Deleting all languages...')
                language_count = Language.objects.all().count()
                Language.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'✅ Deleted {language_count} languages'))

            self.stdout.write(self.style.SUCCESS('\n🎉 All data cleared!'))
            self.stdout.write(self.style.SUCCESS('You can now add fresh test data.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

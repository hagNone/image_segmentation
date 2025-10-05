from __future__ import annotations

from django.core.management.base import BaseCommand

from geopol.scrapers.orchestrator import scrape_all_sources


class Command(BaseCommand):
    help = "Scrape Reuters and Al Jazeera sources into RawNews."

    def add_arguments(self, parser):
        parser.add_argument("--max", type=int, default=10, help="Max articles per source")

    def handle(self, *args, **options):
        n = scrape_all_sources(max_per_source=options["max"])
        self.stdout.write(self.style.SUCCESS(f"Scraped {n} new articles"))

from __future__ import annotations

from django.core.management.base import BaseCommand

from geopol.tasks import run_daily_pipeline


class Command(BaseCommand):
    help = "Run the GeopolStory daily pipeline: cluster, generate, email."

    def handle(self, *args, **options):
        result = run_daily_pipeline.delay()
        self.stdout.write(self.style.SUCCESS(f"Queued daily pipeline task: {result.id}"))

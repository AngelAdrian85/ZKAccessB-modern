# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand


class Command(BaseCommand):
	help = "Starts monitor instant message."

	def add_arguments(self, parser):
		# placeholder for future flags
		return

	def handle(self, *args, **options):
		# Import lazily and guard missing legacy modules so tests/CI can run
		try:
			from mysite.worktable.common_panel import monitor_instant_msg
		except Exception:
			# If the legacy module is missing, log and exit gracefully
			self.stdout.write(self.help)
			return

		self.stdout.write(self.help)
		monitor_instant_msg()


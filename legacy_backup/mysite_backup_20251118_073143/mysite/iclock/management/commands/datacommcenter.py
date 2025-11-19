from django.core.management.base import BaseCommand

class Command(BaseCommand):
	help = "Starts data comm center process."
	args = ''

	def handle(self, *args, **options):
		from mysite.iaccess.dev_comm_center import rundatacommcenter
		print("DataCommCenter starting... ...")
		try:
			rundatacommcenter()
		except Exception:
			import traceback
			traceback.print_exc()

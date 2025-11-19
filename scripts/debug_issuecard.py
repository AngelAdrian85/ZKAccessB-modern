import csv
from zkeco_modern.etl.issuecard import import_issuecards_from_csv
from legacy_models.models import IssueCard
p='zkeco_modern/etl/fixtures/issuecard_sample.csv'
print('Reading', p)
with open(p, newline='', encoding='utf-8') as fh:
    r=list(csv.DictReader(fh))
    print('CSV rows:', r)
res = import_issuecards_from_csv(p, commit=True)
print('import result:', res)
print('IssueCard count:', IssueCard.objects.count())
for ic in IssueCard.objects.all():
    print('IC:', ic.cardno, ic.cardstatus, getattr(ic.userid,'userid', None))

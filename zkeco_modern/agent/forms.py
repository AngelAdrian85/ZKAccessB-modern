from django import forms
from .models import Door, TimeSegment, Holiday, AccessLevel, Employee, EmployeeCard
try:
    from legacy_models.models import (
        Employee as LegacyEmployee,
        Dept as LegacyDept,
        Area as LegacyArea,
        IssueCard as LegacyIssueCard,
        AccessLog as LegacyAccessLog,
    )
except Exception:  # pragma: no cover
    LegacyEmployee = None
    LegacyDept = None
    LegacyArea = None
    LegacyIssueCard = None
    LegacyAccessLog = None


class DoorForm(forms.ModelForm):
    class Meta:
        model = Door
        fields = ["name", "device", "location", "normally_open", "enabled"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "txt"}),
            "location": forms.TextInput(attrs={"class": "txt"}),
        }


class TimeSegmentForm(forms.ModelForm):
    DAYS = [(i, d) for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])]
    days = forms.MultipleChoiceField(
        choices=DAYS, required=False, widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = TimeSegment
        fields = ["name", "start_time", "end_time"]  # days handled manually
        widgets = {"name": forms.TextInput(attrs={"class": "txt"})}


class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ["name", "date", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "txt"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class AccessLevelForm(forms.ModelForm):
    class Meta:
        model = AccessLevel
        fields = ["name", "doors", "time_segments", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "txt"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "doors": forms.SelectMultiple(attrs={"size": 8}),
            "time_segments": forms.SelectMultiple(attrs={"size": 5}),
        }


class EmployeeForm(forms.ModelForm):
    secondary_card_number = forms.CharField(
        required=False,
        max_length=32,
        label="Secondary Card Number",
        widget=forms.TextInput(attrs={"class": "txt"}),
    )
    class Meta:
        model = Employee
        fields = ["first_name", "last_name", "card_number", "access_levels", "active"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "txt"}),
            "last_name": forms.TextInput(attrs={"class": "txt"}),
            "card_number": forms.TextInput(attrs={"class": "txt"}),
            "access_levels": forms.SelectMultiple(attrs={"size": 6}),
        }

    def clean(self):
        cleaned = super().clean()
        secondary = cleaned.get("secondary_card_number")
        if isinstance(secondary, str):
            secondary = secondary.strip()
            cleaned["secondary_card_number"] = secondary
        if not secondary:
            return cleaned
        primary = cleaned.get("card_number")
        if primary and secondary == primary.strip():
            self.add_error(
                "secondary_card_number",
                "Secondary card number must differ from the primary card number.",
            )
            return cleaned
        conflicts = EmployeeCard.objects.filter(card_number=secondary)
        if self.instance and self.instance.pk:
            conflicts = conflicts.exclude(employee=self.instance)
        if conflicts.exists():
            self.add_error(
                "secondary_card_number",
                "This card is already assigned to another employee.",
            )
            return cleaned
        primary_conflict = Employee.objects.filter(card_number=secondary)
        if self.instance and self.instance.pk:
            primary_conflict = primary_conflict.exclude(pk=self.instance.pk)
        if primary_conflict.exists():
            self.add_error(
                "secondary_card_number",
                "This card is already assigned to another employee.",
            )
        return cleaned


class EmployeeExtendedForm(EmployeeForm):
    """Modern + legacy bridge form.

    Displays extra legacy fields if the legacy_models app is present.
    Saves modern Employee; attempts best-effort sync to a matching legacy Employee
    record (matched by userid or badgenumber/card_number) without raising if absent.
    """

    # Legacy-only optional fields
    legacy_userid = forms.IntegerField(required=False, label="Legacy UserID", widget=forms.NumberInput(attrs={"class": "txt", "title": "Identificator numeric unic din sistemul vechi"}))
    dept = forms.ModelChoiceField(required=False, queryset=LegacyDept.objects.all() if LegacyDept else [], label="Departament", widget=forms.Select(attrs={"title": "Departamentul angajatului"}))
    gender = forms.CharField(required=False, max_length=16, label="Gen", widget=forms.TextInput(attrs={"class": "txt", "title": "Gen (M/F)"}))
    hire_date = forms.DateField(required=False, label="Data angajării", widget=forms.DateInput(attrs={"type": "date", "title": "Data angajării în companie"}))
    email = forms.EmailField(required=False, label="Email", widget=forms.EmailInput(attrs={"class": "txt", "title": "Email contact"}))
    phone = forms.CharField(required=False, label="Telefon", max_length=32, widget=forms.TextInput(attrs={"class": "txt", "title": "Număr de telefon"}))
    privilege = forms.CharField(required=False, label="Privilegiu", max_length=64, widget=forms.TextInput(attrs={"class": "txt", "title": "Nivel de privilegiu/rol"}))
    identitycard = forms.CharField(required=False, max_length=64, label="C.I.", widget=forms.TextInput(attrs={"class": "txt", "title": "Carte identitate / act"}))
    site_code = forms.CharField(required=False, max_length=32, label="Cod Site", widget=forms.TextInput(attrs={"class": "txt", "title": "Cod / prefix card (site)"}))
    homeaddress = forms.CharField(required=False, max_length=256, label="Adresă", widget=forms.TextInput(attrs={"class": "txt", "title": "Adresă domiciliu"}))
    street = forms.CharField(required=False, max_length=256, label="Stradă", widget=forms.TextInput(attrs={"class": "txt", "title": "Stradă / detaliu adresă"}))
    acc_startdate = forms.DateField(required=False, label="Acces de la", widget=forms.DateInput(attrs={"type": "date", "title": "Data început valabilitate acces"}))
    acc_enddate = forms.DateField(required=False, label="Acces până la", widget=forms.DateInput(attrs={"type": "date", "title": "Data sfârșit valabilitate acces"}))
    extend_time = forms.IntegerField(required=False, label="Extensie timp", widget=forms.NumberInput(attrs={"class": "txt", "title": "Extensie timp suplimentar (minute)"}))
    delayed_door_open = forms.BooleanField(required=False, label="Întârziere ușă", widget=forms.CheckboxInput(attrs={"title": "Are întârziere la deschiderea ușii"}))
    hiretype = forms.CharField(required=False, max_length=32, label="Tip angajare", widget=forms.TextInput(attrs={"class": "txt", "title": "Tip angajare (ex: Full / Part)"}))
    emptype = forms.CharField(required=False, max_length=32, label="Tip personal", widget=forms.TextInput(attrs={"class": "txt", "title": "Categorie personal"}))
    selfpassword = forms.CharField(required=False, max_length=64, label="Parolă Self", widget=forms.PasswordInput(attrs={"class": "txt", "title": "Parolă autogestiune (opțional)"}))
    reservation_password = forms.CharField(required=False, max_length=64, label="Parolă Rezervare", widget=forms.TextInput(attrs={"class": "txt", "title": "Parolă rezervare / acces secundar"}))
    role_on_device = forms.CharField(required=False, max_length=64, label="Rol pe Dispozitiv", widget=forms.TextInput(attrs={"class": "txt", "title": "Rol pe dispozitiv (ex: Operator)"}))
    elevator_superuser = forms.BooleanField(required=False, label="Elevator Superuser", widget=forms.CheckboxInput(attrs={"title": "Acces special lift"}))
    elevator_level = forms.CharField(required=False, max_length=64, label="Nivel Lift", widget=forms.TextInput(attrs={"class": "txt", "title": "Nivel / grup lift"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing existing, attempt to preload legacy record
        self._legacy_obj = None
        # Preload secondary card if present
        if self.instance and self.instance.pk:
            existing_card = self.instance.cards.order_by("created_at").first()
            if existing_card:
                self.initial.setdefault("secondary_card_number", existing_card.card_number)
        if LegacyEmployee and self.instance and self.instance.pk:
            # Match by card_number -> legacy.card_number or badgenumber
            card = self.instance.card_number
            if card:
                try:
                    self._legacy_obj = LegacyEmployee.objects.filter(card_number=card).first() or LegacyEmployee.objects.filter(badgenumber=card).first()
                except Exception:
                    self._legacy_obj = None
            if self._legacy_obj:
                initial_map = {
                    'legacy_userid': self._legacy_obj.userid,
                    'gender': self._legacy_obj.gender,
                    'hire_date': self._legacy_obj.hiredday,
                    'email': self._legacy_obj.email,
                    'phone': self._legacy_obj.FPHONE,
                    'privilege': self._legacy_obj.Privilege,
                    'identitycard': self._legacy_obj.identitycard,
                    'site_code': self._legacy_obj.site_code,
                    'homeaddress': self._legacy_obj.homeaddress,
                    'street': self._legacy_obj.street,
                    'acc_startdate': self._legacy_obj.acc_startdate,
                    'acc_enddate': self._legacy_obj.acc_enddate,
                    'extend_time': self._legacy_obj.extend_time,
                    'delayed_door_open': self._legacy_obj.delayed_door_open,
                    'hiretype': self._legacy_obj.hiretype,
                    'emptype': self._legacy_obj.emptype,
                    'selfpassword': self._legacy_obj.selfpassword,
                    'reservation_password': getattr(self._legacy_obj,'reservation_password', None),
                    'role_on_device': getattr(self._legacy_obj,'role_on_device', None),
                    'elevator_superuser': getattr(self._legacy_obj,'elevator_superuser', None),
                    'elevator_level': getattr(self._legacy_obj,'elevator_level', None),
                }
                for k,v in initial_map.items():
                    if v is not None:
                        self.initial[k] = v
                if self._legacy_obj.defaultdept:
                    self.initial['dept'] = self._legacy_obj.defaultdept

    def save(self, commit=True):
        self._pending_secondary_card = self.cleaned_data.get("secondary_card_number")
        self._defer_secondary_card_sync = not commit
        emp = super().save(commit=commit)
        if commit:
            self._sync_secondary_card(emp, self._pending_secondary_card)
            self._pending_secondary_card = None
            self._defer_secondary_card_sync = False
        # Basic validation for access dates
        sd = self.cleaned_data.get('acc_startdate')
        ed = self.cleaned_data.get('acc_enddate')
        if sd and ed and ed < sd:
            self.add_error('acc_enddate', 'Data de sfârșit trebuie să fie după data de început')
        # Elevator level validation (restrict to predefined set if provided)
        allowed_levels = {'L1','L2','L3','VIP','STAFF'}
        lvl = self.cleaned_data.get('elevator_level')
        if lvl and lvl not in allowed_levels:
            self.add_error('elevator_level', f'Nivel invalid. Acceptat: {", ".join(sorted(allowed_levels))}')
        if LegacyEmployee:
            try:
                # Update or create legacy record
                leg = self._legacy_obj
                if not leg:
                    # Try by provided legacy_userid else create new
                    uid = self.cleaned_data.get('legacy_userid')
                    if uid:
                        leg = LegacyEmployee.objects.filter(userid=uid).first()
                if not leg:
                    # create minimal if we have identifying info
                    leg = LegacyEmployee(
                        userid=self.cleaned_data.get('legacy_userid') or emp.pk,
                        badgenumber=emp.card_number,
                        firstname=emp.first_name,
                        lastname=emp.last_name,
                    )
                # Sync fields
                leg.firstname = emp.first_name
                leg.lastname = emp.last_name
                leg.badgenumber = emp.card_number
                leg.card_number = emp.card_number
                leg.gender = self.cleaned_data.get('gender') or leg.gender
                leg.hiredday = self.cleaned_data.get('hire_date') or leg.hiredday
                leg.email = self.cleaned_data.get('email') or leg.email
                leg.FPHONE = self.cleaned_data.get('phone') or leg.FPHONE
                leg.Privilege = self.cleaned_data.get('privilege') or leg.Privilege
                # Extended sync
                for f in ['identitycard','site_code','homeaddress','street','acc_startdate','acc_enddate','extend_time','delayed_door_open','hiretype','emptype','selfpassword','reservation_password','role_on_device','elevator_superuser','elevator_level']:
                    val = self.cleaned_data.get(f)
                    if val is not None:
                        setattr(leg, f, val)
                dept = self.cleaned_data.get('dept')
                if dept:
                    leg.defaultdept = dept
                if commit:
                    leg.save()
            except Exception:
                pass
        return emp

    def save_m2m(self):
        super().save_m2m()
        if getattr(self, '_defer_secondary_card_sync', False) and self._pending_secondary_card is not None:
            self._sync_secondary_card(self.instance, self._pending_secondary_card)
            self._pending_secondary_card = None
            self._defer_secondary_card_sync = False

    def _sync_secondary_card(self, emp, secondary_card):
        if not emp or secondary_card is None:
            return
        secondary_card = secondary_card.strip()
        existing_cards = list(emp.cards.order_by('created_at'))
        if not secondary_card:
            for card in existing_cards:
                card.delete()
            return
        primary_card = existing_cards[0] if existing_cards else None
        if primary_card:
            if primary_card.card_number != secondary_card:
                primary_card.card_number = secondary_card
                primary_card.save(update_fields=['card_number'])
        else:
            EmployeeCard.objects.create(employee=emp, card_number=secondary_card)
        for duplicate in existing_cards[1:]:
            duplicate.delete()


class TimeSegmentFormWithDays(TimeSegmentForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            selected = []
            for i in range(7):
                if self.instance.days_mask & (1 << i):
                    selected.append(str(i))
            self.initial["days"] = selected

    def save(self, commit=True):
        obj = super(TimeSegmentForm, self).save(commit=False)
        mask = 0
        for d in self.cleaned_data.get("days", []):
            try:
                idx = int(d)
                mask |= (1 << idx)
            except Exception:
                pass
        obj.days_mask = mask or 0
        if commit:
            obj.save()
        return obj

# ---- New Legacy CRUD Bridge Forms ----

class DeptForm(forms.ModelForm):
    class Meta:
        model = LegacyDept  # type: ignore
        fields = ['DeptName', 'code']
        widgets = {
            'DeptName': forms.TextInput(attrs={'class': 'txt', 'title': 'Nume departament'}),
            'code': forms.TextInput(attrs={'class': 'txt', 'title': 'Cod intern departament'}),
        }


class AreaForm(forms.ModelForm):
    class Meta:
        model = LegacyArea  # type: ignore
        fields = ['areaname']
        widgets = {
            'areaname': forms.TextInput(attrs={'class': 'txt', 'title': 'Nume zonă'}),
        }


class IssueCardForm(forms.ModelForm):
    """Form robustă pentru IssueCard.

    Include câmpurile opționale `card_type` și `valid_until` doar dacă
    acestea există efectiv pe modelul legacy importat. Astfel evităm
    FieldError când rulăm în medii unde schema legacy nu are încă
    aceste coloane.
    """
    # Declarăm manual câmpurile opționale dacă lipsesc din model
    if LegacyIssueCard and not hasattr(LegacyIssueCard, 'valid_until'):
        valid_until = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date','title':'Valabil până la'}))
    if LegacyIssueCard and not hasattr(LegacyIssueCard, 'card_type'):
        card_type = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'txt','title':'Tip card'}))

    class Meta:
        model = LegacyIssueCard  # type: ignore
        _base = ['cardno','cardstatus','userid']
        _optional = []
        if LegacyIssueCard:
            for fname in ['card_type','valid_until']:
                if hasattr(LegacyIssueCard, fname):
                    _optional.append(fname)
        fields = _base + _optional
        widgets = {
            'cardno': forms.TextInput(attrs={'class': 'txt', 'title': 'Număr card'}),
            'cardstatus': forms.TextInput(attrs={'class': 'txt', 'title': 'Status card'}),
        }
        if LegacyIssueCard and hasattr(LegacyIssueCard,'card_type'):
            widgets['card_type'] = forms.TextInput(attrs={'class': 'txt', 'title': 'Tip card'})
        if LegacyIssueCard and hasattr(LegacyIssueCard,'valid_until'):
            widgets['valid_until'] = forms.DateInput(attrs={'type': 'date', 'title': 'Valabil până la'})


class AccessLogFilterForm(forms.Form):
    start = forms.DateField(required=False, label='De la', widget=forms.DateInput(attrs={'type': 'date'}))
    end = forms.DateField(required=False, label='Până la', widget=forms.DateInput(attrs={'type': 'date'}))
    cardno = forms.CharField(required=False, label='Card', widget=forms.TextInput(attrs={'class': 'txt'}))
    event_type = forms.CharField(required=False, label='Tip eveniment', widget=forms.TextInput(attrs={'class': 'txt'}))
    userid = forms.IntegerField(required=False, label='UserID')
    door = forms.CharField(required=False, label='Ușă', widget=forms.TextInput(attrs={'class': 'txt'}))

    def filter_queryset(self, qs):
        if self.is_valid():
            cd = self.cleaned_data
            if cd.get('start'):
                qs = qs.filter(timestamp__date__gte=cd['start'])
            if cd.get('end'):
                qs = qs.filter(timestamp__date__lte=cd['end'])
            if cd.get('cardno'):
                qs = qs.filter(cardno__icontains=cd['cardno'])
            if cd.get('event_type'):
                qs = qs.filter(event_type__icontains=cd['event_type'])
            if cd.get('userid'):
                qs = qs.filter(userid__userid=cd['userid'])
            if cd.get('door'):
                qs = qs.filter(door__name__icontains=cd['door'])
        return qs


# ---- Device Extended Bridge Form ----

class DeviceExtendedForm(forms.Form):
    """Bridge modern Device model with legacy Device details.

    Does not inherit ModelForm directly to allow combining fields from both
    schemas without forcing required legacy presence. Save method performs
    sync operations best-effort.
    """
    name = forms.CharField(label='Nume dispozitiv', max_length=128, widget=forms.TextInput(attrs={'class':'txt','title':'Nume logic'}))
    device_type = forms.CharField(label='Tip', max_length=64, required=False, widget=forms.TextInput(attrs={'class':'txt','title':'Tip dispozitiv'}))
    ip_address = forms.GenericIPAddressField(label='IP', required=False, widget=forms.TextInput(attrs={'class':'txt','title':'Adresă IP'}))
    area_name = forms.CharField(label='Zonă', max_length=64, required=False, widget=forms.TextInput(attrs={'class':'txt','title':'Nume zonă logică'}))
    enabled = forms.BooleanField(label='Activ', required=False, initial=True)
    serial_number = forms.CharField(label='Număr serie', max_length=128, required=False, widget=forms.TextInput(attrs={'class':'txt','title':'Serial (sn)'}))
    firmware_version = forms.CharField(label='Firmware', max_length=64, required=False, widget=forms.TextInput(attrs={'class':'txt','title':'Versiune firmware'}))
    # Legacy enriched details
    comm_type = forms.CharField(label='Comm Type', max_length=32, required=False, widget=forms.TextInput(attrs={'class':'txt','title':'Tip comunicare'}))
    com_port = forms.CharField(label='COM Port', max_length=64, required=False, widget=forms.TextInput(attrs={'class':'txt','title':'Port serial / COM'}))
    com_address = forms.CharField(label='COM Addr', max_length=128, required=False, widget=forms.TextInput(attrs={'class':'txt','title':'Adresă comunicare'}))
    acpanel_type = forms.CharField(label='AC Panel Type', max_length=64, required=False, widget=forms.TextInput(attrs={'class':'txt','title':'Tip panou acces'}))
    fp_count = forms.IntegerField(label='FP Count', required=False)
    transaction_count = forms.IntegerField(label='Tranzacții', required=False)

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)  # modern device instance
        super().__init__(*args, **kwargs)
        # preload from modern instance
        if self.instance:
            self.initial.update({
                'name': self.instance.name,
                'device_type': self.instance.device_type,
                'ip_address': self.instance.ip_address,
                'area_name': self.instance.area_name,
                'enabled': self.instance.enabled,
                'serial_number': self.instance.serial_number,
                'firmware_version': self.instance.firmware_version,
            })
        # Attempt preload legacy match
        try:
            from legacy_models.models import Device as LegacyDevice  # type: ignore
            legacy = None
            if self.instance and self.instance.serial_number:
                legacy = LegacyDevice.objects.filter(sn=self.instance.serial_number).first()
            if not legacy and self.instance and self.instance.name:
                legacy = LegacyDevice.objects.filter(device_name=self.instance.name).first()
            self._legacy = legacy
            if legacy:
                preload_map = {
                    'comm_type': legacy.comm_type,
                    'com_port': legacy.com_port,
                    'com_address': legacy.com_address,
                    'acpanel_type': legacy.acpanel_type,
                    'fp_count': legacy.fp_count,
                    'transaction_count': legacy.transaction_count,
                    'firmware_version': legacy.fw_version or self.initial.get('firmware_version'),
                }
                for k,v in preload_map.items():
                    if v is not None:
                        self.initial[k] = v
                if legacy.area and hasattr(legacy.area,'areaname'):
                    self.initial['area_name'] = legacy.area.areaname
                if legacy.sn and not self.initial.get('serial_number'):
                    self.initial['serial_number'] = legacy.sn
        except Exception:
            self._legacy = None

    def save(self):
        from .models import Device as ModernDevice  # local import
        data = self.cleaned_data
        if self.instance:
            md = self.instance
        else:
            md = ModernDevice()
        md.name = data.get('name') or md.name
        md.device_type = data.get('device_type') or md.device_type
        md.ip_address = data.get('ip_address') or md.ip_address
        md.area_name = data.get('area_name') or md.area_name
        md.enabled = data.get('enabled') if data.get('enabled') is not None else md.enabled
        md.serial_number = data.get('serial_number') or md.serial_number
        md.firmware_version = data.get('firmware_version') or md.firmware_version
        md.save()
        # Legacy sync
        try:
            from legacy_models.models import Device as LegacyDevice, Area as LegacyArea  # type: ignore
            legacy = self._legacy
            if not legacy:
                # create candidate
                legacy = LegacyDevice(
                    sn=md.serial_number or md.name,
                    device_name=md.name,
                    fw_version=md.firmware_version,
                    device_type=0,
                )
            legacy.comm_type = data.get('comm_type') or legacy.comm_type
            legacy.com_port = data.get('com_port') or legacy.com_port
            legacy.com_address = data.get('com_address') or legacy.com_address
            legacy.acpanel_type = data.get('acpanel_type') or legacy.acpanel_type
            legacy.fp_count = data.get('fp_count') or legacy.fp_count
            legacy.transaction_count = data.get('transaction_count') or legacy.transaction_count
            legacy.fw_version = data.get('firmware_version') or legacy.fw_version
            # area assign
            an = data.get('area_name')
            if an:
                area = LegacyArea.objects.filter(areaname=an).first()
                if not area:
                    try:
                        area = LegacyArea.objects.create(areaname=an)
                    except Exception:
                        area = None
                if area:
                    legacy.area = area
            legacy.save()
        except Exception:
            pass
        return md


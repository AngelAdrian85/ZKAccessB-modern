from django import forms
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.password_validation import validate_password
from .models import Door, TimeSegment, Holiday, AccessLevel, Employee, EmployeeCard, Device, DSTime
from .models import DoorFirstCardRule, DoorMultiCardRule
try:
    from legacy_models.models import (
        Area as LegacyArea,
        AccessLog as LegacyAccessLog,
        Dept,
    )
except Exception:  # pragma: no cover
    LegacyArea = None
    LegacyAccessLog = None
    Dept = None


class DoorForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields['device'].queryset = Device.objects.filter(scanner_linked=False).order_by('name')
        except Exception:
            pass

        # Reader names (editable): prefill with derived default to match legacy UX.
        try:
            if 'reader_in_custom_name' in self.fields:
                self.fields['reader_in_custom_name'].required = False
                self.fields['reader_in_custom_name'].widget = forms.TextInput(attrs={
                    "class": "txt",
                    "placeholder": "ex: 192.168.1.201-1 In",
                })
            if 'reader_out_custom_name' in self.fields:
                self.fields['reader_out_custom_name'].required = False
                self.fields['reader_out_custom_name'].widget = forms.TextInput(attrs={
                    "class": "txt",
                    "placeholder": "ex: 192.168.1.201-1 Out",
                })
            if getattr(self, 'instance', None) and getattr(self.instance, 'pk', None):
                # If custom is empty, show derived value for quick edit.
                if not getattr(self.instance, 'reader_in_custom_name', ''):
                    self.initial.setdefault('reader_in_custom_name', getattr(self.instance, 'reader_in_name', '') or '')
                if not getattr(self.instance, 'reader_out_custom_name', ''):
                    self.initial.setdefault('reader_out_custom_name', getattr(self.instance, 'reader_out_name', '') or '')
        except Exception:
            pass

    def clean(self):
        cleaned = super().clean()
        device = cleaned.get('device')
        door_number = cleaned.get('door_number')
        # When mapping to a controller, require a door index (1-32)
        if device is not None:
            try:
                is_controller = bool(getattr(device, 'is_controller', None) and device.is_controller())
            except Exception:
                is_controller = False
            if is_controller and not door_number:
                raise forms.ValidationError('Selectează numărul ușii (1-32) pentru această centrală.')

        # If user leaves reader names equal to the derived default, don't store redundant custom values.
        try:
            ip = getattr(device, 'ip_address', None) if device else None
            dn = door_number
            derived_in = f"{ip}-{dn} In" if (ip and dn) else ""
            derived_out = f"{ip}-{dn} Out" if (ip and dn) else ""
            rin = (cleaned.get('reader_in_custom_name') or '').strip()
            rout = (cleaned.get('reader_out_custom_name') or '').strip()
            if derived_in and rin == derived_in:
                cleaned['reader_in_custom_name'] = ''
            if derived_out and rout == derived_out:
                cleaned['reader_out_custom_name'] = ''
        except Exception:
            pass
        return cleaned

    class Meta:
        model = Door
        fields = [
            "device",
            "door_number",
            "name",
            "reader_in_custom_name",
            "reader_out_custom_name",
            "door_active_time_zone",
            "door_passage_mode_time_zone",
            "lock_open_duration",
            "punch_interval",
            "door_sensor_type",
            "door_status_delay",
            "close_and_reverse_state",
            "verify_mode",
            "duress_password",
            "emergency_password",
            "location",
            "normally_open",
            "enabled",
        ]
        labels = {
            "device": "Centrală",
            "door_number": "Număr ușă (1-32)",
            "name": "Denumire ușă",
            "reader_in_custom_name": "Cititor 1 (IN)",
            "reader_out_custom_name": "Cititor 2 (OUT)",
            "door_active_time_zone": "Interval activ ușă",
            "door_passage_mode_time_zone": "Interval mod pasaj",
            "lock_open_duration": "Durată deschidere yală (sec)",
            "punch_interval": "Interval Punch (sec)",
            "door_sensor_type": "Tip senzor ușă",
            "door_status_delay": "Întârziere status (sec)",
            "close_and_reverse_state": "Închidere și stare inversă",
            "verify_mode": "Mod verificare",
            "duress_password": "Parolă duress",
            "emergency_password": "Parolă urgență",
            "location": "Zonă / Locație",
            "normally_open": "Normal deschis",
            "enabled": "Activ",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "txt"}),
            "location": forms.TextInput(attrs={"class": "txt"}),
            "duress_password": forms.PasswordInput(render_value=True, attrs={"autocomplete": "off"}),
            "emergency_password": forms.PasswordInput(render_value=True, attrs={"autocomplete": "off"}),
        }


class DoorFirstCardRuleForm(forms.ModelForm):
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.all().order_by('last_name', 'first_name'),
        required=False,
        widget=forms.SelectMultiple,
        label='Opening Personnel',
    )

    class Meta:
        model = DoorFirstCardRule
        fields = ["time_segment", "employees"]


class DoorMultiCardRuleForm(forms.ModelForm):
    employees = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.all().order_by('last_name', 'first_name'),
        required=False,
        widget=forms.SelectMultiple,
        label='Personnel',
    )

    class Meta:
        model = DoorMultiCardRule
        fields = ["name", "required_count", "employees"]


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

class DSTimeForm(forms.ModelForm):
    class Meta:
        model = DSTime
        fields = [
            "name",
            "start_month",
            "start_week",
            "start_weekday",
            "start_hour",
            "start_minute",
            "end_month",
            "end_week",
            "end_weekday",
            "end_hour",
            "end_minute",
            "offset_minutes",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "txt", "placeholder": "ex: Romania"}),
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
        label="Card Secundar",
        widget=forms.TextInput(attrs={"class": "txt", "placeholder": "Număr card secundar (opțional)"}),
    )
    class Meta:
        model = Employee
        fields = ["first_name", "last_name", "card_number", "access_levels", "active"]
        labels = {
            "first_name": "Prenume",
            "last_name": "Nume",
            "card_number": "Nr. Card Principal",
            "access_levels": "Niveluri Acces",
            "active": "Activ"
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "txt", "placeholder": "ex: Ion"}),
            "last_name": forms.TextInput(attrs={"class": "txt", "placeholder": "ex: Popescu"}),
            "card_number": forms.TextInput(attrs={"class": "txt", "placeholder": "ex: 1234567890"}),
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
    legacy_userid = forms.IntegerField(required=False, label="Nr. Personal", widget=forms.NumberInput(attrs={"class": "txt", "title": "Identificator numeric unic (Personnel No.)", "placeholder": "ex: 1, 2, 3..."}))
    dept = forms.ModelChoiceField(
        required=False,
        queryset=Dept.objects.all(),
        label="Departament",
        widget=forms.Select(attrs={"title": "Departamentul angajatului"}),
        empty_label="----------"
    )
    gender = forms.CharField(required=False, max_length=16, label="Gen", widget=forms.Select(choices=[('','----------'),('M','Masculin'),('F','Feminin')], attrs={"title": "Gen (M/F)"}))
    
    # Contact fields matching legacy
    ssn = forms.CharField(required=False, max_length=64, label="CNP", widget=forms.TextInput(attrs={"class": "txt", "placeholder": "Cod Numeric Personal"}))
    birthday = forms.DateField(required=False, label="Data Nașterii", widget=forms.DateInput(attrs={"type": "date", "title": "Data nașterii"}))
    mobile_phone = forms.CharField(required=False, max_length=32, label="Telefon Mobil", widget=forms.TextInput(attrs={"class": "txt", "placeholder": "ex: 0722123456"}))
    home_phone = forms.CharField(required=False, max_length=32, label="Telefon Acasă", widget=forms.TextInput(attrs={"class": "txt", "placeholder": "ex: 0212345678"}))
    city = forms.CharField(required=False, max_length=128, label="Oraș", widget=forms.TextInput(attrs={"class": "txt", "placeholder": "ex: București"}))
    
    # Card and password fields
    card_type = forms.CharField(required=False, max_length=64, label="Tip Card", widget=forms.Select(choices=[('','Fără Site Code'),('SITE','Cu Site Code')], attrs={"title": "Tipul cardului de acces"}))
    password_on_record = forms.CharField(required=False, max_length=32, label="Parolă", widget=forms.TextInput(attrs={"class": "txt", "maxlength": "6", "title": "Parolă acces (6 cifre)", "placeholder": "123456"}))
    
    # Access control fields
    access_levels = forms.ModelMultipleChoiceField(
        queryset=AccessLevel.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Niveluri Acces"
    )
    access_superuser = forms.BooleanField(required=False, label="Superuser Acces", widget=forms.CheckboxInput(attrs={"title": "Acces administrator"}))
    multi_card_group = forms.CharField(required=False, max_length=64, label="Grupuri Multi-Card", widget=forms.Select(choices=[('',"----------")], attrs={"title": "Grup pentru acces multi-card"}))
    set_validity = forms.BooleanField(required=False, label="Setează Validitate", widget=forms.CheckboxInput(attrs={"title": "Activează perioada de valabilitate"}))
    
    # Employment fields
    hire_date = forms.DateField(required=False, label="Data Angajării", widget=forms.DateInput(attrs={"type": "date", "title": "Data angajării în companie"}))
    email = forms.EmailField(required=False, label="Email", widget=forms.EmailInput(attrs={"class": "txt", "title": "Email contact", "placeholder": "nume@companie.ro"}))
    phone = forms.CharField(required=False, label="Telefon Birou", max_length=32, widget=forms.TextInput(attrs={"class": "txt", "title": "Număr de telefon birou", "placeholder": "ex: 0212345678"}))
    privilege = forms.CharField(required=False, label="Privilegiu", max_length=64, widget=forms.TextInput(attrs={"class": "txt", "title": "Nivel de privilegiu/rol", "placeholder": "ex: Admin, User"}))
    identitycard = forms.CharField(required=False, max_length=64, label="Adresă Serviciu", widget=forms.TextInput(attrs={"class": "txt", "title": "Adresă de lucru"}))
    site_code = forms.CharField(required=False, max_length=32, label="Cod Site", widget=forms.TextInput(attrs={"class": "txt", "title": "Cod / prefix card (site)"}))
    homeaddress = forms.CharField(required=False, max_length=256, label="Adresă Domiciliu", widget=forms.TextInput(attrs={"class": "txt", "title": "Adresă domiciliu", "placeholder": "Strada, nr, bloc, ap"}))
    street = forms.CharField(required=False, max_length=256, label="Stradă", widget=forms.TextInput(attrs={"class": "txt", "title": "Stradă / detaliu adresă"}))
    acc_startdate = forms.DateField(required=False, label="Acces de la", widget=forms.DateInput(attrs={"type": "date", "title": "Data început valabilitate acces"}))
    acc_enddate = forms.DateField(required=False, label="Acces până la", widget=forms.DateInput(attrs={"type": "date", "title": "Data sfârșit valabilitate acces"}))
    extend_time = forms.IntegerField(required=False, label="Timp Extins", widget=forms.NumberInput(attrs={"class": "txt", "title": "Extensie timp suplimentar (1-254)", "placeholder":"1-254", "min":"1", "max":"254"}))
    delayed_door_open = forms.BooleanField(required=False, label="Deschidere Întârziată", widget=forms.CheckboxInput(attrs={"title": "Are întârziere la deschiderea ușii"}))
    hiretype = forms.CharField(required=False, max_length=32, label="Tip Angajare", widget=forms.Select(choices=[('','----------')], attrs={"title": "Tipul de angajare"}))
    emptype = forms.CharField(required=False, max_length=32, label="Tip Personal", widget=forms.Select(choices=[('','----------')], attrs={"title": "Tipul de personal"}))
    selfpassword = forms.CharField(required=False, max_length=64, label="Parolă Self", widget=forms.PasswordInput(attrs={"class": "txt", "title": "Parolă autogestiune (opțional)"}))
    reservation_password = forms.CharField(required=False, max_length=64, label="Parolă Rezervare", widget=forms.TextInput(attrs={"class": "txt", "title": "Parolă rezervare / acces secundar", "value": "123456"}))
    role_on_device = forms.CharField(required=False, max_length=64, label="Rol Dispozitiv", widget=forms.Select(choices=[('','----------')], attrs={"title": "Rolul pe dispozitiv"}))
    elevator_superuser = forms.BooleanField(required=False, label="Superuser Lift", widget=forms.CheckboxInput(attrs={"title": "Acces special lift"}))
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
            
            # Preload department from dept_id
            if self.instance.dept_id:
                try:
                    dept_obj = Dept.objects.get(id=self.instance.dept_id)
                    self.initial['dept'] = dept_obj
                except Exception:
                    pass
            
            # PRIORITATE: Valorile din Employee model au prioritate absolută
            # Le setăm explicit în self.initial DUPĂ super().__init__()
            employee_values = {
                'legacy_userid': self.instance.legacy_userid,
                'gender': self.instance.gender,
                'ssn': self.instance.ssn,
                'birthday': self.instance.birthday,
                'city': self.instance.city,
                'mobile_phone': self.instance.mobile_phone,
                'home_phone': self.instance.home_phone,
                'phone': self.instance.phone,
                'email': self.instance.email,
                'homeaddress': self.instance.homeaddress,
                'street': self.instance.street,
                'identitycard': self.instance.identitycard,
                'card_type': self.instance.card_type,
                'site_code': self.instance.site_code,
                'password_on_record': self.instance.password_on_record,
                'reservation_password': self.instance.reservation_password,
                'selfpassword': self.instance.selfpassword,
                'hire_date': self.instance.hire_date,
                'hiretype': self.instance.hiretype,
                'emptype': self.instance.emptype,
                'privilege': self.instance.privilege,
                'role_on_device': self.instance.role_on_device,
                'acc_startdate': self.instance.acc_startdate,
                'acc_enddate': self.instance.acc_enddate,
                'extend_time': self.instance.extend_time,
                'delayed_door_open': self.instance.delayed_door_open,
                'access_superuser': self.instance.access_superuser,
                'elevator_superuser': self.instance.elevator_superuser,
                'elevator_level': self.instance.elevator_level,
            }
            # Setează valorile din Employee - acestea au PRIORITATE ABSOLUTĂ
            for k, v in employee_values.items():
                if v is not None and v != '':  # Doar dacă există valoare în Employee
                    self.initial[k] = v

    def clean_legacy_userid(self):
        """Validare legacy_userid pentru a preveni duplicate."""
        userid = self.cleaned_data.get('legacy_userid')
        if userid is not None:
            # Verifică dacă acest userid este deja folosit de alt angajat
            existing = Employee.objects.filter(legacy_userid=userid)
            # Exclude instanța curentă dacă editează (nu e create)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                from django.core.exceptions import ValidationError
                raise ValidationError(
                    f'Nr. Personal {userid} este deja folosit de {existing.first().first_name} {existing.first().last_name}. '
                    'Te rog să alegi un număr diferit sau folosește butonul "Verifică" pentru a găsi unul disponibil.'
                )
        return userid

    def save(self, commit=True):
        # Store secondary card for later processing
        self._pending_secondary_card = self.cleaned_data.get("secondary_card_number")
        self._defer_secondary_card_sync = not commit
        
        # Create/update Employee instance
        emp = super().save(commit=False)
        
        # Sync all extended fields to modern Employee model
        emp.legacy_userid = self.cleaned_data.get('legacy_userid')
        emp.gender = self.cleaned_data.get('gender') or ''
        emp.ssn = self.cleaned_data.get('ssn') or ''
        emp.birthday = self.cleaned_data.get('birthday')
        emp.city = self.cleaned_data.get('city') or ''
        emp.mobile_phone = self.cleaned_data.get('mobile_phone') or ''
        emp.home_phone = self.cleaned_data.get('home_phone') or ''
        emp.phone = self.cleaned_data.get('phone') or ''
        emp.email = self.cleaned_data.get('email') or ''
        emp.homeaddress = self.cleaned_data.get('homeaddress') or ''
        emp.street = self.cleaned_data.get('street') or ''
        emp.identitycard = self.cleaned_data.get('identitycard') or ''
        emp.card_type = self.cleaned_data.get('card_type') or ''
        emp.site_code = self.cleaned_data.get('site_code') or ''
        emp.password_on_record = self.cleaned_data.get('password_on_record') or ''
        emp.reservation_password = self.cleaned_data.get('reservation_password') or '123456'
        emp.selfpassword = self.cleaned_data.get('selfpassword') or ''
        emp.hire_date = self.cleaned_data.get('hire_date')
        emp.hiretype = self.cleaned_data.get('hiretype') or ''
        emp.emptype = self.cleaned_data.get('emptype') or ''
        emp.privilege = self.cleaned_data.get('privilege') or ''
        emp.role_on_device = self.cleaned_data.get('role_on_device') or ''
        emp.acc_startdate = self.cleaned_data.get('acc_startdate')
        emp.acc_enddate = self.cleaned_data.get('acc_enddate')
        emp.extend_time = self.cleaned_data.get('extend_time')
        emp.delayed_door_open = self.cleaned_data.get('delayed_door_open') or False
        emp.access_superuser = self.cleaned_data.get('access_superuser') or False
        emp.elevator_superuser = self.cleaned_data.get('elevator_superuser') or False
        emp.elevator_level = self.cleaned_data.get('elevator_level') or ''
        emp.multi_card_group = self.cleaned_data.get('multi_card_group') or ''
        emp.set_validity = self.cleaned_data.get('set_validity') or False
        
        # Save department ID
        dept = self.cleaned_data.get('dept')
        if dept:
            emp.dept_id = dept.id
        else:
            emp.dept_id = None
        
        # Save Employee instance
        if commit:
            emp.save()
            self.save_m2m()
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
        
        # Legacy database sync REMOVED - now using only agent.Employee
        
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
        model = Dept  # Using agent.Dept instead of legacy_models.Dept
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


# IssueCardForm REMOVED - now using EmployeeCard from agent.models instead


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

class DeviceExtendedForm(forms.ModelForm):
    """Complete device registration form matching legacy app."""
    
    class Meta:
        model = Device
        fields = [
            'name', 'serial_number', 'device_type', 'comm_mode', 'ip_address', 'port',
            'comm_password', 'rs485_port', 'rs485_baudrate', 'rs485_address',
            'area_name', 'time_zone', 'firmware_version', 'hardware_version',
            'enabled', 'auto_sync_time', 'clear_on_add', 'scanner_linked', 'scanner_type',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., FINANCIAR, Medical'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'device_type': forms.Select(attrs={'class': 'form-control'}),
            'comm_mode': forms.RadioSelect(choices=Device.COMM_MODE_CHOICES),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '192.168.1.100'}),
            'port': forms.NumberInput(attrs={'class': 'form-control', 'value': '4370'}),
            'comm_password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '(optional)'}),
            'rs485_port': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'COM1'}),
            'rs485_baudrate': forms.NumberInput(attrs={'class': 'form-control', 'value': '9600'}),
            'rs485_address': forms.NumberInput(attrs={'class': 'form-control'}),
            'area_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Physical location'}),
            'time_zone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Europe/Bucharest'}),
            'firmware_version': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            # Hardware/model string is often needed to infer door capacity (ACP-100/200/400).
            # Keep it editable as a fallback when auto-detection isn't available.
            'hardware_version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: ACP-200'}),
            'enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_sync_time': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'clear_on_add': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comm_mode'].initial = 'tcp'
        self.fields['auto_sync_time'].initial = True
        self.fields['enabled'].initial = True
        self.fields['port'].initial = 4370
        self.fields['rs485_baudrate'].initial = 9600
        self.fields['scanner_linked'] = forms.BooleanField(required=False, label='Scanner Linked', widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
        self.fields['scanner_type'] = forms.ChoiceField(required=False, label='Scanner Type', choices=[('', 'Select'), ('acp', 'ACP TCP'), ('elatec', 'Elatec Serial')], widget=forms.Select(attrs={'class': 'form-control'}))

        # Time zone: legacy-like dropdown list (Etc/GMT offsets + a few defaults).
        # NOTE: A CharField with a Select widget won't render <option> tags unless the
        # widget has choices; use a real ChoiceField for consistent rendering.
        try:
            from agent.tz_utils import build_device_time_zone_choice_tuples

            tz_choices = build_device_time_zone_choice_tuples()

            # Preserve current value (instance / bound data) even if it's not in our preset list.
            current_val = ''
            try:
                if self.is_bound:
                    current_val = (self.data.get('time_zone') or '').strip()
                else:
                    current_val = (self.initial.get('time_zone') or getattr(self.instance, 'time_zone', '') or '').strip()
            except Exception:
                current_val = ''

            base_choices: list[tuple[str, str]] = [('', '— Selectează fus orar —')]
            if current_val and all(v != current_val for v, _ in tz_choices):
                base_choices.append((current_val, f"(curent) {current_val}"))
            base_choices.extend(tz_choices)

            self.fields['time_zone'] = forms.ChoiceField(
                required=False,
                choices=base_choices,
                widget=forms.Select(attrs={'class': 'form-control'}),
                label=self.fields['time_zone'].label or 'Fus Orar',
            )

            if current_val:
                self.fields['time_zone'].initial = current_val
        except Exception:
            # Best-effort only; keep the default field/widget.
            pass

        # Populate Zone/Area dropdown from legacy Areas.
        # Keep the field as a CharField to avoid rejecting values not yet present in legacy,
        # but render as <select> so the UI always shows available zones.
        try:
            from legacy_models.models import Area as LegacyArea  # type: ignore
        except Exception:  # pragma: no cover
            LegacyArea = None

        try:
            items = []
            if LegacyArea is not None:
                items = list(LegacyArea.objects.all().values('id', 'areaname'))
            names = []
            for it in items:
                n = (it.get('areaname') or '').strip()
                if n:
                    names.append(n)
            names = sorted(set(names), key=lambda s: s.lower())

            current_val = ''
            try:
                if self.is_bound:
                    current_val = (self.data.get('area_name') or '').strip()
                else:
                    current_val = (self.initial.get('area_name') or getattr(self.instance, 'area_name', '') or '').strip()
            except Exception:
                current_val = ''

            choices = [('', '— Selectează zonă —')]
            if current_val and current_val not in names:
                choices.append((current_val, current_val))
            choices.extend([(n, n) for n in names])

            self.fields['area_name'].widget = forms.Select(attrs={'class': 'form-control area-select'})
            self.fields['area_name'].widget.choices = choices
        except Exception:
            # Best-effort only; if legacy DB isn't ready, keep default widget.
            pass
    
    def clean(self):
        cleaned = super().clean()
        comm_mode = cleaned.get('comm_mode')
        
        if comm_mode == 'tcp':
            if not cleaned.get('ip_address'):
                self.add_error('ip_address', 'IP address required for TCP/IP')
        elif comm_mode == 'rs485':
            if not cleaned.get('rs485_port'):
                self.add_error('rs485_port', 'Serial port required for RS485')
        
        return cleaned

    def save(self):
        from .models import Device as ModernDevice  # local import
        data = self.cleaned_data
        if self.instance:
            md = self.instance
        else:
            md = ModernDevice()
        md.name = (data.get('name') or md.name)
        md.serial_number = (data.get('serial_number') or md.serial_number)

        md.device_type = (data.get('device_type') or md.device_type)
        md.comm_mode = (data.get('comm_mode') or md.comm_mode)

        md.ip_address = data.get('ip_address') or md.ip_address
        md.port = data.get('port') if data.get('port') is not None else md.port
        md.comm_password = (data.get('comm_password') or md.comm_password)

        md.rs485_port = (data.get('rs485_port') or md.rs485_port)
        md.rs485_baudrate = data.get('rs485_baudrate') if data.get('rs485_baudrate') is not None else md.rs485_baudrate
        md.rs485_address = data.get('rs485_address') if data.get('rs485_address') is not None else md.rs485_address

        md.area_name = (data.get('area_name') or md.area_name)
        md.time_zone = (data.get('time_zone') or md.time_zone)

        md.firmware_version = (data.get('firmware_version') or md.firmware_version)
        md.hardware_version = (data.get('hardware_version') or md.hardware_version)

        md.enabled = data.get('enabled') if data.get('enabled') is not None else md.enabled
        md.auto_sync_time = data.get('auto_sync_time') if data.get('auto_sync_time') is not None else md.auto_sync_time
        md.clear_on_add = data.get('clear_on_add') if data.get('clear_on_add') is not None else md.clear_on_add

        md.scanner_linked = data.get('scanner_linked') if data.get('scanner_linked') is not None else md.scanner_linked
        md.scanner_type = (data.get('scanner_type') or md.scanner_type)

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
            # Legacy fields are best-effort only; modern app remains source of truth.
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


# ---- System Module Forms ----


ROLE_GROUP_PREFIX = 'ROLE_'
ROLE_SUPER_ADMIN = 'ROLE_SUPER_ADMIN'
ROLE_ADMIN = 'ROLE_ADMIN'
ROLE_USER = 'ROLE_USER'
ROLE_VISITOR = 'ROLE_VISITOR'


def _ensure_role_groups_exist() -> None:
    try:
        for name in (ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER, ROLE_VISITOR):
            Group.objects.get_or_create(name=name)
    except Exception:
        # Best-effort only; avoid hard failure during migrations/startup.
        pass


def _all_time_zone_choices():
    try:
        from agent.tz_utils import build_time_zone_choice_tuples

        return build_time_zone_choice_tuples()
    except Exception:
        zones = [
            'Europe/Bucharest',
            'UTC',
            'Etc/UTC',
            'Etc/GMT-2',
            'Etc/GMT+2',
        ]
        return [(z, z) for z in zones]


class SystemUserForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(
        choices=[
            (ROLE_SUPER_ADMIN, 'Super Admin'),
            (ROLE_ADMIN, 'Admin'),
            (ROLE_USER, 'Utilizator'),
            (ROLE_VISITOR, 'Vizitator'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    is_active = forms.BooleanField(required=False, initial=True)
    password1 = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, instance: User | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        _ensure_role_groups_exist()

        if instance is not None and not self.is_bound:
            self.initial.update(
                {
                    'username': instance.username,
                    'first_name': instance.first_name,
                    'last_name': instance.last_name,
                    'email': instance.email,
                    'is_active': instance.is_active,
                }
            )
            # Infer current role from groups / flags
            role = ROLE_USER
            try:
                group_names = set(instance.groups.values_list('name', flat=True))
                for candidate in (ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER, ROLE_VISITOR):
                    if candidate in group_names:
                        role = candidate
                        break
                # Fallback to flags
                if instance.is_superuser:
                    role = ROLE_SUPER_ADMIN
                elif instance.is_staff:
                    role = ROLE_ADMIN
            except Exception:
                pass
            self.initial['role'] = role

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise forms.ValidationError('Username este obligatoriu.')
        qs = User.objects.filter(username=username)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Username deja existent.')
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = (cleaned.get('password1') or '').strip()
        p2 = (cleaned.get('password2') or '').strip()

        # Create: password required; Edit: optional.
        if self.instance is None and not p1:
            self.add_error('password1', 'Parola este obligatorie.')
        if (p1 or p2) and p1 != p2:
            self.add_error('password2', 'Parolele nu coincid.')
        if p1:
            try:
                validate_password(p1)
            except Exception as ex:
                self.add_error('password1', str(ex))
        return cleaned

    def save(self) -> User:
        data = self.cleaned_data
        if self.instance is None:
            user = User()
        else:
            user = self.instance

        user.username = data.get('username')
        user.first_name = data.get('first_name') or ''
        user.last_name = data.get('last_name') or ''
        user.email = data.get('email') or ''
        user.is_active = bool(data.get('is_active'))

        role = data.get('role')
        user.is_superuser = (role == ROLE_SUPER_ADMIN)
        user.is_staff = role in (ROLE_SUPER_ADMIN, ROLE_ADMIN)

        user.save()

        # Enforce exactly one role group.
        _ensure_role_groups_exist()
        try:
            role_groups = list(Group.objects.filter(name__in=[ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_USER, ROLE_VISITOR]))
            user.groups.remove(*role_groups)
            if role:
                g = Group.objects.filter(name=role).first()
                if g:
                    user.groups.add(g)
        except Exception:
            pass

        p1 = (data.get('password1') or '').strip()
        if p1:
            user.set_password(p1)
            user.save(update_fields=['password'])
        return user


class SystemGroupForm(forms.Form):
    name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all().order_by('content_type__app_label', 'codename'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '10'}),
    )

    def __init__(self, *args, instance: Group | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        if instance is not None and not self.is_bound:
            self.initial['name'] = instance.name
            try:
                self.initial['permissions'] = list(instance.permissions.all())
            except Exception:
                self.initial['permissions'] = []

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Numele grupului este obligatoriu.')
        qs = Group.objects.filter(name=name)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Grup deja existent.')
        return name

    def save(self) -> Group:
        data = self.cleaned_data
        if self.instance is None:
            grp = Group()
        else:
            grp = self.instance
        grp.name = data.get('name')
        grp.save()
        try:
            grp.permissions.set(data.get('permissions') or [])
        except Exception:
            pass
        return grp


class TimeZoneSettingForm(forms.Form):
    name = forms.CharField(max_length=64, widget=forms.TextInput(attrs={'class': 'form-control'}))
    region = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Europe'}),
    )
    time_zone = forms.ChoiceField(choices=_all_time_zone_choices(), widget=forms.Select(attrs={'class': 'form-control'}))
    is_active = forms.BooleanField(required=False)

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        if instance is not None and not self.is_bound:
            self.initial['name'] = getattr(instance, 'name', '')
            self.initial['region'] = getattr(instance, 'region', '')
            self.initial['time_zone'] = getattr(instance, 'time_zone', '')
            self.initial['is_active'] = bool(getattr(instance, 'is_active', False))

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Denumirea este obligatorie.')
        try:
            from agent.models import TimeZoneSetting

            qs = TimeZoneSetting.objects.filter(name=name)
            if getattr(self, 'instance', None) is not None:
                try:
                    qs = qs.exclude(pk=self.instance.pk)
                except Exception:
                    pass
            if qs.exists():
                raise forms.ValidationError('Denumire deja existentă.')
        except forms.ValidationError:
            raise
        except Exception:
            pass
        return name

    def clean_region(self):
        region = (self.cleaned_data.get('region') or '').strip()
        if region:
            return region
        tz_name = (self.cleaned_data.get('time_zone') or '').strip()
        if tz_name and '/' in tz_name:
            return tz_name.split('/', 1)[0].strip()
        return ''


class DeviceTimeZoneForm(forms.Form):
    time_zone = forms.ChoiceField(
        choices=_all_time_zone_choices(),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        if instance is not None and not self.is_bound:
            try:
                self.initial['time_zone'] = getattr(instance, 'time_zone', '') or ''
            except Exception:
                pass



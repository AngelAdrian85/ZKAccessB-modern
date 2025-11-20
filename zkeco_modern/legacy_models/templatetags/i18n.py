
"""
Legacy i18n shim (now disabled).

This module previously provided permissive `{% trans %}` and
`{% blocktrans %}` replacements. To avoid duplicating Django's
`i18n` templatetag name and triggering templates.E003, the module is
intentionally left empty — keep it present only for historical
reference. Real translation tags are provided by `django.templatetags.i18n`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django import template
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe

register = template.Library()


@dataclass(frozen=True)
class _Badge:
    css: str
    label: str
    title: str


def _shorten(label: str, limit: int = 18) -> str:
    s = label.strip()
    if len(s) <= limit:
        return s
    return s[: max(0, limit - 1)].rstrip() + "…"


def _status_badge(status_text: Optional[str]) -> _Badge:
    raw = (status_text or "").strip()
    if not raw:
        return _Badge("flag-muted", "—", "Fără status")

    stl = raw.lower()

    # OK / allow
    if stl in {"acceptat", "accepted", "ok", "granted", "allow", "allowed", "permitted", "permit", "success"}:
        return _Badge("flag-ok", "ACCEPTAT", "Acces permis / operațiune reușită")

    # DENY
    if stl in {"respins", "denied", "deny", "rejected", "reject", "forbidden", "blocked"}:
        return _Badge("flag-deny", "RESPINS", "Acces respins / operațiune nepermisă")

    # TIMEOUT / expired
    if "timeout" in stl or "time out" in stl or "expired" in stl or "no response" in stl:
        return _Badge("flag-timeout", "TIMEOUT", "Timeout: dispozitivul nu a răspuns")

    # Alarm-ish
    if "alarm" in stl or stl == "alert" or "panic" in stl or "duress" in stl or "forced" in stl:
        return _Badge("flag-alarm", "ALARMĂ", "Alarmă / eveniment critic")

    # Errors
    if stl == "err" or "error" in stl or "fail" in stl or "invalid" in stl:
        return _Badge("flag-err", "EROARE", "Eroare (execuție/validare/comunicare)")

    # Door state / lock state
    if stl == "open" or "door open" in stl or "unlock" in stl or "unlocked" in stl:
        return _Badge("flag-open", "DESCHIS", "Stare: deschis / deblocat")

    if stl == "closed" or "door closed" in stl or "close" in stl or "lock" in stl or "locked" in stl:
        return _Badge("flag-closed", "ÎNCHIS", "Stare: închis / blocat")

    # Fallback: keep the raw status but make it readable.
    return _Badge("flag-info", _shorten(raw), f"Stare: {raw}")


def _action_badge(action: Optional[str]) -> _Badge:
    a = (action or "").strip().lower()
    if a == "create":
        return _Badge("flag-ok", "ADĂUGARE", "Înregistrare nouă creată")
    if a == "update":
        return _Badge("flag-info", "MODIFICARE", "Înregistrare modificată")
    if a == "delete":
        return _Badge("flag-deny", "ȘTERGERE", "Înregistrare ștearsă")
    if not a:
        return _Badge("flag-muted", "—", "Fără acțiune")
    return _Badge("flag-muted", "ALTELE", "Acțiune neclasificată")


def _details_badge(details: Optional[str]) -> _Badge:
    raw = (details or "").strip()
    if not raw:
        return _Badge("flag-muted", "—", "Fără detalii")

    d = raw.lower()
    # classify payload/details into a compact label from legend
    if "timeout" in d or "time out" in d or "no response" in d:
        return _Badge("flag-timeout", "TIMEOUT", raw)
    if "alarm" in d or "panic" in d or "duress" in d or "forced" in d:
        return _Badge("flag-alarm", "ALARMĂ", raw)
    if "traceback" in d or "error" in d or "exception" in d or "failed" in d or "invalid" in d:
        return _Badge("flag-err", "EROARE", raw)
    # default informational payload (JSON, changes, etc)
    return _Badge("flag-info", "INFO", raw)


def _access_action_badge(kind: Optional[str]) -> _Badge:
    k = (kind or "").strip().lower()
    if not k:
        return _Badge("flag-muted", "—", "Fără acțiune")
    if k in {"command", "cmd", "comanda", "comandă", "door"}:
        return _Badge("flag-info", "COMANDĂ", "Comandă (door control / acțiune operator)")
    if k in {"remote", "remote open", "remote_open"}:
        return _Badge("flag-info", "REMOTE", "Acțiune remote (ex: Remote Open)")
    if k in {"scan", "punch", "pin", "card"}:
        return _Badge("flag-muted", "SCAN", "Scanare (card/PIN/biometric)")
    if k in {"event", "evt"}:
        return _Badge("flag-muted", "EVENT", "Eveniment dispozitiv (door open/close etc.)")
    return _Badge("flag-muted", _shorten(k.upper(), 10), f"Acțiune: {kind}")


@register.filter(name="zk_status_badge")
def zk_status_badge(status_text: Optional[str], hint: Optional[str] = None) -> str:
    b = _status_badge(status_text)
    extra = (hint or '').strip()
    title = b.title if not extra else f"{b.title} | {extra}"
    return format_html(
        '<span class="flag {}" title="{}">{}</span>',
        b.css,
        conditional_escape(title),
        conditional_escape(b.label),
    )


@register.filter(name="zk_action_badge")
def zk_action_badge(action: Optional[str]) -> str:
    b = _action_badge(action)
    return format_html(
        '<span class="flag {}" title="{}">{}</span>',
        b.css,
        conditional_escape(b.title),
        conditional_escape(b.label),
    )


@register.filter(name="zk_details_badge")
def zk_details_badge(details: Optional[str]) -> str:
    b = _details_badge(details)
    return format_html(
        '<span class="flag {}" title="{}">{}</span>',
        b.css,
        conditional_escape(b.title),
        conditional_escape(b.label),
    )


@register.filter(name="zk_access_action_badge")
def zk_access_action_badge(kind: Optional[str]) -> str:
    b = _access_action_badge(kind)
    return format_html(
        '<span class="flag {}" title="{}">{}</span>',
        b.css,
        conditional_escape(b.title),
        conditional_escape(b.label),
    )


@register.simple_tag(name="zk_badge_css")
def zk_badge_css() -> str:
    # Keep the badge CSS centralized so all tabs/embeds look identical.
    css = "\n".join(
        [
            ".flag{display:inline-flex;align-items:center;gap:6px;padding:2px 8px;border-radius:999px;font-size:9px;font-weight:900;letter-spacing:.2px;border:1px solid rgba(255,255,255,0.14);background:rgba(255,255,255,0.06);}",
            ".flag-ok{color:#77e39c;border-color:rgba(45,164,78,0.32);background:rgba(45,164,78,0.10);}",
            ".flag-deny{color:#ffb3bb;border-color:rgba(255,140,153,0.35);background:rgba(255,140,153,0.10);}",
            ".flag-warn{color:#ffd199;border-color:rgba(217,126,74,0.35);background:rgba(217,126,74,0.10);}",
            ".flag-alarm{color:#ffd199;border-color:rgba(217,126,74,0.45);background:rgba(217,126,74,0.14);}",
            ".flag-err{color:#ff8c99;border-color:rgba(255,80,80,0.55);background:rgba(255,80,80,0.12);}",
            ".flag-timeout{color:#ffe08a;border-color:rgba(255,210,80,0.45);background:rgba(255,210,80,0.10);}",
            ".flag-open{color:#9fd2f1;border-color:rgba(61,165,217,0.40);background:rgba(61,165,217,0.14);}",
            ".flag-closed{color:#a8c5d8;border-color:rgba(168,197,216,0.26);background:rgba(168,197,216,0.08);}",
            ".flag-info{color:#9fd2f1;border-color:rgba(61,165,217,0.30);background:rgba(61,165,217,0.10);}",
            ".flag-muted{color:#a8c5d8;border-color:rgba(168,197,216,0.20);background:rgba(168,197,216,0.06);}",
        ]
    )
    return mark_safe(css)

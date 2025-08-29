"""
kb_utils.py — hotel-focused knowledge-to-text helper

This module exposes:
- kb_to_text(kb: dict) -> str
  Produces a compact, stable text rendering of the Hotel Arthur JSON schema:
    meta, policies, amenities, location_transport, faq_examples, escalation_templates.
  If the input doesn't look like the hotel schema, it falls back to a generic stringifier.

Design goals:
- Deterministic order for stable prompts
- Skip empty/missing fields
- Concise but complete enough for grounding
"""

from typing import Any, Dict, Iterable


def _kv(label: str, value: Any) -> str:
    if value is None or value == "" or value is False:
        return ""
    return f"- {label}: {value}\n"


def _join(items: Any, sep: str = ", ") -> str:
    if isinstance(items, (list, tuple)):
        return sep.join([str(x) for x in items if x is not None and x != ""])
    return str(items) if items is not None else ""


def _section(title: str) -> str:
    return f"\n## {title}\n"


def _render_meta(meta: Dict[str, Any]) -> str:
    out = ["# Hotel Knowledge\n"]
    out.append(_kv("Name", meta.get("name")))
    out.append(_kv("Address", meta.get("address")))
    out.append(_kv("City", meta.get("city")))
    contact = (meta or {}).get("contact", {})
    out.append(_kv("Reception Phone", contact.get("reception_phone")))
    out.append(_kv("Reception Email", contact.get("reception_email")))
    return "".join(out)


def _render_policies(pol: Dict[str, Any]) -> str:
    if not pol:
        return ""
    out = [_section("Policies")]
    ci = pol.get("check_in")
    if isinstance(ci, dict):
        out.append(_kv("Check-in (direct booking)", ci.get("direct_booking")))
        out.append(_kv("Check-in (other)", ci.get("other_channels_or_groups")))
    else:
        out.append(_kv("Check-in", ci))

    out.append(_kv("Check-out", pol.get("check_out")))
    out.append(_kv("Luggage storage", pol.get("luggage_storage")))

    pets = pol.get("pets", {})
    if isinstance(pets, dict):
        out.append(_kv("Pets allowed", pets.get("allowed")))
        out.append(_kv("Pet rooms limited", pets.get("rooms_limited")))
        out.append(_kv("Pet fee €/night", pets.get("fee_per_night_eur")))
        out.append(_kv("Must inform when booking", pets.get("must_inform_in_booking")))
        out.append(_kv("Pets unattended allowed", not pets.get("cannot_leave_unattended")))

    smoking = pol.get("smoking", {})
    if isinstance(smoking, dict):
        out.append(_kv("Non-smoking hotel", smoking.get("non_smoking_hotel")))
        out.append(_kv("E-cigarettes banned", smoking.get("e_cigarettes_banned")))
        out.append(_kv("Cleaning fee from €", smoking.get("cleaning_fee_from_eur")))

    out.append(_kv("Minors policy", pol.get("minors")))

    pm = pol.get("payment_methods", {})
    if isinstance(pm, dict):
        out.append(_kv("Cards at hotel", _join(pm.get("cards_hotel"))))
        out.append(_kv("Cash accepted", pm.get("cash")))

    return "".join(out)


def _render_amenities(am: Dict[str, Any]) -> str:
    if not am:
        return ""
    out = [_section("Amenities")]
    out.append(_kv("Wi‑Fi", am.get("wifi")))

    br = am.get("breakfast", {})
    if isinstance(br, dict):
        hours = br.get("hours", {})
        out.append(_kv("Breakfast hours (Mon–Fri)", hours.get("mon_fri")))
        out.append(_kv("Breakfast hours (Sat–Sun/Holidays)", hours.get("sat_sun_holidays")))
        out.append(_kv("Room‑service breakfast", br.get("room_service_breakfast")))

    sauna = am.get("sauna", {})
    if isinstance(sauna, dict):
        out.append(_kv("Private saunas (count)", sauna.get("private_saunas_count")))
        out.append(_kv("Sauna session (min)", sauna.get("session_length_minutes")))
        out.append(_kv("Sauna price direct €/person", sauna.get("price_direct_eur_per_person")))
        out.append(_kv("Sauna price other €/person", sauna.get("price_other_eur_per_person")))
        out.append(_kv("Includes towels", sauna.get("includes_towels")))
        out.append(_kv("Book at reception", sauna.get("book_at_reception")))
        out.append(_kv("Rooms w/ private sauna", _join(sauna.get("rooms_with_private_sauna_examples"))))

    parking = am.get("parking", {})
    if isinstance(parking, dict):
        out.append(_kv("On-site parking", parking.get("on_site")))
        out.append(_kv("Parking recommendation", parking.get("recommendation")))
        out.append(_kv("Max vehicle height (m)", parking.get("max_vehicle_height_m")))
        out.append(_kv("Entrance address", parking.get("entrance_address")))
        out.append(_kv("Street parking", parking.get("street_parking")))

    acc = am.get("accessibility", {})
    if isinstance(acc, dict):
        out.append(_kv("Step‑free WC locations", _join(acc.get("step_free_wc_locations"))))
        out.append(_kv("Wheelchair to meeting wing", acc.get("wheelchair_to_meeting_wing")))
        out.append(_kv("Accessible rooms", acc.get("accessible_rooms")))
        out.append(_kv("Accessibility notes", acc.get("notes")))

    return "".join(out)


def _render_location(lt: Dict[str, Any]) -> str:
    if not lt:
        return ""
    out = [_section("Location & Transport")]
    out.append(_kv("Nearest metro", lt.get("nearest_metro")))
    out.append(_kv("Nearby trams", _join(lt.get("nearby_trams"))))
    out.append(_kv("Walk from Central Station", lt.get("walking_from_station")))

    airport = lt.get("airport_to_city", {})
    if isinstance(airport, dict):
        out.append(_kv("Airport trains", airport.get("trains")))
        out.append(_kv("Airport buses", airport.get("buses")))
        out.append(_kv("Taxi note", airport.get("taxi_note")))
    return "".join(out)


def _render_faq(faq: Iterable[Dict[str, Any]]) -> str:
    faq = list(faq or [])
    if not faq:
        return ""
    out = [_section("FAQ Examples")]
    for i, item in enumerate(faq, 1):
        q_en, a_en = item.get("q_en"), item.get("a_en")
        q_fi, a_fi = item.get("q_fi"), item.get("a_fi")
        if q_en and a_en:
            out.append(f"- EN Q{i}: {q_en}\n  EN A{i}: {a_en}\n")
        if q_fi and a_fi:
            out.append(f"- FI K{i}: {q_fi}\n  FI V{i}: {a_fi}\n")
    return "".join(out)


def _render_escalation(esc: Dict[str, Any]) -> str:
    if not esc:
        return ""
    out = [_section("Escalation Templates")]
    if esc.get("en"):
        out.append(_kv("EN", esc.get("en").strip()))
    if esc.get("fi"):
        out.append(_kv("FI", esc.get("fi").strip()))
    return "".join(out)


def _looks_like_hotel(kb: Dict[str, Any]) -> bool:
    if not isinstance(kb, dict):
        return False
    # Heuristic: must have at least one hotel‑specific key
    return any(k in kb for k in ("meta", "policies", "amenities", "location_transport", "faq_examples"))


def kb_to_text(kb: Dict[str, Any]) -> str:
    """
    Render hotel JSON into prompt text.
    Falls back to generic str() if schema is unknown.
    """
    if _looks_like_hotel(kb):
        parts = []
        parts.append(_render_meta(kb.get("meta", {})))
        parts.append(_render_policies(kb.get("policies", {})))
        parts.append(_render_amenities(kb.get("amenities", {})))
        parts.append(_render_location(kb.get("location_transport", {})))
        parts.append(_render_faq(kb.get("faq_examples", [])))
        parts.append(_render_escalation(kb.get("escalation_templates", {})))
        # Join and strip extra blank lines
        return "".join([p for p in parts if p]).strip()

    # Fallback for unknown schemas (keeps your bakery app from crashing)
    return str(kb)

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from app.settings import get_settings
from mcp_server import book_test_slot, get_test_slot, list_test_slots

REQUIRED_CANDIDATE_FIELDS = {
    "first_name": "first name",
    "last_name": "last name",
    "email": "email",
    "phone": "phone number",
    "passport_number": "passport number",
}


def handle_booking_chat(message: str, session: dict[str, Any], selected_slot_id: int | None = None) -> dict[str, Any]:
    clean_message = message.strip()
    session = dict(session or {})
    candidate = dict(session.get("candidate") or {})
    session["candidate"] = candidate

    if selected_slot_id:
        session["slot_id"] = selected_slot_id

    _capture_candidate_details(clean_message, session)

    lowered = clean_message.lower()
    wants_slots = any(word in lowered for word in ["slot", "available", "availability", "date", "center", "test"])
    wants_booking = any(word in lowered for word in ["book", "reserve", "confirm", "schedule"])

    if wants_slots and not wants_booking:
        slots = _find_slots(clean_message)
        session["last_slots"] = slots
        reply = _ai_reply(
            clean_message,
            f"Found {len(slots)} IELTS test slot(s). Ask the user to choose one by slot ID or city.",
            slots=slots,
        )
        return {"reply": reply, "session": session, "slots": slots, "booking": None}

    chosen_slot_id = _resolve_slot_id(clean_message, session)
    if chosen_slot_id:
        session["slot_id"] = chosen_slot_id
        slot = get_test_slot(chosen_slot_id)
        reply = _ai_reply(
            clean_message,
            f"Selected slot {slot['id']} at {slot['test_center_name']} in {slot['city']}. Ask for missing candidate details.",
            slots=[slot],
        )
        missing = _missing_candidate_fields(session)
        if missing:
            reply = f"{reply} I still need your {', '.join(missing)}."
        return {"reply": reply, "session": session, "slots": [slot], "booking": None}

    if wants_booking or session.get("slot_id"):
        missing = _missing_candidate_fields(session)
        if missing:
            reply = _ai_reply(
                clean_message,
                f"The user wants to book, but these candidate fields are missing: {', '.join(missing)}. Ask for them clearly.",
            )
            return {"reply": reply, "session": session, "slots": None, "booking": None}

        if not session.get("slot_id"):
            slots = _find_slots(clean_message)
            session["last_slots"] = slots
            return {
                "reply": "I can book that. Please choose one of these slots by its slot ID first.",
                "session": session,
                "slots": slots,
                "booking": None,
            }

        booking = book_test_slot(int(session["slot_id"]), candidate)
        session["booking_reference"] = booking["booking"]["booking_reference"]
        reply = _ai_reply(
            clean_message,
            (
                "The booking was created successfully. Mention the booking reference "
                f"{booking['booking']['booking_reference']} and remaining seats {booking['slot_remaining_seats']}."
            ),
        )
        return {"reply": reply, "session": session, "slots": None, "booking": booking}

    return {
        "reply": _ai_reply(
            clean_message,
            "Explain that you can list IELTS test slots and book a selected slot through chat.",
        ),
        "session": session,
        "slots": None,
        "booking": None,
    }


def _find_slots(message: str) -> list[dict[str, Any]]:
    city = _extract_city(message)
    test_date = _extract_date(message)
    return list_test_slots(city=city, test_date=test_date)


def _extract_city(message: str) -> str | None:
    known_cities = {"chennai": "Chennai", "bangalore": "Bangalore", "bengaluru": "Bangalore"}
    lowered = message.lower()
    for key, city in known_cities.items():
        if key in lowered:
            return city
    return None


def _extract_date(message: str) -> str | None:
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", message)
    return match.group(1) if match else None


def _resolve_slot_id(message: str, session: dict[str, Any]) -> int | None:
    explicit = re.search(r"\b(?:slot\s*)?#?(\d{1,6})\b", message.lower())
    if explicit and any(word in message.lower() for word in ["slot", "book", "select", "choose", "#"]):
        return int(explicit.group(1))

    last_slots = session.get("last_slots") or []
    if len(last_slots) == 1 and any(word in message.lower() for word in ["yes", "book", "select", "choose", "confirm"]):
        return int(last_slots[0]["id"])

    return None


def _capture_candidate_details(message: str, session: dict[str, Any]) -> None:
    candidate = session["candidate"]

    patterns = {
        "email": r"[\w.+-]+@[\w-]+\.[\w.-]+",
        "phone": r"(?:\+?\d[\d\s().-]{6,}\d)",
    }
    for field, pattern in patterns.items():
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match and field not in candidate:
            candidate[field] = match.group(0).strip()

    passport_match = re.search(
        r"(?:passport(?:\s+number)?\s*(?:is|:)?\s*)([A-Z0-9]{5,12})",
        message,
        flags=re.IGNORECASE,
    )
    if passport_match:
        candidate["passport_number"] = passport_match.group(1).upper()

    name_match = re.search(r"(?:my name is|name is|i am|i'm)\s+([a-zA-Z]+)\s+([a-zA-Z]+)", message, flags=re.IGNORECASE)
    if name_match:
        candidate.setdefault("first_name", name_match.group(1).title())
        candidate.setdefault("last_name", name_match.group(2).title())

    for field, label in REQUIRED_CANDIDATE_FIELDS.items():
        field_match = re.search(rf"{label}\s*(?:is|:)\s*([^\n,]+)", message, flags=re.IGNORECASE)
        if field_match:
            value = field_match.group(1).strip()
            candidate[field] = value.title() if field.endswith("name") else value


def _missing_candidate_fields(session: dict[str, Any]) -> list[str]:
    candidate = session.get("candidate") or {}
    return [label for field, label in REQUIRED_CANDIDATE_FIELDS.items() if not candidate.get(field)]


def _ai_reply(user_message: str, tool_result: str, slots: list[dict[str, Any]] | None = None) -> str:
    settings = get_settings()
    prompt = (
        "You are an IELTS test booking assistant. Keep replies short, friendly, and action-oriented.\n"
        f"User message: {user_message}\n"
        f"Tool result: {tool_result}\n"
    )
    if slots:
        prompt += f"Slots JSON: {json.dumps(slots[:5], default=str)}\n"

    generated = _call_local_model(settings.local_ai_base_url, settings.local_ai_model, settings.local_ai_api_key, prompt)
    if generated:
        return generated

    if slots:
        slot_lines = [
            f"#{slot['id']} {slot['city']} {slot['test_type']} on {slot['test_date']} at {slot['test_time'][:5]} ({slot['available_seats']} seats)"
            for slot in slots[:5]
        ]
        return "Here are the matching slots: " + "; ".join(slot_lines)

    if "list IELTS test slots" in tool_result:
        return "I can show IELTS test slots by city or date, help you pick one, and create the booking once you share your name, email, phone, and passport number."

    return tool_result


def _call_local_model(base_url: str, model: str, api_key: str, prompt: str) -> str | None:
    return _call_ollama(base_url, model, prompt) or _call_openai_compatible(base_url, model, api_key, prompt)


def _call_ollama(base_url: str, model: str, prompt: str) -> str | None:
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            data = json.loads(response.read().decode())
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    return (data.get("response") or "").strip() or None


def _call_openai_compatible(base_url: str, model: str, api_key: str, prompt: str) -> str | None:
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a concise IELTS booking assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
    ).encode()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            data = json.loads(response.read().decode())
    except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    choices = data.get("choices") or []
    if not choices:
        return None
    return ((choices[0].get("message") or {}).get("content") or "").strip() or None

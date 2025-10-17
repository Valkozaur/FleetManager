import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class AddressSimplifier:
    """Utility to simplify verbose addresses for reliable geocoding and to validate strict matches.

    The goal is to keep street-level details (street/number or company/location name),
    postal code, city and country while removing long descriptive fragments that
    commonly break geocoding results (e.g. warehouse descriptions after colons).
    """

    COMPANY_SUFFIXES = [
        r"\bАД\b",
        r"\bООД\b",
        r"\bASA\b",
        r"\bAS\b",
        r"\bA/S\b",
        r"\bLtd\b",
        r"\bGmbH\b",
        r"\bInc\b",
        r"\bCorp\b",
        r"\bLLC\b",
    ]

    @staticmethod
    def simplify_address(address: str) -> str:
        if not address:
            return address

        addr = address.strip()

        # Remove anything after colon or semicolon which often contains unhelpful descriptions
        addr = re.split(r"[:;]", addr)[0].strip()

        # Normalize multiple spaces
        addr = re.sub(r"\s+", " ", addr)

        # Remove trailing company suffix tokens that don't help geocoding (e.g. ", АД")
        for suffix in AddressSimplifier.COMPANY_SUFFIXES:
            addr = re.sub(rf",?\s*{suffix}(?=,|$)", "", addr, flags=re.IGNORECASE)

        addr = addr.strip().strip(',')

        # If we can find a country code + postal code + city pattern (e.g. "BG 7000 Русе")
        # prioritize and return a minimal address containing that plus one meaningful token before it
        bg_match = re.search(r"\b([A-Z]{2})\s*(\d{4,5})\s*,?\s*([\w\-\u0400-\u04FF]+)", addr)
        if bg_match:
            country, postal, city = bg_match.groups()
            # Try to capture a meaningful token before postal block (like company or street)
            before = addr[:bg_match.start()].strip().rstrip(',')
            if before:
                last_before = [p.strip() for p in before.split(',') if p.strip()][-1]
                return f"{country} {postal} {city}, {last_before}"
            return f"{country} {postal} {city}"

        # International (e.g. '9340 Asaa, Denmark' or 'Saebyvej 3, 9340 Asaa, Denmark')
        intl_match = re.search(r"(\d{4,5})\s*,?\s*([A-Za-z\-\s]+)\s*,?\s*([A-Za-z\s]+)$", addr)
        if intl_match:
            postal, city, country = intl_match.groups()
            # Try to keep street/company part if present
            before = addr[:intl_match.start()].strip().rstrip(',')
            if before:
                return f"{before}, {postal} {city}, {country}"
            return f"{postal} {city}, {country}"

        # Fallback: remove very long trailing descriptions but keep first two comma-separated parts
        parts = [p.strip() for p in addr.split(',') if p.strip()]
        if len(parts) > 2:
            return ", ".join(parts[:2])

        return addr

    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        # Normalize spaces and punctuation
        text = re.sub(r"[\s]+", " ", text)
        text = text.strip()
        return text

    @staticmethod
    def is_strict_match(cleaned_address: str, formatted_address: str) -> bool:
        """Return True if the formatted_address from the geocoder appears to contain
        the key components of the cleaned_address in a way that indicates an exact/close match.

        Criteria used:
        - The postal code (if present) must be present in formatted_address OR
          the city name must be present.
        - At least one of: street name / company token / house number must be present.
        This avoids accepting city-only matches.
        """
        if not cleaned_address or not formatted_address:
            return False

        c = AddressSimplifier._normalize(cleaned_address)
        f = AddressSimplifier._normalize(formatted_address)

        # Extract postal code (4-5 digits)
        postal_match = re.search(r"(\d{4,5})", c)
        city_tokens = [t for t in re.split(r",|\s", c) if t and not t.isdigit()]

        has_postal = False
        if postal_match:
            postal = postal_match.group(1)
            if postal in f:
                has_postal = True

        # Try to find city by looking for the longest non-numeric token (likely the city)
        city_found = False
        if city_tokens:
            # prefer tokens with cyrillic or alpha characters longer than 2
            candidates = [t for t in city_tokens if len(t) > 2]
            for token in candidates:
                if token in f:
                    city_found = True
                    break

        # Check for at least one additional token (street or company) present
        other_tokens = [t.strip() for t in c.split(',') if t.strip()]
        other_tokens = [t for t in other_tokens if not re.search(r"^\d{4,5}$", t)]

        has_other = False
        for tok in other_tokens:
            tok_norm = tok
            if len(tok_norm) >= 3 and tok_norm in f:
                has_other = True
                break

        # Require (postal or city) AND at least one other token (street/company)
        if (has_postal or city_found) and has_other:
            return True

        return False

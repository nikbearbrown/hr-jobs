"""Read a location string well enough to answer two questions: is this job in the United States, and where?

No geocoding. A place the string does not settle stays 'unknown' and the listing is kept, not guessed about.
"""
import re

STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts",
    "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
    "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "PR": "Puerto Rico", "GU": "Guam",
}
_BY_NAME = {v.lower(): k for k, v in STATES.items()}
_US = re.compile(r"\b(United States( of America)?|USA|U\.S\.A?\.?)(?![a-z])|\bUS\b|\bAmericas?\b")
# Cities that employers write without a state. Each is unambiguous enough in a US job listing.
CITY_STATE = {
    "new york": "NY", "new york city": "NY", "nyc": "NY", "brooklyn": "NY", "san francisco": "CA",
    "sf bay area": "CA", "bay area": "CA", "los angeles": "CA", "palo alto": "CA", "mountain view": "CA",
    "san jose": "CA", "san diego": "CA", "menlo park": "CA", "sunnyvale": "CA", "santa clara": "CA",
    "redwood city": "CA", "san mateo": "CA", "seattle": "WA", "bellevue": "WA", "boston": "MA",
    "chicago": "IL", "austin": "TX", "dallas": "TX", "houston": "TX", "denver": "CO", "atlanta": "GA",
    "miami": "FL", "philadelphia": "PA", "pittsburgh": "PA", "phoenix": "AZ", "salt lake city": "UT",
    "nashville": "TN", "raleigh": "NC",
}
_CITY_NAME = {"nyc": "New York", "new york city": "New York", "sf bay area": "", "bay area": ""}
_US_CITY = re.compile(r"\b(" + "|".join(sorted(map(re.escape, CITY_STATE), key=len, reverse=True)) + r")\b", re.I)
_FOREIGN = re.compile(
    r"\b(canada|united kingdom|uk|england|scotland|ireland|india|germany|france|spain|portugal|italy|"
    r"netherlands|belgium|switzerland|austria|sweden|norway|denmark|finland|poland|romania|czech|hungary|"
    r"ukraine|turkey|israel|uae|united arab emirates|saudi arabia|egypt|south africa|nigeria|kenya|japan|"
    r"china|hong kong|taiwan|korea|singapore|malaysia|indonesia|philippines|vietnam|thailand|australia|"
    r"new zealand|mexico|brazil|argentina|chile|colombia|peru|costa rica|emea|apac|latam|europe|asia|"
    r"london|dublin|berlin|munich|paris|amsterdam|madrid|barcelona|lisbon|zurich|stockholm|warsaw|"
    r"tel aviv|dubai|bangalore|bengaluru|hyderabad|mumbai|pune|gurgaon|gurugram|new delhi|delhi|chennai|"
    r"tokyo|seoul|shanghai|beijing|shenzhen|sydney|melbourne|toronto|vancouver|montreal|ottawa|"
    r"mexico city|sao paulo|são paulo|bogota|bogotá|buenos aires|manila|jakarta|kuala lumpur|"
    r"ontario|quebec|british columbia|alberta)\b", re.I)
_CITY_COUNTRY = {"bangalore": "IN", "bengaluru": "IN", "hyderabad": "IN", "mumbai": "IN", "pune": "IN",
                 "gurgaon": "IN", "gurugram": "IN", "new delhi": "IN", "delhi": "IN", "chennai": "IN",
                 "berlin": "DE", "munich": "DE", "toronto": "CA", "vancouver": "CA", "montreal": "CA",
                 "ottawa": "CA", "tel aviv": "IL", "bogota": "CO", "bogotá": "CO", "buenos aires": "AR",
                 "jakarta": "ID"}
_CA_PROV = {"ON", "BC", "QC", "AB", "MB", "SK", "NS", "NB", "NL", "PE"}
_REMOTE = re.compile(r"\bremote\b|\bwork from home\b|\bdistributed\b|\banywhere\b", re.I)


def read_place(text):
    """One location string -> (country, city, state). country is 'US', 'other' or 'unknown'."""
    s = re.sub(r"\([^)]*\)", " ", text or "")                      # "(HQ)", "(Remote)"
    s = re.sub(r"\b(D\.C\.|D\.C)(?![a-z])", "DC", s)
    s = re.sub(r"\b([A-Za-z]{2}) \d{5}(-\d{4})?\b", r"\1", s).strip()   # "IL 60607" -> "IL"
    if not s:
        return "unknown", "", ""
    parts = [p.strip() for p in re.split(r",|\s[-–|/•]\s|[-–]\s", s) if p.strip()]
    parts = [p for p in parts if not re.fullmatch(r"(hybrid|remote|onsite|on-site|in office)", p, re.I)] or parts
    city, state = "", ""
    for i, p in enumerate(parts):
        code = p.upper().rstrip(".")
        if code in _CA_PROV and i > 0:
            return "other", parts[0], ""
        if state:
            break   # several places in one string: the first one counts
        if code in STATES and (i > 0 or (len(parts) == 1 and p.isupper())):
            state = code
        elif p.lower() in _BY_NAME and not (i == 0 and len(parts) > 1 and p.lower() in ("new york", "washington")):
            state = _BY_NAME[p.lower()]
    if state:
        first = parts[0]
        only_state = first.upper() == state or (len(parts) == 1 and first.lower() in _BY_NAME)
        city = "" if only_state or _REMOTE.search(first) or _US.search(first) else first
        if len(parts) == 1 and first.lower() == "new york":   # alone, "New York" means the city
            city = "New York"
    said_us = bool(_US.search(s))
    foreign = bool(_FOREIGN.search(s))
    # "Bangalore, IN" is India and "Toronto, CA" is Canada, but "Dublin, CA" is California.
    collides = len(parts) == 2 and not said_us and _CITY_COUNTRY.get(parts[0].lower()) == state
    if state and not collides:
        return "US", city, state
    if said_us:
        m = _US_CITY.search(s)
        name = m.group(1).lower() if m else ""
        return "US", _CITY_NAME.get(name, name.title()), CITY_STATE.get(name, "")
    if foreign:
        return "other", "", ""
    m = _US_CITY.search(s)
    if m:
        name = m.group(1).lower()
        return "US", _CITY_NAME.get(name, name.title()), CITY_STATE[name]
    return "unknown", "", ""


def summarise(locations, country_codes=(), workplace=None, title=""):
    """All of a listing's locations -> dict(country, city, state, remote, places).

    country: 'US' if any location is in the US, 'other' if every location is settled and none is, else 'unknown'.
    """
    codes = {c.upper() for c in country_codes if c}
    reads = [read_place(l) for l in locations if l]
    us = [r for r in reads if r[0] == "US"]
    if us or codes & {"US", "USA", "UNITED STATES"}:
        country = "US"
    elif codes or (reads and all(r[0] == "other" for r in reads)):
        country = "other"
    else:
        country = "unknown"
    best = next((r for r in us if r[2]), us[0] if us else ("", "", ""))
    text = " ".join([title or ""] + [l for l in locations if l])
    remote = workplace or ("remote" if _REMOTE.search(text) else ("hybrid" if re.search(r"\bhybrid\b", text, re.I) else ""))
    shown = [l for l in locations if l][:4]
    places = "; ".join(shown) + (f"; +{len(locations) - 4} more" if len(locations) > 4 else "")
    return {"country": country, "city": best[1], "state": best[2], "remote": remote, "places": places}

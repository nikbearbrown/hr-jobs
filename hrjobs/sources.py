"""Readers for each source. Every reader yields plain dicts with the same keys (see RAW_KEYS); a field the
source did not state is "" or [], never guessed. 'description' is used in memory to classify generic titles
and is never written to disk."""
import datetime
import html
import os
import re
from pathlib import Path
from urllib.parse import quote, urlencode

from .http import get_json

RAW_KEYS = ("source", "board", "source_id", "title", "employer", "department", "locations", "country_codes",
            "workplace", "posted", "closes", "requisition", "salary", "url", "description", "grade", "open_to")
SOURCE_PRIORITY = ["usajobs", "greenhouse", "lever", "ashby", "adzuna"]   # docs/hr-job-search.md, Part 2


def _raw(**kw):
    rec = {k: ([] if k in ("locations", "country_codes") else "") for k in RAW_KEYS}
    rec.update({k: v for k, v in kw.items() if v not in (None, "")})
    return rec


def _text(markup):
    """HTML (possibly entity-escaped) -> plain text."""
    t = html.unescape(html.unescape(markup or ""))
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t)).strip()


def _day(value):
    """Any ISO-like timestamp -> YYYY-MM-DD ('' when absent)."""
    m = re.match(r"\d{4}-\d{2}-\d{2}", str(value or ""))
    return m.group(0) if m else ""


def _day_from_ms(ms):
    if not ms:
        return ""
    return datetime.datetime.fromtimestamp(int(ms) / 1000, datetime.timezone.utc).strftime("%Y-%m-%d")


def _money(low, high, currency="USD", per="year"):
    def f(v):
        return f"{float(v):,.0f}" if float(v) >= 1000 else f"{float(v):,.2f}"
    try:
        if low and high and float(low) != float(high):
            body = f"{f(low)}-{f(high)}"
        else:
            body = f(low or high)
    except (TypeError, ValueError):
        return ""
    return f"{currency or 'USD'} {body} per {per or 'year'}"


_WORKPLACE = {"on-site": "onsite", "onsite": "onsite", "on site": "onsite", "hybrid": "hybrid", "remote": "remote"}


# ---- company boards: Greenhouse, Lever, Ashby -------------------------------------------------

def board_url(provider, slug):
    return {"greenhouse": f"https://boards-api.greenhouse.io/v1/boards/{quote(slug)}/jobs?content=true",
            "lever": f"https://api.lever.co/v0/postings/{quote(slug)}?mode=json",
            "ashby": f"https://api.ashbyhq.com/posting-api/job-board/{quote(slug)}?includeCompensation=true"}[provider]


def _greenhouse(data, slug, employer):
    for j in data.get("jobs", []):
        depts = [d.get("name") for d in j.get("departments") or [] if isinstance(d, dict) and d.get("name")]
        loc = (j.get("location") or {}).get("name") or ""
        yield _raw(source="greenhouse", board=slug, source_id=str(j["id"]), title=j.get("title"), employer=employer,
                   department=depts[0] if depts else "",
                   locations=[s.strip() for s in re.split(r"\s*\|\s*|;\s*|\s+or\s+", loc) if s.strip()],
                   posted=_day(j.get("first_published") or j.get("updated_at")),
                   requisition=str(j.get("requisition_id") or ""), url=j.get("absolute_url"),
                   description=_text(j.get("content")))


def _lever(data, slug, employer):
    for j in data if isinstance(data, list) else []:
        c = j.get("categories") or {}
        sal = j.get("salaryRange") or {}
        per = {"per-year-salary": "year", "per-hour-wage": "hour", "per-month-salary": "month"}.get(sal.get("interval"), "year")
        lists = " ".join(f"{l.get('text', '')} {_text(l.get('content'))}" for l in j.get("lists") or [] if isinstance(l, dict))
        yield _raw(source="lever", board=slug, source_id=str(j["id"]), title=j.get("text"), employer=employer,
                   department=c.get("department") or c.get("team") or "",
                   locations=list(c.get("allLocations") or ([c["location"]] if c.get("location") else [])),
                   country_codes=[j["country"]] if j.get("country") else [],
                   workplace=_WORKPLACE.get(str(j.get("workplaceType") or "").lower(), ""),
                   posted=_day_from_ms(j.get("createdAt")),
                   salary=_money(sal.get("min"), sal.get("max"), sal.get("currency"), per) if sal.get("min") or sal.get("max") else "",
                   url=j.get("hostedUrl"), description=f"{j.get('descriptionPlain') or ''} {lists}".strip())


def _ashby(data, slug, employer):
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        def place(name, address):
            a = (address or {}).get("postalAddress") or {}
            parts = [a.get("addressLocality"), a.get("addressRegion"), a.get("addressCountry")]
            return ", ".join(p for p in parts if p) or name or ""
        locs = [place(j.get("location"), j.get("address"))]
        for s in j.get("secondaryLocations") or []:
            if isinstance(s, dict):
                locs.append(place(s.get("location"), s.get("address")))
        salary = ""
        for part in (j.get("compensation") or {}).get("summaryComponents") or []:
            if isinstance(part, dict) and part.get("compensationType") == "Salary" and (part.get("minValue") or part.get("maxValue")):
                per = {"1 YEAR": "year", "1 HOUR": "hour", "1 MONTH": "month"}.get(str(part.get("interval", "")).upper(), "year")
                salary = _money(part.get("minValue"), part.get("maxValue"), part.get("currencyCode"), per)
                break
        wp = _WORKPLACE.get(str(j.get("workplaceType") or "").lower(), "") or ("remote" if j.get("isRemote") else "")
        yield _raw(source="ashby", board=slug, source_id=str(j["id"]), title=j.get("title"), employer=employer,
                   department=j.get("department") or j.get("team") or "", locations=[l for l in locs if l],
                   workplace=wp, posted=_day(j.get("publishedAt")), salary=salary, url=j.get("jobUrl"),
                   description=j.get("descriptionPlain") or "")


_BOARD_READERS = {"greenhouse": _greenhouse, "lever": _lever, "ashby": _ashby}


def read_board(provider, slug, employer):
    """Returns (ok, records). A failed read is ok=False, never an empty-looking success."""
    status, data = get_json(board_url(provider, slug))
    if status != 200 or data is None:
        return False, []
    try:
        return True, list(_BOARD_READERS[provider](data, slug, employer))
    except (KeyError, TypeError, AttributeError):
        return False, []


# ---- USAJOBS ---------------------------------------------------------------------------------
USAJOBS_SERIES = "0201;0203"   # HR Specialist; HR Assistant


def _secret(env, path):
    v = os.environ.get(env)
    if v:
        return v.strip()
    p = Path.home() / path
    return p.read_text().strip() if p.is_file() else ""


def usajobs_credentials():
    """(email, key) from HRJOBS_USAJOBS_EMAIL / HRJOBS_USAJOBS_KEY or ~/.usajobs/email and ~/.usajobs/key."""
    return _secret("HRJOBS_USAJOBS_EMAIL", ".usajobs/email"), _secret("HRJOBS_USAJOBS_KEY", ".usajobs/key")


def _usajobs_record(item):
    d = item.get("MatchedObjectDescriptor") or {}
    det = (d.get("UserArea") or {}).get("Details") or {}
    locs, codes = [], []
    for l in d.get("PositionLocation") or []:
        city = re.sub(r",\s*[^,]+$", "", l.get("CityName") or "") or l.get("LocationName") or ""
        country = l.get("CountryCode") or ""
        if country == "United States":
            state = l.get("CountrySubDivisionCode") or ""
            name = (l.get("CityName") or l.get("LocationName") or "").strip()
            locs.append(name if "," in name else ", ".join(p for p in (city, state) if p))
            codes.append("US")
        else:
            locs.append(l.get("LocationName") or city)
            codes.append(country or "")
    pay = (d.get("PositionRemuneration") or [{}])[0]
    per = {"PA": "year", "PH": "hour", "PD": "day", "PM": "month", "BW": "two weeks"}.get(pay.get("RateIntervalCode"), "year")
    low, high = det.get("LowGrade"), det.get("HighGrade")
    plan = ((d.get("JobGrade") or [{}])[0].get("Code") or "").upper()
    grade = ""
    if plan and low:
        grade = f"{plan}-{low}" + (f" to {plan}-{high}" if high and high != low else "")
    duties = det.get("MajorDuties")
    duties = " ".join(duties) if isinstance(duties, list) else (duties or "")
    remote = "remote" if str(det.get("RemoteIndicator")).lower() == "true" else ""
    return _raw(source="usajobs", board="0201-0203", source_id=str(item.get("MatchedObjectId") or ""),
                title=d.get("PositionTitle"), employer=d.get("OrganizationName") or d.get("DepartmentName"),
                department=d.get("DepartmentName"), locations=locs, country_codes=[c for c in codes if c],
                workplace=remote, posted=_day(d.get("PublicationStartDate")), closes=_day(d.get("ApplicationCloseDate")),
                requisition=d.get("PositionID"), salary=_money(pay.get("MinimumRange"), pay.get("MaximumRange"), "USD", per)
                if pay.get("MinimumRange") or pay.get("MaximumRange") else "",
                url=d.get("PositionURI"), description=f"{_text(det.get('JobSummary'))} {_text(duties)}".strip(),
                grade=grade, open_to="; ".join(det.get("HiringPath") or []))


def read_usajobs(max_pages=20, page_size=500):
    """Every open federal posting in series 0201 and 0203. Returns (status, records); status is 'ok',
    'no key' or a failure note. A failed page fails the whole read: no partial lists."""
    email, key = usajobs_credentials()
    if not (email and key):
        return "no key", []
    headers = {"Host": "data.usajobs.gov", "User-Agent": email, "Authorization-Key": key}
    out, total = [], None
    for page in range(1, max_pages + 1):
        q = urlencode({"JobCategoryCode": USAJOBS_SERIES, "WhoMayApply": "All", "ResultsPerPage": page_size, "Page": page})
        status, data = get_json("https://data.usajobs.gov/api/search?" + q, headers=headers)
        result = (data or {}).get("SearchResult") if status == 200 else None
        if not isinstance(result, dict):
            return f"failed (HTTP {status} on page {page})", []
        total = int(result.get("SearchResultCountAll") or 0)
        items = result.get("SearchResultItems") or []
        out.extend(_usajobs_record(i) for i in items)
        if len(out) >= total or not items:
            return "ok", out
    return f"failed (more than {max_pages} pages)", []


# ---- Adzuna ----------------------------------------------------------------------------------

def adzuna_credentials():
    """(app_id, app_key) from HRJOBS_ADZUNA_APP_ID / HRJOBS_ADZUNA_APP_KEY or ~/.adzuna/app_id and ~/.adzuna/app_key."""
    return _secret("HRJOBS_ADZUNA_APP_ID", ".adzuna/app_id"), _secret("HRJOBS_ADZUNA_APP_KEY", ".adzuna/app_key")


def _adzuna_record(j):
    area = (j.get("location") or {}).get("area") or []   # ["US", "California", "San Francisco County", "San Francisco"]
    place = ", ".join(p for p in ((area[-1] if len(area) > 2 else ""), (area[1] if len(area) > 1 else "")) if p)
    low, high = j.get("salary_min"), j.get("salary_max")
    predicted = str(j.get("salary_is_predicted")) == "1"   # Adzuna's own estimate is not a posted salary
    return _raw(source="adzuna", board="us/hr-jobs", source_id=str(j.get("id") or ""), title=_text(j.get("title")),
                employer=(j.get("company") or {}).get("display_name"), locations=[place or (j.get("location") or {}).get("display_name", "")],
                country_codes=["US"], posted=_day(j.get("created")),
                salary=_money(low, high) if (low or high) and not predicted else "",
                url=j.get("redirect_url"), description=_text(j.get("description")))


def read_adzuna(max_pages=40, page_size=50):
    """Newest listings in Adzuna's US 'HR & Recruitment' category. Untested against the live API: no key yet."""
    app_id, app_key = adzuna_credentials()
    if not (app_id and app_key):
        return "no key", []
    out = []
    for page in range(1, max_pages + 1):
        q = urlencode({"app_id": app_id, "app_key": app_key, "category": "hr-jobs", "results_per_page": page_size,
                       "sort_by": "date", "content-type": "application/json"})
        status, data = get_json(f"https://api.adzuna.com/v1/api/jobs/us/search/{page}?{q}")
        if status != 200 or not isinstance(data, dict):
            return f"failed (HTTP {status} on page {page})", []
        results = data.get("results") or []
        out.extend(_adzuna_record(j) for j in results)
        if len(results) < page_size:
            break
    return "ok", out

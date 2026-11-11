"""Scope, classify and annotate HR job listings.

The rules come from docs/hr-job-search.md (the sub-discipline list and its order) and docs/hr-job-titles.md
(role words, levels, sector titles and the titles that mislead). Three steps, always in this order:

1. scope     is this listing an HR job at all?  (source, department or a strong title term)
2. classify  which one sub-discipline?           (title first, then the ad text, else "unclassified")
3. annotate  role word, level, O*NET-SOC code and warning flags

A hand annotation in annotations/overrides.csv beats all of it (see collect.py).
"""
import re

# ---- text ------------------------------------------------------------------------------------

def norm(text):
    """Lowercase, '&' -> 'and', punctuation -> spaces. 'L&D Manager (Remote)' -> 'l and d manager remote'."""
    t = (text or "").lower().replace("&", " and ")
    t = re.sub(r"(/\s*|\bper |\ban |\d\s*)hrs?\b", " ", t)   # "$17/hr", "40 hrs" are pay and hours, not HR
    t = re.sub(r"[^a-z0-9+]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _rx(terms):
    """Whole-word match for each term. A trailing '*' lets the word continue ('investigat*' matches investigator).
    Whole words matter: the plain substring 'er specialist' would match 'customer specialist'."""
    parts = []
    for term in terms:
        stem = term.endswith("*")
        body = re.escape(norm(term.rstrip("*")))
        parts.append(body + ("" if stem else r"(?![a-z0-9])"))
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(parts) + ")")


# ---- step 2 tables: the order is the rule ----------------------------------------------------
# Specific functions first, generalist last, because "HR" is in nearly every title (docs/hr-job-search.md).
SUBDISCIPLINES = [
    ("academic_personnel", ["academic personnel", "academic hr", "faculty affairs", "academic affairs personnel"]),
    # Not one of the thirteen in the search document's classifier. That document names military HR as a
    # sector-specific version of the work, and about a fifth of federal HR postings carry "(Military)".
    ("military_hr", ["military", "mil"]),
    ("labor_relations", ["labor relations", "labour relations", "labor and employee relations",
                         "employee and labor relations", "chief negotiator", "collective bargaining"]),
    ("employee_relations", ["employee relations", "er specialist", "er consultant", "er investigator", "er manager",
                            "workplace investigat*", "hr investigat*"]),
    ("eeo", ["equal employment", "equal opportunity", "eeo", "affirmative action", "hr compliance"]),
    ("compensation", ["compensation", "classification", "total rewards", "job analyst", "equity plan",
                      "stock plan", "equity administrator", "rewards analyst", "rewards manager"]),
    ("benefits_leave", ["benefits", "leave of absence", "leave administrator", "leave specialist",
                        "leave management", "disability management", "accommodation*", "fmla",
                        "retirement plan", "wellness program", "wellbeing program"]),
    ("talent_acquisition", ["recruiter", "recruiters", "recruitment", "recruiting", "talent acquisition", "sourcer",
                            "talent sourc*", "placement", "employer brand", "employer branding",
                            "talent partner", "head of talent", "staffing specialist", "staffing"]),
    ("learning_od", ["learning and development", "l and d", "training", "trainer", "organizational development",
                     "organization development", "organisational development", "talent development",
                     "talent management", "instructional design*", "leadership development",
                     "learning experience", "learning program*", "learning specialist", "learning manager",
                     "learning partner", "employee engagement", "human resource development",
                     "human resources development", "hr development", "enablement"]),
    ("hris_analytics", ["hris", "people analytics", "workday", "hr systems", "information systems",
                        "hr technology", "people technology", "people systems", "hcm", "successfactors", "ukg",
                        "hr analytics", "workforce analytics", "people data", "people insights", "hr data",
                        "people science", "people research"]),
    ("payroll", ["payroll"]),
    ("hr_operations", ["hr coordinator", "hr assistant", "human resources coordinator",
                       "human resources assistant", "human resources assistance", "hr asst", "human resources asst",
                       "shared services",
                       "hr operations", "human resources operations", "people operations", "people ops",
                       "people coordinator", "people operations coordinator", "onboarding", "hr service*",
                       "hr administrator", "hr associate", "personnel technician", "global mobility",
                       "immigration", "people experience", "employee experience"]),
    ("hr_strategy", ["workforce planning", "hr policy", "chief people", "chief human resources", "chro",
                     "hr director", "human resources director", "director of human resources",
                     "director human resources", "director of hr", "director of people", "director people",
                     "vp of people", "vp people", "vp of hr", "vp hr", "vp human resources",
                     "vice president of people", "vice president people", "vice president of human resources",
                     "vice president human resources", "head of people", "head of hr",
                     "head of human resources", "people strategy", "hr strategy", "human capital officer",
                     "human resources officer", "hr officer", "policy planning"]),
    # The titles document files inclusion work with EEO. These words are checked late so that a job naming
    # another function too ("Learning and Inclusion Designer") goes to that function.
    ("eeo", ["diversity", "inclusion", "belonging", "dei", "deib"]),
    ("generalist", ["generalist", "business partner", "business partnering", "people partner", "hr partner",
                    "human resources partner", "hrbp", "hr manager", "human resources manager",
                    "people and culture manager", "people manager hr"]),
]
ORDER = list(dict.fromkeys(name for name, _ in SUBDISCIPLINES)) + ["unclassified"]
_TITLE_RX = [(name, _rx(terms)) for name, terms in SUBDISCIPLINES]

_MILITARY_HIRING = _rx(["recruiter", "recruiting", "veteran", "veterans", "talent acquisition", "sourcer"])

# A title that only says "HR" is too generic to classify ("HR Analyst III", "Human Resources Specialist").
GENERIC_HR = _rx(["human resources", "human resource", "hr", "people", "personnel", "talent", "human capital",
                  "people and culture"])

# Phrases that tell the function when they appear in the ad text. Deliberately not single common words:
# every ad says "benefits", "compensation" and "training" somewhere.
DESCRIPTION_TERMS = {
    "academic_personnel": ["academic personnel", "faculty appointments", "promotion and tenure", "faculty affairs"],
    "military_hr": ["military personnel", "service members", "soldier*", "airmen", "military pay",
                    "strength management", "personnel readiness"],
    "labor_relations": ["collective bargaining", "labor relations", "grievance*", "arbitration*", "union*",
                        "unfair labor practice*", "labor management"],
    "employee_relations": ["employee relations", "investigation*", "disciplinary", "adverse action*",
                           "performance improvement plan*", "misconduct", "conduct and performance"],
    "eeo": ["equal employment opportunity", "affirmative action", "eeo complaint*", "discrimination complaint*",
            "eeo program", "title vii"],
    "compensation": ["job evaluation*", "salary survey*", "market pricing", "pay structure*", "salary structure*",
                     "position classification", "classification determination*", "position description*",
                     "desk audit*", "pay equity", "merit cycle", "compensation program*", "pay setting"],
    "benefits_leave": ["benefits administration", "open enrollment", "fmla", "leave of absence",
                       "leave administration", "benefit plan*", "retirement counseling", "workers compensation",
                       "federal employee health benefits", "fehb", "benefits program*"],
    "talent_acquisition": ["full cycle recruit*", "sourcing", "applicant tracking", "requisition*",
                           "recruitment and placement", "delegated examining", "job opportunity announcement*",
                           "vacancy announcement*", "candidate*", "hiring manager*", "talent acquisition",
                           "merit promotion", "category rating", "job analysis", "staffing"],
    "learning_od": ["instructional design", "training program*", "learning management system", "curriculum",
                    "leadership development", "organizational development", "training needs", "facilitat*",
                    "learning and development", "change management", "succession planning", "talent management"],
    "hris_analytics": ["hris", "workday", "successfactors", "hr systems", "people analytics", "dashboard*",
                       "data integrity", "hr information system*", "system configuration", "hr technology",
                       "oracle hcm", "ukg", "sql", "reporting and analytics"],
    "payroll": ["payroll processing", "pay period*", "timekeeping", "payroll", "garnishment*", "payroll tax*"],
    "hr_operations": ["onboarding", "i 9", "personnel record*", "personnel action*", "new hire paperwork",
                      "background check*", "sf 50", "official personnel folder*", "hr service center",
                      "data entry", "employee records", "offboarding"],
    "hr_strategy": ["workforce planning", "hr strategy", "people strategy", "hr policy", "human capital strategy",
                    "strategic plan*", "executive team", "human capital planning"],
    "generalist": ["full range of hr", "full range of human resources", "variety of hr", "hr generalist",
                   "all aspects of human resources", "business partner", "all areas of human resources",
                   "wide range of human resources", "generalist"],
}
_DESC_RX = {name: [_rx([t]) for t in terms] for name, terms in DESCRIPTION_TERMS.items()}
DESC_MIN_SCORE, DESC_LEAD = 3, 1.5   # at least 3 hits, and half again as many as the runner-up

# ---- step 1: scope ---------------------------------------------------------------------------
HR_DEPARTMENT = _rx(["hr", "human resources", "human resource", "people", "talent", "recruiting", "recruitment",
                     "payroll", "total rewards", "people ops", "employee experience", "learning and development",
                     "l and d", "human capital", "people and culture", "people team", "people operations"])
# Title terms strong enough to mark a listing as HR when the department does not.
STRONG_TITLE = _rx([
    "human resources", "human resource", "hr", "hrbp", "hris", "hr systems", "workday hcm", "people analytics",
    "people operations", "people ops", "people partner", "people business partner", "people and culture",
    "people team", "people experience", "people coordinator", "people generalist", "people specialist",
    "people analyst", "people systems", "people technology", "people programs", "head of people",
    "vp of people", "vp people", "director of people", "chief people", "chro",
    "recruiter", "recruiters", "recruiting", "talent acquisition", "sourcer", "talent sourc*", "talent partner",
    "head of talent", "talent operations", "talent management", "talent development", "employer brand",
    "employer branding", "payroll", "total rewards", "compensation analyst", "compensation manager",
    "compensation partner", "compensation consultant", "compensation specialist", "compensation and benefits",
    "director of compensation", "head of compensation", "executive compensation", "equity administrator",
    "stock plan administrator", "benefits analyst", "benefits specialist", "benefits manager",
    "benefits administrator", "benefits coordinator", "benefits partner", "benefits and leave",
    "leave of absence", "leave administrator", "leave specialist", "employee relations", "labor relations",
    "labour relations", "workplace investigat*", "equal employment", "eeo", "affirmative action analyst",
    "affirmative action officer", "affirmative action specialist", "affirmative action manager",
    "learning and development", "l and d", "instructional design*", "organizational development",
    "organization development", "leadership development manager", "leadership development specialist",
    "leadership development director", "leadership development partner", "leadership development lead",
    "leadership development consultant", "leadership development coordinator",
    "head of leadership development", "director of leadership development", "employee engagement",
    "employee experience", "people science", "people research", "hr partner",
    "employee onboarding", "new hire onboarding", "hr onboarding", "people onboarding", "hr compliance", "workforce planning", "global mobility", "immigration specialist",
    "personnel analyst", "personnel technician", "academic personnel", "faculty affairs",
])
# "Training" jobs count as HR (learning and OD) only with a training role word and no machine-learning sense.
TRAINING_TITLE = re.compile(
    r"(?<![a-z0-9])(training (specialist|coordinator|manager|director|lead|program manager|facilitator|"
    r"developer|designer|consultant|partner|administrator|and development)|(corporate|technical|sales|"
    r"customer|product|staff|clinical|operations)? ?trainer)(?![a-z0-9])")
NOT_HR_TRAINING = _rx(["model", "models", "ml", "machine learning", "llm", "ai", "data", "inference", "compute",
                       "research", "engineer", "scientist", "gpu", "personal trainer", "athletic trainer",
                       "dog trainer", "fitness", "driver", "drivers", "driving", "flight", "pilot", "pilots",
                       "safety driver"])


# Engineering, product and sales jobs at companies that sell HR software carry HR words in their titles
# ("Solutions Consultant, Payroll"). Outside an HR department they are not HR jobs. HR systems work is the
# exception: employers often file it under IT.
OTHER_WORK = _rx(["engineer", "engineers", "engineering", "developer", "product manager", "product designer",
                  "product marketing", "account executive", "account manager", "solutions consultant",
                  "solution consultant", "sales engineer", "architect", "customer success"])
HR_SYSTEMS = _rx(["hris", "workday", "hr systems", "people systems", "hr technology", "people technology",
                  "people analytics", "hcm", "successfactors"])
NOT_A_JOB = _rx(["talent pool", "talent community", "talent network", "general application",
                 "future opportunities", "general interest"])


def scope(title, department=None, source_is_hr=False):
    """Return how the listing qualifies as HR ('source', 'title', 'department') or None when it does not."""
    if source_is_hr:
        return "source"
    t = norm(title)
    if NOT_A_JOB.search(t):
        return None
    in_hr_dept = bool(department and HR_DEPARTMENT.search(norm(department)))
    if OTHER_WORK.search(t) and department and not in_hr_dept and not HR_SYSTEMS.search(t):
        return None
    if STRONG_TITLE.search(t):
        return "title"
    if TRAINING_TITLE.search(t) and not NOT_HR_TRAINING.search(t):
        return "title"
    if department and HR_DEPARTMENT.search(norm(department)):
        return "department"
    return None


# ---- step 2: classify ------------------------------------------------------------------------

def classify_title(title):
    """The ordered title check. Returns a sub-discipline, or None when the title names no function."""
    t = norm(title)
    for name, rx in _TITLE_RX:
        if rx.search(t):
            if name == "military_hr" and _MILITARY_HIRING.search(t):
                continue   # "Military and Veteran Recruiter" recruits veterans; it is not military personnel work
            return name
    return None


def classify_description(text):
    """Score the ad text by function phrases. Returns (sub-discipline or None, scores)."""
    t = norm(text)
    if not t:
        return None, {}
    scores = {}
    for name, rxs in _DESC_RX.items():
        s = sum(min(3, len(rx.findall(t))) for rx in rxs)   # one phrase counts at most three times
        if s:
            scores[name] = s
    if not scores:
        return None, scores
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], ORDER.index(kv[0])))
    best, top = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0
    if top >= DESC_MIN_SCORE and top >= DESC_LEAD * second:
        return best, scores
    return None, scores


def classify(title, description=None):
    """Return (sub_discipline, classified_by). classified_by is 'title', 'description' or 'none'."""
    sub = classify_title(title)
    if sub:
        return sub, "title"
    sub, _ = classify_description(description)
    if sub:
        return sub, "description"
    return "unclassified", "none"


def names_hr(title):
    """True when the title itself says HR in some way: a function term or a generic HR word."""
    t = norm(title)
    return bool(classify_title(title) or GENERIC_HR.search(t) or STRONG_TITLE.search(t))


def clearly_hr_text(description):
    """A stricter reading of the ad text, for listings whose only HR sign is the department they are filed
    under. HR departments also hold executive assistants, office staff and interns for other teams."""
    sub, scores = classify_description(description)
    if not sub:
        return None
    ranked = sorted(scores.values(), reverse=True)
    second = ranked[1] if len(ranked) > 1 else 0
    return sub if ranked[0] >= 6 and ranked[0] >= 2 * second else None


# ---- step 3: annotate ------------------------------------------------------------------------
# Role words, senior first so "Director of Compensation Analysis" reads as director (docs/hr-job-titles.md).
ROLE_WORDS = [
    ("chief", ["chief", "chro"]),
    ("vp", ["vp", "svp", "evp", "vice president"]),
    ("director", ["director", "head of", "head"]),
    ("manager", ["manager", "supervisor", "supervisory"]),
    ("business partner", ["business partner", "people partner", "hrbp"]),
    ("consultant", ["consultant", "advisor", "adviser", "partner"]),
    ("generalist", ["generalist"]),
    ("analyst", ["analyst", "scientist"]),
    ("specialist", ["specialist", "recruiter", "sourcer", "investigator", "designer", "administrator",
                    "representative", "negotiator", "trainer", "officer"]),
    ("coordinator", ["coordinator", "associate"]),
    ("assistant", ["assistant", "clerk", "technician", "intern"]),
]
_ROLE_RX = [(name, _rx(terms)) for name, terms in ROLE_WORDS]
MANAGER_ROLES = {"chief", "vp", "director", "manager"}

_LEVELS = [
    ("intern", _rx(["intern", "internship", "co op"])),
    ("principal", _rx(["principal"])),
    ("lead", _rx(["lead", "staff"])),
    ("senior", _rx(["senior", "sr"])),
    ("associate", _rx(["associate", "junior", "jr", "entry level"])),
]
_ROMAN = re.compile(r"(?<![a-z0-9])(i{1,3}|iv|v|[1-5])$")


def role_word(title):
    t = norm(title)
    for name, rx in _ROLE_RX:
        if rx.search(t):
            return name
    return ""


def level(title, grade=None):
    """A government grade when the source gives one, else the level word or numeral in the title."""
    if grade:
        return grade
    t = norm(title)
    for name, rx in _LEVELS:
        if rx.search(t):
            return name
    m = _ROMAN.search(re.sub(r"\s*(remote|hybrid|onsite)$", "", t))
    return m.group(1).upper() if m else ""


def soc_code(sub, role):
    """O*NET-SOC code from the sub-discipline table in docs/hr-job-search.md. The code names the occupation
    family, so it is a join key, not a claim about one job."""
    mgr = role in MANAGER_ROLES
    return {
        "generalist": "11-3121" if mgr else "13-1071",
        "talent_acquisition": "11-3121" if mgr else "13-1071",
        "compensation": "11-3111" if mgr else "13-1141",
        "benefits_leave": "11-3111" if mgr else "13-1141",
        "employee_relations": "11-3121" if mgr else "13-1071",
        "labor_relations": "11-3121" if mgr else "13-1075",
        "eeo": "13-1041.03",
        "learning_od": "11-3131" if mgr else ("13-1111" if role == "consultant" else "13-1151"),
        "hris_analytics": "15-1211",
        "hr_operations": "43-4161" if role in ("assistant", "coordinator") else "13-1071",
        "payroll": "43-3051",
        "hr_strategy": "11-3121",
        "academic_personnel": "13-1071",   # not in the table; filed with HR specialists
        "military_hr": "43-4161" if role == "assistant" else "13-1071",   # not in the table either
    }.get(sub, "")


_FLAGS = [
    # (flag, title pattern, unless pattern)
    ("talent_ambiguous", _rx(["talent"]), _rx(["talent acquisition", "talent management", "talent development",
                                               "talent sourc*"])),
    ("hr_manager_scope_unknown", _rx(["hr manager", "human resources manager"]), None),
    ("business_partner_range", _rx(["business partner", "people partner", "hrbp"]), None),
    ("head_of_people_startup", _rx(["head of people"]), None),
    ("may_sit_outside_hr", _rx(["credentialing", "title ix", "faculty affairs", "employee health nurse"]), None),
]


def flags(title, scoped_by=None, department=None):
    """Warnings from the 'titles that mislead' list, plus where the employer filed the job. They tell a
    reader to check the duties, nothing more."""
    t = norm(title)
    out = [name for name, rx, unless in _FLAGS if rx.search(t) and not (unless and unless.search(t))]
    if scoped_by == "department" and not names_hr(title):
        out.append("hr_by_department_only")
    if department and not HR_DEPARTMENT.search(norm(department)):
        out.append("filed_outside_hr")     # payroll under Finance, HRIS under IT, training under a product team
    return out


_SECTOR = [
    ("higher education", re.compile(r"\b(university|college|community college|institute of technology|school of)\b", re.I)),
    ("healthcare", re.compile(r"\b(hospital|hospitals|health system|medical center|healthcare system|clinic)\b", re.I)),
    ("state", re.compile(r"\b(state of|commonwealth of)\b", re.I)),
    ("local government", re.compile(r"\b(city of|county of|town of|county|school district|public schools)\b", re.I)),
    ("nonprofit", re.compile(r"\b(foundation|nonprofit|non-profit|association|society)\b", re.I)),
]


def sector(employer, source):
    """Federal comes from the source. Everything else is a guess from the employer's name, defaulting to corporate."""
    if source == "usajobs":
        return "federal"
    for name, rx in _SECTOR:
        if rx.search(employer or ""):
            return name
    return "corporate"

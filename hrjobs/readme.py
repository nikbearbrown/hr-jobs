"""Keep the README's numbers and tables true: rewrite its generated blocks from the data and the code.

    python3 -m hrjobs.readme          # rewrite README.md from data/current/jobs.csv and the latest summary

The README holds four generated blocks, each between a pair of marker comments:

    headline     the one-paragraph count at the top
    stats        what is in the list today (every table under "What is in the list")
    classifier   the sub-disciplines, in checking order, with the title terms and codes the code really uses
    titles       the title guide, copied from docs/hr-job-titles.md

Everything outside the markers is written by hand and left alone. The daily run calls update() after it writes
the list, so the README never describes a list that is no longer there.
"""
import collections
import csv
import datetime
import json
import re
import sys
from pathlib import Path

from . import classify as C
from .places import STATES

ROOT = Path(__file__).resolve().parent.parent
SECTORS = ["corporate", "federal", "state", "local government", "higher education", "healthcare", "nonprofit"]

# Plain name and one-line description of the work, per sub-discipline.
SUBS = {
    "academic_personnel": ("Academic personnel", "Faculty appointments, promotion and tenure files, academic policy"),
    "military_hr": ("Military HR", "Personnel work for service members; nearly all federal"),
    "labor_relations": ("Labor relations", "Union contracts, bargaining, grievances, arbitration"),
    "employee_relations": ("Employee relations", "Investigations, discipline, performance problems, policy interpretation"),
    "eeo": ("EEO, compliance and inclusion", "Equal opportunity compliance, affirmative action plans, HR compliance, inclusion programs"),
    "compensation": ("Compensation and classification", "Job evaluation, pay structures, salary grades, equity plans"),
    "benefits_leave": ("Benefits and leave", "Benefits administration, leaves of absence, accommodations, retirement plans"),
    "talent_acquisition": ("Talent acquisition", "Recruiting, sourcing, running hiring processes"),
    "learning_od": ("Learning and organizational development", "Training, leadership programs, change management, talent management"),
    "hris_analytics": ("HR systems and people analytics", "HR system configuration, reporting, workforce data"),
    "payroll": ("Payroll", "Pay processing and corrections"),
    "hr_operations": ("HR operations and shared services", "Transactions, onboarding, records, global mobility"),
    "hr_strategy": ("HR strategy and leadership", "Workforce planning, HR policy, running the function"),
    "generalist": ("Generalist and business partner", "Advises a unit's managers on all HR issues"),
    "unclassified": ("Unclassified", "An HR job whose title and ad text do not say which function"),
}
SOC_NAMES = {
    "11-3111": "Compensation and Benefits Managers",
    "11-3121": "Human Resources Managers",
    "11-3131": "Training and Development Managers",
    "13-1041.03": "Equal Opportunity Representatives and Officers",
    "13-1071": "Human Resources Specialists",
    "13-1075": "Labor Relations Specialists",
    "13-1111": "Management Analysts",
    "13-1141": "Compensation, Benefits, and Job Analysis Specialists",
    "13-1151": "Training and Development Specialists",
    "15-1211": "Computer Systems Analysts",
    "43-3051": "Payroll and Timekeeping Clerks",
    "43-4161": "Human Resources Assistants, Except Payroll and Timekeeping",
}
FLAG_MEANING = {
    "filed_outside_hr": "The employer filed the job under another department (Finance, IT, Operations)",
    "business_partner_range": "\"Business Partner\" ranges from a senior strategic advisor to a relabeled generalist",
    "talent_ambiguous": "\"Talent\" can mean recruiting or performance and development",
    "hr_manager_scope_unknown": "\"HR Manager\" could be the only HR person or the manager of a team",
    "head_of_people_startup": "At an early startup, \"Head of People\" can be a fairly junior first hire",
    "may_sit_outside_hr": "Credentialing, Title IX and faculty affairs often belong to other offices",
    "hr_by_department_only": "The title names no HR function; the department and ad text do",
}
SOURCE_NAMES = {"greenhouse": "Greenhouse company boards", "lever": "Lever company boards",
                "ashby": "Ashby company boards", "usajobs": "USAJOBS (federal)", "adzuna": "Adzuna"}
METHOD_NAMES = {"title": "By the title", "description": "By the ad text (title too generic)",
                "annotation": "By a hand annotation", "none": "Not classified (title and ad text both too generic)"}
ROLE_ORDER = [name for name, _ in C.ROLE_WORDS] + [""]
_GRADE = re.compile(r"^([A-Z]{2})-0?(\d{1,2})")


def cell(text):
    """Text that is safe inside a markdown table cell."""
    return re.sub(r"\s+", " ", str(text)).replace("|", "/").strip()


def pct(n, total):
    if not total or not n:
        return "0%"
    share = 100 * n / total
    return "under 1%" if share < 0.5 else f"{share:.0f}%"


def table(header, rows, right=()):
    """header: list of column names. right: indexes of right-aligned (number) columns."""
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("---:" if i in right else "---" for i in range(len(header))) + "|"]
    out += ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows]
    return out


def top_titles(rows, n=5):
    """The n most common titles, grouped without regard to case, shown as most often spelled."""
    spellings = collections.defaultdict(collections.Counter)
    for r in rows:
        spellings[C.norm(r["title"])][r["title"].strip()] += 1
    ranked = sorted(spellings.values(), key=lambda c: (-sum(c.values()), c.most_common(1)[0][0].lower()))
    return [(c.most_common(1)[0][0], sum(c.values())) for c in ranked[:n]]


def age_days(day, today):
    try:
        return (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(day[:10])).days
    except (ValueError, TypeError):
        return None


def headline(rows, summary):
    total = len(rows)
    employers = len({r["employer"] for r in rows})
    states = len({r["state"] for r in rows if r["state"]})
    by_sector = collections.Counter(r["sector"] for r in rows)
    parts = [f"{by_sector[s]:,} {s}" for s in SECTORS if by_sector[s]]
    unclassified = sum(1 for r in rows if r["sub_discipline"] == "unclassified")
    biggest = collections.Counter(r["sub_discipline"] for r in rows).most_common(1)
    lines = [f"**On {summary['date']} the list holds {total:,} open HR listings** from {employers:,} employers in "
             f"{states} states and territories ({', '.join(parts)}). The daily run read {summary['postings_read']:,} "
             f"postings to find them."]
    if biggest:
        name = SUBS.get(biggest[0][0], (biggest[0][0],))[0].lower()
        lines.append(f"The largest group is {name} ({biggest[0][1]:,} listings, {pct(biggest[0][1], total)}). "
                     f"The classifier placed {total - unclassified:,} listings and left {unclassified:,} unclassified "
                     f"for a person to look at.")
    return "\n".join(lines)


def stats(rows, summary):
    total = len(rows)
    today = summary["date"]
    count = lambda col: collections.Counter(r[col] for r in rows)
    out = [f"Counted from [data/current/jobs.csv](data/current/jobs.csv) on **{today}**. The daily run rewrites "
           f"this section, so it always describes the list as it is now.", ""]

    # --- at a glance
    with_salary = sum(1 for r in rows if r["salary"])
    remote = count("remote")
    ages = [a for a in (age_days(r["posted"], today) for r in rows) if a is not None]
    week, month = sum(1 for a in ages if a <= 7), sum(1 for a in ages if a <= 30)
    out += ["### At a glance", ""]
    out += table(["Measure", "Count"], [
        ["Open HR listings", f"{total:,}"],
        ["Employers", f"{len({r['employer'] for r in rows}):,}"],
        ["States and territories with a listing", f"{len({r['state'] for r in rows if r['state']})}"],
        ["Postings read to find them", f"{summary['postings_read']:,}"],
        ["New since the previous run", "first run" if summary.get("baseline_run") else f"{summary['new_today']:,}"],
        ["Posted in the last 7 days", f"{week:,} ({pct(week, total)})"],
        ["Posted in the last 30 days", f"{month:,} ({pct(month, total)})"],
        ["Listings that state a salary", f"{with_salary:,} ({pct(with_salary, total)})"],
        ["Listings marked remote", f"{remote['remote']:,} ({pct(remote['remote'], total)})"],
        ["Listings marked hybrid", f"{remote['hybrid']:,} ({pct(remote['hybrid'], total)})"],
    ], right=(1,))

    # --- sub-discipline by sector
    grid = collections.defaultdict(collections.Counter)
    for r in rows:
        grid[r["sub_discipline"]][r["sector"]] += 1
    by_sector = count("sector")
    sectors = [s for s in SECTORS if by_sector[s]] + sorted(s for s in by_sector if s not in SECTORS)
    body = []
    for sub in C.ORDER:
        if sub in grid:
            n = sum(grid[sub].values())
            body.append([f"{SUBS[sub][0]} (`{sub}`)"] + [grid[sub].get(s, "") or "" for s in sectors] + [n, pct(n, total)])
    body.append(["**Total**"] + [f"**{by_sector[s]:,}**" for s in sectors] + [f"**{total:,}**", "**100%**"])
    out += ["", "### Listings by sub-discipline and sector", ""]
    out += table(["Sub-discipline"] + [s.capitalize() for s in sectors] + ["Total", "Share"], body,
                 right=tuple(range(1, len(sectors) + 3)))
    out += ["", "Sector is read from the source for federal jobs. For every other listing it is guessed from the "
            "employer's name and defaults to corporate."]

    # --- titles actually in the list
    out += ["", "### The titles in each sub-discipline", "",
            "The five most common titles in each group, as the employers wrote them, with the number of listings.", ""]
    body = []
    for sub in C.ORDER:
        group = [r for r in rows if r["sub_discipline"] == sub]
        if group:
            distinct = len({C.norm(r["title"]) for r in group})
            body.append([f"{SUBS[sub][0]}", len(group), distinct,
                         "; ".join(f"{t} ({n})" for t, n in top_titles(group))])
    out += table(["Sub-discipline", "Listings", "Different titles", "Most common titles"], body, right=(1, 2))

    # --- role words
    roles = count("role_word")
    out += ["", "### Role words", "",
            "The role word is the part of the title that says what kind of job it is, most senior first. "
            "[What each one means](#role-words-roughly-from-junior-to-senior) is in the title guide below.", ""]
    out += table(["Role word", "Listings", "Share"],
                 [[r or "none in the title", roles[r], pct(roles[r], total)] for r in ROLE_ORDER if roles[r]],
                 right=(1, 2))

    # --- levels
    levels = count("level")
    words = ["intern", "associate", "senior", "lead", "principal"]
    numeral = sum(n for lv, n in levels.items() if re.fullmatch(r"[IV]+|[1-5]", lv))
    graded = sum(n for lv, n in levels.items() if _GRADE.match(lv))
    body = [[w, levels[w], pct(levels[w], total)] for w in words if levels[w]]
    if numeral:
        body.append(["a numeral (II, III, 2)", numeral, pct(numeral, total)])
    if graded:
        body.append(["a government grade", graded, pct(graded, total)])
    body.append(["no level in the title", levels[""], pct(levels[""], total)])
    out += ["", "### Levels", ""] + table(["Level", "Listings", "Share"], body, right=(1, 2))
    if graded:
        lowest = collections.Counter()
        for lv, n in levels.items():
            m = _GRADE.match(lv)
            if m:
                lowest[(m.group(1), int(m.group(2)))] += n
        gs = sorted((g, n) for (plan, g), n in lowest.items() if plan == "GS")
        other = sum(n for (plan, _), n in lowest.items() if plan != "GS")
        out += ["", "Federal listings by starting grade: " + ", ".join(f"GS-{g} ({n})" for g, n in gs)
                + (f", other pay plans ({other})." if other else ".")]

    # --- where
    states = count("state")
    out += ["", "### Where the jobs are", ""]
    body = [[f"{STATES.get(s, s)} ({s})", n, pct(n, total)] for s, n in states.most_common(13) if s][:12]
    if states[""]:
        body.append(["No state given (remote or location not stated)", states[""], pct(states[""], total)])
    out += table(["State", "Listings", "Share"], body, right=(1, 2))
    out += ["", "Work arrangement, as the employer marked it: "
            + ", ".join(f"{k} {remote[k]:,}" for k in ("remote", "hybrid", "onsite") if remote[k])
            + f", not stated {remote['']:,}."]

    # --- employers
    employers = count("employer")
    out += ["", "### Employers with the most listings", ""]
    out += table(["Employer", "Listings"], [[e, n] for e, n in employers.most_common(15)], right=(1,))

    # --- occupation codes
    socs = count("soc_code")
    out += ["", "### O\\*NET-SOC occupation codes", "",
            "The code names the occupation family, so listings can be joined to other O\\*NET data.", ""]
    out += table(["Code", "Occupation", "Listings"],
                 [[c or "none", SOC_NAMES.get(c, "Unclassified listings carry no code"), n]
                  for c, n in sorted(socs.items(), key=lambda kv: (-kv[1], kv[0]))], right=(2,))

    # --- flags
    flags = collections.Counter(f for r in rows for f in r["flags"].split("; ") if f)
    if flags:
        out += ["", "### Warning flags", ""]
        out += table(["Flag", "Listings", "What to check"],
                     [[f"`{f}`", n, FLAG_MEANING.get(f, "")] for f, n in flags.most_common()], right=(1,))

    # --- how classified, and from where
    how = count("classified_by")
    out += ["", "### How the listings were classified", ""]
    out += table(["Method", "Listings", "Share"],
                 [[METHOD_NAMES.get(k, k), f"{n:,}", pct(n, total)] for k, n in how.most_common()], right=(1, 2))
    src = count("source")
    out += ["", "### Where the listings were read", ""]
    out += table(["Source", "Listings", "Share"],
                 [[SOURCE_NAMES.get(k, k), n, pct(n, total)] for k, n in src.most_common()], right=(1, 2))
    d = summary.get("dropped", {})
    out += ["", f"Left out of the list: {d.get('not_hr', 0):,} postings that are not HR jobs, "
            f"{d.get('hr_department_other_work', 0):,} filed under an HR department but doing other work, "
            f"{d.get('outside_us', 0):,} outside the United States, {d.get('closed', 0):,} past their close date, "
            f"and {d.get('duplicate', 0):,} duplicates."]
    if summary.get("carried_forward"):
        out += ["", f"{summary['carried_forward']:,} listings are carried forward from the last good read of a source "
                "that could not be read today."]
    return "\n".join(out)


def classifier():
    """The sub-disciplines in checking order, with the terms and codes the code really uses."""
    terms = collections.defaultdict(list)
    for name, words in C.SUBDISCIPLINES:
        terms[name] += words
    roles = [name for name, _ in C.ROLE_WORDS] + [""]
    body = []
    for i, sub in enumerate(C.ORDER, 1):
        codes = sorted({C.soc_code(sub, r) for r in roles} - {""})
        body.append([i, f"`{sub}`", SUBS[sub][0], SUBS[sub][1],
                     ", ".join(terms[sub]).replace("*", "\\*") if terms[sub] else "nothing matched",
                     ", ".join(codes) or "none"])
    out = ["A listing goes into exactly one sub-discipline. Its title is checked against the rows below from top "
           "to bottom, and the first row with a matching term wins. Specific functions come first and the "
           "generalist row comes last, because \"HR\" appears in nearly every title. A star means the word may "
           "continue (`investigat*` matches \"investigator\").", ""]
    out += table(["Order", "Code name", "Sub-discipline", "The work", "Title terms that match", "O\\*NET-SOC"], body,
                 right=(0,))
    out += ["", "Three things the table does not show:", "",
            "- **Inclusion titles are checked late.** The words diversity, inclusion, belonging, DEI and DEIB go to "
            "`eeo`, but only after every row down to `hr_strategy` has had its turn, so \"Learning and Inclusion "
            "Designer\" goes to learning.",
            "- **Military recruiting is recruiting.** A title with \"military\" and a hiring word (\"Military "
            "Recruiter\", \"Veteran Sourcer\") skips the `military_hr` row.",
            "- **Generic titles go to the ad text.** A title that only says HR (\"HR Analyst III\", \"Human "
            "Resources Specialist\") is scored against phrases in the ad text. It is placed only when one "
            f"sub-discipline scores at least {C.DESC_MIN_SCORE} and leads the runner-up by half again. Otherwise "
            "it stays `unclassified`.", "",
            "### Role words the annotator reads", "",
            "Checked most senior first, so \"Director of Compensation Analysis\" reads as director.", ""]
    out += table(["Role word", "Words in the title that count as it"],
                 [[name, ", ".join(words)] for name, words in C.ROLE_WORDS])
    out += ["", "### Occupation codes", ""]
    out += table(["O\\*NET-SOC code", "Occupation"], [[c, n] for c, n in SOC_NAMES.items()])
    return "\n".join(out)


def titles(doc):
    """The title guide from docs/hr-job-titles.md, from its first section up to the data-download section,
    with each heading moved one level down so it sits under the README's own heading."""
    start = doc.index("## How HR titles are built")
    end = doc.index("## Getting the complete list as data")
    body = re.sub(r"(?m)^(#{2,5}) ", r"#\1 ", doc[start:end].strip())
    return ("This section is copied from [docs/hr-job-titles.md](docs/hr-job-titles.md) each day, so the two "
            "always agree.\n\n" + body)


def replace_block(text, name, body):
    start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
    if start not in text or end not in text:
        return text
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    return f"{head}{start}\n{body.strip()}\n{end}{tail}"


def latest_summary(folder):
    files = sorted((folder / "data" / "summary").glob("*.json"))
    return json.loads(files[-1].read_text()) if files else None


def update(folder=ROOT, readme=None):
    """Rewrite the generated blocks in README.md. Returns True when the file changed."""
    readme = readme or folder / "README.md"
    jobs = folder / "data" / "current" / "jobs.csv"
    summary = latest_summary(folder)
    if not readme.is_file() or not jobs.is_file() or summary is None:
        return False
    with open(jobs, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    old = text = readme.read_text(encoding="utf-8")
    text = replace_block(text, "headline", headline(rows, summary))
    text = replace_block(text, "stats", stats(rows, summary))
    text = replace_block(text, "classifier", classifier())
    guide = ROOT / "docs" / "hr-job-titles.md"
    if guide.is_file():
        text = replace_block(text, "titles", titles(guide.read_text(encoding="utf-8")))
    if text != old:
        readme.write_text(text, encoding="utf-8")
    return text != old


if __name__ == "__main__":
    changed = update()
    print("README.md updated" if changed else "README.md already up to date (or nothing to read)")
    sys.exit(0)

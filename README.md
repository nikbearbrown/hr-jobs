# hr-jobs

## Summary

This repo collects open human resources jobs in the United States once a day, sorts each one into an HR
sub-discipline, and adds notes about its title. It does not rank anything.

- **The current list:** [data/current/jobs.csv](data/current/jobs.csv), one row per open listing.
- **Today's counts:** [reports/latest.md](reports/latest.md), a table of sub-discipline by sector plus the
  listings first seen that day.
- **The two documents the work follows:** [docs/hr-job-search.md](docs/hr-job-search.md) (the sub-disciplines,
  the sources, the rules) and [docs/hr-job-titles.md](docs/hr-job-titles.md) (what HR titles mean).

The first collection, on 2026-11-11, found 1,369 listings: 1,177 from company job boards and 192 federal.
The classifier placed 1,310 of them and left 59 unclassified for a person to look at.

**What it does not cover yet.** Only two kinds of source are being read: company job boards (mostly technology
companies) and USAJOBS. Universities, state and local government, hospitals and nonprofits are almost absent,
so the counts say little about those sectors. The [sources table](#sources) shows why for each one.

## Why HR needs its own search

"HR" is a family of jobs, not one search term. A compensation analyst and an employee relations investigator
do different work and are not hired for each other's jobs. The same job also has different names in different
sectors, and employers file HR work in different places: payroll under Finance, HR systems under IT. The search
document explains this in full. The practical result is the three steps below.

## How a listing is handled

Every listing goes through three steps, in this order. The code is in
[hrjobs/classify.py](hrjobs/classify.py).

1. **Scope: is this an HR job?** A listing qualifies in one of three ways: its source lists only HR jobs
   (USAJOBS series 0201 and 0203), its title carries a strong HR term ("Recruiter", "HRIS Analyst",
   "Payroll Specialist"), or its employer filed it under an HR department. Weak words such as "training" or
   "information systems" count only with other evidence, because they also match jobs that are not HR.
2. **Classify: which one sub-discipline?** The title is checked against the sub-disciplines in a fixed order,
   specific functions first and generalist last, because "HR" appears in nearly every title. A title too
   generic to place ("HR Analyst III") is classified from the ad text. If the ad text does not settle it either,
   the listing is marked `unclassified`.
3. **Annotate.** Each listing gets a role word (analyst, specialist, manager), a level (senior, II, GS-9), an
   O\*NET-SOC code, a sector, and warning flags for titles that mislead.

A person's judgment beats the classifier: a row in
[annotations/overrides.csv](annotations/overrides.csv) sets a listing's sub-discipline by hand.
See [annotations/README.md](annotations/README.md).

## Sub-disciplines

Checked in this order. The first match wins.

| Sub-discipline | The work |
|---|---|
| `academic_personnel` | Faculty appointments, promotion files, academic policy |
| `military_hr` | Personnel work for service members; nearly all federal |
| `labor_relations` | Union contracts, bargaining, grievances |
| `employee_relations` | Investigations, discipline, policy interpretation |
| `eeo` | Equal opportunity compliance, affirmative action, HR compliance, inclusion |
| `compensation` | Job evaluation, classification, pay structures |
| `benefits_leave` | Benefits, leaves of absence, accommodations |
| `talent_acquisition` | Recruiting and sourcing |
| `learning_od` | Training, leadership programs, organizational development, talent management |
| `hris_analytics` | HR systems, people analytics |
| `payroll` | Pay processing |
| `hr_operations` | Transactions, onboarding, records, global mobility |
| `hr_strategy` | Workforce planning, HR policy, running the function |
| `generalist` | HR generalists and business partners |
| `unclassified` | An HR job whose title and ad text do not say which function |

**One addition to the search document.** Its classifier has thirteen sub-disciplines. This repo adds a
fourteenth, `military_hr`. The document names military HR as a federal specialty, and 78 of the 192 federal
listings in the first collection carry "(Military)" in the title. Without the extra bucket they would all sit
in `unclassified`. To remove it, delete one line from `SUBDISCIPLINES` in `hrjobs/classify.py`.

## Columns in jobs.csv

| Column | Meaning |
|---|---|
| `key` | Stable id for the listing; use it in `annotations/overrides.csv` |
| `sub_discipline` | One value from the table above |
| `classified_by` | `title`, `description` (the ad text), `annotation` (a person), or `none` |
| `title`, `employer` | As posted |
| `sector` | `federal` comes from the source. The rest is guessed from the employer's name and defaults to `corporate`. |
| `city`, `state`, `remote`, `places` | First US location, remote or hybrid status, and up to four locations as posted |
| `role_word`, `level` | Read from the title; for federal jobs the level is the grade |
| `soc_code` | O\*NET-SOC code for the occupation family, from the table in the search document |
| `salary` | Only when the employer posted one |
| `posted`, `closes` | Dates as posted. Company boards rarely give a close date. |
| `requisition` | The employer's own job number, when given |
| `department` | Where the employer filed the job |
| `open_to` | Federal only: who may apply (`public`, `fed-competitive`, and so on) |
| `flags` | Warnings; see below |
| `source`, `board`, `url` | Where the listing was read and the link to apply |
| `first_seen` | The first day this repo saw the listing |

The text of each ad is read to classify generic titles and is not stored.

### Flags

| Flag | What to check |
|---|---|
| `filed_outside_hr` | The employer filed the job under another department (Finance, IT, Operations) |
| `talent_ambiguous` | "Talent" can mean recruiting or performance and development |
| `business_partner_range` | Ranges from a senior strategic advisor to a relabeled generalist |
| `hr_manager_scope_unknown` | Could be the only HR person or the manager of a team |
| `head_of_people_startup` | At an early startup this can be a fairly junior first hire |
| `may_sit_outside_hr` | Credentialing, Title IX and faculty affairs often belong to other offices |
| `hr_by_department_only` | The title names no HR function; the department and ad text do |

## Sources

Checked 2026-11-11.

| Source | Status |
|---|---|
| USAJOBS API, series 0201 and 0203 | **Reading.** Needs the free API key on the machine that runs it. |
| Greenhouse, Lever, Ashby company boards | **Reading** 631 boards, listed in [config/boards.json](config/boards.json). The list comes from the ai-jobs project and leans toward technology companies. |
| Adzuna API | Reader written, **not yet tried**: there is no key. Free key from developer.adzuna.com. |
| SHRM job board | **Not read.** It answers automated readers with a challenge page (HTTP 403). |
| CUPA-HR JobLine | **Not read.** The listings sit inside a members' web app with its own terms. Needs a closer look. |
| HigherEdJobs | **Not read.** The site sits behind a bot wall. |
| GovernmentJobs.com | **Not read.** Its robots.txt allows named search engines and disallows everyone else. |
| State job portals | Not started. One per state. |
| Workday career sites | Not started. This is where most universities and hospitals post. |
| LinkedIn, Indeed | Never. Their terms bar scraping. |

A source that cannot be read on a given day keeps its last known listings, so one bad day does not delete them.

## Running it

Python 3.10 or newer, standard library only.

```bash
python3 -m unittest discover -s tests
```

```bash
python3 -m hrjobs.collect
```

A trial run that reads 20 boards and writes to a scratch folder instead of the repo:

```bash
python3 -m hrjobs.collect --limit-boards 20 --out /tmp/hr-jobs-trial
```

For the federal source, put the USAJOBS key in `~/.usajobs/key` and the registered email in `~/.usajobs/email`.
Without them the run skips USAJOBS and says so in the report.

The daily run lives on a Hetzner server. See [ops/README.md](ops/README.md).

## Known limits

- **Sector is a guess** outside the federal source. An employer whose name does not say "University" or
  "Hospital" is counted as corporate.
- **Title rules misfire.** Companies that sell HR software post sales and product jobs with HR words in the
  title, and some get through. The `filed_outside_hr` flag marks the likely ones.
- **Generic titles stay unclassified** when the ad text is also vague. The search document suggests a language
  model as a second pass; that is not built.
- **No ranking and no target.** With no specialty or location chosen, the counts are the product: they show
  which sub-disciplines and sectors are hiring.

## License

MIT. See [LICENSE](LICENSE).

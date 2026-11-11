# HR Job Search: Sub-Discipline Map and Lectern Setup

## The core problem

"HR" is a family of jobs, not a single search term. A search built on the keyword "HR" fails in three ways:

1. **The sub-disciplines are separate job markets.** A compensation analyst and an employee relations investigator do different work and aren't hired for each other's jobs. A national search for all of HR returns thousands of listings. Grouping them by sub-discipline is what makes the output usable.
2. **The same job has different names in different sectors.** Companies say "Talent Acquisition," the federal government says "Recruitment and Placement," and universities often say "Employment." Matching on titles alone breaks across sectors.
3. **Employers file HR work in different places.** Payroll often sits under Finance. HRIS often sits under IT, and training under a learning or education group. A search for "HR" misses all of them.

## Part 1: HR sub-disciplines

| Sub-discipline | What the work is | Title variants to match | O\*NET-SOC |
|---|---|---|---|
| Generalist / business partner | Advises a unit's managers on all HR issues | HR Generalist, HR Business Partner, People Partner, HR Manager | 13-1071, 11-3121 |
| Talent acquisition | Recruiting, sourcing, running hiring processes | Recruiter, Talent Acquisition Specialist, Sourcer, Recruitment Coordinator, HR Specialist (Recruitment and Placement) | 13-1071 |
| Compensation and classification | Job evaluation, pay structures, salary grades | Compensation Analyst, Classification and Compensation Analyst, Total Rewards Analyst, HR Specialist (Classification) | 13-1141, 11-3111 |
| Benefits and leave | Benefits administration, leaves of absence, disability management | Benefits Analyst, Leave Administrator, Disability Management Specialist | 13-1141, 11-3111 |
| Employee relations | Investigations, discipline, performance problems, policy interpretation | Employee Relations Specialist, ER Consultant, ER Investigator | 13-1071 |
| Labor relations | Union contracts, bargaining, grievances, arbitration | Labor Relations Specialist, Labor Relations Manager, HR Specialist (Employee and Labor Relations) | 13-1075 |
| EEO and affirmative action | Equal opportunity compliance, affirmative action plans, discrimination complaints | EEO Officer, Affirmative Action Analyst, EEO Investigator | 13-1041.03 |
| Learning and org development | Training, leadership programs, change management | L&D Specialist, Training Manager, Organizational Development Consultant | 13-1151, 11-3131, 13-1111 |
| HRIS and people analytics | HR system configuration, reporting, workforce data | HRIS Analyst, People Analytics Analyst, Workday HCM Analyst, HR Specialist (Information Systems) | no HR code; usually 15-1211 |
| HR operations / shared services | Transactions, onboarding paperwork, records, I-9 | HR Coordinator, HR Assistant, HR Operations Specialist, HR Shared Services Analyst | 43-4161, 13-1071 |
| Payroll | Pay processing and corrections | Payroll Specialist, Payroll Analyst | 43-3051 |
| HR strategy and leadership | Workforce planning, HR policy, running the function | HR Policy Analyst, Workforce Planning Manager, HR Director, Chief People Officer | 11-3121 |

Specialized versions show up in particular sectors:

- **Academic personnel / faculty affairs** in universities. This covers faculty appointments, promotion files, and academic policy.
- **Healthcare HR** in hospital systems. This work is heavily unionized and depends on licensure.
- **Military HR** in the federal government.

The SOC codes give every listing a common reference. They map one-to-one to the O\*NET data already in the AI Exposure Explorer, so tagged results can be joined to exposure scores directly.

## Part 2: Where HR jobs are posted

Structured feeds are the reliable core, and job boards fill in the gaps.

| Source | What it covers | Access |
|---|---|---|
| USAJOBS API | Federal jobs | Free API key. Filter by occupational series 0201 (HR Specialist) and 0203 (HR Assistant). |
| Greenhouse, Lever, Ashby job boards | Corporate jobs at companies that use those applicant tracking systems | Public JSON endpoint per company. Needs a list of company board names. |
| Workday career sites | Large employers, including many universities and hospitals | No official public API. The sites' internal JSON endpoints work but can break without notice. |
| Adzuna API | Broad aggregator, with an HR and recruitment category | Free tier with an API key. Good coverage, but duplicates the company boards. |
| SHRM job board | HR-only, mostly corporate | Web board. Use alerts or careful polite fetching. |
| CUPA-HR JobLine | HR-only, higher education | Low volume, but the listings are real searches. |
| HigherEdJobs | All of higher education, with HR categories | Wide coverage of universities. |
| GovernmentJobs.com (NEOGOV) | Cities, counties, special districts | Public-sector HR, where labor relations work is common. |
| State job portals | State government | One per state; titles are often "Personnel Analyst." |
| LinkedIn, Indeed | Everything | Their terms bar scraping. Use them as a manual cross-check only. |

## Part 3: How this search differs from the other Lectern searches

The advocate search treats listings as evidence that a company cares about something. This search treats listings as real jobs to apply to, so it needs different handling:

1. **Freshness matters.** Drop expired listings and surface close dates.
2. **Deduplication matters.** One job can show up on the company's own board, on Adzuna, and on a niche board. Match on employer plus requisition number. Fall back to employer, title, and location.
3. **Classify each listing by function first, and rank second.** Title matching handles most listings. It fails on generic titles like "HR Analyst III." For those, classify from the job description, or send them to a model as a second pass.
4. **Don't rank until there's a target.** With no specialty or location chosen, group the results and report counts. The counts per sub-discipline and region tell you which markets are actually hiring.

### Title classifier (starting point)

The order of the checks matters. Specific functions go first, and the generalist bucket goes last, because "HR" appears in nearly every title.

```python
SUBDISCIPLINES = [
    ("academic_personnel", ["academic personnel", "academic hr", "faculty affairs"]),
    ("labor_relations", ["labor relations", "labor and employee relations", "employee and labor relations"]),
    ("employee_relations", ["employee relations", "er specialist", "er consultant", "workplace investigat"]),
    ("eeo", ["equal employment", "eeo", "affirmative action"]),
    ("compensation", ["compensation", "classification", "total rewards", "job analyst"]),
    ("benefits_leave", ["benefits", "leave of absence", "leave administrator", "disability management"]),
    ("talent_acquisition", ["recruiter", "recruitment", "recruiting", "talent acquisition", "sourcer", "placement"]),
    ("learning_od", ["learning and development", "training", "organizational development", "talent development"]),
    ("hris_analytics", ["hris", "people analytics", "workday", "hr systems", "information systems"]),
    ("payroll", ["payroll"]),
    ("hr_operations", ["hr coordinator", "hr assistant", "shared services", "hr operations", "people operations", "onboarding"]),
    ("hr_strategy", ["workforce planning", "hr policy", "chief people", "hr director", "vp of people"]),
    ("generalist", ["generalist", "business partner", "people partner", "human resources", "hr "]),
]

def classify(title: str) -> str:
    t = f" {title.lower()} "
    for sub, terms in SUBDISCIPLINES:
        if any(term in t for term in terms):
            return sub
    return "unclassified"  # send to description-based or model classification
```

Two known weak spots:

- **"Training" and "information systems" also match non-HR jobs.** Run this classifier only on listings that are already HR-scoped by source, category, or occupational series. Don't run it on every job a feed returns.
- **"Employee and Labor Relations" lands in labor relations.** That's acceptable, since the job covers both.

### Paste into Muse

Copy the block below into Muse as is. It sets up a national search with no ranking.

```text
Add a new search to lectern: an HR job search.

Treat listings in this search as real openings to apply to, not as signals of company interest. Keep its output separate from the advocate and speaker searches. Write results to hr-search/YYYY-MM-DD.md and hr-search/YYYY-MM-DD.csv in the lectern repo.

Scope: United States, all locations, including remote roles.

Sources, in priority order:
1. USAJOBS API, occupational series 0201 and 0203.
2. Greenhouse, Lever, and Ashby public job board endpoints. If lectern already keeps a list of companies, check each company's boards on these systems. Keep only HR jobs (by department or title).
3. Adzuna API, HR and recruitment category.
4. SHRM job board.
5. CUPA-HR JobLine: https://cupahr.org/jobline/
6. HigherEdJobs, human resources categories.
7. GovernmentJobs.com, human resources categories.
Do not scrape LinkedIn or Indeed.

Also include these jobs even when the listing is not labeled HR: payroll, HR systems (HRIS, Workday HCM), training and talent development, organizational development.

Classify every listing into exactly one of these sub-disciplines, checking in this order: academic_personnel, labor_relations, employee_relations, eeo, compensation, benefits_leave, talent_acquisition, learning_od, hris_analytics, payroll, hr_operations, hr_strategy, generalist. If the title is too generic to classify (for example "HR Analyst III"), classify from the job description. If it still can't be classified, mark it unclassified.

For each listing, record: title, employer, sector (corporate, federal, state, local government, higher education, healthcare, nonprofit), city, state, remote status, sub-discipline, O*NET-SOC code, salary range if posted, posting date, close date, requisition number, source, URL.

Deduplicate listings that appear on more than one source. Match on employer plus requisition number; if there is no requisition number, match on employer plus title plus city. Keep the URL from the employer's own site when there is one, otherwise from the highest-priority source.

Drop listings whose close date has passed.

Do not rank listings. At the top of the daily markdown report, give the total count and a count table of sub-discipline by sector. Below that, group listings by sub-discipline, newest first.
```

## Further reading

- O\*NET occupations (the codes above): https://www.onetonline.org
- OPM classification standard for the HR job family (GS-0200), which defines the federal HR specialties: https://www.opm.gov/fedclass/gs0200a.pdf
- USAJOBS developer API: https://developer.usajobs.gov
- Greenhouse Job Board API: https://developers.greenhouse.io/job-board.html
- CUPA-HR JobLine: https://cupahr.org/jobline/

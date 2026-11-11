# hr-jobs

## Summary

This repo collects open human resources jobs in the United States once a day, sorts each one into an HR
sub-discipline, and adds notes about its title. It does not rank anything.

- **The current list:** [data/current/jobs.csv](data/current/jobs.csv), one row per open listing.
- **Today's counts:** [reports/latest.md](reports/latest.md), a table of sub-discipline by sector plus the
  listings first seen that day.
- **The two documents the work follows:** [docs/hr-job-search.md](docs/hr-job-search.md) (the sub-disciplines,
  the sources, the rules) and [docs/hr-job-titles.md](docs/hr-job-titles.md) (what HR titles mean).

<!-- headline:start -->
**On 2026-11-11 the list holds 1,365 open HR listings** from 336 employers in 48 states and territories (1,172 corporate, 192 federal, 1 healthcare). The daily run read 51,174 postings to find them.
The largest group is talent acquisition (592 listings, 43%). The classifier placed 1,306 listings and left 59 unclassified for a person to look at.
<!-- headline:end -->

**What it does not cover yet.** Only two kinds of source are being read: company job boards (mostly technology
companies) and USAJOBS. Universities, state and local government, hospitals and nonprofits are almost absent,
so the counts say little about those sectors. The [sources table](#sources) shows why for each one.

A server reads the sources every day at 05:30 UTC, rewrites the list, and rewrites the numbers on this page.

## Contents

- [What is in the list](#what-is-in-the-list): today's counts by sub-discipline, sector, title, role, level,
  state, employer and source
- [Classifications](#classifications): the sub-disciplines, the title terms that put a listing in each one,
  and the occupation codes
- [Job titles and what they mean](#job-titles-and-what-they-mean): how HR titles are built, the titles in each
  sub-discipline, titles specific to one sector, and titles that mislead
- [How a listing is handled](#how-a-listing-is-handled)
- [Columns in jobs.csv](#columns-in-jobscsv) and [flags](#flags)
- [Sources](#sources)
- [Running it](#running-it)
- [Known limits](#known-limits)

## What is in the list

<!-- stats:start -->
Counted from [data/current/jobs.csv](data/current/jobs.csv) on **2026-11-11**. The daily run rewrites this section, so it always describes the list as it is now.

### At a glance

| Measure | Count |
|---|---:|
| Open HR listings | 1,365 |
| Employers | 336 |
| States and territories with a listing | 48 |
| Postings read to find them | 51,174 |
| New since the previous run | 0 |
| Posted in the last 7 days | 293 (21%) |
| Posted in the last 30 days | 680 (50%) |
| Listings that state a salary | 399 (29%) |
| Listings marked remote | 166 (12%) |
| Listings marked hybrid | 173 (13%) |

### Listings by sub-discipline and sector

| Sub-discipline | Corporate | Federal | Healthcare | Total | Share |
|---|---:|---:|---:|---:|---:|
| Military HR (`military_hr`) |  | 78 |  | 78 | 6% |
| Labor relations (`labor_relations`) |  | 10 |  | 10 | 1% |
| Employee relations (`employee_relations`) | 20 | 4 |  | 24 | 2% |
| EEO, compliance and inclusion (`eeo`) | 1 |  |  | 1 | under 1% |
| Compensation and classification (`compensation`) | 81 | 16 |  | 97 | 7% |
| Benefits and leave (`benefits_leave`) | 21 | 4 |  | 25 | 2% |
| Talent acquisition (`talent_acquisition`) | 565 | 26 | 1 | 592 | 43% |
| Learning and organizational development (`learning_od`) | 100 | 3 |  | 103 | 8% |
| HR systems and people analytics (`hris_analytics`) | 82 | 3 |  | 85 | 6% |
| Payroll (`payroll`) | 40 | 1 |  | 41 | 3% |
| HR operations and shared services (`hr_operations`) | 86 | 8 |  | 94 | 7% |
| HR strategy and leadership (`hr_strategy`) | 28 | 10 |  | 38 | 3% |
| Generalist and business partner (`generalist`) | 118 |  |  | 118 | 9% |
| Unclassified (`unclassified`) | 30 | 29 |  | 59 | 4% |
| **Total** | **1,172** | **192** | **1** | **1,365** | **100%** |

Sector is read from the source for federal jobs. For every other listing it is guessed from the employer's name and defaults to corporate.

### The titles in each sub-discipline

The five most common titles in each group, as the employers wrote them, with the number of listings.

| Sub-discipline | Listings | Different titles | Most common titles |
|---|---:|---:|---|
| Military HR | 78 | 38 | HUMAN RESOURCES SPECIALIST (MILITARY) (12); HR SPEC (MILITARY) (7); HUMAN RESOURCES ASSISTANT (MILITARY) (TITLE 32) (7); HUMAN RESOURCES SPECIALIST (MILITARY) (TITLE 32) (6); HUMAN RESOURCES ASSISTANT (MILITARY) (5) |
| Labor relations | 10 | 9 | HUMAN RESOURCES SPECIALIST (LABOR RELATIONS/EMPLOYEE RELATIONS) (2); Employee & Labor Relations Specialist NF4 (1); HR Specialist (Employee and Labor Relations) (1); HR Specialist (Employee Relations/Labor Relations) (1); Human Resources Specialist (ER-LR) (1) |
| Employee relations | 24 | 17 | Human Resources Coordinator (Employee Relations) (3); Employee Relations Business Partner (2); Employee Relations Partner (2); HR Business Partner (Employee Relations) (2); HUMAN RESOURCES SPECIALIST (EMPLOYEE RELATIONS/PLACEMENT) (2) |
| EEO, compliance and inclusion | 1 | 1 | People Operations Specialist, HR Compliance (1) |
| Compensation and classification | 97 | 75 | HUMAN RESOURCES SPECIALIST (CLASSIFICATION) (5); Director, Compensation (3); Sales Compensation Analyst (3); Senior Compensation Analyst (3); Total Rewards Lead (3) |
| Benefits and leave | 25 | 19 | Benefits Analyst (3); Human Resources Specialist (Employee Benefits) (3); Benefits Coordinator (2); Benefits Specialist (2); Benefits Manager (1) |
| Talent acquisition | 592 | 379 | Senior Technical Recruiter (18); Technical Recruiter (18); Recruiting Coordinator (12); GTM Recruiter (10); Recruiter (8) |
| Learning and organizational development | 103 | 91 | Associate Instructional Designer (5); Travel Driver Trainer (4); Human Resources Specialist (Human Resource Development) (2); Principal Organizational Development Strategist (2); Senior Training Specialist (2) |
| HR systems and people analytics | 85 | 68 | People Research Scientist (4); Senior HRIS Analyst (4); People Systems Analyst (3); Senior People Science Analyst (12 month FTC) (3); Full Stack Software Engineer - People Systems (2) |
| Payroll | 41 | 32 | Payroll Specialist (5); Payroll Manager (4); Payroll Analyst (3); Director, Payroll (1); Global Head of Payroll (1) |
| HR operations and shared services | 94 | 64 | Human Resources Assistant (7); People Operations Generalist (4); People Operations Specialist (4); Global Mobility Program Manager, Tax (3); People Operations Associate (3) |
| HR strategy and leadership | 38 | 27 | Human Resources Officer (5); Director, M&A People Strategy & Integration (3); Head of People (3); Director, People Success (2); People Strategy Manager (2) |
| Generalist and business partner | 118 | 71 | Senior People Business Partner (11); People Partner (9); HR Business Partner (6); Senior People Partner (6); HR Generalist (5) |
| Unclassified | 59 | 41 | Human Resources Specialist (12); Senior Manager, M&A People Integration (3); Staff People Program Manager, Production (3); Supervisory Human Resources Specialist (3); Senior Manager, Talent Operations (2) |

### Role words

The role word is the part of the title that says what kind of job it is, most senior first. [What each one means](#role-words-roughly-from-junior-to-senior) is in the title guide below.

| Role word | Listings | Share |
|---|---:|---:|
| chief | 2 | under 1% |
| vp | 5 | under 1% |
| director | 85 | 6% |
| manager | 194 | 14% |
| business partner | 109 | 8% |
| consultant | 75 | 5% |
| generalist | 18 | 1% |
| analyst | 77 | 6% |
| specialist | 557 | 41% |
| coordinator | 76 | 6% |
| assistant | 41 | 3% |
| none in the title | 126 | 9% |

### Levels

| Level | Listings | Share |
|---|---:|---:|
| intern | 11 | 1% |
| associate | 21 | 2% |
| senior | 332 | 24% |
| lead | 74 | 5% |
| principal | 22 | 2% |
| a numeral (II, III, 2) | 3 | under 1% |
| a government grade | 190 | 14% |
| no level in the title | 710 | 52% |

Federal listings by starting grade: GS-1 (1), GS-4 (2), GS-5 (8), GS-6 (3), GS-7 (30), GS-8 (1), GS-9 (46), GS-11 (12), GS-12 (22), GS-13 (14), GS-14 (14), GS-15 (10), other pay plans (27).

### Where the jobs are

| State | Listings | Share |
|---|---:|---:|
| California (CA) | 435 | 32% |
| New York (NY) | 166 | 12% |
| Texas (TX) | 81 | 6% |
| Washington (WA) | 76 | 6% |
| Massachusetts (MA) | 65 | 5% |
| District of Columbia (DC) | 50 | 4% |
| Virginia (VA) | 45 | 3% |
| Illinois (IL) | 34 | 2% |
| Arizona (AZ) | 27 | 2% |
| Florida (FL) | 20 | 1% |
| Colorado (CO) | 19 | 1% |
| Georgia (GA) | 15 | 1% |
| No state given (remote or location not stated) | 173 | 13% |

Work arrangement, as the employer marked it: remote 166, hybrid 173, onsite 141, not stated 885.

### Employers with the most listings

| Employer | Listings |
|---|---:|
| Anduril | 110 |
| SpaceX | 79 |
| Brex | 30 |
| Army National Guard Units | 29 |
| Carvana | 29 |
| Air National Guard Units | 24 |
| Legora | 22 |
| Datadog | 22 |
| Harvey | 18 |
| Crusoe | 18 |
| Shield AI | 17 |
| Stripe | 16 |
| OpenAI | 14 |
| CoreWeave | 14 |
| Rocket Lab | 14 |

### O\*NET-SOC occupation codes

The code names the occupation family, so listings can be joined to other O\*NET data.

| Code | Occupation | Listings |
|---|---|---:|
| 13-1071 | Human Resources Specialists | 751 |
| 11-3121 | Human Resources Managers | 150 |
| 15-1211 | Computer Systems Analysts | 85 |
| 13-1141 | Compensation, Benefits, and Job Analysis Specialists | 79 |
| 13-1151 | Training and Development Specialists | 75 |
| none | Unclassified listings carry no code | 59 |
| 43-4161 | Human Resources Assistants, Except Payroll and Timekeeping | 45 |
| 11-3111 | Compensation and Benefits Managers | 43 |
| 43-3051 | Payroll and Timekeeping Clerks | 41 |
| 11-3131 | Training and Development Managers | 24 |
| 13-1075 | Labor Relations Specialists | 8 |
| 13-1111 | Management Analysts | 4 |
| 13-1041.03 | Equal Opportunity Representatives and Officers | 1 |

### Warning flags

| Flag | Listings | What to check |
|---|---:|---|
| `filed_outside_hr` | 264 | The employer filed the job under another department (Finance, IT, Operations) |
| `business_partner_range` | 118 | "Business Partner" ranges from a senior strategic advisor to a relabeled generalist |
| `talent_ambiguous` | 55 | "Talent" can mean recruiting or performance and development |
| `hr_by_department_only` | 9 | The title names no HR function; the department and ad text do |
| `head_of_people_startup` | 5 | At an early startup, "Head of People" can be a fairly junior first hire |
| `hr_manager_scope_unknown` | 3 | "HR Manager" could be the only HR person or the manager of a team |

### How the listings were classified

| Method | Listings | Share |
|---|---:|---:|
| By the title | 1,236 | 91% |
| By the ad text (title too generic) | 70 | 5% |
| Not classified (title and ad text both too generic) | 59 | 4% |

### Where the listings were read

| Source | Listings | Share |
|---|---:|---:|
| Greenhouse company boards | 817 | 60% |
| Ashby company boards | 291 | 21% |
| USAJOBS (federal) | 192 | 14% |
| Lever company boards | 65 | 5% |

Left out of the list: 49,138 postings that are not HR jobs, 172 filed under an HR department but doing other work, 499 outside the United States, 0 past their close date, and 0 duplicates.
<!-- stats:end -->

## Classifications

<!-- classifier:start -->
A listing goes into exactly one sub-discipline. Its title is checked against the rows below from top to bottom, and the first row with a matching term wins. Specific functions come first and the generalist row comes last, because "HR" appears in nearly every title. A star means the word may continue (`investigat*` matches "investigator").

| Order | Code name | Sub-discipline | The work | Title terms that match | O\*NET-SOC |
|---:|---|---|---|---|---|
| 1 | `academic_personnel` | Academic personnel | Faculty appointments, promotion and tenure files, academic policy | academic personnel, academic hr, faculty affairs, academic affairs personnel | 13-1071 |
| 2 | `military_hr` | Military HR | Personnel work for service members; nearly all federal | military, mil | 13-1071, 43-4161 |
| 3 | `labor_relations` | Labor relations | Union contracts, bargaining, grievances, arbitration | labor relations, labour relations, labor and employee relations, employee and labor relations, chief negotiator, collective bargaining | 11-3121, 13-1075 |
| 4 | `employee_relations` | Employee relations | Investigations, discipline, performance problems, policy interpretation | employee relations, er specialist, er consultant, er investigator, er manager, workplace investigat\*, hr investigat\* | 11-3121, 13-1071 |
| 5 | `eeo` | EEO, compliance and inclusion | Equal opportunity compliance, affirmative action plans, HR compliance, inclusion programs | equal employment, equal opportunity, eeo, affirmative action, hr compliance, diversity, inclusion, belonging, dei, deib | 13-1041.03 |
| 6 | `compensation` | Compensation and classification | Job evaluation, pay structures, salary grades, equity plans | compensation, classification, total rewards, job analyst, equity plan, stock plan, equity administrator, rewards analyst, rewards manager | 11-3111, 13-1141 |
| 7 | `benefits_leave` | Benefits and leave | Benefits administration, leaves of absence, accommodations, retirement plans | benefits, leave of absence, leave administrator, leave specialist, leave management, disability management, accommodation\*, fmla, retirement plan, wellness program, wellbeing program | 11-3111, 13-1141 |
| 8 | `talent_acquisition` | Talent acquisition | Recruiting, sourcing, running hiring processes | recruiter, recruiters, recruitment, recruiting, talent acquisition, sourcer, talent sourc\*, placement, employer brand, employer branding, talent partner, head of talent, staffing specialist, staffing | 11-3121, 13-1071 |
| 9 | `learning_od` | Learning and organizational development | Training, leadership programs, change management, talent management | learning and development, l and d, training, trainer, organizational development, organization development, organisational development, talent development, talent management, instructional design\*, leadership development, learning experience, learning program\*, learning specialist, learning manager, learning partner, employee engagement, human resource development, human resources development, hr development, enablement | 11-3131, 13-1111, 13-1151 |
| 10 | `hris_analytics` | HR systems and people analytics | HR system configuration, reporting, workforce data | hris, people analytics, workday, hr systems, information systems, hr technology, people technology, people systems, hcm, successfactors, ukg, hr analytics, workforce analytics, people data, people insights, hr data, people science, people research | 15-1211 |
| 11 | `payroll` | Payroll | Pay processing and corrections | payroll | 43-3051 |
| 12 | `hr_operations` | HR operations and shared services | Transactions, onboarding, records, global mobility | hr coordinator, hr assistant, human resources coordinator, human resources assistant, human resources assistance, hr asst, human resources asst, shared services, hr operations, human resources operations, people operations, people ops, people coordinator, people operations coordinator, onboarding, hr service\*, hr administrator, hr associate, personnel technician, global mobility, immigration, people experience, employee experience | 13-1071, 43-4161 |
| 13 | `hr_strategy` | HR strategy and leadership | Workforce planning, HR policy, running the function | workforce planning, hr policy, chief people, chief human resources, chro, hr director, human resources director, director of human resources, director human resources, director of hr, director of people, director people, vp of people, vp people, vp of hr, vp hr, vp human resources, vice president of people, vice president people, vice president of human resources, vice president human resources, head of people, head of hr, head of human resources, people strategy, hr strategy, human capital officer, human resources officer, hr officer, policy planning | 11-3121 |
| 14 | `generalist` | Generalist and business partner | Advises a unit's managers on all HR issues | generalist, business partner, business partnering, people partner, hr partner, human resources partner, hrbp, hr manager, human resources manager, people and culture manager, people manager hr | 11-3121, 13-1071 |
| 15 | `unclassified` | Unclassified | An HR job whose title and ad text do not say which function | nothing matched | none |

Three things the table does not show:

- **Inclusion titles are checked late.** The words diversity, inclusion, belonging, DEI and DEIB go to `eeo`, but only after every row down to `hr_strategy` has had its turn, so "Learning and Inclusion Designer" goes to learning.
- **Military recruiting is recruiting.** A title with "military" and a hiring word ("Military Recruiter", "Veteran Sourcer") skips the `military_hr` row.
- **Generic titles go to the ad text.** A title that only says HR ("HR Analyst III", "Human Resources Specialist") is scored against phrases in the ad text. It is placed only when one sub-discipline scores at least 3 and leads the runner-up by half again. Otherwise it stays `unclassified`.

### Role words the annotator reads

Checked most senior first, so "Director of Compensation Analysis" reads as director.

| Role word | Words in the title that count as it |
|---|---|
| chief | chief, chro |
| vp | vp, svp, evp, vice president |
| director | director, head of, head |
| manager | manager, supervisor, supervisory |
| business partner | business partner, people partner, hrbp |
| consultant | consultant, advisor, adviser, partner |
| generalist | generalist |
| analyst | analyst, scientist |
| specialist | specialist, recruiter, sourcer, investigator, designer, administrator, representative, negotiator, trainer, officer |
| coordinator | coordinator, associate |
| assistant | assistant, clerk, technician, intern |

### Occupation codes

| O\*NET-SOC code | Occupation |
|---|---|
| 11-3111 | Compensation and Benefits Managers |
| 11-3121 | Human Resources Managers |
| 11-3131 | Training and Development Managers |
| 13-1041.03 | Equal Opportunity Representatives and Officers |
| 13-1071 | Human Resources Specialists |
| 13-1075 | Labor Relations Specialists |
| 13-1111 | Management Analysts |
| 13-1141 | Compensation, Benefits, and Job Analysis Specialists |
| 13-1151 | Training and Development Specialists |
| 15-1211 | Computer Systems Analysts |
| 43-3051 | Payroll and Timekeeping Clerks |
| 43-4161 | Human Resources Assistants, Except Payroll and Timekeeping |
<!-- classifier:end -->

**One addition to the search document.** Its classifier has thirteen sub-disciplines. This repo adds a
fourteenth, `military_hr`. The document names military HR as a federal specialty, and about two in five federal
listings carry "(Military)" in the title. Without the extra row they would all sit in `unclassified`. To remove
it, delete one line from `SUBDISCIPLINES` in `hrjobs/classify.py`.

A person's judgment beats the classifier: a row in [annotations/overrides.csv](annotations/overrides.csv) sets
a listing's sub-discipline by hand. See [annotations/README.md](annotations/README.md).

## Job titles and what they mean

<!-- titles:start -->
This section is copied from [docs/hr-job-titles.md](docs/hr-job-titles.md) each day, so the two always agree.

### How HR titles are built

Most HR titles have three parts: a level, a function, and a role word. "Senior Compensation Analyst" is level (Senior) + function (Compensation) + role (Analyst). Once you can read the parts, most titles decode themselves. The hard part is that the same words mean different things at different employers.

#### Role words, roughly from junior to senior

| Role word | What it usually means |
|---|---|
| Assistant | Clerical support: data entry, filing, records, scheduling. Entry level, often hourly. |
| Coordinator | Runs the logistics of a process, such as interview scheduling, onboarding paperwork, or open enrollment. Entry to early career. |
| Specialist | Does one function's work directly: processes cases, answers questions, applies policy. Early to mid career. |
| Analyst | Like a specialist, with more data and design work (pay ranges, system reports, workforce data). In government and universities, "Analyst" is often just the standard title for any HR professional. |
| Generalist | Covers many functions at a working level, usually for one site or a small company. |
| Business Partner | Advises one business unit's leaders on people issues and hands detailed work to specialists. Mid to senior, though some companies give the title to generalists. |
| Consultant | An experienced individual contributor who advises inside one function (employee relations, org development, compensation). Can also mean an outside advisor. |
| Manager | Either manages HR staff or is the only HR person at a small company. Check whether the job has direct reports. |
| Director / Head of | Runs a function (Director of Total Rewards) or HR for a division. At startups, "Head of" can mean anything from a first hire to a VP. |
| VP / SVP | Senior executive over HR or over a major HR function. |
| CHRO / Chief People Officer | The top HR executive, reporting to the CEO. |

#### Level modifiers

Levels show up as Roman numerals (HR Specialist I, II, III), as words (Associate, Senior, Lead, Principal), or as government grades (GS-9, GS-12). "Lead" often means guiding a team without formal reports. "Principal" is rare in HR and marks a top individual contributor.

#### "People" means HR

People Operations, People Partner, People Team, and Chief People Officer are the same jobs under a newer name, common in tech companies. Treat them as synonyms for HR.

### Titles by sub-discipline

#### Generalist and leadership

| Title | What it means |
|---|---|
| HR Generalist | Handles a bit of everything for a site or company: onboarding, policy questions, basic employee issues, leave, benefits questions. |
| HR Business Partner (HRBP) | Strategic HR advisor to one division's leadership, covering org changes, performance, retention, and staffing plans. |
| HR Manager | Runs HR for a site or small company, or manages a team of generalists. |
| HR Director | Runs HR for a company or a large division. |
| VP of HR / VP of People | Senior executive over HR, usually at larger companies. |
| CHRO / Chief People Officer | Top HR executive. Sets people strategy, sits on the executive team. |
| Head of People | Top HR job at a startup. Often the first dedicated HR hire. |

#### Recruiting (talent acquisition)

| Title | What it means |
|---|---|
| Recruiting Coordinator | Schedules interviews, manages candidate logistics and communication. |
| Sourcer | Finds and contacts people who haven't applied, then hands them to a recruiter. |
| Recruiter | Runs hiring for open jobs, from first screen to offer. |
| Technical Recruiter | A recruiter who specializes in engineering, data, and IT jobs. |
| Executive Recruiter | Hires senior leaders. Often works at an outside search firm. |
| Campus / University Recruiter | Hires students and new graduates: career fairs, internships, early-career programs. |
| Talent Acquisition Partner | A senior recruiter who advises hiring managers on hiring strategy, not just individual openings. |
| Recruitment Marketing / Employer Brand Specialist | Writes job ads, runs the careers site, manages how the company looks to job seekers. |
| Recruiting Operations | Runs the applicant tracking system, hiring processes, and recruiting data. |
| Talent Acquisition Manager / Director | Manages the recruiting team. |

#### Compensation

| Title | What it means |
|---|---|
| Compensation Analyst | Compares jobs to market salary surveys, builds pay ranges, reviews offers and raises. |
| Classification Analyst / Job Analyst | Studies what a job actually involves and assigns it a grade. Most common in government and universities. |
| Compensation Consultant | Senior advisor on pay design, often for a group of business units. |
| Executive Compensation Analyst | Handles executive pay, equity awards, and the pay disclosures public companies must file. |
| Equity / Stock Plan Administrator | Manages employee stock grants and vesting. |
| Total Rewards Manager / Director | Oversees compensation and benefits together. |

#### Benefits and leave

| Title | What it means |
|---|---|
| Benefits Specialist / Coordinator | Handles enrollment, employee questions, and problems with insurance vendors. |
| Benefits Analyst | Analyzes plan costs and usage, supports renewals and plan design. |
| Leave Administrator / Leave of Absence Specialist | Manages FMLA and state leave cases, tracks time off, coordinates return to work. |
| Accommodations / Disability Management Specialist | Handles ADA accommodation requests and disability claims. |
| Retirement Plan Administrator | Runs the 401(k), 403(b), or pension plan. |
| Wellness Program Manager | Runs health and wellbeing programs for employees. |
| Benefits Manager | Manages the benefits team and vendor relationships. |

#### Employee relations and labor relations

| Title | What it means |
|---|---|
| Employee Relations Specialist | Handles employee complaints, advises managers on discipline and performance problems, interprets policy. |
| Workplace Investigator | Investigates misconduct and harassment complaints and writes findings. |
| Employee Relations Manager | Leads ER cases and sets ER practice. |
| Labor Relations Specialist / Representative | Applies union contracts day to day and handles grievances. |
| Labor Relations Manager / Director | Leads contract bargaining and the relationship with unions. |
| Chief Negotiator | Represents the employer at the bargaining table. Usually senior labor relations or an outside lawyer. |

#### Compliance, EEO, and inclusion

| Title | What it means |
|---|---|
| EEO Specialist / Officer | Handles discrimination complaints and equal employment compliance. |
| Affirmative Action Analyst | Prepares the affirmative action plans that federal contractors are required to keep. |
| HR Compliance Specialist | Audits HR practices against employment law: wage and hour, I-9s, required postings, record retention. |
| Inclusion / Belonging / Culture titles | Program and strategy roles under many changing names. Search for all of these words, not only "diversity." |

#### Learning and organizational development

| Title | What it means |
|---|---|
| Training Specialist / Coordinator | Delivers or schedules training sessions. |
| Instructional Designer | Builds courses and training materials. |
| Learning and Development (L&D) Manager | Runs the training program. |
| Leadership Development Manager | Runs programs for managers and future leaders. |
| Organizational Development (OD) Consultant | Works on change management, team effectiveness, and org design. |
| Talent Management Specialist | Runs performance reviews, succession planning, and career paths. Despite the name, this is not recruiting. |
| Employee Engagement Manager | Runs engagement surveys and acts on the results. |

#### HR systems and analytics

| Title | What it means |
|---|---|
| HRIS Analyst | Configures and maintains the HR system (Workday, SAP SuccessFactors, UKG, Oracle HCM) and builds reports. |
| Workday HCM Analyst / Consultant | The same job, tied to one product. Common enough to search for by name. |
| People Analytics Analyst / Data Scientist | Analyzes workforce data: turnover, hiring pipelines, pay equity. |
| Workforce Planning Analyst | Forecasts headcount and skills needs. |
| HR Technology Manager | Owns the set of HR systems and their vendors. |

#### HR operations and shared services

| Title | What it means |
|---|---|
| HR Assistant | Clerical work and record-keeping. |
| HR Coordinator | Entry-level all-rounder: onboarding paperwork, scheduling, records. |
| HR Operations Specialist / People Operations Specialist | Processes hires, job changes, and terminations in the system, and audits records. |
| HR Service Center Representative / Shared Services Specialist | Answers employee HR questions in a central service center and processes transactions in volume. |
| Onboarding Specialist | Gets new hires through paperwork, background checks, and first-day setup. |
| Global Mobility / Immigration Specialist | Handles relocations and work authorization, including H-1B and other visa sponsorship, working with outside immigration counsel. |

#### Payroll

| Title | What it means |
|---|---|
| Payroll Specialist | Processes pay and timekeeping, fixes pay errors. |
| Payroll Analyst | Reconciles payroll, handles payroll tax filings and audits. |
| Payroll Manager | Runs payroll. Often reports to Finance, not HR. |

### Titles specific to one sector

#### Federal government

Nearly every federal HR professional has the title **Human Resources Specialist** (series GS-0201), with a specialty in parentheses: Recruitment and Placement, Classification, Employee and Labor Relations, Information Systems, and others. Support staff are **Human Resources Assistants** (series GS-0203). Grades run from about GS-5 to GS-15. A federal search should match on the series number, since the title alone barely changes.

#### State and local government

| Title | What it means |
|---|---|
| Personnel Analyst / HR Analyst | The standard professional HR title. Covers recruiting, classification, or employee relations, depending on the assignment. |
| Personnel Technician | Paraprofessional support, roughly between an assistant and an analyst. |
| Classification and Compensation Analyst | Assigns jobs to civil service classes and pay ranges. |
| Exam Analyst / Test Developer | Writes and scores civil service exams. Unique to government merit systems. |
| Labor Relations Officer | Handles union contracts. Public-sector workforces are heavily unionized, so this is a bigger role than in most companies. |

#### Higher education

| Title | What it means |
|---|---|
| Academic Personnel Analyst / Faculty Affairs Specialist | Handles faculty appointments, promotion and tenure files, and academic policy. Often sits in the provost's office, not HR. |
| Department HR Manager / HR Business Partner | HR for one college or school inside the university. |
| Student Employment Coordinator | Runs student jobs and work-study hiring. |

#### Healthcare

| Title | What it means |
|---|---|
| Nurse Recruiter / Physician Recruiter | Recruiters who specialize in clinical hiring. |
| Employee Health Nurse | A clinician who handles employee health screening and work injuries. Sometimes sits in HR. |
| Credentialing Specialist | Verifies clinicians' licenses and privileges. Looks like HR but usually sits in Medical Staff Services. |

### Titles that mislead

- **HR Manager.** At a 50-person company, this can be the only HR person. At a large company, it can mean managing a team of 20.
- **Talent.** "Talent Acquisition" is recruiting. "Talent Management" is performance and development. Some companies use "Talent" for both.
- **Business Partner.** Ranges from a senior strategic advisor to a relabeled generalist. Read the duties.
- **Specialist.** In the federal government, Specialist is a professional title. At many companies, it's entry level.
- **Analyst.** In government and universities, this is often just the generic professional title, with no analytics involved.
- **Head of People.** At an early startup, this can be a fairly junior first hire.
- **Titles outside HR that sound like HR.** Credentialing (healthcare), Title IX coordinator (usually a civil rights office), and Faculty Affairs (usually the provost) can all show up in HR searches without being HR jobs.
<!-- titles:end -->

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

The order of the checks, and every term they use, is in [Classifications](#classifications).

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

Rewrite the numbers and tables on this page from the current list (the daily run does this by itself):

```bash
python3 -m hrjobs.readme
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

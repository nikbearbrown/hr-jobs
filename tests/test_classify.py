import unittest

from hrjobs import classify as C
from hrjobs import collect, places, sources


class Scope(unittest.TestCase):
    def test_strong_titles_are_hr(self):
        for t in ("Senior Technical Recruiter", "HR Business Partner", "Payroll Specialist", "HRIS Analyst",
                  "People Operations Manager", "Workday HCM Analyst", "L&D Manager", "Training Specialist"):
            self.assertEqual(C.scope(t), "title", t)

    def test_lookalikes_are_not_hr(self):
        for t in ("ML Training Engineer", "Customer Specialist", "Customer Onboarding Specialist",
                  "Information Systems Security Officer", "Data Classification Engineer", "Software Engineer"):
            self.assertIsNone(C.scope(t), t)

    def test_department_and_source(self):
        self.assertEqual(C.scope("Program Manager", "People & Talent"), "department")
        self.assertEqual(C.scope("Director", None, source_is_hr=True), "source")
        self.assertIsNone(C.scope("Program Manager", "Engineering"))


class Classify(unittest.TestCase):
    CASES = {
        "Academic Personnel Analyst": "academic_personnel",
        "Human Resources Specialist (Military)": "military_hr",
        "Labor Relations Specialist": "labor_relations",
        "HR Specialist (Employee and Labor Relations)": "labor_relations",   # lands here on purpose
        "Employee Relations Specialist": "employee_relations",
        "Workplace Investigator": "employee_relations",
        "EEO Officer": "eeo",
        "Senior Compensation Analyst": "compensation",
        "Human Resources Specialist (Classification)": "compensation",
        "Total Rewards Analyst": "compensation",
        "Leave Administrator": "benefits_leave",
        "Benefits Analyst": "benefits_leave",
        "Human Resources Specialist (Recruitment & Placement)": "talent_acquisition",
        "Sourcer": "talent_acquisition",
        "Talent Management Specialist": "learning_od",    # despite the name, not recruiting
        "Organizational Development Consultant": "learning_od",
        "HR Specialist (Information Systems)": "hris_analytics",
        "People Analytics Analyst": "hris_analytics",
        "Payroll Analyst": "payroll",
        "HR Coordinator": "hr_operations",
        "HR Shared Services Analyst": "hr_operations",
        "Chief People Officer": "hr_strategy",
        "Workforce Planning Manager": "hr_strategy",
        "HR Generalist": "generalist",
        "People Partner": "generalist",
        "HR Manager": "generalist",
    }

    def test_titles(self):
        for title, want in self.CASES.items():
            self.assertEqual(C.classify(title), (want, "title"), title)

    def test_order_specific_before_generalist(self):
        self.assertEqual(C.classify_title("HR Business Partner, Compensation")[0:], "compensation")

    def test_whole_words_only(self):
        # the plain substring "er specialist" would have matched this
        self.assertIsNone(C.classify_title("Customer Specialist"))

    def test_generic_title_uses_the_ad_text(self):
        ad = ("Processes position classification actions, conducts desk audits and writes classification "
              "determinations. Reviews position descriptions for pay setting.")
        self.assertEqual(C.classify("HR Analyst III", ad), ("compensation", "description"))

    def test_generic_title_without_a_clear_ad_stays_unclassified(self):
        self.assertEqual(C.classify("HR Analyst III", "Great benefits and training. Competitive compensation."),
                         ("unclassified", "none"))
        self.assertEqual(C.classify("Human Resources Specialist"), ("unclassified", "none"))


class Annotate(unittest.TestCase):
    def test_role_word_and_level(self):
        self.assertEqual(C.role_word("Senior Compensation Analyst"), "analyst")
        self.assertEqual(C.level("Senior Compensation Analyst"), "senior")
        self.assertEqual(C.level("HR Specialist II"), "II")
        self.assertEqual(C.level("Human Resources Specialist", "GS-9 to GS-11"), "GS-9 to GS-11")
        self.assertEqual(C.role_word("Director of Total Rewards"), "director")
        self.assertEqual(C.role_word("Supervisory Human Resources Specialist"), "manager")

    def test_soc_codes(self):
        self.assertEqual(C.soc_code("compensation", "analyst"), "13-1141")
        self.assertEqual(C.soc_code("compensation", "director"), "11-3111")
        self.assertEqual(C.soc_code("labor_relations", "specialist"), "13-1075")
        self.assertEqual(C.soc_code("hr_operations", "assistant"), "43-4161")
        self.assertEqual(C.soc_code("payroll", "specialist"), "43-3051")
        self.assertEqual(C.soc_code("unclassified", "analyst"), "")

    def test_flags(self):
        self.assertIn("talent_ambiguous", C.flags("Talent Partner"))
        self.assertNotIn("talent_ambiguous", C.flags("Talent Acquisition Partner"))
        self.assertIn("hr_manager_scope_unknown", C.flags("HR Manager"))
        self.assertIn("may_sit_outside_hr", C.flags("Credentialing Specialist"))
        self.assertIn("filed_outside_hr", C.flags("Payroll Manager", "title", "Finance"))

    def test_sector(self):
        self.assertEqual(C.sector("Internal Revenue Service", "usajobs"), "federal")
        self.assertEqual(C.sector("Northeastern University", "greenhouse"), "higher education")
        self.assertEqual(C.sector("Acme Robotics", "ashby"), "corporate")


class Places(unittest.TestCase):
    def test_read_place(self):
        self.assertEqual(places.read_place("New York, NY"), ("US", "New York", "NY"))
        self.assertEqual(places.read_place("Austin, Texas, United States"), ("US", "Austin", "TX"))
        self.assertEqual(places.read_place("Remote - US")[0], "US")
        self.assertEqual(places.read_place("London, UK")[0], "other")
        self.assertEqual(places.read_place("Bangalore, IN")[0], "other")
        self.assertEqual(places.read_place("Remote")[0], "unknown")

    def test_summarise_keeps_a_job_with_one_us_location(self):
        got = places.summarise(["London, UK", "Boston, MA"])
        self.assertEqual((got["country"], got["city"], got["state"]), ("US", "Boston", "MA"))
        self.assertEqual(places.summarise(["Dublin, Ireland"])["country"], "other")
        self.assertEqual(places.summarise(["Remote"])["remote"], "remote")


def row(**kw):
    base = {c: "" for c in collect.COLUMNS}
    base.update(kw)
    return base


class Dedupe(unittest.TestCase):
    def test_same_requisition_keeps_the_better_source(self):
        rows = [row(key="a", employer="Acme", requisition="R-1", title="Recruiter", source="adzuna"),
                row(key="b", employer="ACME", requisition="R-1", title="Recruiter (NYC)", source="greenhouse")]
        kept, dropped = collect.dedupe(rows)
        self.assertEqual(([r["key"] for r in kept], dropped), (["b"], 1))

    def test_no_requisition_falls_back_to_title_and_city(self):
        rows = [row(key="a", employer="Acme", title="HR Generalist", city="Boston", source="lever"),
                row(key="b", employer="Acme", title="HR Generalist", city="Boston", source="adzuna"),
                row(key="c", employer="Acme", title="HR Generalist", city="Denver", source="adzuna")]
        kept, dropped = collect.dedupe(rows)
        self.assertEqual((sorted(r["key"] for r in kept), dropped), (["a", "c"], 1))


class CarryForward(unittest.TestCase):
    def test_a_source_that_is_down_keeps_its_open_listings(self):
        previous = {"f1": row(key="f1", source="usajobs", board="0201-0203", closes="2026-12-01"),
                    "f2": row(key="f2", source="usajobs", board="0201-0203", closes="2026-11-01"),   # closed since
                    "g1": row(key="g1", source="greenhouse", board="acme"),                          # board is up: gone
                    "g2": row(key="g2", source="greenhouse", board="downco")}
        rows = [row(key="n1", source="greenhouse", board="acme")]
        stats = {"sources_down": ["usajobs"], "boards_failed": ["greenhouse/downco"]}
        kept = collect.carry_forward(rows, previous, stats, "2026-11-11")
        self.assertEqual((kept, sorted(r["key"] for r in rows)), (2, ["f1", "g2", "n1"]))


class Readers(unittest.TestCase):
    def test_usajobs_record(self):
        item = {"MatchedObjectId": "123", "MatchedObjectDescriptor": {
            "PositionID": "ABC-26-1", "PositionTitle": "Human Resources Specialist (Classification)",
            "PositionURI": "https://www.usajobs.gov/job/123", "OrganizationName": "Example Agency",
            "DepartmentName": "Department of Examples",
            "PositionLocation": [{"LocationName": "Denver, Colorado", "CountryCode": "United States",
                                  "CountrySubDivisionCode": "Colorado", "CityName": "Denver, Colorado"}],
            "PositionRemuneration": [{"MinimumRange": "60000", "MaximumRange": "80000", "RateIntervalCode": "PA"}],
            "JobGrade": [{"Code": "GS"}], "PublicationStartDate": "2026-11-01T00:00:00",
            "ApplicationCloseDate": "2026-11-30T23:59:59",
            "UserArea": {"Details": {"LowGrade": "9", "HighGrade": "11", "HiringPath": ["public"],
                                     "JobSummary": "Classifies positions.", "MajorDuties": ["Desk audits."]}}}}
        r = sources._usajobs_record(item)
        self.assertEqual((r["requisition"], r["grade"], r["closes"], r["open_to"]),
                         ("ABC-26-1", "GS-9 to GS-11", "2026-11-30", "public"))
        self.assertEqual(r["salary"], "USD 60,000-80,000 per year")
        self.assertEqual(places.summarise(r["locations"], r["country_codes"])["state"], "CO")

    def test_adzuna_record_drops_predicted_salary(self):
        r = sources._adzuna_record({"id": 9, "title": "<strong>HR</strong> Generalist", "created": "2026-11-02T10:00:00Z",
                                    "company": {"display_name": "Acme"}, "salary_min": 50000, "salary_max": 50000,
                                    "salary_is_predicted": "1", "redirect_url": "https://example.org/9",
                                    "location": {"area": ["US", "Ohio", "Franklin County", "Columbus"]}})
        self.assertEqual((r["title"], r["salary"], r["locations"]), ("HR Generalist", "", ["Columbus, Ohio"]))


if __name__ == "__main__":
    unittest.main()

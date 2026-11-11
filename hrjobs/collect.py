"""Daily run: read every source, keep the HR jobs in the United States, classify, annotate, de-duplicate, write.

    python3 -m hrjobs.collect                  # full run, writes data/ and reports/
    python3 -m hrjobs.collect --limit-boards 20 --out /tmp/hr-test   # quick trial that touches nothing here

Writes:
    data/current/jobs.csv        every open listing, one row each
    data/summary/DATE.json       the day's counts
    reports/DATE.md, reports/latest.md   counts table plus the listings first seen that day

Exit code 2 means more than half the company boards failed to load; nothing is written in that case.
"""
import argparse
import collections
import concurrent.futures
import csv
import datetime
import hashlib
import json
import sys
from pathlib import Path

from . import classify as C
from . import places, sources

ROOT = Path(__file__).resolve().parent.parent
COLUMNS = ["key", "sub_discipline", "classified_by", "title", "employer", "sector", "city", "state", "remote",
           "places", "role_word", "level", "soc_code", "salary", "posted", "closes", "requisition", "department",
           "open_to", "flags", "source", "board", "url", "first_seen"]
SECTORS = ["corporate", "federal", "state", "local government", "higher education", "healthcare", "nonprofit"]


def make_key(raw):
    return hashlib.sha1(f"{raw['source']}|{raw['board']}|{raw['source_id']}".encode()).hexdigest()[:12]


def build_row(raw, scoped_by, today):
    """One raw record -> one output row, or (None, reason) when the listing is out of scope."""
    place = places.summarise(raw["locations"], raw["country_codes"], raw["workplace"], raw["title"])
    if place["country"] == "other":
        return None, "outside_us"
    if raw["closes"] and raw["closes"] < today:
        return None, "closed"
    if scoped_by == "department" and not C.names_hr(raw["title"]):
        sub, how = C.clearly_hr_text(raw["description"]), "description"
        if not sub:
            return None, "hr_department_other_work"
    else:
        sub, how = C.classify(raw["title"], raw["description"])
    role = C.role_word(raw["title"])
    return {
        "key": make_key(raw), "sub_discipline": sub, "classified_by": how, "title": raw["title"].strip(),
        "employer": raw["employer"], "sector": C.sector(raw["employer"], raw["source"]),
        "city": place["city"], "state": place["state"], "remote": place["remote"], "places": place["places"],
        "role_word": role, "level": C.level(raw["title"], raw["grade"]), "soc_code": C.soc_code(sub, role),
        "salary": raw["salary"], "posted": raw["posted"], "closes": raw["closes"], "requisition": raw["requisition"],
        "department": raw["department"], "open_to": raw["open_to"],
        "flags": "; ".join(C.flags(raw["title"], scoped_by, raw["department"] if raw["source"] != "usajobs" else None)), "source": raw["source"], "board": raw["board"], "url": raw["url"],
        "first_seen": today,
    }, None


def dedupe(rows):
    """One job on several sources is one listing: match on employer plus requisition number, else on
    employer, title and city. The copy from the highest-priority source stays."""
    rank = {s: i for i, s in enumerate(sources.SOURCE_PRIORITY)}
    groups = collections.defaultdict(list)
    for r in rows:
        who = C.norm(r["employer"])
        match = (who, "req", C.norm(r["requisition"])) if r["requisition"] else (who, C.norm(r["title"]), C.norm(r["city"]))
        groups[match].append(r)
    kept, dropped = [], 0
    for group in groups.values():
        best = min(rank.get(r["source"], 99) for r in group)
        keep = [r for r in group if rank.get(r["source"], 99) == best]
        dropped += len(group) - len(keep)
        kept.extend(keep)
    return kept, dropped


def load_overrides(path):
    """annotations/overrides.csv: key, sub_discipline, note. A hand annotation beats the classifier."""
    out = {}
    if path.is_file():
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key, sub = (row.get("key") or "").strip(), (row.get("sub_discipline") or "").strip()
                if key and sub in C.ORDER:
                    out[key] = sub
    return out


def load_previous(path):
    """Yesterday's rows by key, or None when there is no earlier file (the first run)."""
    if not path.is_file():
        return None
    with open(path, newline="", encoding="utf-8") as f:
        return {row["key"]: {c: row.get(c, "") for c in COLUMNS} for row in csv.DictReader(f)}


def carry_forward(rows, previous, stats, today):
    """A source that could not be read today keeps its last known listings (minus any now past their close
    date). Otherwise one bad day would delete them and bring them back as 'new'."""
    have = {r["key"] for r in rows}
    boards_down = {tuple(b.split("/", 1)) for b in stats["boards_failed"]}
    kept = 0
    for key, old in (previous or {}).items():
        down = old["source"] in stats["sources_down"] or (old["source"], old["board"]) in boards_down
        if down and key not in have and not (old["closes"] and old["closes"] < today):
            rows.append(old)
            kept += 1
    return kept


def sort_rows(rows):
    def inverse(day):   # newest first inside a text sort
        return "".join(chr(ord("9") - ord(c) + ord("0")) if c.isdigit() else c for c in (day or "0000-00-00"))
    return sorted(rows, key=lambda r: (C.ORDER.index(r["sub_discipline"]), inverse(r["posted"]), r["employer"].lower(),
                                       r["title"].lower(), r["key"]))


def collect(boards, workers=3, log=print):
    """Read all sources. Returns (rows, stats)."""
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    stats = {"boards_total": len(boards), "boards_ok": 0, "boards_failed": [], "postings_read": 0,
             "dropped": collections.Counter(), "sources": {}, "sources_down": []}
    rows = []

    def take(raws, source_is_hr):
        for raw in raws:
            stats["postings_read"] += 1
            scoped_by = C.scope(raw["title"], raw["department"], source_is_hr)
            if not scoped_by:
                stats["dropped"]["not_hr"] += 1
                continue
            row, why = build_row(raw, scoped_by, today)
            if row is None:
                stats["dropped"][why] += 1
            else:
                rows.append(row)

    def one(board):
        return board, sources.read_board(board["provider"], board["slug"], board["employer"])

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for n, (board, (ok, raws)) in enumerate(pool.map(one, boards), 1):
            if ok:
                stats["boards_ok"] += 1
                take(raws, False)
            else:
                stats["boards_failed"].append(f"{board['provider']}/{board['slug']}")
            if n % 100 == 0:
                log(f"  boards read: {n}/{len(boards)}, HR listings so far: {len(rows)}")
    stats["sources"]["company boards (Greenhouse, Lever, Ashby)"] = (
        f"ok: {stats['boards_ok']} of {len(boards)} boards answered" if boards else "skipped")

    for sid, name, reader in (("usajobs", "USAJOBS (series 0201, 0203)", sources.read_usajobs),
                              ("adzuna", "Adzuna (US, HR category)", sources.read_adzuna)):
        status, raws = reader()
        stats["sources"][name] = f"ok: {len(raws)} postings" if status == "ok" else status
        if status != "ok":
            stats["sources_down"].append(sid)
        log(f"  {name}: {stats['sources'][name]}")
        take(raws, True)
    return rows, stats


def summarise(rows, stats, date, new_keys, baseline):
    by = lambda col: dict(collections.Counter(r[col] for r in rows).most_common())
    table = collections.defaultdict(collections.Counter)
    for r in rows:
        table[r["sub_discipline"]][r["sector"]] += 1
    return {
        "date": date, "total": len(rows), "new_today": len(new_keys), "baseline_run": baseline,
        "by_sub_discipline": {s: sum(table[s].values()) for s in C.ORDER if s in table},
        "by_sector": by("sector"), "by_source": by("source"), "classified_by": by("classified_by"),
        "sub_discipline_by_sector": {s: dict(table[s]) for s in C.ORDER if s in table},
        "postings_read": stats["postings_read"], "dropped": dict(stats["dropped"]), "sources": stats["sources"],
        "carried_forward": stats.get("carried_forward", 0),
        "boards_failed": sorted(stats["boards_failed"]),
    }


def line(r):
    where = ", ".join(p for p in (r["city"], r["state"]) if p) or r["places"] or "location not stated"
    bits = [where + (f" ({r['remote']})" if r["remote"] else "")]
    if r["level"]:
        bits.append(r["level"])
    if r["salary"]:
        bits.append(r["salary"])
    if r["posted"]:
        bits.append(f"posted {r['posted']}")
    if r["closes"]:
        bits.append(f"closes {r['closes']}")
    return f"- [{r['title']}]({r['url']}), {r['employer']}. " + " · ".join(bits)


def report(rows, summary, new_keys):
    s = summary
    sectors = [c for c in SECTORS if c in s["by_sector"]] + [c for c in s["by_sector"] if c not in SECTORS]
    out = [f"# HR jobs, {s['date']}", "",
           f"**{s['total']:,} open HR listings in the United States**, from {s['postings_read']:,} postings read. "
           + ("This is the first run, so every listing is new." if s["baseline_run"] else f"{s['new_today']:,} are new today."),
           "", "No ranking: listings are grouped by sub-discipline, newest first. The full list is "
           "[data/current/jobs.csv](../data/current/jobs.csv).", "",
           "## Listings by sub-discipline and sector", "",
           "| Sub-discipline | " + " | ".join(sectors) + " | Total |", "|---|" + "---:|" * (len(sectors) + 1)]
    for sub, counts in s["sub_discipline_by_sector"].items():
        out.append(f"| {sub} | " + " | ".join(str(counts.get(c, "")) for c in sectors) + f" | {sum(counts.values())} |")
    out.append("| **Total** | " + " | ".join(f"**{s['by_sector'][c]}**" for c in sectors) + f" | **{s['total']}** |")
    out += ["", "Sector is read from the source (federal) or guessed from the employer's name; everything else "
            "defaults to corporate.", "", "## How the listings were classified", "",
            "| Method | Listings |", "|---|---:|"]
    names = {"title": "By the title", "description": "By the ad text (title too generic)",
             "annotation": "By a hand annotation", "none": "Not classified (title and ad text both too generic)"}
    out += [f"| {names.get(k, k)} | {v} |" for k, v in s["classified_by"].items()]
    out += ["", "## Sources read", "", "| Source | Result |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in s["sources"].items()]
    d = s["dropped"]
    out += ["", f"Left out: {d.get('not_hr', 0):,} postings that are not HR jobs, {d.get('hr_department_other_work', 0):,} "
            f"filed under an HR department but doing other work (assistants, office staff, interns for other teams), "
            f"{d.get('outside_us', 0):,} outside the United States, {d.get('closed', 0):,} past their close date, "
            f"{d.get('duplicate', 0):,} duplicates."]
    if s["carried_forward"]:
        out += ["", f"{s['carried_forward']:,} listings are carried forward from the last successful read of a source "
                "that could not be read today."]
    if s["boards_failed"]:
        out += ["", f"{len(s['boards_failed'])} company boards did not answer: " + ", ".join(s["boards_failed"][:40])
                + (" and more." if len(s["boards_failed"]) > 40 else ".")]
    if not s["baseline_run"]:
        out += ["", "## New today"]
        fresh = [r for r in rows if r["key"] in new_keys]
        if not fresh:
            out += ["", "Nothing new today."]
        for sub in C.ORDER:
            group = [r for r in fresh if r["sub_discipline"] == sub]
            if group:
                out += ["", f"### {sub} ({len(group)})", ""] + [line(r) for r in group[:200]]
                if len(group) > 200:
                    out.append(f"- and {len(group) - 200} more in jobs.csv")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT, help="folder to write data/ and reports/ into (default: the repo)")
    ap.add_argument("--limit-boards", type=int, help="read only the first N company boards (for a trial run)")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--date", default=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"))
    a = ap.parse_args(argv)

    boards = json.loads((ROOT / "config" / "boards.json").read_text())[: a.limit_boards]
    print(f"hr-jobs collect {a.date}: {len(boards)} company boards")
    rows, stats = collect(boards, a.workers)
    if boards and len(stats["boards_failed"]) > len(boards) / 2:
        print(f"more than half the boards failed ({len(stats['boards_failed'])} of {len(boards)}); writing nothing")
        return 2

    rows, stats["dropped"]["duplicate"] = dedupe(rows)
    overrides = load_overrides(ROOT / "annotations" / "overrides.csv")
    for r in rows:
        if r["key"] in overrides:
            r["sub_discipline"], r["classified_by"] = overrides[r["key"]], "annotation"
            r["soc_code"] = C.soc_code(r["sub_discipline"], r["role_word"])

    current = a.out / "data" / "current" / "jobs.csv"
    previous = load_previous(current)
    baseline = previous is None
    for r in rows:
        r["first_seen"] = ((previous or {}).get(r["key"]) or {}).get("first_seen") or a.date
    new_keys = {r["key"] for r in rows if r["key"] not in (previous or {})}
    stats["carried_forward"] = carry_forward(rows, previous, stats, a.date)
    rows = sort_rows(rows)

    summary = summarise(rows, stats, a.date, new_keys, baseline)
    for sub in ("data/current", "data/summary", "reports"):
        (a.out / sub).mkdir(parents=True, exist_ok=True)
    with open(current, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    (a.out / "data" / "summary" / f"{a.date}.json").write_text(json.dumps(summary, indent=1) + "\n")
    text = report(rows, summary, new_keys)
    (a.out / "reports" / f"{a.date}.md").write_text(text)
    (a.out / "reports" / "latest.md").write_text(text)
    print(f"wrote {len(rows)} listings ({len(new_keys)} new); by sub-discipline: {summary['by_sub_discipline']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

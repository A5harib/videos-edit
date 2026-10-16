import json
from pathlib import Path
def big(eye, text, sm=False): return f'<div class="card"><div class="eyebrow">{eye}</div><div class="big{" sm" if sm else ""}">{text}</div></div>'
def rows(title, items, on, cls="r3"):
    r = "".join(f'<div class="row{"" if i < on else " off"}"><span class=k>{k}</span>{t}</div>' for i, (k, t) in enumerate(items))
    return f'<div class="card"><h1>{title}</h1><div class="rows {cls}">{r}</div></div>'
def chips(title, items, on=None):
    on = len(items) if on is None else on
    c = "".join(f'<span class="chip{" red" if i == 0 else ""}{"" if i < on else " off"}">{t}</span>' for i, t in enumerate(items))
    return f'<div class="card"><h1>{title}</h1><div class="chips">{c}</div></div>'
ben = [("1","No re-entry rule"),("2","Open a bank account"),("3","Medical insurance"),("4","Sponsor your family")]
spon = ["Kids","Wife","Maid","Driver"]
prop = [("&#10003;","Investor: 750,000"),("&#10003;","From 1 Sept: 450,000"),("&#10003;","Golden: 2 million")]
proc = [("&#10003;","Golden Visa: 3 days"),("&#10003;","Investor: 15 to 20 days")]
V = {
 "v4": [(18.46, big("Today's video", "Golden Visa <em>and</em> Investor Visa", True)),
        (30.64, big("At the end of the video", "Very good <em>news</em>")),
        (40.64, big("What is the Golden Visa", "<em>10-year</em> Dubai PR")),
        (57.12, big("Coming up", "Golden Visa <em>vs</em> Investor Visa", True))],
 "v5": [(0, big("Golden Visa", "<em>10-year</em> Dubai PR")),
        (5.0, rows("Golden Visa benefits", ben, 1, "r4")), (15.66, rows("Golden Visa benefits", ben, 2, "r4")),
        (17.86, rows("Golden Visa benefits", ben, 3, "r4")), (32.12, rows("Golden Visa benefits", ben, 4, "r4")),
        (33.32, chips("You can sponsor", spon, 1)), (39.70, chips("You can sponsor", spon, 2)),
        (41.28, chips("You can sponsor", spon, 3)), (42.92, chips("You can sponsor", spon, 4)),
        (54.94, big("PR means", "Permanent residency for <em>10 years</em>", True)),
        (69.98, big("Small fee", "<em>Renewed</em> for the next 10 years", True)),
        (88.10, chips("Kids' education: campuses in UAE", ["Canada","America","UK"])),
        (108.10, big("On the Golden Visa", "Do any <em>business</em>"))],
 "v6": [(0, chips("Banking", ["Bank account","Mortgage","Credit cards"])),
        (16.40, big("On this visa", "Do a <em>business</em> or a <em>job</em>", True)),
        (32.38, chips("Tax-free income", ["Business","Job","Property rental"])),
        (58.78, rows("Investor Visa", [("&#10003;","Same benefits"),("&#10003;","Only two years")], 1)),
        (63.82, rows("Investor Visa", [("&#10003;","Same benefits"),("&#10003;","Only two years")], 2)),
        (75.52, rows("Property you need", prop, 1, "r3 sm")), (80.70, rows("Property you need", prop, 2, "r3 sm")),
        (86.12, rows("Property you need", prop, 3, "r3 sm")),
        (91.10, big("Coming up", "The shortest way to a <em>2 million</em> property", True)),
        (106.60, rows("Golden vs Investor", [("&#10003;","Golden: 10 years"),("&#10003;","Investor: 2 years"),("&#10003;","Same benefits")], 3))],
 "v1": [(0, chips("Same benefits", ["Banking","Kids education","Insurance","Medical","Sponsorships","Property","Business","Job"])),
        (22.20, big("International travel", "Easy visas for <em>America, UK, Canada</em>", True)),
        (52.80, rows("The only difference", [("&#10003;","Golden: 10 years"),("&#10003;","Investor: 2 years"),("&#10003;","Both renewable")], 3)),
        (77.90, big("How you get it", "<em>Buy a property</em> in UAE", True)),
        (88.30, big("Investor Visa", "450,000 to <em>750,000</em>", True)),
        (93.80, big("Golden Visa", "<em>2 million</em> property", True)),
        (103.40, big("Important point", "Buy on a <em>down payment</em>", True)),
        (112.40, big("Dubai Land Department", "A document that says <em>you own it</em>", True))],
 "v3": [(0, big("Down payment paid", "You get the <em>Oqood</em>")),
        (15.00, big("With the Oqood", "Apply for the <em>Golden</em> or <em>Investor</em> Visa", True)),
        (40.00, rows("Processing time", proc, 1, "r3 sm")), (45.00, rows("Processing time", proc, 2, "r3 sm")),
        (64.00, big("Within three days", "Visas for your <em>wife and kids</em>", True)),
        (70.00, big("The golden opportunity", "My company <em>pays</em> and <em>processes</em> it", True)),
        (89.00, big("If you buy from me", "Your Golden Visa is <em>my responsibility</em>", True)),
        (100.00, chips("Any questions?", ["WhatsApp me","Subscribe","DM me"]))],
 "v2": [(0, big("According to your budget", "I suggest the right <em>developer</em>", True)),
        (16.00, big("Me and my company", "<em>15 years</em> in this field", True)),
        (33.00, big("Oqood", "The property <em>ownership</em> documents", True)),
        (37.00, big("Once the Oqood arrives", "Golden Visa in <em>3 days</em>", True)),
        (44.00, big("Process and payment", "<em>100%</em> my responsibility", True)),
        (54.00, chips("Talk to me", ["Subscribe","DM me","WhatsApp"])),
        (74.50, big("Subscribe", "WhatsApp me for <em>full details</em>", True))],
}
job = json.loads(Path("job.json").read_text())
src = {"v1":"Snapchat-1611768532.mp4","v2":"Snapchat-1632222677.mp4","v3":"Snapchat-1825273248.mp4",
       "v4":"Snapchat-2042960597.mp4","v5":"Snapchat-2055819348.mp4","v6":"Snapchat-675608657.mp4"}
dur = {"v1":120.0,"v2":82.85,"v3":120.0,"v4":66.18,"v5":120.0,"v6":120.0}
order = ["v4","v5","v6","v1","v3","v2"]
job["landscape"] = True; job["transpose"] = 2
job["src_dir"] = str(Path("src").resolve()); job["out_dir"] = str(Path("parts").resolve())
for vid, cards in V.items():
    html = '<!doctype html>\n<html><head><meta charset="utf-8"><link rel="stylesheet" href="cards.css"></head><body>\n' + "\n".join(c for _, c in cards) + "\n</body></html>\n"
    Path(f"cards/{vid}.html").write_text(html, encoding="utf-8")
    end = 83.0 if vid == "v2" else dur[vid]
    job["videos"][vid] = {"src": src[vid], "out": f"part{order.index(vid)+1}.mp4", "trim": [0.0, end],
                          "cap_size": 70, "timeline": [[t, i] for i, (t, _) in enumerate(cards)]}
Path("job.json").write_text(json.dumps(job, indent=1))
print("ok")

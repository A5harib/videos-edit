import json, re, sys
from pathlib import Path
# phrase fixes: old words -> new words ('' drops a word, its time goes to the previous one)
FIX = {
 "v4": [("Hello Assalamu alaikum.","Hello, assalam o-alaikum."),("So today video","So today's video"),
        ("So today video","So today's video"),("investor meter visa","investor _ visa,"),
        ("I'm going to find you","I'm going to define _"),("10 years peak","10 years PR"),
        ("There is our","There are other")],
 "v5": [("Golden visa golden visa","Golden visa. _ _"),("your servants have recommended getting","your servants _ are getting"),
        ("as your mate","as your maid"),("on this P on this PR","on this _ _ _ PR"),
        ("your spawn your sponsors servants mates","your spouse, your sponsored servants, maids,"),
        ("is where we were esteemed","is very _ _ esteemed,"),("take your students","take your students,")],
 "v6": [("advantages of the Go of the","advantages _ _ _ of the"),("first bank","first, bank"),
        ("2 million 2","2 million. 2")],
 "v1": [("from a firm, UAE","from _ _ UAE"),("like 750,000, no, 2 million,","like 750,000, no, 2 million,")],
 "v3": [("collaboration visa with","collaboration _ with"),("link number","WhatsApp number")],
 "v2": [],
}
SUB = {"Huey":"UAE","Huey.":"UAE.","akut.":"Oqood.","akut,":"Oqood,","akut":"Oqood","accout":"Oqood","accout.":"Oqood.","accout,":"Oqood,"}
for vid in FIX:
    d = json.loads(Path(f"tr/{vid}.json").read_text(encoding="utf-8"))
    W = [w for s in d["segments"] for w in s["words"] if w["w"].strip()]
    for w in W: w["w"] = w["w"].strip()
    # glue split tokens: "-entry", ",000"
    out = []
    for w in W:
        if out and (w["w"].startswith("-") or w["w"].startswith(",0")):
            out[-1]["w"] += w["w"]; out[-1]["e"] = w["e"]
        else: out.append(w)
    W = out
    for w in W: w["w"] = SUB.get(w["w"], w["w"])
    for old, new in FIX[vid]:
        o, n = old.split(), new.split(); hit = 0
        for i in range(len(W) - len(o) + 1):
            if [x["w"] for x in W[i:i+len(o)]] == o:
                for k in range(len(o)): W[i+k]["w"] = n[k] if k < len(n) else "_"
                hit += 1
        if not hit: print(vid, "NO MATCH:", old)
    res = []
    for w in W:
        if w["w"] == "_":
            if res: res[-1]["e"] = w["e"]
            continue
        res.append(w)
    d["segments"] = [{"words": res}]
    Path(f"tr_fix/{vid}.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")

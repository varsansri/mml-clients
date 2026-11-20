"""Build the Mi Media Labs "who we work for" page.

Inputs: facts.jsonl (public facts per brand, with sources) and the scraped
portfolio (portfolio_tagged.json). Output: index.html + impact.csv.
Only facts found online are shown. Mi Media's own impact numbers come
from the team (impact.csv), never guessed.
"""
import csv, html, json, collections, re
from pathlib import Path

HERE = Path(__file__).parent
PORT = Path(r"C:/Users/varsa/mimedialabs-seo/audit/portfolio_tagged.json")

# one big number per brand: (figure, label)
HEAD = {
    "Salzer": ("₹1,418 cr", "revenue, FY2025 · listed on NSE"),
    "CRI Pumps": ("120", "countries sell its pumps"),
    "Ramakrishna Pain Institute": ("1,000", "beds at Sri Ramakrishna Hospital"),
    "Anjappar": ("50+", "restaurants worldwide"),
    "Covai Anganan": ("1926", "first biriyani served"),
    "Darmona Premium Tea": ("1984", "single-estate tea since"),
    "Shree Kumaran Thangamaligai": ("7", "cities with showrooms"),
    "Karpagam": ("1971", "jewellers since"),
    "Avila Convent School": ("1967", "school since"),
    "VLB Janakiammal College": ("1991", "college since · NAAC B++"),
    "Coimbatore Vizha": ("18", "editions of the city festival"),
    "YI": ("180+", "members, India's largest Yi chapter (2016)"),
    "Astral": ("200+", "client companies"),
    "Cyclecount": ("600", "locations audited across India"),
    "Latchelp": ("16,000+", "mothers helped"),
    "oodu implementers": ("100+", "Odoo enterprise projects"),
    "Servall Engineering": ("400 t", "a day: biggest paper machine built"),
    "Essensuals by Toni & Guy": ("London", "salon brand, franchise salons across India"),
    "Anamalais Toyota": ("3", "districts: Coimbatore, Tiruppur, Erode"),
    "ACTA": ("ISO", "27001 + 9001 certified"),
    "Erp Audit": ("6", "ERP systems audited"),
    "Hystan Spinning Mills": ("101–500", "people on staff"),
    "Window Works": ("250", "customers since 2015"),
    "Rock Tawa": ("36", "cast-iron products"),
    "Flavoursavenue": ("60", "products, own farm"),
    "DX-Sound": ("19", "speakers in the range"),
    "Hanging Huts": ("Only", "eco resort in Kotagiri"),
    "Poorna Ayur": ("2", "Ayurveda centres"),
    "Skanda": ("5", "pack sizes, own factory"),
    "Naati Grains": ("Pan-India", "online store"),
    "ASM Melange Yarns": ("Tiruppur", "India's knitwear capital"),
    "Lotus Property Developers": ("2–3 BHK", "homes in Coimbatore"),
}

IND = {
    "food": "Food & drink", "industrial-b2b": "Industry", "education": "Education",
    "real-estate": "Real estate", "jewellery": "Jewellery", "fashion-textile": "Fashion & textile",
    "beauty-wellness": "Beauty & wellness", "healthcare": "Healthcare",
    "professional-services": "Services", "events-media": "Events & media", "hospitality": "Hospitality",
}
CAT = {"branding": "Branding", "brouchure": "Brochure", "package_design": "Packaging",
       "website": "Website", "logo": "Logo", "digital_marketing": "Digital marketing"}
# portfolio names that are not brands, or are duplicates of another name
SKIP = {"Package Design", "Bar Menu Card Design", "Menu Card Design", "Paper Bag Package Design"}
ALIAS = {"Akshyam": "Akshayam", "Freeshfeel": "Fresh Feel", "Schatz Enterprises": "SCHATZ",
         "Digital Marketing SEO / SMM - BirthdayBlasters": "Birthday Blasters",
         "Digital Marketing SEO / SMM - LunchBox": "Lunchbox",
         "Lunchbox Restaurant Standee Design": "Lunchbox",
         "Digital Marketing SEO / SMM - Haji Ali": "Haji Ali",
         "PKR Brochure": "PKR", "Sysres Brochure": "Sysres", "Vcvv Broucher": "VCVV",
         "Seirra Logo": "Seirra", "lipbamp": "Lip balm",
         "Thiru Janarthana Matriculation Higher Secondary Sc": "Thiru Janarthana Matric School"}
NICE = {"oodu implementers": "Oodu Implementers", "YI": "Young Indians (CII) Coimbatore",
        "Ramakrishna Pain Institute": "Sri Ramakrishna Pain Institute", "Astral": "Astral Business Consulting",
        "Karpagam": "Karpagam Jewellers", "Salzer": "Salzer Electronics", "Skanda": "Skanda Premium Ghee",
        "Erp Audit": "ERP Audit", "Flavoursavenue": "Flavours Avenue"}

def esc(s): return html.escape(str(s), quote=True)

# ---- facts, merged per client
facts = collections.OrderedDict()
for line in (HERE / "facts.jsonl").read_text(encoding="utf-8").splitlines():
    if not line.strip(): continue
    r = json.loads(line)
    f = facts.setdefault(r["client"], {"facts": [], "sources": [], "site": None})
    for x in r["facts"]:
        if x not in f["facts"]: f["facts"].append(x)
    for s in r["sources"]:
        if s not in f["sources"]: f["sources"].append(s)
    f["site"] = f["site"] or r.get("site")

# ---- portfolio, grouped per client
port = json.loads(PORT.read_text(encoding="utf-8"))
work = collections.OrderedDict()
for p in port:
    name = (p.get("client") or p["name"]).strip()
    if name in SKIP: continue
    name = ALIAS.get(name, name)
    w = work.setdefault(name, {"n": 0, "cats": collections.Counter(), "ind": p.get("industry"),
                               "img": None, "url": p["url"]})
    w["n"] += 1
    w["cats"][p["cat"]] += 1
    if not w["img"] and p.get("img_ok", True) and p.get("main_img"):
        w["img"] = p["main_img"]; w["url"] = p["url"]

missing = [c for c in facts if c not in work]
assert not missing, missing

def card(name):
    f, w = facts[name], work[name]
    big, lab = HEAD.get(name, ("", ""))
    cats = " · ".join(CAT.get(c, c) for c, _ in w["cats"].most_common())
    li = "".join(f"<li>{esc(x)}</li>" for x in f["facts"])
    src = " ".join(f'<a href="{esc(s)}" rel="noopener" target="_blank">{i+1}</a>'
                   for i, s in enumerate(f["sources"]))
    img = (f'<a class="shot" href="{esc(w["url"])}" target="_blank" rel="noopener">'
           f'<img src="{esc(w["img"])}" alt="{esc(NICE.get(name, name))}: our work" loading="lazy"></a>') if w["img"] else ""
    return f'''<article class="card" data-ind="{esc(w["ind"])}">
  {img}
  <div class="body">
    <p class="tag">{esc(IND.get(w["ind"], w["ind"]))}</p>
    <h3>{esc(NICE.get(name, name))}</h3>
    <p class="big"><b>{esc(big)}</b> <span>{esc(lab)}</span></p>
    <ul>{li}</ul>
    <p class="did"><span>We did</span> {esc(cats)} <em>({w["n"]} project{"s" if w["n"] > 1 else ""})</em></p>
    <p class="src">Sources {src}</p>
  </div>
</article>'''

# order: biggest names first (the HEAD order), then the rest with facts
order = [c for c in HEAD if c in facts] + [c for c in facts if c not in HEAD]
cards = "\n".join(card(c) for c in order)

rest = [n for n in work if n not in facts]
by_ind = collections.defaultdict(list)
for n in rest: by_ind[work[n]["ind"]].append(n)
rest_html = "".join(
    f'<div class="grp"><h4>{esc(IND.get(i, i))} <span>{len(v)}</span></h4><p>{" · ".join(esc(x) for x in sorted(v, key=str.lower))}</p></div>'
    for i, v in sorted(by_ind.items(), key=lambda kv: -len(kv[1])))

inds = collections.Counter(work[c]["ind"] for c in order)
chips = '<button class="chip on" data-f="all">All <span>{}</span></button>'.format(len(order)) + "".join(
    f'<button class="chip" data-f="{esc(i)}">{esc(IND.get(i, i))} <span>{n}</span></button>'
    for i, n in inds.most_common())

total_projects = sum(w["n"] for w in work.values())
page = (HERE / "template.html").read_text(encoding="utf-8")
page = (page.replace("{{CARDS}}", cards).replace("{{REST}}", rest_html).replace("{{CHIPS}}", chips)
            .replace("{{N_FACTS}}", str(len(order))).replace("{{N_CLIENTS}}", str(len(work)))
            .replace("{{N_PROJECTS}}", str(total_projects)).replace("{{N_REST}}", str(len(rest))))
(HERE / "index.html").write_text(page, encoding="utf-8")

# impact sheet for the team: one row per brand, only real numbers go in
with open(HERE / "impact.csv", "w", newline="", encoding="utf-8-sig") as fh:
    wr = csv.writer(fh)
    wr.writerow(["Brand", "Industry", "Projects on site", "What we did", "Public size fact (found online)",
                 "Mi Media result (team fills: number + period)", "Client OK to publish? (yes/no)"])
    for n in order + rest:
        w = work[n]
        size = " ".join(HEAD.get(n, ("", ""))).strip()
        wr.writerow([NICE.get(n, n), IND.get(w["ind"], w["ind"]), w["n"],
                     ", ".join(CAT.get(c, c) for c in w["cats"]), size, "", ""])
print(len(order), "brands with facts;", len(rest), "others;", len(work), "clients;", total_projects, "projects")

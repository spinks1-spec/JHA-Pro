
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date

st.set_page_config(page_title="JHA Builder V2", page_icon="🦺", layout="wide")

# ---------------- Risk model ----------------
LIKELIHOOD = {
    1: "Rare", 2: "Unlikely", 3: "Possible", 4: "Likely", 5: "Almost Certain"
}
SEVERITY = {
    1: "Insignificant", 2: "Minor", 3: "Moderate", 4: "Major", 5: "Catastrophic"
}

def risk_level(score):
    if score <= 4: return "Low"
    if score <= 9: return "Moderate"
    if score <= 16: return "High"
    return "Critical"

def risk_score(l, s):
    return int(l) * int(s)

# ---------------- JHA knowledge library ----------------
LIBRARY = {
"Scaffolding": [
("Inspect work area / scaffold location",
 "Uneven ground, overhead hazards, electrical contact, traffic, falling objects",
 "Inspect ground and supporting surfaces; identify overhead/electrical hazards; establish exclusion zone; coordinate with site traffic controls."),
("Unload and stage scaffold components",
 "Manual handling, pinch points, struck-by, dropped materials",
 "Use mechanical assistance where practical; team lift; maintain stable stacks; wear gloves and required PPE; keep people clear."),
("Erect scaffold",
 "Falls from height, collapse, struck-by, dropped objects, unstable structure",
 "Follow engineered/manufacturer requirements; competent workers; level and secure scaffold; install required braces, guardrails, toe boards and access; inspect progressively."),
("Install access / platforms",
 "Falls, ladder hazards, improper access, openings",
 "Provide compliant access; secure ladders; fully deck platforms; install guardrails and toe boards; maintain safe access."),
("Inspect and release scaffold",
 "Structural defects, missing components, unauthorized use",
 "Competent-person inspection; verify foundations, ties, braces, platforms and guardrails; tag/status the scaffold; restrict use until accepted.")
],
"Hot Work": [
("Prepare hot-work area", "Fire, explosion, combustible materials, fumes",
 "Remove or protect combustibles; establish fire watch; verify gas testing where required; provide suitable extinguishers and ventilation."),
("Set up welding/cutting equipment", "Electrical shock, gas release, damaged equipment",
 "Pre-use inspect equipment, leads, regulators and hoses; ground equipment; secure cylinders; separate fuel/oxygen as required."),
("Perform hot work", "Burns, fire, fumes, arc flash/UV, flying particles",
 "Use welding PPE and screens; maintain ventilation; keep fire watch; control sparks; follow hot-work permit requirements."),
("Close out hot work", "Smoldering fire, hot surfaces, residual energy",
 "Inspect surrounding areas; maintain fire watch for required period; shut down and isolate equipment; remove hot materials safely.")
],
"Lifting / Rigging": [
("Plan lift", "Dropped load, overload, struck-by, crane contact",
 "Confirm load weight and center of gravity; select suitable lifting equipment; verify capacity and lift path; establish exclusion zone."),
("Inspect rigging", "Rigging failure, dropped load, pinch points",
 "Inspect slings, shackles, hooks and hardware; remove damaged equipment; verify identification and capacity."),
("Rig load", "Pinch/crush injuries, unstable load",
 "Use approved rigging method; keep hands clear; use tag lines where appropriate; verify load balance."),
("Lift and move load", "Dropped load, swinging load, struck-by, overhead contact",
 "Use qualified operators/riggers; controlled movement; maintain communication; barricade lift zone; stop for unsafe conditions."),
("Set down and unrig", "Crush/pinch injuries, unstable load",
 "Prepare stable landing area; keep personnel clear until load is secure; release tension carefully; store rigging properly.")
],
"Excavation": [
("Locate excavation area", "Underground utilities, traffic, ground instability",
 "Confirm drawings and utility locates; establish excavation limits; implement traffic controls where required."),
("Excavate", "Cave-in, utility strike, mobile equipment interaction",
 "Use protective systems as required; maintain safe spoil/material setbacks; inspect excavation; maintain equipment exclusion zones."),
("Access excavation", "Falls, ladder/access failure, water accumulation",
 "Provide suitable access/egress; secure ladders; keep access clear; control water accumulation."),
("Work in excavation", "Cave-in, hazardous atmosphere, falling materials",
 "Complete required inspections; maintain protective system; atmospheric test where applicable; keep loads/equipment away from edges.")
],
"General Maintenance": [
("Isolate equipment", "Unexpected startup, stored energy, electrical/mechanical energy",
 "Identify energy sources; perform lockout/tagout according to site procedure; verify zero energy before work."),
("Prepare tools and work area", "Defective tools, slips/trips, struck-by",
 "Inspect tools; remove defective equipment; maintain housekeeping; establish work boundaries."),
("Perform maintenance", "Pinch points, sharp edges, chemicals, unexpected movement",
 "Use task-specific procedures and PPE; maintain isolation; use guards and tools appropriate to the task."),
("Test and return to service", "Unexpected movement, electrical exposure, personnel in danger zone",
 "Clear personnel; remove tools; restore guards; controlled re-energization; communicate before testing.")
],
}

DEFAULT_COLUMNS = [
"Job Step","Hazards","Controls",
"Pre Likelihood","Pre Severity","Pre Risk",
"Post Likelihood","Post Severity","Post Risk"
]

def build_df(rows):
    data=[]
    for step,hazard,control,pl,ps,pol,pos in rows:
        data.append([step,hazard,control,pl,ps,pl*ps,pol,pos,pol*pos])
    return pd.DataFrame(data, columns=DEFAULT_COLUMNS)

if "jha" not in st.session_state:
    st.session_state.jha = pd.DataFrame(columns=DEFAULT_COLUMNS)
if "meta" not in st.session_state:
    st.session_state.meta = {
        "Project":"","Company / Contractor":"","Location":"",
        "Work Activity":"","Prepared By":"","Date":str(date.today()),"Revision":"0"
    }

# ---------------- Header ----------------
st.title("🦺 JHA Builder V2")
st.caption("Create, generate, review and export Job Hazard Analyses.")

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("JHA Information")
    for k in list(st.session_state.meta):
        if k == "Date":
            st.session_state.meta[k] = st.date_input(k, pd.to_datetime(st.session_state.meta[k])).isoformat()
        else:
            st.session_state.meta[k] = st.text_input(k, st.session_state.meta[k])
    st.divider()
    st.markdown("### Risk Method")
    st.write("**Risk = Likelihood × Severity**")
    st.write("1–4 Low  •  5–9 Moderate  •  10–16 High  •  17–25 Critical")
    st.caption("Generated ratings are starting points only. Review against your approved company/site risk matrix.")

tabs = st.tabs(["✨ Generate JHA","✏️ Edit JHA","📊 Risk Matrix","📚 Hazard Library","⬇️ Export"])

# ---------------- Generator ----------------
with tabs[0]:
    st.subheader("Generate a JHA")
    st.write("Describe the work in plain language. Select a library template or enter your own task.")
    c1,c2 = st.columns([2,1])
    with c1:
        task = st.text_area(
            "Work description",
            placeholder="Example: Erect a 30 ft scaffold around a conveyor in an operating plant, including material handling and final inspection.",
            height=120
        )
    with c2:
        template = st.selectbox("Starting template", ["Custom"] + list(LIBRARY.keys()))
        num_rows = st.slider("Custom number of job steps", 1, 12, 5)

    if st.button("✨ Generate JHA", type="primary", use_container_width=True):
        if template != "Custom":
            rows = LIBRARY[template]
            st.session_state.jha = build_df([
                (s,h,c,3,4,2,3) for s,h,c in rows
            ])
            if not st.session_state.meta["Work Activity"]:
                st.session_state.meta["Work Activity"] = template
            st.success(f"Generated a {template} JHA with {len(rows)} job steps.")
        elif task.strip():
            # Keyword-based starter generation for offline/deployable operation.
            t = task.lower()
            chosen=[]
            if any(x in t for x in ["scaffold","scaffolding"]): chosen += LIBRARY["Scaffolding"]
            if any(x in t for x in ["weld","welding","cutting","hot work"]): chosen += LIBRARY["Hot Work"]
            if any(x in t for x in ["lift","rig","crane","hoist"]): chosen += LIBRARY["Lifting / Rigging"]
            if any(x in t for x in ["excavat","trench","dig"]): chosen += LIBRARY["Excavation"]
            if any(x in t for x in ["maintenance","repair","service"]): chosen += LIBRARY["General Maintenance"]
            if not chosen:
                chosen = [
                    ("Prepare work area","Slips/trips, struck-by, interaction with other work","Inspect area; establish boundaries; maintain housekeeping; coordinate simultaneous work."),
                    ("Set up tools/equipment","Defective equipment, pinch points, electrical hazards","Complete pre-use inspections; remove defective equipment; use appropriate PPE and tools."),
                    ("Perform task", "Task-specific hazards, unexpected movement, exposure to equipment/materials","Follow approved procedure; maintain controls and exclusion zones; use required PPE."),
                    ("Complete and demobilize","Residual energy, housekeeping, interaction with traffic","Make equipment safe; restore guards; remove waste; inspect area before leaving.")
                ]
            st.session_state.jha = build_df([(s,h,c,3,4,2,3) for s,h,c in chosen[:num_rows]])
            st.session_state.meta["Work Activity"] = task[:100]
            st.success("Starter JHA generated. Review and edit every row before use.")
        else:
            st.warning("Enter a work description or select a template.")

    st.info("V2 is intentionally deployable without an external AI API. The generator uses a built-in hazard/control library and keyword matching. A future V3 can connect to an AI provider for richer task-specific generation.")

# ---------------- Editor ----------------
with tabs[1]:
    st.subheader("Edit JHA")
    if st.session_state.jha.empty:
        st.info("Generate a JHA first, or add a row below.")
        if st.button("➕ Add first row"):
            st.session_state.jha = build_df([("","","",3,3,2,2)])
            st.rerun()
    else:
        edited = st.data_editor(
            st.session_state.jha,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Job Step": st.column_config.TextColumn(width="medium"),
                "Hazards": st.column_config.TextColumn(width="large"),
                "Controls": st.column_config.TextColumn(width="large"),
                "Pre Likelihood": st.column_config.SelectboxColumn(options=list(LIKELIHOOD.keys()), required=True),
                "Pre Severity": st.column_config.SelectboxColumn(options=list(SEVERITY.keys()), required=True),
                "Pre Risk": st.column_config.NumberColumn(disabled=True),
                "Post Likelihood": st.column_config.SelectboxColumn(options=list(LIKELIHOOD.keys()), required=True),
                "Post Severity": st.column_config.SelectboxColumn(options=list(SEVERITY.keys()), required=True),
                "Post Risk": st.column_config.NumberColumn(disabled=True),
            },
            key="jha_editor_v2"
        )
        edited = edited.copy()
        for col in ["Pre Likelihood","Pre Severity","Post Likelihood","Post Severity"]:
            edited[col] = pd.to_numeric(edited[col], errors="coerce").fillna(1).clip(1,5).astype(int)
        edited["Pre Risk"] = edited["Pre Likelihood"] * edited["Pre Severity"]
        edited["Post Risk"] = edited["Post Likelihood"] * edited["Post Severity"]
        st.session_state.jha = edited

        view = edited.copy()
        view["Pre Rating"] = view["Pre Risk"].apply(lambda x: f"{x} — {risk_level(x)}")
        view["Post Rating"] = view["Post Risk"].apply(lambda x: f"{x} — {risk_level(x)}")
        st.markdown("### Review Summary")
        st.dataframe(view[["Job Step","Pre Rating","Post Rating"]], use_container_width=True, hide_index=True)

        nonblank = view[view["Job Step"].fillna("").astype(str).str.strip()!=""]
        a,b,c,d = st.columns(4)
        a.metric("Steps",len(nonblank))
        b.metric("Pre High/Critical",int((nonblank["Pre Risk"]>=10).sum()))
        c.metric("Post High/Critical",int((nonblank["Post Risk"]>=10).sum()))
        d.metric("Highest Post Risk",int(nonblank["Post Risk"].max()) if len(nonblank) else 0)

        high = nonblank[nonblank["Post Risk"]>=17]
        if len(high):
            st.error(f"{len(high)} step(s) have Critical post-control risk. Review controls and the approved site risk process before work proceeds.")
        elif len(nonblank[nonblank["Post Risk"]>=10]):
            st.warning("One or more steps remain High post-control risk. Confirm additional controls or required authorization.")

# ---------------- Matrix ----------------
with tabs[2]:
    st.subheader("5 × 5 Risk Matrix")
    matrix = pd.DataFrame(
        [[f"{i*j} — {risk_level(i*j)}" for j in range(1,6)] for i in range(5,0,-1)],
        index=["5 Almost Certain","4 Likely","3 Possible","2 Unlikely","1 Rare"],
        columns=["1 Insignificant","2 Minor","3 Moderate","4 Major","5 Catastrophic"]
    )
    st.dataframe(matrix, use_container_width=True)
    st.markdown("""
**Likelihood:** 1 Rare · 2 Unlikely · 3 Possible · 4 Likely · 5 Almost Certain

**Severity:** 1 Insignificant · 2 Minor · 3 Moderate · 4 Major · 5 Catastrophic

**Classification:** 1–4 Low · 5–9 Moderate · 10–16 High · 17–25 Critical
""")

# ---------------- Library ----------------
with tabs[3]:
    st.subheader("Hazard & Control Library")
    for name, rows in LIBRARY.items():
        with st.expander(name):
            for step,h,c in rows:
                st.markdown(f"**{step}**")
                st.write("Hazards:", h)
                st.write("Controls:", c)

# ---------------- Export ----------------
with tabs[4]:
    st.subheader("Export JHA")
    if st.session_state.jha.empty:
        st.info("Generate or enter a JHA before exporting.")
    else:
        df = st.session_state.jha.copy()
        df["Pre Rating"] = df["Pre Risk"].apply(lambda x: risk_level(x))
        df["Post Rating"] = df["Post Risk"].apply(lambda x: risk_level(x))

        def excel():
            out=BytesIO()
            with pd.ExcelWriter(out, engine="openpyxl") as writer:
                pd.DataFrame(list(st.session_state.meta.items()),columns=["Field","Value"]).to_excel(writer,index=False,sheet_name="JHA Information")
                df.to_excel(writer,index=False,sheet_name="JHA")
                matrix=pd.DataFrame([[risk_level(i*j) for j in range(1,6)] for i in range(1,6)])
                matrix.to_excel(writer,index=False,sheet_name="Risk Matrix")
            return out.getvalue()

        def pdf():
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import landscape, letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph,Spacer
            out=BytesIO()
            doc=SimpleDocTemplate(out,pagesize=landscape(letter),leftMargin=20,rightMargin=20,topMargin=20,bottomMargin=20)
            styles=getSampleStyleSheet()
            small=ParagraphStyle("small",parent=styles["BodyText"],fontSize=7,leading=8)
            title=ParagraphStyle("title",parent=styles["Title"],fontSize=16,alignment=TA_CENTER)
            story=[Paragraph("JOB HAZARD ANALYSIS",title),Spacer(1,8)]
            m=st.session_state.meta
            meta=[["Project",m["Project"],"Company / Contractor",m["Company / Contractor"]],
                  ["Location",m["Location"],"Work Activity",m["Work Activity"]],
                  ["Prepared By",m["Prepared By"],"Date",m["Date"]],
                  ["Revision",m["Revision"],"Risk Method","Likelihood × Severity"]]
            mt=Table(meta,colWidths=[70,210,100,210])
            mt.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.4,colors.grey),("BACKGROUND",(0,0),(0,-1),colors.lightgrey),("BACKGROUND",(2,0),(2,-1),colors.lightgrey),("VALIGN",(0,0),(-1,-1),"TOP")]))
            story += [mt,Spacer(1,8)]
            data=[["Job Step","Hazards","Controls","Pre","Pre Rating","Post","Post Rating"]]
            for _,r in df.iterrows():
                data.append([Paragraph(str(r["Job Step"]),small),Paragraph(str(r["Hazards"]),small),Paragraph(str(r["Controls"]),small),str(r["Pre Risk"]),str(r["Pre Rating"]),str(r["Post Risk"]),str(r["Post Rating"])])
            t=Table(data,repeatRows=1,colWidths=[100,125,235,45,60,45,60])
            t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.35,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.darkgrey),("TEXTCOLOR",(0,0),(-1,0),colors.white),("VALIGN",(0,0),(-1,-1),"TOP"),("FONTSIZE",(0,0),(-1,-1),7)]))
            story += [t,Spacer(1,8),Paragraph("Risk scores are calculated from the selected Likelihood and Severity values. Review against the organization's approved risk matrix and applicable procedures before use.",small)]
            doc.build(story)
            return out.getvalue()

        st.download_button("⬇️ Download Excel",excel(),"JHA_V2.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
        st.download_button("⬇️ Download PDF",pdf(),"JHA_V2.pdf","application/pdf",use_container_width=True)

st.caption("JHA Builder V2 • Editable generated content • Risk = Likelihood × Severity")

import streamlit as st
import pandas as pd
import os, json
from io import BytesIO
from datetime import date

st.set_page_config(page_title="JHA Builder V3", page_icon="🦺", layout="wide")

LIKELIHOOD={1:"Rare",2:"Unlikely",3:"Possible",4:"Likely",5:"Almost Certain"}
SEVERITY={1:"Insignificant",2:"Minor",3:"Moderate",4:"Major",5:"Catastrophic"}
COLS=["Job Step","Hazards","Controls","Pre Likelihood","Pre Severity","Pre Risk","Pre Rating",
      "Post Likelihood","Post Severity","Post Risk","Post Rating","Sources"]

def rating(n):
    return "Low" if n<=4 else "Moderate" if n<=9 else "High" if n<=16 else "Critical"

def make_df(items):
    rows=[]
    for x in items:
        pl=max(1,min(5,int(x.get("pre_likelihood",3))))
        ps=max(1,min(5,int(x.get("pre_severity",4))))
        ql=max(1,min(5,int(x.get("post_likelihood",2))))
        qs=max(1,min(5,int(x.get("post_severity",3))))
        rows.append([x.get("job_step",""),"; ".join(x.get("hazards",[])),
                     "; ".join(x.get("controls",[])),pl,ps,pl*ps,rating(pl*ps),
                     ql,qs,ql*qs,rating(ql*qs),"; ".join(x.get("sources",[]))])
    return pd.DataFrame(rows,columns=COLS)

SYSTEM_PROMPT = """You are an occupational health and safety JHA specialist.
Create a site-specific starting-point Job Hazard Analysis from the user's task.
Use live web search before answering. Prioritize free authoritative sources such as
government regulators, CCOHS, OSHA/NIOSH, manufacturers and recognized safety organizations.
Prefer the selected jurisdiction. Never invent site facts or legal requirements.

Return ONLY JSON:
{"job_steps":[{"job_step":"...","hazards":["..."],"controls":["..."],
"pre_likelihood":1,"pre_severity":1,"post_likelihood":1,"post_severity":1,
"sources":["https://..."]}]}

Create 5-12 logical work steps. Include multiple credible hazards and specific controls.
Use the hierarchy of controls where practical. Pre risk represents conditions before
the listed controls. Post risk represents residual risk after those controls.
Risk numbers are estimates, not legal facts. Severe hazards may remain High/Critical.
Cite public sources that materially support each step."""

def generate(task,jurisdiction,key,model):
    from openai import OpenAI
    client=OpenAI(api_key=key)
    prompt=f"Jurisdiction: {jurisdiction}\nJob: {task}\nUse web search for current public safety information."
    r=client.responses.create(model=model,tools=[{"type":"web_search"}],
                              input=[{"role":"system","content":SYSTEM_PROMPT},
                                     {"role":"user","content":prompt}])
    text=r.output_text.strip()
    if text.startswith("```"):
        text=text.split("```",2)[1]
        if text.lstrip().startswith("json"):
            text=text.lstrip()[4:]
    return json.loads(text)

if "jha" not in st.session_state:
    st.session_state.jha=pd.DataFrame(columns=COLS)
if "meta" not in st.session_state:
    st.session_state.meta={"Project":"","Company / Contractor":"","Location":"","Work Activity":"",
                           "Prepared By":"","Date":str(date.today()),"Revision":"0"}

st.title("🦺 JHA Builder V3 — Web-Verified")
st.caption("AI-assisted JHA generation using live public web research, source citations and automatic 5×5 risk scoring.")

with st.sidebar:
    st.header("JHA Information")
    for k in st.session_state.meta:
        if k=="Date":
            st.session_state.meta[k]=str(st.date_input(k,pd.to_datetime(st.session_state.meta[k])))
        else:
            st.session_state.meta[k]=st.text_input(k,st.session_state.meta[k])
    st.divider()
    st.header("AI / Web Search")
    key=st.text_input("OpenAI API key",value=os.getenv("OPENAI_API_KEY",""),type="password")
    model=st.selectbox("Model",["gpt-5.6-luna","gpt-5.6-terra"],index=0)
    jurisdiction=st.selectbox("Jurisdiction",["Ontario, Canada","Canada — federal",
                                              "Alberta, Canada","British Columbia, Canada",
                                              "United States","Other"])

gen,edit,review,sources,matrix,export=st.tabs(["🤖 Generate","✏️ Edit","🔎 Review","📚 Sources","📊 Matrix","⬇️ Export"])

with gen:
    task=st.text_area("Describe the work",height=160,
      placeholder="Example: Remove and replace a 500 HP motor in an operating smelter using a mobile crane. Include isolation, rigging, lifting, positioning, reconnection and testing.")
    if st.button("🚀 Search web + Build JHA",type="primary",use_container_width=True):
        if not key:
            st.error("Enter an OpenAI API key. V3 uses the API's built-in web-search capability.")
        elif not task.strip():
            st.warning("Describe the job first.")
        else:
            with st.spinner("Searching public safety sources and building the JHA..."):
                try:
                    data=generate(task,jurisdiction,key,model)
                    st.session_state.jha=make_df(data.get("job_steps",[]))
                    st.session_state.meta["Work Activity"]=task[:150]
                    st.success(f"Generated {len(st.session_state.jha)} job steps. Review every row before use.")
                except Exception as e:
                    st.error(f"Generation failed: {e}")
    st.info("Web sources support the hazards and controls. Risk ratings are estimates based on the 1–5 matrix and must be reviewed against your company's approved matrix and actual site conditions.")

with edit:
    if st.session_state.jha.empty:
        st.info("Generate a JHA first.")
    else:
        edited=st.data_editor(st.session_state.jha,num_rows="dynamic",hide_index=True,use_container_width=True,
          column_config={
            "Pre Likelihood":st.column_config.SelectboxColumn(options=list(LIKELIHOOD.keys())),
            "Pre Severity":st.column_config.SelectboxColumn(options=list(SEVERITY.keys())),
            "Post Likelihood":st.column_config.SelectboxColumn(options=list(LIKELIHOOD.keys())),
            "Post Severity":st.column_config.SelectboxColumn(options=list(SEVERITY.keys())),
            "Pre Risk":st.column_config.NumberColumn(disabled=True),
            "Pre Rating":st.column_config.TextColumn(disabled=True),
            "Post Risk":st.column_config.NumberColumn(disabled=True),
            "Post Rating":st.column_config.TextColumn(disabled=True)})
        st.session_state.jha=edited
        for c in ["Pre Likelihood","Pre Severity","Post Likelihood","Post Severity"]:
            st.session_state.jha[c]=pd.to_numeric(st.session_state.jha[c],errors="coerce").fillna(1).clip(1,5).astype(int)
        st.session_state.jha["Pre Risk"]=st.session_state.jha["Pre Likelihood"]*st.session_state.jha["Pre Severity"]
        st.session_state.jha["Post Risk"]=st.session_state.jha["Post Likelihood"]*st.session_state.jha["Post Severity"]
        st.session_state.jha["Pre Rating"]=st.session_state.jha["Pre Risk"].apply(rating)
        st.session_state.jha["Post Rating"]=st.session_state.jha["Post Risk"].apply(rating)

with review:
    if st.session_state.jha.empty:
        st.info("Generate a JHA first.")
    else:
        d=st.session_state.jha
        a,b,c,dcol=st.columns(4)
        a.metric("Job Steps",len(d))
        b.metric("Pre High/Critical",int((d["Pre Risk"]>=10).sum()))
        c.metric("Post High/Critical",int((d["Post Risk"]>=10).sum()))
        dcol.metric("Post Critical",int((d["Post Risk"]>=17).sum()))
        if (d["Post Risk"]>=17).any(): st.error("Critical residual risks remain and require explicit review before work proceeds.")
        if ((d["Post Risk"]>=10)&(d["Post Risk"]<17)).any(): st.warning("High residual risks remain. Confirm controls and approval requirements.")
        st.dataframe(d[["Job Step","Pre Risk","Pre Rating","Post Risk","Post Rating"]],use_container_width=True,hide_index=True)
        st.markdown("### Human review")
        for item in ["Site conditions and simultaneous operations checked",
                     "Applicable legislation/company requirements checked",
                     "Manufacturer instructions checked where applicable",
                     "Permits and competent-person requirements checked",
                     "Emergency/rescue arrangements checked",
                     "Controls verified as actually implemented"]:
            st.checkbox(item,key="review_"+item)

with sources:
    if st.session_state.jha.empty:
        st.info("Sources appear after generation.")
    else:
        for i,row in st.session_state.jha.iterrows():
            with st.expander(f"{i+1}. {row['Job Step']}"):
                st.write(row["Sources"])

with matrix:
    st.subheader("5 × 5 Risk Matrix")
    m=pd.DataFrame([[f"{i*j} — {rating(i*j)}" for j in range(1,6)] for i in range(5,0,-1)],
                   index=["5 Almost Certain","4 Likely","3 Possible","2 Unlikely","1 Rare"],
                   columns=["1 Insignificant","2 Minor","3 Moderate","4 Major","5 Catastrophic"])
    st.dataframe(m,use_container_width=True)
    st.write("Risk = Likelihood × Severity: 1–4 Low, 5–9 Moderate, 10–16 High, 17–25 Critical.")

with export:
    if st.session_state.jha.empty:
        st.info("Generate a JHA first.")
    else:
        out=BytesIO()
        with pd.ExcelWriter(out,engine="openpyxl") as w:
            pd.DataFrame(st.session_state.meta.items(),columns=["Field","Value"]).to_excel(w,index=False,sheet_name="JHA Information")
            st.session_state.jha.to_excel(w,index=False,sheet_name="JHA")
        st.download_button("⬇️ Download Excel",out.getvalue(),"JHA_V3_Web_Verified.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
        st.download_button("⬇️ Download CSV",st.session_state.jha.to_csv(index=False).encode(),
                           "JHA_V3_Web_Verified.csv","text/csv",use_container_width=True)

st.caption("JHA Builder V3 • Live public web research • Source citations • Automatic risk scoring • Human review required")

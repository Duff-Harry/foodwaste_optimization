# ============================================================
# LANDING SCREEN — shown first, standalone, full-bleed.
# No header, no tab chrome. Click "Get Started" to reveal the app.
# ============================================================
if "app_started" not in st.session_state:
    st.session_state["app_started"] = False

def _hero_bg_base64(path="Foodwaste_1.png"):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

if not st.session_state["app_started"]:

    _bg = _hero_bg_base64()
    _bg_css = f"url('data:image/png;base64,{_bg}')" if _bg else "none"

    st.markdown(f"""
    <style>
      .ef-landing {{
        position: fixed !important;
        top: 0; left: 0; right: 0; bottom: 0;
        margin: 0;
        display: flex; flex-direction: column; justify-content: center;
        padding: 60px 80px;
        background:
          linear-gradient(180deg, rgba(20,31,23,0.90) 0%, rgba(20,31,23,0.85) 55%, rgba(20,31,23,0.92) 100%),
          {_bg_css} center 32% / cover no-repeat;
        z-index: 9999;
        overflow-y: auto;
      }}
      div[data-testid="stButton"] {{
        position: fixed !important;
        bottom: 90px !important;
        left: 80px !important;
        width: auto !important;
        z-index: 10000;
      }}
      div[data-testid="stButton"] button {{
        background-color: #8FBF3F !important;
        color: #141F17 !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        padding: 12px 28px !important;
        border-radius: 4px !important;
        width: auto !important;
      }}
      div[data-testid="stButton"] button:hover {{
        background-color: #a3d456 !important;
      }}
    </style>

    <div class="ef-landing">
      <h1 style="font-size:44px; font-weight:800; line-height:1.12; margin:0 0 20px; max-width:720px; color:#F1EDE4 !important;">
        Turn a waste stream into the<br>
        <span style="color:#8FBF3F !important;">lowest-cost, lowest-emissions</span> route to a product.
      </h1>
      <p style="font-size:17px; line-height:1.55; color:rgba(241,237,228,0.85) !important; max-width:560px; margin:0 0 8px;">
        Enter what you're throwing away. ECO-FAST runs every viable processing pathway —
        digestion, composting, liquefaction, incineration — and returns the one that costs
        least, pollutes least, or balances both.
      </p>
      <p style="font-family:'Courier New',monospace; font-size:13px; color:rgba(241,237,228,0.65) !important; text-decoration:underline; margin-top:80px;">
        see how the model works
      </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Describe your waste stream →", key="get_started_btn"):
        st.session_state["app_started"] = True
        st.rerun()

    st.stop()
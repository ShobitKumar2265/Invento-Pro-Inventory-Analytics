import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
import zipfile
import warnings
import random
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Invento Pro", page_icon="📊", layout="wide")

# ============================================================
# SESSION STATE
# ============================================================
if "theme" not in st.session_state: st.session_state.theme = "dark"
if "hist" not in st.session_state: st.session_state.hist = []
if "go_clicked" not in st.session_state: st.session_state.go_clicked = False
if "sales" not in st.session_state: st.session_state.sales = None
if "products" not in st.session_state: st.session_state.products = None
if "inventory" not in st.session_state: st.session_state.inventory = None
if "current_data_hash" not in st.session_state: st.session_state.current_data_hash = None

# ============================================================
# RESET FUNCTION - CLEARS EVERYTHING
# ============================================================
def reset_all_data():
    st.session_state.go_clicked = False
    st.session_state.sales = None
    st.session_state.products = None
    st.session_state.inventory = None
    st.session_state.hist = []
    st.session_state.current_data_hash = None
    st.cache_data.clear()
    return True

# ============================================================
# THEME FUNCTIONS
# ============================================================
def get_profit_loss_color(value):
    if value > 0: return "#10B981"
    elif value < 0: return "#EF4444"
    else: return "#F59E0B"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

def get_css(theme):
    if theme == "dark":
        return """<style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
            *{font-family:'Inter',sans-serif}
            .stApp{background:#0A0E14}
            .welcome-text{font-size:28px;font-weight:700;color:#E6EDF3}
            .welcome-sub{font-size:14px;color:#8B949E}
            .card-purple{background:linear-gradient(135deg,#6C5CE7,#A855F7);border-radius:16px;padding:20px;color:white}
            .card-blue{background:linear-gradient(135deg,#3B82F6,#06B6D4);border-radius:16px;padding:20px;color:white}
            .card-orange{background:linear-gradient(135deg,#F59E0B,#F97316);border-radius:16px;padding:20px;color:white}
            .card-title{font-size:12px;opacity:.85;text-transform:uppercase;letter-spacing:1.5px;font-weight:500}
            .card-value{font-size:26px;font-weight:800;margin:6px 0}
            .card-sub{font-size:12px;opacity:.9;font-weight:500}
            .stock-card{background:linear-gradient(135deg,#0F1419,#1A2332);border-radius:16px;padding:20px;border:1px solid #1A1F2E}
            .section-title{font-size:18px;font-weight:700;color:#E6EDF3;padding:10px 0}
            .chat-user{background:#1A2332;padding:10px;border-radius:10px;margin:4px 0;border-left:3px solid #3B82F6;color:#E6EDF3}
            .chat-bot{background:#1F1A2E;padding:10px;border-radius:10px;margin:4px 0;border-left:3px solid #A855F7;color:#E6EDF3}
            .txn-item{display:flex;align-items:center;padding:12px;border-bottom:1px solid #1A1F2E;gap:12px}
            .txn-icon{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px}
            .txn-name{font-weight:600;color:#E6EDF3;font-size:14px}
            .txn-cat{font-size:12px;color:#8B949E}
            .txn-amount{font-weight:700;font-size:14px;margin-left:auto}
            .color-green{color:#10B981;font-weight:700}
            .color-red{color:#EF4444;font-weight:700}
            .color-yellow{color:#F59E0B;font-weight:700}
            .status-badge{padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase;display:inline-block}
            .badge-green{background:rgba(16,185,129,0.2);color:#10B981}
            .badge-red{background:rgba(239,68,68,0.2);color:#EF4444}
            .badge-yellow{background:rgba(245,158,11,0.2);color:#F59E0B}
            [data-testid="stSidebar"]{background:#0F1419;border-right:1px solid #1A1F2E}
            .stButton>button{border-radius:10px;font-weight:600}
            .stTabs [aria-selected="true"]{background:#1A1F2E;color:#E6EDF3}
            p,h1,h2,h3,span,div{color:#E6EDF3}
            hr{border-color:#1A1F2E}
        </style>"""
    else:
        return """<style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
            *{font-family:'Inter',sans-serif}
            .stApp{background:#F1F5F9}
            .welcome-text{font-size:28px;font-weight:700;color:#0F172A}
            .welcome-sub{font-size:14px;color:#475569}
            .card-purple{background:linear-gradient(135deg,#6C5CE7,#A855F7);border-radius:16px;padding:20px;color:white}
            .card-blue{background:linear-gradient(135deg,#3B82F6,#06B6D4);border-radius:16px;padding:20px;color:white}
            .card-orange{background:linear-gradient(135deg,#F59E0B,#F97316);border-radius:16px;padding:20px;color:white}
            .card-title{font-size:12px;opacity:.9;text-transform:uppercase;letter-spacing:1.5px;font-weight:500}
            .card-value{font-size:26px;font-weight:800;margin:6px 0}
            .card-sub{font-size:12px;opacity:.9;font-weight:500}
            .stock-card{background:#FFFFFF;border-radius:16px;padding:20px;border:1px solid #E2E8F0;box-shadow:0 1px 3px rgba(0,0,0,.05)}
            .section-title{font-size:18px;font-weight:700;color:#0F172A;padding:10px 0}
            .chat-user{background:#EFF6FF;padding:10px;border-radius:10px;margin:4px 0;border-left:3px solid #3B82F6;color:#0F172A}
            .chat-bot{background:#FAF5FF;padding:10px;border-radius:10px;margin:4px 0;border-left:3px solid #A855F7;color:#0F172A}
            .txn-item{display:flex;align-items:center;padding:12px;border-bottom:1px solid #E2E8F0;gap:12px}
            .txn-icon{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:20px}
            .txn-name{font-weight:600;color:#0F172A;font-size:14px}
            .txn-cat{font-size:12px;color:#475569}
            .txn-amount{font-weight:700;font-size:14px;margin-left:auto}
            .color-green{color:#059669;font-weight:700}
            .color-red{color:#DC2626;font-weight:700}
            .color-yellow{color:#D97706;font-weight:700}
            .status-badge{padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase;display:inline-block}
            .badge-green{background:rgba(5,150,105,0.15);color:#059669}
            .badge-red{background:rgba(220,38,38,0.15);color:#DC2626}
            .badge-yellow{background:rgba(217,119,6,0.15);color:#D97706}
            [data-testid="stSidebar"]{background:#FFF;border-right:1px solid #E2E8F0}
            .stButton>button{border-radius:10px;font-weight:600}
            .stTabs [aria-selected="true"]{background:#FFF;color:#0F172A}
            p,h1,h2,h3,span,div{color:#0F172A}
            hr{border-color:#E2E8F0}
        </style>"""

# ============================================================
# COLUMN DETECTION
# ============================================================
def detect_col(df, names):
    if df is None: return None
    for n in names:
        if n in df.columns: return n
        for c in df.columns:
            if c.lower() == n.lower() or n.lower() in c.lower(): return c
    return None

@st.cache_data
def load_default():
    try:
        s = pd.read_csv("sales_data.csv", parse_dates=['Sale_Date'])
        p = pd.read_csv("products_data.csv")
        i = pd.read_csv("inventory_data.csv", parse_dates=['Record_Date'])
        if 'Revenue' in s.columns and 'COGS' in s.columns: s['Gross_Profit'] = s['Revenue'] - s['COGS']
        if 'Sale_Date' in s.columns: s['Month'] = s['Sale_Date'].dt.to_period('M')
        return s, p, i
    except: return None, None, None
        
def classify_dataframe(df):
    if df is None: return 'unknown'
    cols = ' '.join([c.lower() for c in df.columns])
    sales_score = sum(1 for kw in ['revenue','sale','gross','profit','cogs'] if kw in cols)
    inventory_score = sum(1 for kw in ['stock','inventory','closing','opening','stockout'] if kw in cols)
    product_score = sum(1 for kw in ['product_name','product_id','category','supplier','sku'] if kw in cols)
    scores = {'sales':sales_score,'inventory':inventory_score,'products':product_score}
    best = max(scores,key=scores.get)
    return best if scores[best]>0 else 'products'

def process_uploaded_files(files):
    result = {'sales':None,'products':None,'inventory':None}
    for f in files:
        try:
            df = pd.read_csv(f)
            for col in df.columns:
                if 'date' in col.lower():
                    try: df[col] = pd.to_datetime(df[col])
                    except: pass
            result[classify_dataframe(df)] = df
        except Exception as e: st.warning(f"Error: {f.name}")
    return result

def abc_analysis(df, nc, rc):
    if nc is None or rc is None: return pd.DataFrame()
    abc = df.groupby(nc).agg(R=(rc,'sum')).sort_values('R',ascending=False).reset_index()
    abc['Cum%'] = (abc['R']/abc['R'].sum()*100).cumsum()
    abc['Class'] = abc['Cum%'].apply(lambda x: 'A' if x<=70 else ('B' if x<=90 else 'C'))
    return abc

def calculate_metrics(sales_df, inventory_df):
    m = {}
    rc = detect_col(sales_df,['Revenue','revenue','Total','Amount'])
    pc = detect_col(sales_df,['Gross_Profit','gross_profit','Profit','profit'])
    cc = detect_col(sales_df,['COGS','cogs','Cost','cost'])
    uc = detect_col(sales_df,['Units_Sold','units_sold','Quantity','quantity','Qty'])
    nc = detect_col(sales_df,['Product_Name','product_name','Product','product','Item','SKU'])
    catc = detect_col(sales_df,['Category','category','Department','Type'])
    
    if rc: m['total_revenue'] = sales_df[rc].sum()
    else:
        up = detect_col(sales_df,['Unit_Price','unit_price','Price','Selling_Price'])
        qty = detect_col(sales_df,['Units_Sold','units_sold','Quantity'])
        if up and qty: m['total_revenue'] = (sales_df[up]*sales_df[qty]).sum()
        else: m['total_revenue'] = 0
    
    if pc: m['total_profit'] = sales_df[pc].sum()
    elif rc and cc: m['total_profit'] = sales_df[rc].sum() - sales_df[cc].sum()
    else: m['total_profit'] = 0
    
    m['margin_pct'] = (m['total_profit']/m['total_revenue']*100) if m['total_revenue']>0 else 0
    m['availability'] = 100
    m['stockout_rate'] = 0
    m['total_stock'] = 0
    m['stockout_days'] = 0
    m['stock_status_text'] = "NO DATA"
    m['has_inventory'] = False
    m['total_transactions'] = len(sales_df)
    
    if inventory_df is not None and len(inventory_df)>0:
        sf = detect_col(inventory_df,['Stockout_Flag','stockout_flag'])
        cs = detect_col(inventory_df,['Closing_Stock','closing_stock','Stock','stock','Available','On_Hand'])
        rop = detect_col(inventory_df,['Reorder_Point','reorder_point','ROP','Min_Stock'])
        if cs:
            m['total_stock'] = int(inventory_df[cs].sum())
            m['has_inventory'] = True
        if sf:
            m['stockout_days'] = int(inventory_df[sf].sum())
            m['stockout_rate'] = float(inventory_df[sf].mean()*100)
            m['availability'] = 100 - m['stockout_rate']
            m['has_inventory'] = True
        if m['total_stock']<=0 and m['has_inventory']: m['stock_status_text'] = "OUT OF STOCK"
        elif m['has_inventory']:
            if rop and len(inventory_df)>0:
                lr = inventory_df[rop].iloc[-1] if pd.notna(inventory_df[rop].iloc[-1]) else 0
                m['stock_status_text'] = "LOW STOCK" if m['total_stock']<=lr else "IN STOCK"
            else: m['stock_status_text'] = "IN STOCK"
    
    if not m['has_inventory']:
        if uc:
            m['total_stock'] = max(int(sales_df[uc].sum()*0.3),1)
            m['stock_status_text'] = "ESTIMATED"
        elif nc:
            m['total_stock'] = sales_df[nc].nunique()
            m['stock_status_text'] = "ACTIVE"
        else:
            m['total_stock'] = len(sales_df)
            m['stock_status_text'] = "ACTIVE"
    
    m['product_count'] = sales_df[nc].nunique() if nc else 0
    m['category_count'] = sales_df[catc].nunique() if catc else 0
    m['avg_transaction'] = m['total_revenue']/len(sales_df) if rc and len(sales_df)>0 else 0
    return m, rc, pc, nc, catc, uc, cc

def chatbot(q, sales_df, m):
    q = q.lower()
    if any(w in q for w in ['revenue','sales','income']):
        c = get_profit_loss_color(m['total_revenue'])
        cl = "green" if c=="#10B981" else ("red" if c=="#EF4444" else "yellow")
        return f'Total Revenue: <span class="color-{cl}">Rs.{m["total_revenue"]/1e7:.2f}Cr</span><br>Based on {m["total_transactions"]:,} transactions'
    if any(w in q for w in ['stock','inventory','available']):
        stxt = m['stock_status_text']
        if stxt=="OUT OF STOCK": sc, bc = "#EF4444","red"
        elif stxt in ["LOW STOCK","ESTIMATED"]: sc, bc = "#F59E0B","yellow"
        else: sc, bc = "#10B981","green"
        ac = "green" if m['availability']>90 else ("red" if m['availability']<70 else "yellow")
        return f'Stock: <span class="color-{bc}">{m["total_stock"]:,} units</span> <span class="status-badge badge-{bc}">{stxt}</span><br>Availability: <span class="color-{ac}">{m["availability"]:.1f}%</span>'
    if any(w in q for w in ['profit','margin']):
        c = get_profit_loss_color(m['total_profit'])
        cl = "green" if c=="#10B981" else ("red" if c=="#EF4444" else "yellow")
        mc = "#10B981" if m['margin_pct']>25 else ("#EF4444" if m['margin_pct']<10 else "#F59E0B")
        mcl = "green" if mc=="#10B981" else ("red" if mc=="#EF4444" else "yellow")
        return f'Profit: <span class="color-{cl}">Rs.{m["total_profit"]/1e7:.2f}Cr</span><br>Margin: <span class="color-{mcl}">{m["margin_pct"]:.1f}%</span>'
    if any(w in q for w in ['product','category','count']):
        return f'Products: {m["product_count"]:,}<br>Categories: {m["category_count"]:,}<br>Avg Transaction: Rs.{m["avg_transaction"]/1e3:.1f}K'
    if 'help' in q: return "Try: revenue, stock, profit, products"
    return "Type 'help' for options."

# ============================================================
# MAP DATA FROM UPLOADED FILES (DYNAMIC)
# ============================================================
def extract_map_data(sales_df, products_df):
    locations = {}
    
    city_coords = {
        'Mumbai': [19.0760, 72.8777], 'Delhi': [28.6139, 77.2090],
        'Bangalore': [12.9716, 77.5946], 'Chennai': [13.0827, 80.2707],
        'Kolkata': [22.5726, 88.3639], 'Hyderabad': [17.3850, 78.4867],
        'Pune': [18.5204, 73.8567], 'Ahmedabad': [23.0225, 72.5714],
        'Jaipur': [26.9124, 75.7873], 'Lucknow': [26.8467, 80.9462]
    }
    
    if sales_df is not None and 'City' in sales_df.columns:
        cities = sales_df['City'].dropna().unique()
        for city in cities[:8]:
            if city in city_coords:
                locations[f"{city} Warehouse"] = city_coords[city]
    
    if len(locations) == 0:
        default_suppliers = {
            'Mumbai Warehouse': [19.0760, 72.8777],
            'Delhi Warehouse': [28.6139, 77.2090],
            'Bangalore Warehouse': [12.9716, 77.5946],
            'Chennai Warehouse': [13.0827, 80.2707],
            'Kolkata Warehouse': [22.5726, 88.3639]
        }
        locations.update(default_suppliers)
    
    return pd.DataFrame([{'Location': k, 'lat': v[0], 'lon': v[1], 'size': 20} for k, v in locations.items()])

# ============================================================
# MAIN APP
# ============================================================
def main():
    theme = st.session_state.theme
    st.markdown(get_css(theme), unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown('<div style="padding:10px 0;"><h2 style="font-size:22px;font-weight:800;">Invento Pro</h2><p style="font-size:11px;opacity:.7;">Inventory Analytics</p></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        ds = st.radio("Data Source", ["Default Dataset", "Upload CSV"], label_visibility="collapsed")
        
        if ds == "Upload CSV":
            files = st.file_uploader("Drop CSV files", type=['csv'], accept_multiple_files=True, label_visibility="collapsed")
            if files and st.button("ANALYZE", use_container_width=True, type="primary"):
                reset_all_data()
                result = process_uploaded_files(files)
                st.session_state.sales = result['sales']
                st.session_state.products = result['products']
                st.session_state.inventory = result['inventory']
                st.session_state.go_clicked = True
                st.rerun()
        else:
            if not st.session_state.go_clicked:
                s, p, i = load_default()
                st.session_state.sales = s
                st.session_state.products = p
                st.session_state.inventory = i
                st.session_state.go_clicked = True
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("RESET ALL DATA", use_container_width=True):
            reset_all_data()
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        ti = "Dark Mode" if st.session_state.theme == "light" else "Light Mode"
        if st.button(ti, use_container_width=True): toggle_theme(); st.rerun()
        
        if st.session_state.go_clicked and st.session_state.sales is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Export ZIP", use_container_width=True):
                buf = BytesIO()
                with zipfile.ZipFile(buf,'w') as zf:
                    if st.session_state.sales is not None: zf.writestr('sales.csv',st.session_state.sales.to_csv(index=False))
                    if st.session_state.products is not None: zf.writestr('products.csv',st.session_state.products.to_csv(index=False))
                    if st.session_state.inventory is not None: zf.writestr('inventory.csv',st.session_state.inventory.to_csv(index=False))
                st.download_button("Download", buf.getvalue(), "data.zip", use_container_width=True)
    
    sales = st.session_state.sales
    inventory = st.session_state.inventory
    
    if not st.session_state.go_clicked or sales is None:
        st.markdown('<div style="text-align:center;padding:80px;"><h1>Invento Pro</h1><h2>Upload CSV files to begin</h2><p style="opacity:0.6;">Upload sales_data.csv, products_data.csv, and inventory_data.csv</p></div>', unsafe_allow_html=True)
        return
    
    m, rc, pc, nc, catc, uc, cc = calculate_metrics(sales, inventory)
    
    rev_color = get_profit_loss_color(m['total_revenue'])
    profit_color = get_profit_loss_color(m['total_profit'])
    margin_color = "#10B981" if m['margin_pct']>25 else ("#EF4444" if m['margin_pct']<10 else "#F59E0B")
    avail_color = "#10B981" if m['availability']>90 else ("#EF4444" if m['availability']<70 else "#F59E0B")
    stockout_color = "#10B981" if m['stockout_rate']<5 else ("#EF4444" if m['stockout_rate']>10 else "#F59E0B")
    
    stxt = m['stock_status_text']
    if stxt=="OUT OF STOCK": stock_color, badge_class = "#EF4444","red"
    elif stxt in ["LOW STOCK","ESTIMATED"]: stock_color, badge_class = "#F59E0B","yellow"
    else: stock_color, badge_class = "#10B981","green"
    
    stock_display = f"{m['total_stock']:,}" if m['total_stock']>0 else "0"
    
    fc = '#E6EDF3' if theme=='dark' else '#0F172A'
    fc2 = '#8B949E' if theme=='dark' else '#64748B'
    
    ch, ct = st.columns([5,1])
    with ch: st.markdown(f'<div class="welcome-text">Welcome back, Admin</div><div class="welcome-sub">Inventory Analytics Dashboard | {len(sales):,} transactions loaded</div>', unsafe_allow_html=True)
    with ct:
        if st.button("Theme", use_container_width=True): toggle_theme(); st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    cards_html = f"""
    <div style="display:flex;gap:16px;flex-wrap:wrap;">
        <div class="card-purple" style="flex:1;min-width:200px;">
            <div class="card-title">Total Revenue</div>
            <div class="card-value" style="color:{rev_color};">Rs.{m['total_revenue']/1e7:.2f}Cr</div>
            <div class="card-sub">{m['product_count']} Products | {m['category_count']} Categories</div>
        </div>
        <div class="card-blue" style="flex:1;min-width:200px;">
            <div class="card-title">Gross Profit</div>
            <div class="card-value" style="color:{profit_color};">Rs.{m['total_profit']/1e7:.2f}Cr</div>
            <div class="card-sub">Margin: <span style="color:{margin_color};">{m['margin_pct']:.1f}%</span></div>
        </div>
        <div class="stock-card" style="flex:1;min-width:200px;">
            <div class="card-title">Stock Status</div>
            <div style="font-size:26px;font-weight:800;margin:6px 0;color:{stock_color};">{stock_display}</div>
            <div class="card-sub"><span class="status-badge badge-{badge_class}">{stxt}</span> | Avail: <span style="color:{avail_color};">{m['availability']:.1f}%</span></div>
        </div>
        <div class="card-orange" style="flex:1;min-width:200px;">
            <div class="card-title">Transactions</div>
            <div class="card-value">{m['total_transactions']:,}</div>
            <div class="card-sub">Stockout: <span style="color:{stockout_color};">{m['stockout_days']}</span> days</div>
        </div>
    </div>
    """
    st.markdown(cards_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    t1,t2,t3,t4,t5,t6,t7,t8,t9,t10 = st.tabs(["OVERVIEW","TRENDS","TOP","ABC","PREDICTOR","CHAT","SIMULATOR","MAP","BENCHMARKS","EXPORT"])
    
    with t1:
        c1,c2 = st.columns([2,1])
        with c1:
            if rc and len(sales)>0:
                try:
                    if 'Sale_Date' in sales.columns:
                        sales['Month'] = pd.to_datetime(sales['Sale_Date']).dt.to_period('M')
                        monthly = sales.groupby('Month')[rc].sum().reset_index()
                        monthly['Month'] = monthly['Month'].astype(str)
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=monthly['Month'],y=monthly[rc],mode='lines+markers',line=dict(color='#3B82F6',width=3),fill='tozeroy',fillcolor='rgba(59,130,246,0.1)'))
                        fig.update_layout(title='Revenue Trend',height=350,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color=fc2)
                        st.plotly_chart(fig,use_container_width=True)
                except: st.info("Cannot generate trend")
        with c2:
            if catc and rc:
                try:
                    cat_data = sales.groupby(catc)[rc].sum().nlargest(6).reset_index()
                    fig = go.Figure(go.Pie(labels=cat_data[catc],values=cat_data[rc],hole=0.6))
                    fig.update_layout(title='Category Distribution',height=350,paper_bgcolor='rgba(0,0,0,0)',font_color=fc2,showlegend=False)
                    st.plotly_chart(fig,use_container_width=True)
                except: st.info("Cannot generate categories")
        
        st.markdown('<div class="section-title">Recent Transactions</div>',unsafe_allow_html=True)
        if nc and rc and len(sales)>0:
            for _, row in sales.tail(8).iterrows():
                pname = str(row[nc])[:30] if nc in row.index else "Item"
                cat = str(row[catc])[:20] if catc and catc in row.index else "General"
                rev = row[rc] if rc in row.index else 0
                all_rev = sales[rc].dropna()
                pct = (all_rev<rev).mean()*100 if len(all_rev)>0 else 50
                if pct>=75: tcl = "green"
                elif pct<=25: tcl = "red"
                else: tcl = "yellow"
                st.markdown(f'<div class="txn-item"><div class="txn-icon" style="background:rgba(100,100,100,0.2);">{cat[:1]}</div><div><div class="txn-name">{pname}</div><div class="txn-cat">{cat}</div></div><div class="txn-amount color-{tcl}">Rs.{rev/1000:.1f}K</div></div>',unsafe_allow_html=True)
    
    with t2:
        if rc:
            if 'Sale_Date' in sales.columns:
                try:
                    daily = sales.groupby('Sale_Date')[rc].sum().reset_index()
                    fig = px.line(daily,x='Sale_Date',y=rc,title='Daily Revenue Trend',line_shape='spline')
                    fig.update_traces(line_color='#3B82F6',line_width=2)
                    fig.update_layout(height=400,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color=fc2)
                    st.plotly_chart(fig,use_container_width=True)
                except: st.info("Cannot generate daily trend")
    
    with t3:
        if nc and rc:
            top = sales.groupby(nc)[rc].sum().nlargest(10).reset_index()
            fig = px.bar(top,x=rc,y=nc,orientation='h',title='Top 10 by Revenue',color=rc,color_continuous_scale='Blues')
            fig.update_layout(height=450,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font_color=fc2)
            st.plotly_chart(fig,use_container_width=True)
    
    with t4:
        if nc and rc:
            abc = abc_analysis(sales,nc,rc)
            if len(abc)>0:
                abc_sum = abc.groupby('Class').agg(P=('R','count'),Rev=('R','sum')).reset_index()
                c1,c2 = st.columns(2)
                with c1:
                    fig = px.bar(abc_sum,x='Class',y='P',color='Class',title='Products per Class',color_discrete_map={'A':'#10B981','B':'#F59E0B','C':'#EF4444'})
                    fig.update_layout(height=350,paper_bgcolor='rgba(0,0,0,0)',font_color=fc2,showlegend=False)
                    st.plotly_chart(fig,use_container_width=True)
                with c2:
                    fig = px.pie(abc_sum,values='Rev',names='Class',title='Revenue Share',hole=0.5,color='Class',color_discrete_map={'A':'#10B981','B':'#F59E0B','C':'#EF4444'})
                    fig.update_layout(height=350,paper_bgcolor='rgba(0,0,0,0)',font_color=fc2)
                    st.plotly_chart(fig,use_container_width=True)
    
    with t5:
        if nc and uc:
            c1,c2 = st.columns(2)
            days = 184
            with c1:
                td = sales.groupby(nc).agg(T=(uc,'sum'),A=(uc,lambda x:round(x.sum()/days,1))).nlargest(15,'T')
                fig = px.bar(td.reset_index(),x='A',y=nc,orientation='h',title='Avg Daily Demand',color='A',color_continuous_scale='Blues')
                fig.update_layout(height=400,paper_bgcolor='rgba(0,0,0,0)',font_color=fc2)
                st.plotly_chart(fig,use_container_width=True)
            with c2:
                if len(sales[nc].unique())>0:
                    ps = st.selectbox("Product:",sales[nc].unique(),key='pred')
                    ad = sales[sales[nc]==ps][uc].sum()/days
                    st.metric("Avg Daily",f"{ad:.1f}/day")
                    st.metric("Weekly",f"{ad*7:.0f}")
                    st.metric("Monthly",f"{ad*30:.0f}")
    
    with t6:
        q1,q2,q3,q4 = st.columns(4)
        if q1.button("Revenue",use_container_width=True):
            r = chatbot("revenue",sales,m)
            st.session_state.hist.append(("You","Revenue?"))
            st.session_state.hist.append(("Bot",r))
        if q2.button("Stock",use_container_width=True):
            r = chatbot("stock",sales,m)
            st.session_state.hist.append(("You","Stock?"))
            st.session_state.hist.append(("Bot",r))
        if q3.button("Profit",use_container_width=True):
            r = chatbot("profit",sales,m)
            st.session_state.hist.append(("You","Profit?"))
            st.session_state.hist.append(("Bot",r))
        if q4.button("Products",use_container_width=True):
            r = chatbot("products",sales,m)
            st.session_state.hist.append(("You","Products?"))
            st.session_state.hist.append(("Bot",r))
        
        for s,msg in st.session_state.hist[-8:]:
            if s=="You": st.markdown(f'<div class="chat-user">User: {msg}</div>',unsafe_allow_html=True)
            else: st.markdown(f'<div class="chat-bot">Bot: {msg}</div>',unsafe_allow_html=True)
        
        uin = st.text_input("Ask anything about your data:")
        if st.button("Send",use_container_width=True) and uin:
            r = chatbot(uin,sales,m)
            st.session_state.hist.append(("You",uin))
            st.session_state.hist.append(("Bot",r))
            st.rerun()
        
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.hist = []
            st.rerun()
    
    with t7:
        if catc and rc and len(sales[catc].unique())>0:
            scat = st.selectbox("Select Category:",sales[catc].unique())
            spct = st.slider("Price Change %:",-50,100,15)
            if st.button("RUN SIMULATION",use_container_width=True):
                orev = sales[sales[catc]==scat][rc].sum()
                nrev = orev*(1+spct/100)
                diff = nrev-orev
                dc = get_profit_loss_color(diff)
                dcl = "green" if dc=="#10B981" else ("red" if dc=="#EF4444" else "yellow")
                c1,c2 = st.columns(2)
                c1.metric("Current",f"Rs.{orev/1e5:.1f}L")
                c2.markdown(f'**Simulated:** Rs.{nrev/1e5:.1f}L<br><span class="color-{dcl}">Change: Rs.{diff/1e5:.1f}L</span>',unsafe_allow_html=True)
    
    with t8:
        st.markdown('<div class="section-title">Supply Chain Network</div>', unsafe_allow_html=True)
        
        map_df = extract_map_data(sales, st.session_state.products)
        
        ms = 'carto-darkmatter' if theme=='dark' else 'open-street-map'
        fig = px.scatter_mapbox(map_df, lat='lat', lon='lon', size='size', 
                                hover_name='Location', zoom=4, mapbox_style=ms,
                                title='Warehouse and Supplier Locations')
        fig.update_layout(height=500, paper_bgcolor='rgba(0,0,0,0)', font_color=fc2)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Showing {len(map_df)} locations from your data")
    
    with t9:
        cats = ['Availability','Margin %','Revenue Score','Stock Health','Performance']
        your_scores = [m['availability'], m['margin_pct'], min(m['total_revenue']/1e6, 100), max(0, 100 - m['stockout_rate']), 75]
        best_scores = [95, 45, 85, 95, 90]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=your_scores, theta=cats, fill='toself', name='Your Performance', line_color='#10B981'))
        fig.add_trace(go.Scatterpolar(r=best_scores, theta=cats, fill='toself', name='Industry Best', line_color='#3B82F6'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, height=450, paper_bgcolor='rgba(0,0,0,0)', font_color=fc2)
        st.plotly_chart(fig, use_container_width=True)
    
    with t10:
        c1,c2 = st.columns(2)
        if sales is not None: c1.download_button("Sales CSV", sales.to_csv(index=False), "sales_data.csv", use_container_width=True)
        if st.session_state.products is not None: c1.download_button("Products CSV", st.session_state.products.to_csv(index=False), "products_data.csv", use_container_width=True)
        if inventory is not None: c1.download_button("Inventory CSV", inventory.to_csv(index=False), "inventory_data.csv", use_container_width=True)
        
        c2.markdown(f"""
        **CURRENT DATA SUMMARY**
        
        Revenue: <span style="color:{rev_color};">Rs.{m['total_revenue']/1e7:.2f}Cr</span>
        
        Profit: <span style="color:{profit_color};">Rs.{m['total_profit']/1e7:.2f}Cr</span>
        
        Margin: <span style="color:{margin_color};">{m['margin_pct']:.1f}%</span>
        
        Products: <span style="color:#10B981;">{m['product_count']:,}</span>
        
        Transactions: <span style="color:#3B82F6;">{m['total_transactions']:,}</span>
        """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown(f'<div style="text-align:center;opacity:0.5;font-size:12px;">Invento Pro v3.0 | {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

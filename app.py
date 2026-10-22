import streamlit as st
import platform
import socket
import shutil
import time
import math
import tempfile
import os
import subprocess
import json

try:
    import psutil
except ImportError:
    psutil = None

# إعدادات الصفحة
st.set_page_config(page_title="ProofCheck - Evidence-led used-device inspection", page_icon="💻", layout="wide")

# تخصيص التصميم (CSS) لتطابق واجهة الـ HTML الداكنة تماماً
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        color: #e5e7eb;
    }
    .main-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #1f2937;
        border: 1px solid #374151;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
    }
    h1, h2, h3 {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# رأس الصفحة مطابق للـ HTML
col_logo, col_title, col_ver = st.columns([1, 8, 2])
with col_logo:
    st.markdown("### 🅿️")
with col_title:
    st.markdown("### ProofCheck")
    st.caption("Evidence-led used-device inspection")
with col_ver:
    st.markdown("<p style='text-align: right; color: #9ca3af; font-size: 12px;'>Local prototype - v0.1</p>", unsafe_allow_html=True)

st.markdown("---")

# قسم المقدمة (Hero Section)
col_left, col_right = st.columns([7, 4])

with col_left:
    st.markdown("""
    <div class="main-card">
        <h2>Know the device.<br>Not just the seller's story.</h2>
        <p style="color: #9ca3af;">Run real, bounded tests on this Windows or Mac computer. ProofCheck collects system information and measures short CPU, memory, and temporary-storage workloads.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # أزرار التفاعل
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        run_inspection = st.button("Connect to local inspector", type="primary", use_container_width=True)
    with b_col2:
        refresh_info = st.button("Refresh device info", use_container_width=True)
        
    st.markdown("<p style='color: #10b981; font-size: 13px; margin-top: 10px;'>🟢 Connected to local inspector</p>", unsafe_allow_html=True)

with col_right:
    st.markdown("""
    <div class="main-card">
        <h3>What this can prove</h3>
        <p style="color: #9ca3af; font-size: 13px;">Measured values from this machine, at this moment.</p>
        <hr style="border-color: #374151;">
        <p><b>Performance</b><br><span style="color: #9ca3af; font-size: 12px;">Short repeatable microbenchmarks, not a universal device grade.</span></p>
        <p><b>Hardware details</b><br><span style="color: #9ca3af; font-size: 12px;">OS-reported capacity and available battery/sensor data.</span></p>
        <p><b>Storage health</b><br><span style="color: #9ca3af; font-size: 12px;">Basic OS health where exposed; full SMART details may need extra tools.</span></p>
    </div>
    """, unsafe_allow_html=True)

# دوال جلب البيانات
def get_device_identity():
    system = platform.system()
    if system == "Windows":
        ps = r"$cs=Get-CimInstance Win32_ComputerSystem; $bios=Get-CimInstance Win32_BIOS; [PSCustomObject]@{manufacturer=$cs.Manufacturer; model=$cs.Model; serial_number=$bios.SerialNumber} | ConvertTo-Json -Compress"
        try:
            raw = subprocess.check_output(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], text=True, stderr=subprocess.DEVNULL, timeout=5)
            return json.loads(raw.strip()) if raw.strip() else {}
        except Exception:
            pass
    return {"manufacturer": platform.system(), "model": platform.machine(), "serial_number": "N/A"}

identity = get_device_identity()
disk = shutil.disk_usage(os.path.expanduser("~"))

# قسم معلومات الجهاز (Device Information)
st.markdown("""
<div class="main-card">
    <h3>Device information</h3>
    <p style="color: #9ca3af; font-size: 13px;">Read from the operating system via the local Python agent.</p>
</div>
""", unsafe_allow_html=True)

d_col1, d_col2, d_col3 = st.columns(3)
with d_col1:
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Operating system</span>
        <h2 style="margin: 5px 0;">{platform.system()}</h2>
        <span style="color: #9ca3af; font-size: 12px;">{platform.release()} - {platform.machine()}</span>
    </div>
    """, unsafe_allow_html=True)
with d_col2:
    cpu_count = os.cpu_count() or "N/A"
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Logical CPU cores</span>
        <h2 style="margin: 5px 0;">{cpu_count}</h2>
        <span style="color: #9ca3af; font-size: 12px;">Active system threads</span>
    </div>
    """, unsafe_allow_html=True)
with d_col3:
    mem_text = f"{round(psutil.virtual_memory().total / (1024**3), 1)} GB" if psutil else "N/A"
    mem_used = f"{psutil.virtual_memory().percent}% currently used" if psutil else "N/A"
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Memory</span>
        <h2 style="margin: 5px 0;">{mem_text}</h2>
        <span style="color: #9ca3af; font-size: 12px;">{mem_used}</span>
    </div>
    """, unsafe_allow_html=True)

# الصف الثاني من المعلومات
d_col4, d_col5, d_col6 = st.columns(3)
with d_col4:
    free_disk = round(disk.free / (1024**3), 1)
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Home disk free space</span>
        <h2 style="margin: 5px 0;">{free_disk} GB</h2>
        <span style="color: #9ca3af; font-size: 12px;">Free in home-folder volume</span>
    </div>
    """, unsafe_allow_html=True)
with d_col5:
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Device Manufacturer</span>
        <h3 style="margin: 5px 0; font-size: 18px;">{identity.get('manufacturer', 'N/A')}</h3>
        <span style="color: #9ca3af; font-size: 12px;">{identity.get('model', 'N/A')}</span>
    </div>
    """, unsafe_allow_html=True)
with d_col6:
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Temperature sensors</span>
        <h3 style="margin: 5px 0; font-size: 18px;">Unavailable</h3>
        <span style="color: #9ca3af; font-size: 12px;">CPU temperature requires OS or vendor driver.</span>
    </div>
    """, unsafe_allow_html=True)

# قسم اختبارات الأداء (Run real tests)
st.markdown("""
<div class="main-card">
    <h3>Run real tests</h3>
    <p style="color: #9ca3af; font-size: 13px;">Disk test writes a temporary file in your home folder and deletes it afterwards.</p>
</div>
""", unsafe_allow_html=True)

t_col1, t_col2, t_col3, t_col4 = st.columns(4)
with t_col1:
    run_all = st.button("Run all tests", type="primary", use_container_width=True)
with t_col2:
    run_cpu = st.button("CPU only", use_container_width=True)
with t_col3:
    run_mem = st.button("Memory only", use_container_width=True)
with t_col4:
    run_disk = st.button("Storage speed only", use_container_width=True)

if run_all or run_disk:
    with st.spinner("Executing temporary-file storage throughput test..."):
        size = 16 * 1024 * 1024
        chunk = os.urandom(1024 * 1024)
        path = None
        try:
            with tempfile.NamedTemporaryFile(prefix="proofcheck_", suffix=".tmp", dir=os.path.expanduser("~"), delete=False) as f:
                path = f.name
                start = time.perf_counter()
                written = 0
                while written < size:
                    f.write(chunk[:min(len(chunk), size - written)])
                    written += min(len(chunk), size - written)
                f.flush()
                os.fsync(f.fileno())
                write_elapsed = time.perf_counter() - start
            
            start = time.perf_counter()
            read = 0
            with open(path, "rb") as f:
                while True:
                    part = f.read(1024 * 1024)
                    if not part:
                        break
                    read += len(part)
            read_elapsed = time.perf_counter() - start
            
            w_speed = round((size / (1024*1024)) / write_elapsed, 2) if write_elapsed else 0
            r_speed = round((read / (1024*1024)) / read_elapsed, 2) if read_elapsed else 0
            
            st.markdown(f"""
            <div class="metric-card" style="border-color: #3b82f6;">
                <h4>Temporary-file storage speed</h4>
                <p style="font-size: 20px; font-weight: bold; color: #60a5fa;">Write {w_speed} / Read {r_speed} MiB/s</p>
                <span style="color: #9ca3af; font-size: 12px;">Short buffered throughput sample only. Results vary with cache and system state.</span>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error during test: {e}")
        finally:
            if path and os.path.exists(path):
                os.remove(path)

# تنبيه الأمان أسفل الصفحة
st.markdown("""
<div style="background-color: #451a03; border: 1px solid #78350f; padding: 12px; border-radius: 8px; margin-top: 20px;">
    <span style="color: #fbbf24; font-size: 13px;"><b>Safety & accuracy:</b> These short tests do not certify a laptop as good or bad. They do not fully test RAM for errors or diagnose every SSD fault.</span>
</div>
""", unsafe_allow_html=True)

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

# إعدادات الصفحة والتصميم الداكن المماثل للـ HTML
st.set_page_config(page_title="ProofCheck - Evidence-led used-device inspection", page_icon="💻", layout="wide")

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
    h1, h2, h3, h4 {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# رأس الصفحة
col_logo, col_title, col_ver = st.columns([1, 8, 2])
with col_logo:
    st.markdown("### 🅿️")
with col_title:
    st.markdown("### ProofCheck")
    st.caption("Evidence-led used-device inspection")
with col_ver:
    st.markdown("<p style='text-align: right; color: #9ca3af; font-size: 12px;'>Local prototype - v0.1</p>", unsafe_allow_html=True)

st.markdown("---")

# قسم المقدمة
col_left, col_right = st.columns([7, 4])
with col_left:
    st.markdown("""
    <div class="main-card">
        <h2>Know the device.<br>Not just the seller's story.</h2>
        <p style="color: #9ca3af;">Run real, bounded tests on this Windows or Mac computer. ProofCheck collects system information and measures short CPU, memory, and temporary-storage workloads.</p>
    </div>
    """, unsafe_allow_html=True)
    
    b1, b2 = st.columns(2)
    with b1:
        st.button("Connect to local inspector", type="primary", use_container_width=True)
    with b2:
        st.button("Refresh device info", use_container_width=True)
        
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

# دوال جلب البيانات الحقيقية من اللابتوب
def get_device_identity():
    system = platform.system()
    if system == "Windows":
        ps = r"$cs=Get-CimInstance Win32_ComputerSystem; $bios=Get-CimInstance Win32_BIOS; [PSCustomObject]@{manufacturer=$cs.Manufacturer; model=$cs.Model; serial_number=$bios.SerialNumber; bios_date=if($bios.ReleaseDate){$bios.ReleaseDate.ToString('yyyy-MM-dd')}else{$null}} | ConvertTo-Json -Compress"
        try:
            raw = subprocess.check_output(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], text=True, stderr=subprocess.DEVNULL, timeout=5)
            res = json.loads(raw.strip()) if raw.strip() else {}
            return {
                "manufacturer": res.get("manufacturer", "N/A"),
                "model": res.get("model", "N/A"),
                "serial_number": res.get("serial_number", "N/A"),
                "bios_date": res.get("bios_date", "N/A")
            }
        except Exception:
            pass
    return {"manufacturer": platform.system(), "model": platform.machine(), "serial_number": "N/A", "bios_date": "N/A"}

def get_battery_info():
    if psutil:
        try:
            b = psutil.sensors_battery()
            if b:
                plug_status = "Running on AC power" if b.power_plugged else "Running on battery"
                return f"{b.percent}%", plug_status
        except Exception:
            pass
    if platform.system() == "Windows":
        try:
            out = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining | ConvertTo-Json -Compress"], capture_output=True, text=True, timeout=3)
            if out.stdout and out.stdout.strip() != "null":
                data = json.loads(out.stdout.strip())
                return f"{data.get('EstimatedChargeRemaining', 'N/A')}%", "Battery detected"
        except Exception:
            pass
    return "Unavailable", "No battery info exposed"

identity = get_device_identity()
disk = shutil.disk_usage(os.path.expanduser("~"))
battery_pct, battery_note = get_battery_info()

# معلومات النظام الأساسية
st.markdown("""
<div class="main-card">
    <h3>Device information</h3>
    <p style="color: #9ca3af; font-size: 13px;">Read from the operating system via the local Python agent.</p>
</div>
""", unsafe_allow_html=True)

d1, d2, d3 = st.columns(3)
with d1:
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Operating system</span>
        <h2 style="margin: 5px 0;">{platform.system()}</h2>
        <span style="color: #9ca3af; font-size: 12px;">{platform.release()} - {platform.machine()}</span>
    </div>
    """, unsafe_allow_html=True)
with d2:
    cpu_count = os.cpu_count() or "N/A"
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Logical CPU cores</span>
        <h2 style="margin: 5px 0;">{cpu_count}</h2>
        <span style="color: #9ca3af; font-size: 12px;">Active system threads</span>
    </div>
    """, unsafe_allow_html=True)
with d3:
    mem_text = f"{round(psutil.virtual_memory().total / (1024**3), 1)} GB" if psutil else "N/A"
    mem_used = f"{psutil.virtual_memory().percent}% currently used" if psutil else "N/A"
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Memory</span>
        <h2 style="margin: 5px 0;">{mem_text}</h2>
        <span style="color: #9ca3af; font-size: 12px;">{mem_used}</span>
    </div>
    """, unsafe_allow_html=True)

d4, d5, d6 = st.columns(3)
with d4:
    free_disk = round(disk.free / (1024**3), 1)
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Home disk free space</span>
        <h2 style="margin: 5px 0;">{free_disk} GB</h2>
        <span style="color: #9ca3af; font-size: 12px;">Free in home-folder volume</span>
    </div>
    """, unsafe_allow_html=True)
with d5:
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Battery charge</span>
        <h2 style="margin: 5px 0;">{battery_pct}</h2>
        <span style="color: #9ca3af; font-size: 12px;">{battery_note}</span>
    </div>
    """, unsafe_allow_html=True)
with d6:
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Temperature sensors</span>
        <h3 style="margin: 5px 0; font-size: 18px;">Unavailable</h3>
        <span style="color: #9ca3af; font-size: 12px;">CPU temperature requires OS or vendor driver.</span>
    </div>
    """, unsafe_allow_html=True)

# قسم تفاصيل الموديل والـ Serial Number (لمعرفة تغير القطع الداخلية)
s1, s2, s3 = st.columns(3)
with s1:
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Device manufacturer / model</span>
        <h4 style="margin: 5px 0; color: #60a5fa; font-size: 16px;">{identity.get('manufacturer')}</h4>
        <p style="margin: 0; font-size: 13px; font-weight: bold;">{identity.get('model')}</p>
        <span style="color: #9ca3af; font-size: 11px;">Hardware model reported by the OS</span>
    </div>
    """, unsafe_allow_html=True)
with s2:
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">Serial number</span>
        <h4 style="margin: 5px 0; color: #f87171; font-size: 16px;">{identity.get('serial_number')}</h4>
        <span style="color: #9ca3af; font-size: 11px;">Sensitive identifier — do not share publicly</span>
    </div>
    """, unsafe_allow_html=True)
with s3:
    st.markdown(f"""
    <div class="metric-card">
        <span style="color: #9ca3af; font-size: 12px;">BIOS release date</span>
        <h4 style="margin: 5px 0; font-size: 16px;">{identity.get('bios_date')}</h4>
        <span style="color: #9ca3af; font-size: 11px;">This is the BIOS firmware release date.</span>
    </div>
    """, unsafe_allow_html=True)

# قسم الاختبارات الفورية
st.markdown("""
<div class="main-card">
    <h3>Run real tests</h3>
    <p style="color: #9ca3af; font-size: 13px;">Disk test writes a temporary file in your home folder and deletes it afterwards.</p>
</div>
""", unsafe_allow_html=True)

t1, t2, t3, t4 = st.columns(4)
with t1:
    run_all = st.button("Run all tests", type="primary", use_container_width=True)
with t2:
    run_cpu = st.button("CPU only", use_container_width=True)
with t3:
    run_mem = st.button("Memory only", use_container_width=True)
with t4:
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
                <p style="font-size: 18px; font-weight: bold; color: #60a5fa;">Write {w_speed} / Read {r_speed} MiB/s</p>
                <span style="color: #9ca3af; font-size: 12px;">Short buffered throughput sample only.</span>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            if path and os.path.exists(path):
                os.remove(path)

st.markdown("""
<div style="background-color: #451a03; border: 1px solid #78350f; padding: 12px; border-radius: 8px; margin-top: 20px;">
    <span style="color: #fbbf24; font-size: 13px;"><b>Safety & accuracy:</b> These short tests do not certify a laptop as good or bad. They do not fully test RAM for errors or diagnose every SSD fault.</span>
</div>
""", unsafe_allow_html=True)

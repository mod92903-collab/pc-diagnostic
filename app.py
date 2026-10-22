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

st.set_page_config(page_title="ProofCheck - نظام فحص الكمبيوتر", page_icon="💻", layout="centered")

st.title("💻 ProofCheck - فحص وتشخيص عيوب الكمبيوتر")
st.write("أداة تشخيص محلية لفحص أداء المعالج، الذاكرة، والتخزين.")

def get_device_identity():
    system = platform.system()
    if system == "Windows":
        ps = r"$cs=Get-CimInstance Win32_ComputerSystem; $bios=Get-CimInstance Win32_BIOS; [PSCustomObject]@{manufacturer=$cs.Manufacturer; model=$cs.Model; serial_number=$bios.SerialNumber} | ConvertTo-Json -Compress"
        try:
            raw = subprocess.check_output(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps], text=True, stderr=subprocess.DEVNULL, timeout=5)
            return json.loads(raw.strip()) if raw.strip() else {}
        except Exception:
            pass
    return {"manufacturer": platform.system(), "model": platform.machine()}

def cpu_benchmark():
    start = time.perf_counter()
    n = 220_000
    acc = 0.0
    for i in range(1, n + 1):
        acc += math.sqrt(i) * math.sin(i / 17.0)
    elapsed = time.perf_counter() - start
    return round(n / elapsed, 1) if elapsed else 0

if st.button("بدء الفحص الشامل", type="primary"):
    with st.spinner("جاري فحص مكونات الجهاز..."):
        time.sleep(0.5)
        identity = get_device_identity()
        disk = shutil.disk_usage(os.path.expanduser("~"))
        
        st.success("تم إتمام الفحص بنجاح!")
        
        st.subheader("📊 معلومات النظام الأساسية:")
        st.info(f"**نظام التشغيل:** {platform.system()} {platform.release()} ({platform.machine()})")
        st.info(f"**اسم الجهاز (Hostname):** {socket.gethostname()}")
        
        col1, col2 = st.columns(2)
        with col1:
            if psutil:
                vm = psutil.virtual_memory()
                st.metric(label="استهلاك الذاكرة (RAM)", value=f"{vm.percent}%", delta=f"المتاح: {round(vm.available/(1024**3), 1)} GB")
            else:
                st.metric(label="التخزين المستخدم", value=f"{round(disk.used/(1024**3), 1)} GB")
                
        with col2:
            score = cpu_benchmark()
            st.metric(label="أداء المعالج (Benchmark)", value=f"{score} ops/sec")

        st.warning("⚠️ ملاحظة: هذا الفحص يقرأ حالة المكونات والبيانات الحية المرتبطة بالنظام التشغيلي.")

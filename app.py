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

# إعدادات الواجهة
st.set_page_config(page_title="ProofCheck - فحص عيوب الكمبيوتر", page_icon="💻", layout="centered")

st.title("💻 ProofCheck - نظام فحص وتشخيص عيوب الكمبيوتر")
st.write("أداة فحص محلية متكاملة لفحص المعالج، الذاكرة، التخزين، والبطارية.")

# دوال الفحص والتشخيص الشاملة
def get_battery():
    if psutil:
        try:
            b = psutil.sensors_battery()
            if b:
                return {
                    "percent": b.percent,
                    "plugged_in": b.power_plugged,
                    "seconds_left": b.secsleft if b.secsleft >= 0 else None,
                    "source": "psutil"
                }
        except Exception:
            pass
    system = platform.system()
    if system == "Windows":
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-CimInstance Win32_Battery | Select-Object EstimatedChargeRemaining,BatteryStatus | ConvertTo-Json -Compress"],
                           capture_output=True, text=True, timeout=4)
        if out.stdout and out.stdout.strip() != "null":
            try:
                return {"windows_battery": json.loads(out.stdout.strip()), "source": "Win32_Battery"}
            except Exception:
                pass
    return {"available": False, "note": "بيانات البطارية غير متوفرة مباشرة عبر هذا النظام."}

def cpu_benchmark():
    start = time.perf_counter()
    n = 220_000
    acc = 0.0
    for i in range(1, n + 1):
        acc += math.sqrt(i) * math.sin(i / 17.0)
    elapsed = time.perf_counter() - start
    return {
        "elapsed_seconds": round(elapsed, 4),
        "operations_per_second": round(n / elapsed, 1) if elapsed else None,
        "checksum": round(acc, 4)
    }

def memory_benchmark():
    size = 8 * 1024 * 1024
    start = time.perf_counter()
    block = bytearray(size)
    step = 4096
    for i in range(0, size, step):
        block[i] = (i // step) % 256
    checksum = sum(block[::step])
    elapsed = time.perf_counter() - start
    del block
    return {
        "bytes_tested": size,
        "elapsed_seconds": round(elapsed, 4),
        "checksum": checksum
    }

def disk_benchmark():
    size = 16 * 1024 * 1024  # 16 ميجابايت للفحص السريع على السحابة
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
        
        return {
            "write_mib_sec": round((size / (1024*1024)) / write_elapsed, 2) if write_elapsed else None,
            "read_mib_sec": round((read / (1024*1024)) / read_elapsed, 2) if read_elapsed else None,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        if path:
            try:
                os.remove(path)
            except OSError:
                pass

# زر بدء الفحص الشامل
if st.button("بدء الفحص الشامل المتقدم", type="primary"):
    with st.spinner("جاري تشخيص مكونات الجهاز بدقة..."):
        time.sleep(1)
        
        disk = shutil.disk_usage(os.path.expanduser("~"))
        battery = get_battery()
        cpu_res = cpu_benchmark()
        mem_res = memory_benchmark()
        disk_res = disk_benchmark()
        
        st.success("تم إتمام الفحص الشامل بنجاح!")
        
        # 1. معلومات النظام
        st.subheader("🖥️ معلومات النظام واللوحة")
        st.info(f"**نظام التشغيل:** {platform.system()} {platform.release()} ({platform.machine()})")
        st.info(f"**المعالج:** {platform.processor() or 'غير متوفر'}")
        
        # 2. الموارد والذاكرة
        st.subheader("📊 الذاكرة والتخزين")
        col1, col2 = st.columns(2)
        with col1:
            if psutil:
                vm = psutil.virtual_memory()
                st.metric(label="استهلاك الذاكرة (RAM)", value=f"{vm.percent}%", delta=f"المتاح: {round(vm.available/(1024**3), 1)} GB")
            else:
                st.metric(label="التخزين المستخدم", value=f"{round(disk.used/(1024**3), 1)} GB")
        with col2:
            st.metric(label="إجمالي مساحة القرص", value=f"{round(disk.total/(1024**3), 1)} GB", delta=f"المتبقي: {round(disk.free/(1024**3), 1)} GB")

        # 3. نتائج الاختبارات والأداء (Benchmarks)
        st.subheader("⚡ نتائج اختبارات الأداء (Benchmarks)")
        st.write(f"- **أداء المعالج الحسابي:** {cpu_res.get('operations_per_second')} عملية/ثانية")
        st.write(f"- **اختبار استجابة الذاكرة (RAM):** تم اختبار {round(mem_res.get('bytes_tested')/(1024*1024))} ميجابايت بنجاح.")
        if "write_mib_sec" in disk_res:
            st.write(f"- **سرعة التخزين (كتابة):** {disk_res.get('write_mib_sec')} ميجابايت/ثانية")
            st.write(f"- **سرعة التخزين (قراءة):** {disk_res.get('read_mib_sec')} ميجابايت/ثانية")

        # 4. حالة البطارية
        st.subheader("🔋 حالة البطارية والطاقة")
        st.json(battery)

        st.warning("⚠️ ملاحظة: هذه البيانات تُفحص محلياً لتشخيص الأداء وكشف أي قصور محتمل في المكونات.")

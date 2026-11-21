import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

base_url=os.getenv("TEST_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
out=Path(__file__).resolve().parents[1]/"evidence"/os.getenv("TEST_EVIDENCE_DIR", "local")
out.mkdir(exist_ok=True)
errors=[]
results=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel="msedge",headless=True)
    page=browser.new_page(viewport={"width":1440,"height":1000})
    page.on("pageerror",lambda error:errors.append(str(error)))
    page.goto(base_url,wait_until="networkidle")
    page.locator("#chatForm input").fill("Kapan jam operasional SSC?")
    with page.expect_response(lambda r: "/api/chat" in r.url,timeout=90000) as pending:
        page.locator("#chatForm").evaluate("form => form.requestSubmit()")
    res=pending.value
    results.append({"case":"mahasiswa_ssc","status":res.status,"data":res.json()})
    page.wait_for_timeout(800)
    page.screenshot(path=str(out/"01_chat_mahasiswa.png"),full_page=True)
    page.locator("#chatForm input").fill("Apa kode verifikasi moderasi nilai dosen?")
    with page.expect_response(lambda r: "/api/chat" in r.url,timeout=90000) as pending:
        page.locator("#chatForm").evaluate("form => form.requestSubmit()")
    res=pending.value
    results.append({"case":"mahasiswa_internal_ditolak","status":res.status,"data":res.json()})
    assert "MODERASI-8472" not in res.json()["answer"]
    assert all(not item["title"].startswith("INTERNAL") for item in res.json()["sources"])
    page.wait_for_timeout(500)
    page.screenshot(path=str(out/"04_isolasi_mahasiswa.png"),full_page=True)
    page.locator("#userName").fill("dosen")
    page.locator("#userPassword").fill(os.environ.get("TEST_DOSEN_PASSWORD", "dosen123"))
    page.locator("#userLogin").evaluate("form => form.requestSubmit()")
    page.wait_for_function("sessionStorage.getItem('userRole') === 'dosen'")
    page.wait_for_load_state("networkidle")
    page.locator("#chatForm input").fill("Apa kode verifikasi moderasi dan batas waktu berita acara moderasi nilai dosen?")
    with page.expect_response(lambda r: "/api/chat" in r.url,timeout=90000) as pending:
        page.locator("#chatForm").evaluate("form => form.requestSubmit()")
    res=pending.value
    results.append({"case":"dosen_internal","status":res.status,"data":res.json()})
    page.wait_for_timeout(800)
    page.screenshot(path=str(out/"02_chat_dosen.png"),full_page=True)
    assert "MODERASI-8472" in res.json()["answer"]
    docid=res.json()["sources"][0]["document_id"]
    page.evaluate("id => openSourceModal(id, 'Panduan Dosen')",docid)
    page.wait_for_function("document.getElementById('sourceModalBody').textContent.includes('MODERASI-8472')")
    page.screenshot(path=str(out/"05_sumber_dosen.png"),full_page=True)
    page.goto(base_url+"/admin",wait_until="networkidle")
    page.locator("#loginUsername").fill("admin")
    page.locator("#loginPassword").fill(os.environ.get("TEST_ADMIN_PASSWORD", "admin123"))
    page.locator("#loginForm").evaluate("form => form.requestSubmit()")
    page.locator("#dashboardSection").wait_for(state="visible")
    page.wait_for_function("document.querySelectorAll('#roleChoices input').length >= 2")
    page.wait_for_timeout(800)
    page.screenshot(path=str(out/"03_admin_roles.png"),full_page=True)
    (out/"browser_results.json").write_text(json.dumps({"results":results,"page_errors":errors},ensure_ascii=False,indent=2),encoding="utf-8")
    browser.close()
(out/"browser_results.json").write_text(json.dumps({"results":results,"page_errors":errors},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"page_errors":errors,"responses":[{"case":r["case"],"status":r["status"],"answer":r["data"].get("answer")} for r in results]},ensure_ascii=True,indent=2))
if errors: raise SystemExit(1)

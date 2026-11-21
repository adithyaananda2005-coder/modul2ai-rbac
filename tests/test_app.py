import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TEMP = tempfile.TemporaryDirectory()
os.environ["DB_PATH"] = str(Path(TEMP.name) / "test.db")
os.environ["UPLOAD_DIR"] = str(Path(TEMP.name) / "uploads")
os.environ["GROQ_API_KEY"] = ""
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["DOSEN_USERNAME"] = "dosen"
os.environ["DOSEN_PASSWORD"] = "dosen123"
from fastapi.testclient import TestClient
from app.main import app

class ApplicationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()
        cls.admin = {"Authorization": "Bearer " + cls.client.post("/api/auth/login", json={"username":"admin","password":"admin123"}).json()["token"]}
        cls.dosen = {"Authorization": "Bearer " + cls.client.post("/api/auth/user-login", json={"username":"dosen","password":"dosen123"}).json()["token"]}

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None,None,None)

    def test_pages_and_seed(self):
        for path in ["/", "/admin", "/health"]:
            self.assertEqual(self.client.get(path).status_code, 200)
        docs=self.client.get("/api/documents",headers=self.admin).json()["documents"]
        self.assertEqual(len(docs),5)
        self.assertTrue(all(d["total_chunks"] > 0 for d in docs))

    def test_authentication_and_spoofing(self):
        self.assertEqual(self.client.get("/api/documents").status_code,401)
        self.assertEqual(self.client.post("/api/auth/login",json={"username":"admin","password":"wrong"}).status_code,401)
        self.assertEqual(self.client.post("/api/chat",json={"question":"moderasi nilai", "role":"dosen"}).status_code,403)
        self.assertEqual(self.client.post("/api/chat",headers={"Authorization":"Bearer invalid"},json={"question":"halo"}).status_code,401)

    def test_sensitive_sources_and_download(self):
        docs=self.client.get("/api/documents",headers=self.admin).json()["documents"]
        doc=next(d for d in docs if d["title"].startswith("INTERNAL"))
        docid=doc["id"]
        self.assertEqual(self.client.get(f"/api/public/documents/{docid}").status_code,404)
        self.assertEqual(self.client.get(f"/uploads/{doc['filename']}").status_code,404)
        self.assertEqual(self.client.get(f"/api/public/documents/{docid}?role=dosen").status_code,403)
        res=self.client.get(f"/api/public/documents/{docid}?role=dosen",headers=self.dosen)
        self.assertIn("MODERASI-8472",res.json()["content"])
        self.assertEqual(self.client.get(res.json()["url"],headers=self.dosen).status_code,200)
        with patch("app.main.generate_answer", side_effect=lambda q,r,ch:{"answer":" | ".join(c["text"] for c in ch),"sources":[c["document_id"] for c in ch]}):
            student=self.client.post("/api/chat",json={"question":"kode verifikasi moderasi nilai dosen", "role":"mahasiswa"}).json()
            lecturer=self.client.post("/api/chat",headers=self.dosen,json={"question":"kode verifikasi moderasi nilai dosen", "role":"dosen"}).json()
        self.assertNotIn(docid,student["sources"])
        self.assertNotIn("MODERASI-8472",student["answer"])
        self.assertIn("MODERASI-8472",lecturer["answer"])

    def test_role_upload_toggle_delete(self):
        res=self.client.post("/api/roles",headers=self.admin,json={"name":"penguji"})
        self.assertEqual(res.status_code,201)
        rid=res.json()["role"]["id"]
        self.assertEqual(self.client.post("/api/documents/upload",headers=self.admin,data={"role_ids":"[99999]"},files={"file":("test.txt",b"test")}).status_code,400)
        res=self.client.post("/api/documents/upload",headers=self.admin,data={"role_ids":f"[{rid}]"},files={"file":("test.txt",b"Pengujian role khusus penguji.")})
        self.assertEqual(res.status_code,201)
        did=res.json()["document_id"]
        self.assertEqual(self.client.get(f"/api/documents/{did}/chunks",headers=self.admin).status_code,200)
        self.assertEqual(self.client.patch(f"/api/documents/{did}/toggle",headers=self.admin).json()["is_active"],False)
        self.assertEqual(self.client.delete(f"/api/documents/{did}",headers=self.admin).status_code,200)
        self.assertEqual(self.client.delete(f"/api/roles/{rid}",headers=self.admin).status_code,200)

    def test_offline_and_validation(self):
        res=self.client.post("/api/chat",json={"question":"jam operasional SSC"})
        self.assertEqual(res.status_code,200)
        self.assertTrue(res.json()["sources"])
        self.assertEqual(self.client.post("/api/chat",json={"question":" "}).status_code,400)
        self.assertEqual(self.client.get("/api/admin/groq-quota",headers=self.admin).status_code,200)

if __name__ == "__main__":
    unittest.main(verbosity=2)

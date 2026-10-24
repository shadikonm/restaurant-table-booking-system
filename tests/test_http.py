import importlib.util,tempfile,unittest
from pathlib import Path
@unittest.skipUnless(importlib.util.find_spec("flask"),"Flask not installed")
class HTTP(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import app
  cls.module=app
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  self.old=self.module.DATABASE
  self.module.DATABASE=str(Path(self.temp.name)/"test.db")
  self.module.app.config["TESTING"]=True
  self.module.init_db()
  self.client=self.module.app.test_client()
 def tearDown(self):
  self.module.DATABASE=self.old
  self.temp.cleanup()
 def test_home(self): self.assertEqual(self.client.get("/").status_code,200)
 def test_missing_availability(self): self.assertEqual(self.client.get("/api/availability").status_code,400)
 def test_bad_availability_date(self): self.assertEqual(self.client.get("/api/availability?date=bad&time=19:00&guests=2").status_code,400)
 def test_admin_guest(self): self.assertIn(self.client.get("/admin").status_code,(301,302,303,307,308))

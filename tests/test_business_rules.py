import ast
from datetime import datetime,timedelta
from pathlib import Path
import re,unittest
SOURCE=Path(__file__).resolve().parents[1]/"app.py"
tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
names={"overlap","normalize_phone","normalize_name"}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
scope={"datetime":datetime,"timedelta":timedelta,"re":re,"BOOKING_DURATION_HOURS":2}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE),"exec"),scope)
class Rules(unittest.TestCase):
 def test_overlap(self): self.assertTrue(scope["overlap"]("19:00","20:00"))
 def test_no_overlap_on_boundary(self): self.assertFalse(scope["overlap"]("19:00","21:00"))
 def test_no_overlap_far_apart(self): self.assertFalse(scope["overlap"]("12:00","19:00"))
 def test_phone(self): self.assertEqual(scope["normalize_phone"]("+7 (701) 123-45-67"),"77011234567")
 def test_name(self): self.assertEqual(scope["normalize_name"]("  Айгүл   ТЕСТ  "),"айгүл тест")
 def test_tables(self):
  n=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="TABLES" for t in n.targets))
  tables=ast.literal_eval(n.value)
  self.assertEqual((len(tables),sum(k<=10 for k in tables),sum(k>10 for k in tables)),(16,10,6))

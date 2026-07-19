import json, tempfile, threading, unittest, urllib.error, urllib.request
from pathlib import Path
from atintel.server import Handler, ThreadingHTTPServer
from atintel.storage import connect, ingest_file

class ServerContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.db=Path(self.tmp.name)/"x.sqlite3"
        ingest_file(connect(self.db),Path(__file__).parents[1]/"examples/manual_private_import.synthetic.json")
        self.server=ThreadingHTTPServer(("127.0.0.1",0),Handler); self.server.db_path=str(self.db)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.base=f"http://127.0.0.1:{self.server.server_port}"
    def tearDown(self): self.server.shutdown(); self.server.server_close(); self.tmp.cleanup()
    def get(self,path):
        with urllib.request.urlopen(self.base+path,timeout=3) as r:return r.status,json.load(r)
    def test_read_only_and_no_secret_fields(self):
        status,health=self.get("/api/health"); self.assertEqual(status,200)
        self.assertEqual(health["private_browser_automation"],"disabled_by_platform_terms")
        payload=[]
        for path in ("/api/summary","/api/works","/api/archives","/api/tags","/api/profiles","/api/comments","/api/comments/synthetic-comment-1","/api/rights/candidates","/api/rights/cases"):
            payload.append(self.get(path)[1])
        text=json.dumps(payload).lower()
        for forbidden in ('"password"','"cookie"','"cookies"','"authorization"','"localstorage"','"otp"','"token"','"session"'):
            self.assertNotIn(forbidden,text)
        req=urllib.request.Request(self.base+"/api/summary",data=b"{}",method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx: urllib.request.urlopen(req,timeout=3)
        self.assertEqual(ctx.exception.code,405)

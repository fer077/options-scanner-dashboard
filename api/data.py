from http.server import BaseHTTPRequestHandler
import json, os, ssl, urllib.request

def _get(path):
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(
        f"{url}/rest/v1/{path}",
        headers={"apikey": key, "Authorization": f"Bearer {key}"}
    )
    with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
        return json.loads(r.read())

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            rows = _get("scans?select=scan_id,created_at,opportunities,meta&order=created_at.desc&limit=1")
            if rows:
                row  = rows[0]
                body = json.dumps({
                    "scan_id":       row.get("scan_id"),
                    "timestamp":     row.get("created_at"),
                    "opportunities": row.get("opportunities", []),
                    "meta":          row.get("meta", {}),
                    "count":         len(row.get("opportunities", [])),
                    "status":        {"active": True}
                })
            else:
                body = json.dumps({"opportunities": [], "count": 0, "status": {"active": False}})
        except Exception as e:
            body = json.dumps({"error": str(e), "opportunities": [], "count": 0})

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args):
        pass

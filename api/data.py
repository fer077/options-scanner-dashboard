"""
api/data.py — Endpoint serverless en Vercel
Lee los datos de Supabase y los devuelve al dashboard.
"""

import os, json
from http.server import BaseHTTPRequestHandler


def get_supabase_data(endpoint: str) -> dict:
    """Consulta Supabase REST API directamente (sin librería)."""
    import urllib.request, urllib.error

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")

    if not url or not key:
        return {"error": "Supabase no configurado"}

    try:
        req = urllib.request.Request(
            f"{url}/rest/v1/{endpoint}",
            headers={
                "apikey":        key,
                "Authorization": f"Bearer {key}",
                "Content-Type":  "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/api/data" or path == "/api/data/latest":
            # Último scan
            rows = get_supabase_data(
                "scans?select=scan_id,created_at,opportunities,meta"
                "&order=created_at.desc&limit=1"
            )
            if isinstance(rows, list) and rows:
                row  = rows[0]
                body = json.dumps({
                    "scan_id":       row.get("scan_id"),
                    "timestamp":     row.get("created_at"),
                    "opportunities": row.get("opportunities", []),
                    "meta":          row.get("meta", {}),
                    "count":         len(row.get("opportunities", [])),
                })
            else:
                body = json.dumps({"opportunities": [], "count": 0, "error": str(rows)})

        elif path == "/api/data/history":
            # Historial (solo meta, sin oportunidades)
            rows = get_supabase_data(
                "scans?select=scan_id,created_at,meta"
                "&order=created_at.desc&limit=20"
            )
            history = []
            if isinstance(rows, list):
                for r in reversed(rows):
                    meta = r.get("meta") or {}
                    history.append({
                        "scan_id":   r.get("scan_id"),
                        "timestamp": r.get("created_at"),
                        "count":     meta.get("count", 0),
                        "top_score": meta.get("top_score", 0),
                    })
            body = json.dumps({"history": history})

        elif path == "/api/data/status":
            # Estado del scanner basado en antigüedad del último scan
            from datetime import datetime, timezone, timedelta
            rows = get_supabase_data(
                "scans?select=created_at&order=created_at.desc&limit=1"
            )
            if isinstance(rows, list) and rows:
                ts_str  = rows[0].get("created_at", "")
                try:
                    ts      = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    age_min = (datetime.now(timezone.utc) - ts).total_seconds() / 60
                    body = json.dumps({
                        "active":      age_min < 15,
                        "last_scan":   ts_str,
                        "age_minutes": round(age_min, 1),
                    })
                except Exception:
                    body = json.dumps({"active": False, "last_scan": None})
            else:
                body = json.dumps({"active": False, "last_scan": None})
        else:
            body = json.dumps({"error": "Endpoint no encontrado"})

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args):
        pass  # Silenciar logs de Vercel

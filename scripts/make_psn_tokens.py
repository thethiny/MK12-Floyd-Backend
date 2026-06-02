import os
import sys
import tempfile
import webbrowser
from src.api.psn_service import PSNService
from src.api.psn_web import PSNAuth

HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>PSN Reseed</title>
<style>
  body {{ font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #1a1a2e; color: #eee; }}
  h2 {{ margin-bottom: 32px; }}
  .buttons {{ display: flex; gap: 16px; }}
  a {{ text-decoration: none; padding: 14px 28px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }}
  .login {{ background: #003087; color: #fff; }}
  .npsso {{ background: #00439c; color: #fff; }}
  a:hover {{ opacity: 0.85; }}
  p {{ margin-top: 24px; color: #aaa; font-size: 14px; }}
</style>
</head>
<body>
<h2>PSN Token Reseed</h2>
<div class="buttons">
  <a class="login" href="{login_url}" target="_blank">Login to PlayStation</a>
  <a class="npsso" href="{npsso_url}" target="_blank">Get NPSSO</a>
</div>
<p>Copy the "npsso" value from the JSON, then run:<br><code>python -m scripts.make_psn_tokens &lt;npsso&gt;</code></p>
</body>
</html>""".format(login_url=PSNAuth.LOGIN_URL, npsso_url=PSNAuth.SSOCOOKIE_URL)

if __name__ == "__main__":
    npsso = sys.argv[1] if len(sys.argv) > 1 else os.getenv("PSN_NPSSO", "")
    if not npsso:
        print("No NPSSO provided. Opening helper page...")
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
            f.write(HTML)
            webbrowser.open(f"file://{f.name}")
        npsso = input("Paste NPSSO (string or JSON): ").strip()
        if not npsso:
            print("No NPSSO entered. Exiting.")
            sys.exit(1)

    # Accept plain string or JSON dict with "npsso" and optional "expires_in" keys
    npsso_expires_in = None
    try:
        import json
        data = json.loads(npsso)
        npsso = data.get("npsso", "").strip()
        npsso_expires_in = data.get("expires_in")
        if not npsso:
            print("JSON provided but missing 'npsso' key.")
            sys.exit(1)
    except (json.JSONDecodeError, AttributeError):
        npsso = npsso.strip()

    if npsso_expires_in:
        print(f"NPSSO expires_in: {npsso_expires_in}s")

    tokens_folder = "db"
    psn = PSNService(token_cache_folder=tokens_folder)
    psn.reseed(npsso, npsso_expires_in=npsso_expires_in)
    print(f"PSN tokens saved to {tokens_folder}/psn_tokens.json")

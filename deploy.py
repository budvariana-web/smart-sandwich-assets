"""Deploy Smart Sandwich Bar GAS web app.
Updates the SAME deployment (stable URL).
Usage: python deploy.py [description]
"""

import json, urllib.request, urllib.parse, sys, os

SCRIPT_ID = "1ocvsaP1j5MPe3INWrUQmbSw0IT2ZOi-ZszAMeaDPoJgqLnjLBqvdzjJr"
DEPLOYMENT_ID = "AKfycbxlyDvP-_TbVVXGXG7_rxKdXvowJxPu8gn8BXpLKuGnfsCmpHL71CXIWSVUbbamwY4skg"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hermes", "projects", "smart-sandwich-bar", ".credentials")

def get_token():
    creds_path = os.path.join(CREDS_DIR, "oauth-token.json")
    cs_path = os.path.join(CREDS_DIR, "client-secret.json")
    with open(creds_path) as f:
        creds = json.load(f)
    with open(cs_path) as f:
        cs = json.load(f)
    k = list(cs.keys())[0]
    data = urllib.parse.urlencode({
        "client_id": cs[k]["client_id"],
        "client_secret": cs[k]["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    resp = urllib.request.urlopen(req)
    nc = json.loads(resp.read())
    creds["access_token"] = nc["access_token"]
    creds["expiry_date"] = time.time() * 1000 + nc.get("expires_in", 3600) * 1000
    with open(creds_path, "w") as f:
        json.dump(creds, f, indent=2)
    return creds["access_token"]

import time

def api(token, path, method="GET", body=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"https://script.googleapis.com/v1/{path}",
        data=data, headers=headers, method=method
    )
    return json.loads(urllib.request.urlopen(req).read())

def deploy(description="deploy"):
    token = get_token()

    # Read files
    files = []
    for fname in ["Code.gs", "Index.html", "Assets.html", "appsscript.json"]:
        path = os.path.join(BASE_DIR, "delivery", "smart-sandwich-menu-display", fname)
        if not os.path.exists(path):
            path = os.path.join(BASE_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if fname == "Code.gs":
            files.append({"name": fname, "type": "SERVER_JS", "source": content})
        elif fname == "appsscript.json":
            files.append({"name": "appsscript", "type": "JSON", "source": content})
        else:
            files.append({"name": fname.replace(".html", ""), "type": "HTML", "source": content})

    # Upload content
    print("Uploading content...")
    api(token, f"projects/{SCRIPT_ID}/content", method="PUT", body={"files": files})

    # Create version
    print(f"Creating version: {description}...")
    ver = api(token, f"projects/{SCRIPT_ID}/versions", method="POST",
              body={"description": description})
    vnum = ver["versionNumber"]
    print(f"  Version {vnum} created")

    # Update existing deployment (same URL!)
    print(f"Updating deployment {DEPLOYMENT_ID[:20]}...")
    result = api(token, f"projects/{SCRIPT_ID}/deployments/{DEPLOYMENT_ID}", method="PUT",
                 body={"deploymentConfig": {"versionNumber": vnum, "description": description}})
    url = result["entryPoints"][0]["webApp"]["url"]
    print(f"  URL: {url}")
    return url

if __name__ == "__main__":
    desc = sys.argv[1] if len(sys.argv) > 1 else "deploy"
    deploy(desc)

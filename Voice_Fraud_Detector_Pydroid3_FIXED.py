import json
import re
import threading
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

HOST = "127.0.0.1"
PORT = 8080
HISTORY = []

PATTERNS = {
    "OTP / Verification": ["otp", "one time password", "verification code", "security code", "share otp", "tell me the otp", "give me the otp", "share the code", "tell me the code"],
    "Bank / Card Information": ["bank account", "account number", "bank details", "card number", "debit card", "credit card", "cvv", "atm pin", "pin number", "banking details"],
    "Payment Request": ["send money", "transfer money", "send the money", "pay now", "make a payment", "payment required", "processing fee", "registration fee", "upi payment", "upi id", "send payment", "transfer the amount"],
    "Urgency / Threat": ["urgent", "very urgent", "immediately", "act immediately", "last warning", "account will be blocked", "account will be closed", "account will be suspended", "legal action", "police complaint", "within 10 minutes", "within 5 minutes"],
    "Remote Access": ["remote access", "screen sharing", "share your screen", "screen share", "install this app", "download this app", "anydesk", "teamviewer", "remote desktop"],
    "Prize / Lottery": ["you have won", "you won", "lottery", "lottery winner", "prize money", "cash prize", "lucky winner", "claim your prize"],
    "Fake KYC": ["kyc update", "kyc expired", "update your kyc", "verify your kyc", "account verification", "bank verification"],
    "Impersonation": ["calling from the bank", "i am calling from the bank", "bank officer", "bank employee", "customer care", "police officer", "cyber crime officer", "government officer"]
}

def clean(text):
    text = text.lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text)).strip()

def analyze(text):
    t = clean(text)
    categories = []
    matches = []

    for category, words in PATTERNS.items():
        for word in words:
            if word in t:
                if category not in categories:
                    categories.append(category)
                if word not in matches:
                    matches.append(word)

    score = len(categories) * 15 + len(matches) * 5

    if "Bank / Card Information" in categories:
        score += 10
    if "Payment Request" in categories:
        score += 10
    if "Urgency / Threat" in categories:
        score += 10
    if "Payment Request" in categories and "Urgency / Threat" in categories:
        score += 15
    if "OTP / Verification" in categories and "Urgency / Threat" in categories:
        score += 15
    if "Remote Access" in categories:
        score += 15

    score = min(score, 100)

    if score >= 70:
        level = "HIGH RISK"
    elif score >= 40:
        level = "MEDIUM RISK"
    else:
        level = "LOW RISK"

    result = {
        "text": text,
        "level": level,
        "score": score,
        "categories": categories,
        "matches": matches,
        "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }

    HISTORY.append(result)
    return result


HTML = r"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice Fraud Detector</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#101820;color:white;font-family:Arial,sans-serif}
.container{max-width:650px;margin:auto;padding:20px 14px 35px}
h1{text-align:center;font-size:30px;margin:15px 0 8px}
.subtitle{text-align:center;color:#aeb8c2;font-size:18px;margin-bottom:20px}
button{width:100%;border:0;border-radius:3px;padding:16px 10px;margin:7px 0;font-size:19px;color:white;background:#2d4658}
#voiceBtn{background:#3d9cff}
button:disabled{opacity:.55}
.status{text-align:center;color:#aeb8c2;min-height:25px;margin:5px 0 12px}
h2{font-size:22px;margin:15px 0 8px}
.speech{width:100%;min-height:180px;background:#182631;border:1px solid #9aa3aa;color:white;padding:14px;font-size:17px;line-height:1.45}
.card{background:#182631;padding:18px;margin-top:10px;text-align:center}
.risk{font-size:28px;font-weight:bold}
.score{color:#aeb8c2;font-size:21px;margin-top:10px}
.details{color:#d4dce2;text-align:left;margin-top:15px;line-height:1.6}
.footer{text-align:center;color:#aeb8c2;margin-top:40px;font-size:14px}
.green{color:#22c77a}.yellow{color:#f5c542}.red{color:#ff4d5a}
.history{text-align:left;background:#182631;padding:15px;margin-top:10px;display:none}
.historyItem{border-bottom:1px solid #40505c;padding:12px 0}
.small{color:#aeb8c2;font-size:14px}
</style>
</head>
<body>
<div class="container">
<h1>VOICE FRAUD DETECTOR</h1>
<div class="subtitle">Voice Recognition + Scam Detection</div>
<button id="voiceBtn" onclick="startVoice()">START VOICE RECOGNITION</button>
<div id="status" class="status">Ready</div>
<h2>Recognized Speech</h2>
<div id="speech" class="speech">No speech recognized yet.</div>
<button onclick="analyzeSpeech()">ANALYZE SPEECH</button>
<div class="card">
<div id="risk" class="risk">RISK LEVEL: --</div>
<div id="score" class="score">Risk Score: 0/100</div>
<div id="details" class="details">No analysis yet.</div>
</div>
<button onclick="showHistory()">VIEW HISTORY</button>
<div id="history" class="history"></div>
<div class="footer">Educational fraud detection prototype</div>
</div>
<script>
let recognizedText = "";

function setStatus(text,color){
    const s=document.getElementById("status");
    s.innerText=text;
    s.style.color=color||"#aeb8c2";
}

function startVoice(){
    const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;

    if(!SpeechRecognition){
        setStatus("Voice recognition not supported. Use Chrome on Android.","#ff4d5a");
        alert("Open this page in Google Chrome and allow microphone permission.");
        return;
    }

    const recognition=new SpeechRecognition();
    const btn=document.getElementById("voiceBtn");

    recognition.lang="en-IN";
    recognition.interimResults=false;
    recognition.continuous=false;
    recognition.maxAlternatives=1;

    btn.disabled=true;
    btn.innerText="LISTENING...";
    setStatus("Listening... Speak now","#22c77a");

    recognition.onresult=function(event){
        recognizedText=event.results[0][0].transcript;
        document.getElementById("speech").innerText=recognizedText;
        setStatus("Voice recognized","#22c77a");
        btn.disabled=false;
        btn.innerText="START VOICE RECOGNITION";
        analyzeSpeech();
    };

    recognition.onerror=function(event){
        setStatus("Voice error: "+event.error,"#ff4d5a");
        btn.disabled=false;
        btn.innerText="START VOICE RECOGNITION";
    };

    recognition.onend=function(){
        btn.disabled=false;
        btn.innerText="START VOICE RECOGNITION";
    };

    try{
        recognition.start();
    }catch(error){
        setStatus("Could not start voice recognition.","#ff4d5a");
        btn.disabled=false;
        btn.innerText="START VOICE RECOGNITION";
    }
}

function analyzeSpeech(){
    if(!recognizedText){
        alert("Please use voice recognition first.");
        return;
    }

    setStatus("Analyzing speech...","#f5c542");

    const t = recognizedText.toLowerCase();
    const rules = {
        "OTP / Verification": ["otp","one time password","verification code","security code","share otp","tell me the otp","give me the otp","share the code","tell me the code"],
        "Bank / Card Information": ["bank account","account number","bank details","card number","debit card","credit card","cvv","atm pin","pin number","banking details"],
        "Payment Request": ["send money","transfer money","send the money","pay now","make a payment","payment required","processing fee","registration fee","upi payment","upi id","send payment","transfer the amount"],
        "Urgency / Threat": ["urgent","very urgent","immediately","act immediately","last warning","account will be blocked","account will be closed","account will be suspended","legal action","police complaint","within 10 minutes","within 5 minutes"],
        "Remote Access": ["remote access","screen sharing","share your screen","screen share","install this app","download this app","anydesk","teamviewer","remote desktop"],
        "Prize / Lottery": ["you have won","you won","lottery","lottery winner","prize money","cash prize","lucky winner","claim your prize"],
        "Fake KYC": ["kyc update","kyc expired","update your kyc","verify your kyc","account verification","bank verification"],
        "Impersonation": ["calling from the bank","i am calling from the bank","bank officer","bank employee","customer care","police officer","cyber crime officer","government officer"]
    };

    let categories = [];
    let matches = [];

    Object.keys(rules).forEach(function(category){
        rules[category].forEach(function(word){
            if(t.includes(word)){
                if(!categories.includes(category)) categories.push(category);
                if(!matches.includes(word)) matches.push(word);
            }
        });
    });

    let score = categories.length * 15 + matches.length * 5;

    if(categories.includes("Bank / Card Information")) score += 10;
    if(categories.includes("Payment Request")) score += 10;
    if(categories.includes("Urgency / Threat")) score += 10;
    if(categories.includes("Payment Request") && categories.includes("Urgency / Threat")) score += 15;
    if(categories.includes("OTP / Verification") && categories.includes("Urgency / Threat")) score += 15;
    if(categories.includes("Remote Access")) score += 15;

    score = Math.min(score,100);

    let level = "LOW RISK";
    if(score >= 70) level = "HIGH RISK";
    else if(score >= 40) level = "MEDIUM RISK";

    document.getElementById("risk").innerText = "RISK LEVEL: " + level;
    document.getElementById("score").innerText = "Risk Score: " + score + "/100";

    const risk = document.getElementById("risk");
    risk.className = "risk";
    if(score >= 70) risk.classList.add("red");
    else if(score >= 40) risk.classList.add("yellow");
    else risk.classList.add("green");

    let details = "";

    if(categories.length){
        details += "<b>Detected indicators:</b><br>";
        categories.forEach(function(x){
            details += "• " + x + "<br>";
        });
        if(matches.length){
            details += "<br><b>Matched terms:</b><br>" + matches.join(", ");
        }
    }else{
        details = "No common scam indicators detected.<br><br>This is an educational rule-based detector and cannot guarantee that a call is safe.";
    }

    document.getElementById("details").innerHTML = details;
    setStatus("Analysis complete","#22c77a");

    // Save history locally in the browser. No Python POST is needed.
    const history = JSON.parse(localStorage.getItem("fraudHistory") || "[]");
    history.push({
        text: recognizedText,
        level: level,
        score: score,
        time: new Date().toLocaleString()
    });
    localStorage.setItem("fraudHistory", JSON.stringify(history));
}

function showHistory(){
    const box=document.getElementById("history");

    if(box.style.display==="block"){
        box.style.display="none";
        return;
    }

    const data=JSON.parse(localStorage.getItem("fraudHistory") || "[]");
    box.innerHTML="";

    if(!data.length){
        box.innerHTML="No detection history yet.";
    }else{
        data.slice().reverse().forEach(function(item){
            const div=document.createElement("div");
            div.className="historyItem";
            div.innerHTML="<b>"+item.level+"</b> — "+item.score+"/100<br><span class='small'>"+item.time+"</span><br><br>"+item.text;
            box.appendChild(div);
        });
    }

    box.style.display="block";
}
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):

    def send_content(self, content, content_type="text/html"):
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self.send_content(HTML)
        elif path == "/history":
            self.send_content(json.dumps(HISTORY), "application/json")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path

        if path != "/analyze":
            self.send_response(404)
            self.end_headers()
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            text = str(data.get("text", "")).strip()

            if text:
                result = analyze(text)
            else:
                result = {
                    "text": "",
                    "level": "LOW RISK",
                    "score": 0,
                    "categories": [],
                    "matches": [],
                    "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                }

            self.send_content(json.dumps(result), "application/json")

        except Exception as error:
            data = json.dumps({"error": str(error)}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def log_message(self, format, *args):
        pass


def main():
    server = HTTPServer((HOST, PORT), Handler)

    print("==========================================")
    print("       VOICE FRAUD DETECTOR")
    print("==========================================")
    print("Server: http://127.0.0.1:8080")
    print("Keep Pydroid running.")
    print("==========================================")

    threading.Thread(
        target=server.serve_forever,
        daemon=True
    ).start()

    try:
        webbrowser.open("http://127.0.0.1:8080")
    except Exception:
        pass

    try:
        while True:
            input()
    except (KeyboardInterrupt, EOFError):
        server.shutdown()


if __name__ == "__main__":
    main()

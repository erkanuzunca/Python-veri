from flask import Flask, render_template
import requests
import urllib3
import json
from jinja2 import Environment
from flask import Flask
app = Flask(__name__)

# Jinja2 filtresini tanımlama
def floatformat(value, places=2):
    return round(value, places)

# Jinja2 çevresini alın ve filtre eklemesi yapın
jinja2_env = Environment()
jinja2_env.filters['floatformat'] = floatformat

# SSL sertifikası doğrulamasını devre dışı bırak
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Token alma URL'si
token_url = "https://efatura.etrsoft.com/fmi/data/v1/databases/testdb/sessions"

# Kullanıcı adı ve şifre
username = "apitest"
password = "test123"

# Token alma isteği için başlıklar
token_headers = {
    "Content-Type": "application/json"
}

# Token alma isteği gönderme
token_response = requests.post(token_url, headers=token_headers, auth=(username, password), verify=False)

# Yanıtı kontrol etme
if token_response.status_code == 200:
    token = token_response.json()["response"]["token"]
    print("Token alındı:", token)
else:
    print("Token alma başarısız oldu. Hata kodu:", token_response.status_code)

# Veri çekme URL'si
data_url = "https://efatura.etrsoft.com/fmi/data/v1/databases/testdb/layouts/testdb/records/1"

# Veri çekme isteği için gönderilecek veri
data_payload = {
    "fieldData": {},
    "script": "getData"
}

# Verileri işleyen işlev

def process_data(data):
    results = {"with_3_digits": {}, "with_5_digits": {}, "with_8_digits": {}}

    for entry in data:
        if "hesap_kodu" in entry and "borc" in entry:
            hesap_kodu = entry["hesap_kodu"]
            borc = entry["borc"]

            try:
                borc = float(borc)
            except ValueError:
                borc = 0.0

            # Hesap kodunu noktalara göre ayır
            parts = hesap_kodu.split(".")

            if len(parts) >= 1:
                results["with_3_digits"][parts[0]] = results["with_3_digits"].get(parts[0], 0) + borc

            if len(parts) >= 2:
                results["with_5_digits"][f"{parts[0]}.{parts[1]}"] = results["with_5_digits"].get(f"{parts[0]}.{parts[1]}", 0) + borc

            if len(parts) >= 3:
                results["with_8_digits"][hesap_kodu] = results["with_8_digits"].get(hesap_kodu, 0) + borc

    return results

# Veri çekme isteği için başlıklar
data_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# Bu fonksiyonu burada tanımlayın
def get_api_data():
    # Veri çekme isteğini gönderme
    data_response = requests.patch(data_url, headers=data_headers, json=data_payload, verify=False)

    # Yanıtı kontrol etme
    if data_response.status_code == 200:
        data = json.loads(data_response.json()["response"]["scriptResult"])
        processed_data = process_data(data)
        return processed_data  # API verilerini döndür

    return None  # Hata durumunda None döndür

@app.route('/')
def index():
    # API'den verileri çekme
    api_data = get_api_data()

    if api_data is not None:
        
        return render_template('index.html', data=api_data)
    else:
        return "API verileri alınamadı."

if __name__ == '__main__':
    app.run(debug=True)
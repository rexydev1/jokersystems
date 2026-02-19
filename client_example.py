import requests

def api_sorgula(arama_tipi, kelime):
    # API Adresi (rexy-services.py dosyasını çalıştırdığında bu adresten yayın yapar)
    url = "http://localhost:5001/api/search"
    
    # Parametreler
    params = {
        "type": arama_tipi,   # log, plaka veya craftrise
        "query": kelime,
        "limit": 10           # İsteğe bağlı limit
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data["success"]:
            print(f"\n--- {arama_tipi.upper()} Sonuçları ({data['count']} adet) ---")
            for result in data["results"]:
                print(f"-> {result}")
        else:
            print(f"Hata: {data['message']}")
            
    except Exception as e:
        print(f"API'ye bağlanılamadı: {e}")

if __name__ == "__main__":
    print("Rexy API Test İstemcisi")
    
    # Örnek sorgular
    aranacak_kelime = input("Aranacak kelimeyi girin: ")
    api_sorgula("log", aranacak_kelime)

from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Yardımcı Fonksiyon: Klasör İçinde Arama Yap
def search_in_folder(folder_name, query, limit=100):
    found = []
    if not os.path.exists(folder_name):
        return found
    
    query = query.lower()
    for filename in os.listdir(folder_name):
        if filename.endswith(".txt"):
            filepath = os.path.join(folder_name, filename)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if query in line.lower():
                            found.append(line.strip())
                            if len(found) >= limit:
                                return found
            except Exception:
                continue
    return found

@app.route('/api/search', methods=['GET'])
def search_api():
    # Parametreleri al: ?type=log&query=isim&limit=10
    search_type = request.args.get('type', 'log')  # log, plaka, craftrise
    query = request.args.get('query', '')
    limit = int(request.args.get('limit', 1000))

    if not query:
        return jsonify({"success": False, "message": "Query parameter is required"}), 400

    # Klasör eşleşmesi
    folder_map = {
        "log": "data",
        "plaka": "plaka",
        "craftrise": "craftrise"
    }

    folder = folder_map.get(search_type)
    if not folder:
        return jsonify({"success": False, "message": "Invalid search type"}), 400

    results = search_in_folder(folder, query, limit)
    
    return jsonify({
        "success": True,
        "type": search_type,
        "query": query,
        "count": len(results),
        "results": results
    })

if __name__ == '__main__':
    print("Rexy Services API Sunucusu Başlatılıyor...")
    print("Adres: http://localhost:1453/api/search?type=log&query=test")
    app.run(debug=True, port=1453)

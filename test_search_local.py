import os

def mock_search(keyword):
    print(f"--- '{keyword}' aranıyor ---")
    data_folder = 'data'
    found = False
    if not os.path.exists(data_folder):
        print("Data klasörü yok!")
        return

    for filename in os.listdir(data_folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(data_folder, filename)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if keyword.lower() in line.lower():
                            print(f"BULUNDU ({filename}): {line.strip()}")
                            found = True
            except Exception as e:
                print(f"Hata: {e}")
    
    if not found:
        print("Sonuç bulunamadı.")
    print("---------------------------------")

if __name__ == "__main__":
    # Test cases
    mock_search("ornek.com")
    mock_search("admin")
    mock_search("olmayanveri")

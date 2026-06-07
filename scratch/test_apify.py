import sys
import os

# Menambahkan root project ke sys.path
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.logic.apify_base import ApifyBase

def main():
    print("=== TEST APIFY LANGSUNG ===")
    
    apify = ApifyBase()
    payload = {
        "searchStringsArray": ["wisata lembang"],
        "language": "id",
        "countryCode": "id",
        "maxCrawledPlacesPerSearch": 2,
        "zoom": 10,
        "includeReviews": True,
        "reviewsMaxCount": 5,
        "reviewsSort": "newest",
        "includeOpeningHours": True,    
        "includeImages": True,
        "maxImageCount": 2,
        "includeWebResults": True       
    }
    
    print(f"Payload: {payload}")
    df = apify.run_actor_sync(payload)
    if df is not None:
        print(f"Banyak data: {len(df)}")
        if not df.empty:
            print(df[['title', 'address']].head())
        else:
            print("Dataframe kosong!")
    else:
        print("DF None")

if __name__ == '__main__':
    main()

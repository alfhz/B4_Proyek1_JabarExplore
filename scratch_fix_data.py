import json
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def fix_data():
    with open('data/data_wisata.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # The first 50 are the original ones. The rest are the scraped ones that didn't match exactly.
    original_items = data[:50]
    scraped_items = data[50:]
    
    # Also collect any original items that ALREADY successfully matched and have photos
    scraped_pool = scraped_items + [item for item in original_items if item['identitas'].get('foto', 'default.png') != 'default.png']
    
    for orig in original_items:
        if orig['identitas'].get('foto', 'default.png') != 'default.png':
            continue # already has a photo
            
        orig_name = orig['identitas']['nama']
        
        # Find the best match from the scraped_pool
        best_match = None
        best_score = 0.0
        
        for scrap in scraped_pool:
            scrap_name = scrap['identitas']['nama']
            
            # Custom word match
            orig_words = set(orig_name.lower().replace('gunung', 'gn').replace('.', '').split())
            scrap_words = set(scrap_name.lower().replace('gunung', 'gn').replace('.', '').split())
            
            common = orig_words.intersection(scrap_words)
            score = len(common) / max(len(orig_words), 1)
            
            # SequenceMatcher score
            seq_score = similar(orig_name, scrap_name)
            
            total_score = score + seq_score
            
            if total_score > best_score:
                best_score = total_score
                best_match = scrap
                
        if best_match and best_score > 0.5:
            print(f"Matching: {orig_name} --> {best_match['identitas']['nama']} (Score: {best_score})")
            orig['identitas']['foto'] = best_match['identitas']['foto']
            orig['identitas']['galeri'] = best_match['identitas'].get('galeri', [])
            
    # Clean up the duplicates! Keep only the original 50 items.
    cleaned_data = original_items
    
    with open('data/data_wisata.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=4)
        
    print(f"Data fixed! Kept {len(cleaned_data)} items.")

if __name__ == '__main__':
    fix_data()

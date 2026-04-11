import uuid
from src.utils.file_handler import buka_json, simpan_json

def tambah_data_wisata(data_baru):
    list_data = buka_json()
    data_baru['id'] = str(uuid.uuid4())[:8] # Generate ID
    list_data.append(data_baru)
    simpan_json(list_data)

def update_data_wisata(id_wisata, data_update):
    list_data = buka_json()
    for i, item in enumerate(list_data):
        if str(item.get('id')) == str(id_wisata):
            data_update['id'] = id_wisata # Tahan ID lama
            list_data[i] = data_update
            simpan_json(list_data)
            return True
    return False

def hapus_data_wisata(id_wisata):
    list_data = buka_json()
    data_filter = [item for item in list_data if str(item.get('id')) != str(id_wisata)]
    simpan_json(data_filter)
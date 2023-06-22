cache = {}

def get_cache(key):
    if key in cache:
        print(f"LA INFORMACIÓN CON CLAVE {key} SE RECUPERÓ DEL CACHÉ")
        return cache[key]
    
    print(f"NO SE ENCONTRÓ NADA CON LA CLAVE {key} EN EL CACHÉ")
    return None


def set_cache(key, value):
    cache[key] = value
    print(f"INFORMACIÓN CON CLAVE {key} GUARDADA EN CACHÉ")
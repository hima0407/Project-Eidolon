import urllib.request
import os

os.makedirs('../xflr5', exist_ok=True)

# Blueprint Airfoils + Trade Study Candidates
airfoils = {
    #baseline
    'naca23012.dat': 'https://m-selig.ae.illinois.edu/ads/coord/naca23012.dat', # Main Wing
    'naca0010.dat':  'https://m-selig.ae.illinois.edu/ads/coord/naca0010.dat',  # Horizontal Tail
    'naca0012.dat':  'https://m-selig.ae.illinois.edu/ads/coord/naca0012.dat',  # Vertical Tail
    
    #newones
    'naca4412.dat':  'https://m-selig.ae.illinois.edu/ads/coord/naca4412.dat',  # High-lift cambered baseline
    'naca2412.dat':  'https://m-selig.ae.illinois.edu/ads/coord/naca2412.dat',  # Cessna 172 standard
    'ls0417.dat':    'https://m-selig.ae.illinois.edu/ads/coord/ls0417.dat'     # GA(W)-1 NASA high-lift
}

print("\n[ EIDOLON AERO ] Expanding Airfoil Library for Trade Study...")

for name, url in airfoils.items():
    filepath = f'../xflr5/{name}'
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f" [+] Acquired: {name}")
    except Exception as e:
        print(f" [!] Error fetching {name}: {e}")

print("\n[ EIDOLON AERO ] Database update complete.\n")

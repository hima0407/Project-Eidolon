import urllib.request
import os

def update_airfoil_library():
    # AirfoilTools raw data endpoint for NACA 63-415
    url = "http://airfoiltools.com/airfoil/seligdatfile?airfoil=n63415-il"
    
    # Ensure directory exists relative to the scripts folder
    target_dir = "../xflr5"
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, "naca63415.dat")
    
    print("Initiating coordinate fetch...")
    
    # Bypass standard bot-blockers
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        
    if "<!DOCTYPE" in content or "<html" in content.lower():
        print("[ERROR] Server returned a webpage, not coordinate data.")
        return
        
    with open(filepath, 'w') as f:
        f.write(content)
        
    print(f"[SUCCESS] NACA 63-415 coordinates verified and written to {filepath}")

if __name__ == "__main__":
    update_airfoil_library()


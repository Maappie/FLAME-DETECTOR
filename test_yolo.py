import cv2

print("Searching for cameras...")

# Test indices 0 through 4
for i in range(5):
    
    # Try with DSHOW backend first
    cap_dshow = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    is_open_dshow = cap_dshow.isOpened()
    if is_open_dshow:
        print(f"--- Camera found at index {i} (using CAP_DSHOW) ---")
        cap_dshow.release()
    
    # Also try with MSMF backend
    cap_msmf = cv2.VideoCapture(i, cv2.CAP_MSMF)
    is_open_msmf = cap_msmf.isOpened()
    if is_open_msmf:
        print(f"--- Camera found at index {i} (using CAP_MSMF) ---")
        cap_msmf.release()

    if not is_open_dshow and not is_open_msmf:
        print(f"No camera found at index {i}")

print("Search complete.")
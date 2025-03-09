import pandas as pd
import numpy as np
import re

def process_data(df):
    OWNER_GROUP_MAPPING = {
        "Timir Chakraborty": "Admin", "Jhuma Roy Chowdhury": "Admin", "Nilanjan Bhattacherjee": "Admin",
        "Barnali Bhattacherjee": "Admin", "Twinkle Barua": "Admin", "Surajit Mukherjee": "Admin",
        "Paritosh Debbarma": "Admin", "Group Leader": "Admin", "Harendranath Ghosh": "Admin",
        "Admin ": "Admin", "Edutrack": "Admin",
        
        "Telecaller 3": "ATL1", "Telecaller 4": "ATL1", "Telecaller 15": "ATL1", "Telecaller 16": "ATL1",
        "Telecaller 17": "ATL1", "Telecaller 22": "ATL1", "Telecaller 25": "ATL1", "Telecaller 27": "ATL1",
        "Telecaller 28": "ATL1", "Telecaller 49": "ATL1", "Telecaller 63": "ATL1", "Telecaller 65": "ATL1",
        
        "Telecaller 1": "TL1", "Telecaller 12": "TL1", "Telecaller 19": "TL1", "Telecaller 21": "TL1",
        "Telecaller 26": "TL1", "Telecaller 41": "TL1", "Telecaller 48": "TL1", "Telecaller 53": "TL1",
        "Telecaller 55": "TL1", "Telecaller 56": "TL1", "Telecaller 60": "TL1", "Telecaller 62": "TL1",
        "Telecaller 64": "TL1", "Telecaller 66": "TL1", "TCE Mousumi": "TL1",

        "Telecaller 5": "TL2", "Telecaller 6": "TL2", "Telecaller 7": "TL2", "Telecaller 13": "TL2",
        "Telecaller 23": "TL2", "Telecaller 45": "TL2", "Telecaller 46": "TL2", "Telecaller 50": "TL2",
        "Telecaller 51": "TL2", "Telecaller 52": "TL2", "Telecaller 54": "TL2", "Telecaller 57": "TL2",
        "Telecaller 58": "TL2", "Telecaller 59": "TL2", "Telecaller 67": "TL2"
    }
    try:
        # Ensure "Owner" column exists before mapping
        if "Owner" in df.columns:
            df["Group"] = df["Owner"].map(OWNER_GROUP_MAPPING).fillna("Unknown")
        else:
            df["Group"] = "Unknown"

        # Ensure "Call Duration" column exists before conversion
        if "Call Duration" in df.columns:
            df["Call Duration Seconds"] = df["Call Duration"].apply(lambda x: convert_duration_to_seconds(str(x)) if pd.notna(x) else np.nan)
        else:
            df["Call Duration Seconds"] = np.nan  # If missing, fill with NaN

        return df  # Return the processed DataFrame
    except Exception as e:
        print(f"Error in process_data: {e}")  # Debugging
        return df  # Return original df to prevent crashes
    
    # Convert Call Duration to seconds

def convert_duration_to_seconds(duration):
    try:
        # Extract numbers using regex (handles cases like "0h:1m:35s" or "1h:20s")
        h, m, s = 0, 0, 0
        match = re.match(r'(?:(\d+)h:)?(?:(\d+)m:)?(?:(\d+)s)?', duration)
        if match:
            h = int(match.group(1) or 0)
            m = int(match.group(2) or 0)
            s = int(match.group(3) or 0)
        return h * 3600 + m * 60 + s
    except Exception as e:
        return np.nan
    


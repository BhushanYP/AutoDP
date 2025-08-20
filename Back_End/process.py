import streamlit as st
import base64
import pandas as pd
import chardet
import os

pd.options.mode.copy_on_write = True

@st.cache_data
def get_base64_webp(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def set_bg_image(image_file: str):
    if not os.path.exists(image_file):
        st.warning(f"Background image '{image_file}' not found.")
        return

    if not image_file.lower().endswith(".webp"):
        st.error("Only WebP format is supported.")
        return

    base64_str = get_base64_webp(image_file)

    st.markdown(f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/webp;base64,{base64_str}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: top;
            background-attachment: fixed;
        }}
        </style>
    """, unsafe_allow_html=True)

def detect_date_columns(df):
    """Detect columns that are likely to contain dates."""
    date_columns = []
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]) or pd.api.types.is_bool_dtype(df[column]):
            continue
        try:
            temp = pd.to_datetime(df[column], errors='coerce')
            if temp.notna().mean() >= 0.8:
                date_columns.append(column)
        except Exception:
            continue
    return date_columns

def normalize_dates(df, column_name):
    """Normalize dates to YYYY-MM-DD format."""
    try:
        df[column_name] = pd.to_datetime(df[column_name], errors='coerce')
        df = df.dropna(subset=[column_name])
        df[column_name] = df[column_name].dt.strftime('%Y-%m-%d')
        return df
    except Exception:
        return df

MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1 GB

def detect_encoding(file, sample_size=32768, samples=3):
    """
    Detects encoding of a file path or file-like object.
    Limits file size to 1 GB for safety.
    """
    try:
        raw_data = b""

        if isinstance(file, str):  # File path
            file_size = os.path.getsize(file)
            if file_size > MAX_FILE_SIZE:
                return None, f"❌ File too large ({file_size / (1024**3):.2f} GB). Limit is 1 GB."

            positions = [0]
            if file_size > sample_size:
                step = file_size // (samples + 1)
                positions.extend(step * i for i in range(1, samples))

            with open(file, "rb") as f:
                chunks = []
                for pos in positions:
                    f.seek(pos)
                    chunks.append(f.read(sample_size))
                raw_data = b"".join(chunks)

        else:  # File-like object
            if hasattr(file, "seek") and hasattr(file, "tell"):
                file.seek(0, 2)
                size = file.tell()
                if size > MAX_FILE_SIZE:
                    return None, f"❌ File too large ({size / (1024**3):.2f} GB). Limit is 1 GB."
                file.seek(0)

            raw_data = file.read(sample_size * samples)
            if hasattr(file, "seek"):
                file.seek(0)

        result = chardet.detect(raw_data)
        encoding = result.get("encoding")
        confidence = result.get("confidence", 0)

        if encoding and confidence >= 0.5:
            return encoding, f"✅ Detected encoding '{encoding}' (confidence {confidence:.2f})"
        else:
            return "utf-8", "⚠️ Low confidence detection. Falling back to 'utf-8'."

    except Exception as e:
        return None, f"❌ Encoding detection failed: {e}"


def read_csv_with_encoding(file):
    """
    Reads a CSV with robust encoding fallback.
    Always returns (DataFrame, message).
    """
    encodings = []
    encoding, msg = detect_encoding(file)
    if encoding:
        encodings.append(encoding)
    encodings.extend(["utf-8", "utf-8-sig", "latin1", "ISO-8859-1", "cp1252"])

    for i, enc in enumerate(encodings):
        try:
            if not isinstance(file, str):
                file.seek(0)  # reset every time
            df = pd.read_csv(file, encoding=enc)

            if not df.empty:
                if i == 0 and "✅" in msg:  
                    return df, msg.replace("✅", "✅ Read successfully with")
                elif i == 0 and "⚠️" in msg:  
                    return df, f"⚠️ Fallback to '{enc}', read successfully"
                else:
                    return df, f"✅ Read successfully with fallback encoding '{enc}'"
        except Exception:
            continue

    # Last resort
    try:
        if not isinstance(file, str):
            file.seek(0)
        df = pd.read_csv(file, encoding="utf-8", errors="ignore")
        return df, "⚠️ Forced read with utf-8 (errors ignored)"
    except Exception as e:
        return pd.DataFrame(), f"❌ Completely failed to read CSV: {e}"


def remove_outliers_iqr(df, columns=None, factor=1.5):
    # Automatically use all numeric columns if none specified
    if columns is None:
        columns = df.select_dtypes(include='number').columns
    else:
        # Keep only numeric columns from the user-specified list
        columns = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]

    # Initialize mask as all True (keep all rows initially)
    mask = pd.Series(True, index=df.index)

    for col in columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - factor * IQR
        upper_bound = Q3 + factor * IQR

        # Update mask: keep only rows within bounds for this column
        mask &= df[col].between(lower_bound, upper_bound)

    return df[mask]




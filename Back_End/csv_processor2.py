import pandas as pd
import chardet
import io
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from datetime import datetime

pd.options.mode.copy_on_write = True


def detect_encoding(file):
    try:
        if isinstance(file, str):
            with open(file, "rb") as f:
                result = chardet.detect(f.read(100000))
        else:
            result = chardet.detect(file.read(100000))
            file.seek(0)
        return result["encoding"]
    except Exception as e:
        print(f"Encoding detection error: {e}")
        return None


import pandas as pd
import chardet

def detect_encoding(file, sample_size=10000):
    """Detect encoding from file path or file-like object."""
    if isinstance(file, (str, os.PathLike)):
        # File path case
        with open(file, "rb") as f:
            raw_data = f.read(sample_size)
    else:
        # File-like object (e.g. UploadedFile)
        raw_data = file.read(sample_size)
        file.seek(0)  # reset pointer for next read
    
    result = chardet.detect(raw_data)
    return result.get("encoding")

def read_csv_with_encoding(file, sample_size=None):
    detected_encoding = detect_encoding(file)
    if detected_encoding is None:
        return None, "Encoding detection failed."

    try:
        df = pd.read_csv(
            file,
            encoding=detected_encoding,
            nrows=sample_size,
            sep=None,
            engine="python"
        )
    except Exception:
        # fallback encoding
        try:
            if isinstance(file, (str, os.PathLike)):
                df = pd.read_csv(file, encoding="ISO-8859-1", nrows=sample_size, sep=None, engine="python")
            else:
                file.seek(0)
                df = pd.read_csv(file, encoding="ISO-8859-1", nrows=sample_size, sep=None, engine="python")
        except Exception as e2:
            return None, f"Encoding Error: {e2}"

    if df.empty or len(df.columns) <= 1:
        try:
            if not isinstance(file, (str, os.PathLike)):
                file.seek(0)
            df = pd.read_csv(file, encoding=detected_encoding, header=None, sep=None, engine="python")
        except Exception as e:
            return None, f"Final Read Error: {e}"

    return df, None

def add_table_of_contents(p):
    p.setFont("Helvetica-Bold", 18)
    p.drawString(180, 750, "Table of Contents")

    p.setFont("Helvetica", 12)
    toc_items = [
        "1. Dataset Summary",
        "2. Correlation Heatmap",
        "3. Correlated Feature Comparisons",
        "4. Numeric Column Visualizations",
        "5. Categorical Column Visualizations",
        "6. Date/Time Column Visualizations"
    ]

    y = 710
    for item in toc_items:
        p.drawString(70, y, item)
        y -= 20

    p.showPage()

def add_dataset_summary(df, column_types, p):
    p.setFont("Helvetica-Bold", 18)
    p.drawString(180, 750, "Dataset Summary")

    p.setFont("Helvetica", 12)
    y = 720
    p.drawString(50, y, f"Total Rows: {len(df)}")
    y -= 20
    p.drawString(50, y, f"Total Columns: {df.shape[1]}")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Column Type Distribution:")
    y -= 20
    p.setFont("Helvetica", 12)
    for key, cols in column_types.items():
        p.drawString(70, y, f"{key.capitalize()}: {len(cols)}")
        y -= 20

    y -= 10
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Missing Value Summary:")
    y -= 20
    p.setFont("Helvetica", 10)
    nulls = df.isnull().sum()
    for col in df.columns:
        missing_pct = 100 * nulls[col] / len(df)
        if missing_pct > 0:
            p.drawString(70, y, f"{col}: {missing_pct:.1f}% missing")
            y -= 15
            if y < 100:
                p.showPage()
                y = 750

    p.showPage()

def detect_column_types(df):
    column_types = {
        'numeric': [],
        'categorical': [],
        'datetime': [],
        'boolean': [],
        'text': [],
        'unsupported': []
    }

    for col in df.columns:
        dtype = df[col].dtype

        if pd.api.types.is_numeric_dtype(dtype):
            column_types['numeric'].append(col)
        elif pd.api.types.is_bool_dtype(dtype):
            column_types['boolean'].append(col)
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            column_types['datetime'].append(col)
        elif pd.api.types.is_object_dtype(dtype):
            try:
                converted = pd.to_datetime(df[col], errors='raise')
                df[col] = converted
                column_types['datetime'].append(col)
            except:
                unique_ratio = df[col].nunique() / max(1, len(df[col]))
                if unique_ratio < 0.5:
                    column_types['categorical'].append(col)
                else:
                    column_types['text'].append(col)
        else:
            column_types['unsupported'].append(col)

    return column_types, df


def draw_image_on_canvas(p, img_buffer, y_position, height=300):
    img = ImageReader(img_buffer)
    p.drawImage(img, 50, y_position - height, width=500, height=height, preserveAspectRatio=True)
    y_position -= (height + 20)
    if y_position < 100:
        p.showPage()
        y_position = 750
    return y_position

def generate_histograms(df, p):
    plot_count = 0
    for col in df.columns:
        try:
            plt.figure(figsize=(10, 5))
            if pd.api.types.is_integer_dtype(df[col]) and df[col].nunique() < 20:
                sns.countplot(x=df[col])
            else:
                sns.histplot(df[col], kde=True, color='blue', bins=30)
            plt.title(f"Histogram for {col}")
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100)
            img_buffer.seek(0)
            plt.close()
            plot_count = draw_plot_with_limit(p, img_buffer, plot_count)
        except Exception as e:
            print(f"Failed histogram for {col}: {e}")
    return plot_count

def generate_bar_charts(df, p):
    plot_count = 0
    for col in df.columns:
        try:
            counts = df[col].value_counts().nlargest(10)
            if counts.empty:
                continue
            plt.figure(figsize=(10, 5))
            sns.barplot(x=counts.values, y=counts.index, hue=counts.index, palette="Set2", legend=False)
            plt.title(f"Top Categories in {col}")
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100)
            img_buffer.seek(0)
            plt.close()
            plot_count = draw_plot_with_limit(p, img_buffer, plot_count)
        except Exception as e:
            print(f"Failed bar chart for {col}: {e}")
    return plot_count

def generate_time_series(df, p):
    plot_count = 0
    for col in df.columns:
        try:
            time_counts = df[col].dt.to_period("M").value_counts().sort_index()
            if time_counts.empty:
                continue
            plt.figure(figsize=(12, 5))
            time_counts.plot(kind='bar')
            plt.title(f"Records Over Time in {col}")
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100)
            img_buffer.seek(0)
            plt.close()
            plot_count = draw_plot_with_limit(p, img_buffer, plot_count)
        except Exception as e:
            print(f"Failed time series for {col}: {e}")
    return plot_count

def generate_correlation_heatmap(df, p, y_position):
    corr_matrix = df.corr(numeric_only=True)
    plt.figure(figsize=(12, 7))
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', cbar=True)
    plt.title("Correlation Heatmap")
    plt.tight_layout()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100)
    img_buffer.seek(0)
    plt.close()

    return draw_image_on_canvas(p, img_buffer, y_position)

def generate_correlation_pair_plots(df, p, y_position, threshold=0.5):
    corr_matrix = df.corr(numeric_only=True)
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

    correlated_pairs = [
        (row, col, upper.loc[row, col])
        for row in upper.index
        for col in upper.columns
        if not pd.isna(upper.loc[row, col]) and abs(upper.loc[row, col]) >= threshold
    ]

    if not correlated_pairs:
        p.setFont("Helvetica", 10)
        p.drawString(50, y_position, "No significantly correlated pairs found (|corr| >= 0.5).")
        return y_position

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, f"Top Correlated Feature Pairs (|corr| ≥ {threshold})")
    y_position -= 30

    plot_count = 0
    for col1, col2, corr_value in correlated_pairs[:5]:
        plt.figure(figsize=(8, 5))
        sns.regplot(data=df, x=col1, y=col2, line_kws={"color": "red"})
        plt.title(f"{col1} vs {col2} (corr = {corr_value:.2f})")
        plt.tight_layout()
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100)
        img_buffer.seek(0)
        plt.close()
        plot_count = draw_plot_with_limit(p, img_buffer, plot_count)
    return y_position

def draw_plot_with_limit(p, img_buffer, plot_count, max_per_page=2):
    width, height = letter
    y_position = height - 300 if plot_count % max_per_page == 0 else height - 600
    img = ImageReader(img_buffer)
    p.drawImage(img, 50, y_position, width=500, height=250)
    plot_count += 1
    if plot_count % max_per_page == 0:
        p.showPage()
    return plot_count

def generate_boxplots(df, p):
    plot_count = 0
    for col in df.columns:
        try:
            plt.figure(figsize=(10, 5))
            sns.boxplot(x=df[col], color='orange')
            plt.title(f"Boxplot for {col}")
            plt.tight_layout()
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=100)
            img_buffer.seek(0)
            plt.close()
            plot_count = draw_plot_with_limit(p, img_buffer, plot_count)
        except Exception as e:
            print(f"Failed boxplot for {col}: {e}")
    return plot_count

def process_file(file, sample_size=None):
    df, error = read_csv_with_encoding(file, sample_size)
    if error:
        return None, error

    try:
        column_types, df = detect_column_types(df)

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y_position = height - 50

        # Title Page
        p.setFont("Helvetica-Bold", 20)
        p.drawString(180, y_position, "CSV Analysis Report")
        y_position -= 30
        p.setFont("Helvetica", 10)
        p.drawString(180, y_position, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        p.showPage()
        y_position = height - 50

        # Add table_of_contents
        add_table_of_contents(p)
        add_dataset_summary(df, column_types, p)

        # Correlation Heatmap
        y_position = generate_correlation_heatmap(df, p, y_position)
        p.showPage()
        y_position = height - 30

        # Correlation Heatmap pairs
        y_position = generate_correlation_pair_plots(df, p, y_position, threshold=0.5)
        p.showPage()
        y_position = height - 30

        generate_histograms(df[column_types['numeric']], p)
        p.showPage()

        generate_bar_charts(df[column_types['categorical']], p)
        p.showPage()

        generate_time_series(df[column_types['datetime']], p)
        p.showPage()

        # Boxplots for outlier detection
        if column_types['numeric']:
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y_position, "Boxplots for Outlier Detection")
            y_position -= 30
            generate_boxplots(df[column_types['numeric']], p)
            y_position = height - 30

        p.save()
        buffer.seek(0)
        return buffer

    except Exception as e:
        print(f"An error occurred: {e}")

        return None, f"Processing error: {e}"


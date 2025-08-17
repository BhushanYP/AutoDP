import pandas as pd
import io
import process
import joblib

pd.options.mode.copy_on_write = True

def process_file(file, model_path):
    """Process a CSV file and make predictions using a saved pipeline model."""
    # Step 1: Read CSV file with encoding detection
    try:
        df, error = process.read_csv_with_encoding(file)
        if error:
            return None, f"CSV read error: {error}"
    except Exception as e:
        return None, f"Unexpected error while reading CSV: {e}"

    # Step 2: Load model pipeline package
    try:
        model_package = joblib.load(model_path)
    except Exception as e:
        return None, f"Failed to load model from '{model_path}': {e}"

    pipeline = model_package.get('pipeline')
    if pipeline is None:
        return None, "Model package does not contain a 'pipeline'."

    y_scaler = model_package.get('y_scaler', None)
    task_type = model_package.get('task_type', 'regression')  # Default to regression
    model_name = model_package.get('model_name', 'Unknown')
    model_params = model_package.get('model_params', {})

    print(f"Model used: {model_name}")
    print(f"Hyperparameters: {model_params}")

    # Step 3: Make predictions
    try:
        predictions = pipeline.predict(df)
    except Exception as e:
        return None, f"Prediction failed: {e}"

    df_result = df.copy()

    if task_type == 'regression':
        # If needed, reshape predictions and reverse scaling
        if y_scaler is not None:
            try:
                if predictions.ndim == 1:
                    predictions = predictions.reshape(-1, 1)
                predictions = y_scaler.inverse_transform(predictions).ravel()
            except Exception as e:
                return None, f"Failed to inverse transform regression predictions: {e}"
        df_result['Predictions'] = predictions

    elif task_type == 'classification':
        try:
            df_result['Predicted Class'] = predictions
            # Add class probabilities if available
            if hasattr(pipeline, 'predict_proba'):
                proba = pipeline.predict_proba(df)
                class_labels = pipeline.classes_
                for i, label in enumerate(class_labels):
                    df_result[f'Prob_{label}'] = proba[:, i]
        except Exception as e:
            return None, f"Classification prediction error: {e}"

    else:
        return None, f"Unsupported task type: '{task_type}'"

    # Step 4: Write output to CSV in memory
    try:
        csv_output = io.StringIO()
        df_result.to_csv(csv_output, index=False)
        csv_output.seek(0)
    except Exception as e:
        return None, f"Failed to write output CSV: {e}"

    # Step 5: Return results and metadata
    return csv_output, {
        'model_name': model_name,
        'model_params': model_params,
        'task_type': task_type
    }
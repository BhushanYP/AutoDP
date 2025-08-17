import numpy as np
import logging
from sklearn.preprocessing import LabelEncoder, StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import warnings
import sys
import os
import joblib

sys.path.append(os.path.dirname(__file__))
from Back_End import process

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)

def get_target_column(df):
    return df.columns[-1]

def preprocess_data(df, target_col):
    X = df.drop(columns=[target_col])
    y = df[target_col]

    task_type = None
    y_scaler = None
    y_original = y.copy()

    if not np.issubdtype(y.dtype, np.number):
        task_type = 'classification'
        y = LabelEncoder().fit_transform(y)
    elif y.nunique() <= 5:
        task_type = 'classification'
    else:
        task_type = 'regression'
        y_scaler = StandardScaler()
        y = y_scaler.fit_transform(y.values.reshape(-1, 1)).ravel()

    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(include=['object', 'bool']).columns.tolist()

    transformers = []
    if numeric_cols:
        transformers.append(('num', StandardScaler(), numeric_cols))
    if categorical_cols:
        transformers.append(('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols))

    preprocessor = ColumnTransformer(transformers)

    return X, y, task_type, y_scaler, preprocessor, y_original

def train_and_evaluate_models(X, y, task_type, preprocessor, y_scaler=None):
    import numpy as np
    import logging
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import GridSearchCV, cross_val_score
    from sklearn.linear_model import LogisticRegression, LinearRegression
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
    from sklearn.svm import SVC, SVR
    from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
    from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
    from sklearn.neural_network import MLPClassifier, MLPRegressor

    logging.basicConfig(level=logging.INFO)

    # Optional: Try importing XGBoost
    try:
        from xgboost import XGBClassifier, XGBRegressor
        has_xgboost = True
    except ImportError:
        has_xgboost = False

    # Define models
    models = {
        'Logistic Regression': LogisticRegression() if task_type == 'classification' else None,
        'Linear Regression': LinearRegression() if task_type == 'regression' else None,
        'Random Forest': RandomForestClassifier() if task_type == 'classification' else RandomForestRegressor(),
        'SVM': SVC() if task_type == 'classification' else SVR(),
        'Decision Tree': DecisionTreeClassifier() if task_type == 'classification' else DecisionTreeRegressor(),
        'K-Nearest Neighbors': KNeighborsClassifier() if task_type == 'classification' else KNeighborsRegressor(),
        'Gradient Boosting': GradientBoostingClassifier() if task_type == 'classification' else GradientBoostingRegressor(),
        'MLP (Neural Net)': MLPClassifier(max_iter=500) if task_type == 'classification' else MLPRegressor(max_iter=500),
        'XGBoost': XGBClassifier(use_label_encoder=False, eval_metric='logloss') if task_type == 'classification' and has_xgboost else 
                   XGBRegressor() if task_type == 'regression' and has_xgboost else None
    }

    # Define hyperparameter grids
    param_grids = {
        'Random Forest': {'model__n_estimators': [50, 100], 'model__max_depth': [None, 10]},
        'SVM': {'model__C': [0.1, 1, 10], 'model__kernel': ['linear', 'rbf']} if task_type == 'classification' else {'model__C': [0.1, 1, 10], 'model__epsilon': [0.01, 0.1, 1]},
        'Decision Tree': {'model__max_depth': [None, 5, 10]},
        'K-Nearest Neighbors': {'model__n_neighbors': [3, 5, 7]},
        'Gradient Boosting': {'model__n_estimators': [100], 'model__learning_rate': [0.01, 0.1]},
        'MLP (Neural Net)': {'model__hidden_layer_sizes': [(50,), (100,)], 'model__alpha': [0.0001, 0.001]},
        'XGBoost': {'model__n_estimators': [100], 'model__learning_rate': [0.01, 0.1]} if has_xgboost else {}
    }

    scoring = 'f1_weighted' if task_type == 'classification' else 'r2'

    best_model = None
    best_score = -np.inf
    best_model_name = None
    best_params = None
    all_results = {}

    for name, model in models.items():
        if model is None:
            continue

        logging.info(f"Training model: {name}")

        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('model', model)
        ])

        grid_params = param_grids.get(name, {})

        if grid_params:
            grid = GridSearchCV(pipeline, grid_params, cv=5, scoring=scoring, n_jobs=-1)
            grid.fit(X, y)
            trained_model = grid.best_estimator_
            score = grid.best_score_
            params = grid.best_params_
            std = None  # GridSearchCV doesn’t expose std directly
        else:
            scores = cross_val_score(pipeline, X, y, cv=5, scoring=scoring)
            score = scores.mean()
            std = scores.std()
            trained_model = pipeline.fit(X, y)
            params = None

        all_results[name] = {
            'score': score,
            'std': std,
            'params': params,
            'model': trained_model
        }

        if score > best_score:
            best_score = score
            best_model = trained_model
            best_model_name = name
            best_params = params

    return best_model, best_model_name, best_score, best_params, all_results

def process_file(file):
    df, error = process.read_csv_with_encoding(file)
    if error:
        return error

    df = process.remove_outliers_iqr(df)

    target_col = get_target_column(df)
    X, y, inferred_task_type, y_scaler, preprocessor, y_original = preprocess_data(df, target_col)

    best_model, best_model_name, best_score, best_params, all_results = train_and_evaluate_models(X, y, inferred_task_type, preprocessor, y_scaler)

    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', best_model.named_steps['model'] if hasattr(best_model, 'named_steps') else best_model)
    ])

    model_filename = "best_model.pkl"
    model_package = {
    'pipeline': pipeline,
    'y_scaler': y_scaler,
    'task_type': inferred_task_type,
    'model_name': best_model_name,
    'model_params': best_params
    }

    joblib.dump(model_package, model_filename)

    return model_filename, best_model_name, best_score, best_params
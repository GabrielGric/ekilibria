run-sintetico:
	python3 generate_synthetic_dataset.py

run-auth:
	python3 google_suite/auth/authenticate_google_user.py

run-features:
	python3 google_suite/services/extract_features.py

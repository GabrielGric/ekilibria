run-sintetico:
	python3 generate_synthetic_dataset.py

run-auth:
	python3 ekilibria/google_suite/auth/authenticate_google_user.py

run-features:
	python3 ekilibria/google_suite/services/extract_features.py --from 2025-06-16 --to 2025-06-25

run-api:
	uvicorn ekilibria.api.fast:app --reload

run-streamlit:
	streamlit run ekilibria/interface/streamlit_app.py

run-streamlit2:
	streamlit run ekilibria/interface/streamlit_app_v2.py

run-streamlit3:
	streamlit run ekilibria/interface/streamlit_app_v3.py


reinstall_package:
	@pip uninstall -y ekilibria || :
	@pip install -e .

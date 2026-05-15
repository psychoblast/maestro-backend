.PHONY: help verify-seeds-in-image build-test

IMAGE ?= plmkr-test

help:
	@echo "Targets:"
	@echo "  build-test              — Build Docker image locally (no push)"
	@echo "  verify-seeds-in-image   — Confirm seed scripts are present inside built image"

build-test:
	docker build --no-cache -t $(IMAGE) .

# Confirm all three seed scripts are present in the Docker image at /app.
# Run after 'make build-test'. Does not start the app or touch any database.
verify-seeds-in-image: ## Confirm seed_*.py files exist in /app inside the built image
	@echo "=== Checking seed scripts in image $(IMAGE) ==="
	docker run --rm $(IMAGE) ls /app/seed_curators.py /app/seed_pr_contacts.py /app/seed_booking_contacts.py
	@echo "=== All three seed scripts confirmed present in image ==="

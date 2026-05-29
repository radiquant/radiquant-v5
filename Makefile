.PHONY: verify check-bootstrap

verify: check-bootstrap

check-bootstrap:
	python3 scripts/verify_bootstrap.py

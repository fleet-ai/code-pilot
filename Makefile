.PHONY: docs code

docs:
	@echo "Running read_and_upsert with library name: $(lib_name)"
	@python scripts.py --libray_name=$(lib_name)

code:
	@echo "Cloning repository from GitHub link: $(gh_link)"
	@git clone $(gh_link)
	@python scripts.py --code
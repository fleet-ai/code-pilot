.PHONY: docs code

docs:
	@echo "Running read_and_upsert with library name: $(library_name)"
	@python scripts.py --library_name=$(library_name)

code:
	@echo "Cloning repository from GitHub link: $(url)"
	@mkdir -p src_code && cd src_code && git clone $(url)
	@python scripts.py --code
all help test-system test-dev test-ifx test-all summary clean:
	@$(MAKE) -C pr $@

provenance-check:
	@python3 scripts/check_testsuite_provenance.py --top 50

provenance-check-all:
	@python3 scripts/check_testsuite_provenance.py --scope all --top 50

.DEFAULT:
	@$(MAKE) -C pr $@

.PHONY: all help test-system test-dev test-ifx test-all summary provenance-check provenance-check-all clean

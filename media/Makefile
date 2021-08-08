all: overview.svg

.PHONY: all

%.pdf: %.tex
	$(eval BUILDDIR := $(shell mktemp -d "build-XXXXXXXXX"))
	xelatex -output-directory=$(BUILDDIR) $<
	mv $(BUILDDIR)/$@ $@
	rm -rf $(BUILDDIR)

%.svg: %.pdf
	pdf2svg $< $@
	svgo --pretty $@ -o $@.min
	mv $@.min $@

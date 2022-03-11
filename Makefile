#/***************************************************************************
# TmcAlgorithms
#
# Export clusters to DXF
#							 -------------------
#		begin				: 2020-09-16
#		git sha				: $Format:%H$
#		copyright			: (C) 2020 by Basil Eric Rabi
#		email				: basil.rabi@tmc.nickelasia.com
# ***************************************************************************/
#
#/***************************************************************************
# *																		    *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or	    *
# *   (at your option) any later version.								    *
# *																		    *
# ***************************************************************************/


PLUGINNAME = tmc_algorithms
PY_FILES = __init__.py \
	$(PLUGINNAME).py \
	$(PLUGINNAME)_provider.py
EXTRAS = metadata.txt 
PLUGINDIR=$(HOME)/.local/share/QGIS/QGIS3/profiles/default/python/plugins/$(PLUGINNAME)


.PHONY: default
default:
	@echo "TMC Algorithms"

deploy:
	@echo "Installing plugin..."
	mkdir -p $(PLUGINDIR)
	cp -vf $(PY_FILES) $(PLUGINDIR)/
	cp -vf $(EXTRAS) $(PLUGINDIR)/
	cp -rvf algorithm $(PLUGINDIR)/
	cp -rvf lib $(PLUGINDIR)/

dclean:
	find $(PLUGINDIR) -iname ".git" -prune -exec rm -Rf {} \;

derase:
	rm -Rf $(PLUGINDIR)

zip: deploy dclean
	rm -f $(PLUGINNAME).zip
	cd $(PLUGINDIR); cd ..; zip -9r $(CURDIR)/$(PLUGINNAME).zip $(PLUGINNAME)


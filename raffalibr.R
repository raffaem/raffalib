#!/usr/bin/env R

chwd2curr <- function(fnc, cont) {
	# Change WD to current file
	# - source and knit
	srcdir <- getSrcDirectory(fnc)[1]
	if (srcdir != "") {
		print("Using getSrcDirectory")
	}
	else {
		# - run
		print("Using rstudioapi")
		srcdir <- dirname(cont$path)
	}
	setwd(srcdir)
	print(paste0("Working directory changed to: ", srcdir))
	return(srcdir)
}

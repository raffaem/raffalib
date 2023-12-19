#!/usr/bin/env R

#' CWD to current file's dir
#'
#' Change the current working directory 
#' to the directory in which the script we are running resides.
#'
#' @param fnc A function that takes no argument and returns nothing (\code{function(){}})
#' @param verbose Whether to print debug messages
#' @param fatal Whether to call stop() if we can't get the directory of the currently running script
#' 
#' @importFrom utils getSrcDirectory
#' 
#' @return None
#'
#' @examples
#' chwd2curr(function(){})
#'
#' @export
chwd2curr <- function(fnc, verbose=TRUE, fatal=FALSE) {
  requireNamespace("rstudioapi")
	# Change WD to current file
	# - source and knit
  srcdirl <- utils::getSrcDirectory(fnc)
  if (length(srcdirl)>0) {
    srcdir <- srcdirl[1]
    if(srcdir == "") {
      srcdir <- NULL
    }
  }
  else {
    srcdir <- NULL
  }
	if ( is.null(srcdir) ) {
	  if(verbose) {
	    print("Using rstudioapi")
	  }
	  srcdir <- tryCatch({
	      cont <- rstudioapi::getActiveDocumentContext()
	      srcdir <- dirname(cont$path)
	    },
	    error=function(cond){
	      NULL
	  })
	}
  else if(verbose) {
      print("Using utils::getSrcDirectory")
  }
  
  if(is.null(srcdir)) {
    if(fatal) {
      stop("Cannot get current working directory")
    }
    else if(verbose) {
      print("Cannot get current working directory")
    }
    return()
  }
  
	setwd(srcdir)
	if(verbose) {
	  print(paste0("Working directory changed to: ", srcdir)) 
	}
}

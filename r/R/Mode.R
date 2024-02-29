#' Compute the mode of a vector
#' see: https://stackoverflow.com/a/8189441/1719931
#'
#' @param x a vector
#'
#' @return the mode
#'
#' @export
Mode <- function(x) {
  ux <- unique(x)
  ux[which.max(tabulate(match(x, ux)))]
}

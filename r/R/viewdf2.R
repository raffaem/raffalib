#' View dataframe with Javascript Datatables library
#' with server-side rendering
#'
#' @param df A dataframe
#'
#' @return None
#'
#' @export
viewdf2 <- function(df, ...) {
  dtss(df2dt(df, ...))
}

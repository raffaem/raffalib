#' Convert a dataframe to DT::datatable for visualization
#'
#' @param df A dataframe
#' @param to_truncate Text columns too long that needs to be truncated
#' @param truncate_max An integer with maximum length of a string before it is truncated
#' @param truncate_max_title An integer representing the maximum length of the substring in tooltip
#' @param types_in_colnames A boolean equal to TRUE if datatypes should be appended to column names
#' @param filter Position of the filter widgets
#' @param to_round A character vector with numeric colum names that have to be rounded
#' @param to_round_digits Maximum number of digits for rounded columns
#'
#' @return a DT::datatable
#'
#' @export
df2dt <- function(df,
                   to_truncate = NULL,
                   truncate_max = 10,
                   truncate_max_title = 200,
                   types_in_colnames = TRUE,
                   filter = "top",
                   to_round = NULL,
                   to_round_digits = 2) {
  # column names to display
  newcolnames <- colnames(df)
  for (i in seq(1, length(newcolnames))) {
    newcolnames[i] <- stringr::str_replace_all(newcolnames[i], "_", " ")
  }
  if (types_in_colnames) {
    for (i in seq(1, length(colnames(df)))) {
      col <- colnames(df)[i]
      newcolnames[i] <- paste0(
        newcolnames[i],
        "\n{",
        class(df[[col]]),
        "}"
      )
    }
  }
  # We need to replace NA values with a character value
  # for columns we are going to truncate,
  # otherwise DT crashes and show an empty table
  to_truncate_ix <- which(colnames(df) %in% to_truncate)
  l <- list()
  for (el in to_truncate) {
    l[[el]] <- "NA"
  }
  df %<>% tidyr::replace_na(l)
  # Generate DT table
  dtobj <- DT::datatable(df,
    colnames = newcolnames,
    filter = filter,
    options = list(
      pageLength = 20,
      filter = "top",
      autoWidth = TRUE,
      columnDefs = list(list(
        targets = to_truncate_ix,
        render = DT::JS(
          "function(data, type, row, meta) {",
          "return type === 'display' && ",
          "data.length > ", truncate_max, " ?",
          "'<span title=\"' + ",
          "data.substr(0,", truncate_max_title, ") + ",
          "'...\">' + ",
          "data.substr(0, ", truncate_max, ") + ",
          "'...</span>' : data;",
          "}"
        )
      ))
    )
  )
  # Round number columns
  for (col in to_round) {
    dtobj %<>% DT::formatRound(col, to_round_digits)
  }
  return(dtobj)
}

